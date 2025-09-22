from flask import Blueprint, jsonify, request
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy import func, case, text

from src.extensions import db
from src.models.integrate_test_model import IntegrateTest
from src.auth.decorators import require_auth, require_role

integrate_tests_bp = Blueprint('integrate_tests_bp', __name__, url_prefix='/api/integrate_tests')

# 配置日志
logger = logging.getLogger(__name__)

@integrate_tests_bp.route('', methods=['POST'])
def create_integrate_test():
    """创建新的集成测试记录"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        # 验证必填字段
        error, status = validate_required_fields(json_data)
        if error:
            return jsonify(error), status
        
        logger.info(f"Creating integrate test for SN: {json_data['product_sn']}")
        
        new_test = IntegrateTest()
        populate_test_fields(new_test, json_data)
        
        db.session.add(new_test)
        db.session.commit()
        
        logger.info(f"Integrate test created successfully with ID: {new_test.id}")
        return jsonify(new_test.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error creating integrate test: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500





@require_auth()
@integrate_tests_bp.route('', methods=['GET'])
def get_all_integrate_tests():
    """获取所有集成测试记录 (自动过滤已删除)"""
    try:
        # 添加分页支持
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # 限制最大每页数量
        
        # 添加排序支持
        sort_by = request.args.get('sort_by', 'update_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 添加筛选支持 - 修改字段名
        product_sn = request.args.get('product_sn')
        integrate_test_result = request.args.get('integrate_test_result')
        
        # 时间范围筛选参数（支持 YYYY-MM-DD 或 ISO 格式）
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 使用 IntegrateTest.query 会自动过滤 is_deleted=False
        query = IntegrateTest.query

        # 应用时间范围筛选（基于 create_time 字段）
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(IntegrateTest.create_time >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD or ISO format'}), 400

        if end_date:
            try:
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                # 如果是日期格式，包含当天的所有记录
                if 'T' not in end_date:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(IntegrateTest.create_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400

        # 应用筛选条件
        if product_sn:
            query = query.filter(IntegrateTest.product_sn.like(f'%{product_sn}%'))

        if integrate_test_result:
            query = query.filter(IntegrateTest.integrate_test_result == integrate_test_result)
        
        # 应用排序
        if hasattr(IntegrateTest, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(IntegrateTest, sort_by).desc())
            else:
                query = query.order_by(getattr(IntegrateTest, sort_by).asc())
        
        # 分页查询
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'data': [test.to_dict() for test in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    except Exception as e:
        logger.error(f"Error fetching integrate tests: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500




@require_auth()
@integrate_tests_bp.route('/<string:test_id>', methods=['GET'])
def get_integrate_test(test_id):
    """获取特定ID的集成测试记录"""
    try:
        # 使用 IntegrateTest.query 会自动过滤 is_deleted=False
        test = IntegrateTest.query.filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'Integrate test record not found'}), 404
        return jsonify(test.to_dict())
    except Exception as e:
        logger.error(f"Error fetching integrate test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500











@require_role('admin')
@integrate_tests_bp.route('/<string:test_id>', methods=['PUT'])
def update_integrate_test(test_id):
    """更新特定ID的集成测试记录"""
    try:
        # 使用 IntegrateTest.query 会自动过滤 is_deleted=False
        test = IntegrateTest.query.filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'Integrate test record not found'}), 404
        
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        logger.info(f"Updating integrate test ID: {test_id}")
        
        populate_test_fields(test, json_data, is_update=True)
        
        db.session.commit()
        
        logger.info(f"Integrate test updated successfully: {test_id}")
        return jsonify(test.to_dict())
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error updating test {test_id}: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating integrate test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500







@require_role('admin')
@integrate_tests_bp.route('/<string:test_id>', methods=['DELETE'])
def delete_integrate_test(test_id):
    """软删除特定ID的集成测试记录"""
    try:
        # 使用 db.session.query 绕过 ActiveQuery，确保能找到记录
        test = db.session.query(IntegrateTest).filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'Integrate test record not found'}), 404
        
        if test.is_deleted:
            return jsonify({'message': 'Record already deleted'}), 200

        logger.info(f"Soft-deleting integrate test ID: {test_id}")
        
        # 执行软删除
        test.is_deleted = True
        test.delete_time = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Integrate test soft-deleted successfully: {test_id}")
        return jsonify({'message': 'Integrate test record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting integrate test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500















@require_auth()
@integrate_tests_bp.route('/stats', methods=['GET'])
def get_integrate_test_stats():
    """
    获取集成测试统计信息
    
    支持的查询参数:
    - start_date: 开始日期 (格式: YYYY-MM-DD 或 ISO格式)
    - end_date: 结束日期 (格式: YYYY-MM-DD 或 ISO格式) 
    - product_sn: 产品序列号 (支持模糊匹配)
    
    返回格式:
    {
        "total_count": 总记录数,
        "success_count": 成功记录数,
        "fail_count": 失败记录数,
        "breakdown": {"pass": 10, "fail": 5},
        "filters": {...}
    }
    """
    try:
        # 获取可选的筛选条件
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        product_sn = request.args.get('product_sn')
        integrate_test_result = request.args.get('integrate_test_result')
        
        # 构建基础查询，自动过滤软删除记录
        query = IntegrateTest.query.filter(IntegrateTest.is_deleted == False)
        
        # 应用时间范围筛选（基于create_time字段）
        if start_date:
            try:
                # 支持多种日期格式
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(IntegrateTest.create_time >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        if end_date:
            try:
                # 结束日期加1天，确保包含当天的所有记录
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                if 'T' not in end_date:  # 如果是日期格式，则包含当天23:59:59
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(IntegrateTest.create_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 应用产品序列号筛选（模糊匹配）
        if product_sn:
            query = query.filter(IntegrateTest.product_sn.like(f'%{product_sn}%'))

        if integrate_test_result:
            query = query.filter(IntegrateTest.integrate_test_result == integrate_test_result)

        # 使用单次聚合查询获取所有统计数据，提高查询效率
        # 一次查询同时获取总数和各状态的统计
        stats_result = db.session.query(
            func.count(IntegrateTest.id).label('total_count'),
            func.sum(case((IntegrateTest.integrate_test_result == 'pass', 1), else_=0)).label('success_count'),
            func.sum(case((IntegrateTest.integrate_test_result == 'fail', 1), else_=0)).label('fail_count')
        ).filter(query.whereclause if query.whereclause is not None else True).one()
        
        # 获取详细的状态分组统计（用于breakdown）
        breakdown_stats = db.session.query(
            IntegrateTest.integrate_test_result,
            func.count(IntegrateTest.id).label('count')
        ).filter(query.whereclause if query.whereclause is not None else True
        ).group_by(IntegrateTest.integrate_test_result).all()
        
        # 转换结果为字典格式
        total_count = int(stats_result.total_count or 0)
        success_count = int(stats_result.success_count or 0)
        fail_count = int(stats_result.fail_count or 0)
        
        # 构建详细分组统计
        breakdown = {}
        for result, count in breakdown_stats:
            breakdown[result or 'unknown'] = int(count)
        
        # 计算其他状态的记录数
        other_count = total_count - success_count - fail_count
        
        # 构建返回结果
        response_data = {
            'total_count': total_count,
            'success_count': success_count,
            'fail_count': fail_count,
            'other_count': other_count,
            'breakdown': breakdown,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'product_sn': product_sn
            }
        }
        
        logger.info(f"Integrate test stats query completed. Total: {total_count}, Success: {success_count}, Fail: {fail_count}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching integrate test stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500































@require_auth()
@integrate_tests_bp.route('/boards-stats', methods=['GET'])
def get_integrate_board_stats():
    """
    获取集成测试产品维度的统计信息
    
    支持的查询参数:
    - start_date: 开始日期 (格式: YYYY-MM-DD 或 ISO格式)
    - end_date: 结束日期 (格式: YYYY-MM-DD 或 ISO格式)
    
    返回格式:
    {
        "test_stats": {
            "total_tests": 总测试次数,
            "success_tests": 成功测试次数,
            "fail_tests": 失败测试次数
        },
        "product_stats": {
            "total_products": 总产品数,
            "success_products": 成功产品数,
            "fail_products": 失败产品数,
            "success_breakdown": {
                "always_success": 一直成功的产品数,
                "final_success": 最终成功的产品数(有过失败)
            },
            "fail_breakdown": {
                "always_fail": 一直失败的产品数,
                "final_fail": 最终失败的产品数(有过成功)
            }
        },
        "filters": {...}
    }
    """
    try:
        # 获取筛选条件
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 构建时间筛选条件
        time_filter = ""
        params = {}
        
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                time_filter += " AND create_time >= :start_date"
                params['start_date'] = start_dt
            except ValueError:
                return jsonify({'error': 'Invalid start_date format'}), 400
        
        if end_date:
            try:
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                if 'T' not in end_date:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                time_filter += " AND create_time <= :end_date"
                params['end_date'] = end_dt
            except ValueError:
                return jsonify({'error': 'Invalid end_date format'}), 400
        
        # 1. 测试记录维度统计
        test_stats_sql = text(f"""
        SELECT 
            COUNT(*) as total_tests,
            SUM(CASE WHEN integrate_test_result = 'pass' THEN 1 ELSE 0 END) as success_tests,
            SUM(CASE WHEN integrate_test_result = 'fail' THEN 1 ELSE 0 END) as fail_tests
        FROM integrate_tests 
        WHERE is_deleted = 0 {time_filter}
        """)
        
        test_result = db.session.execute(test_stats_sql, params).fetchone()
        
        # 2. 产品维度统计 - 使用窗口函数获取每个产品的最新测试结果
        product_stats_sql = text(f"""
        WITH latest_tests AS (
            SELECT 
                product_sn,
                integrate_test_result,
                ROW_NUMBER() OVER (PARTITION BY product_sn ORDER BY create_time DESC) as rn
            FROM integrate_tests 
            WHERE is_deleted = 0 {time_filter}
        ),
        product_history AS (
            SELECT 
                product_sn,
                COUNT(*) as total_tests,
                SUM(CASE WHEN integrate_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN integrate_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count
            FROM integrate_tests 
            WHERE is_deleted = 0 {time_filter}
            GROUP BY product_sn
        )
        SELECT 
            COUNT(DISTINCT l.product_sn) as total_products,
            SUM(CASE WHEN l.integrate_test_result = 'pass' THEN 1 ELSE 0 END) as success_products,
            SUM(CASE WHEN l.integrate_test_result = 'fail' THEN 1 ELSE 0 END) as fail_products,
            -- 一直成功的产品：最新是成功且从未失败
            SUM(CASE 
                WHEN l.integrate_test_result = 'pass' AND h.fail_count = 0 
                THEN 1 ELSE 0 
            END) as always_success_products,
            -- 最终成功的产品：最新是成功但有过失败
            SUM(CASE 
                WHEN l.integrate_test_result = 'pass' AND h.fail_count > 0 
                THEN 1 ELSE 0 
            END) as final_success_products,
            -- 一直失败的产品：最新是失败且从未成功
            SUM(CASE 
                WHEN l.integrate_test_result = 'fail' AND h.success_count = 0 
                THEN 1 ELSE 0 
            END) as always_fail_products,
            -- 最终失败的产品：最新是失败但有过成功
            SUM(CASE 
                WHEN l.integrate_test_result = 'fail' AND h.success_count > 0 
                THEN 1 ELSE 0 
            END) as final_fail_products
        FROM latest_tests l
        JOIN product_history h ON l.product_sn = h.product_sn
        WHERE l.rn = 1
        """)
        
        product_result = db.session.execute(product_stats_sql, params).fetchone()
        
        # 构建返回结果
        response_data = {
            'test_stats': {
                'total_tests': int(test_result.total_tests or 0),
                'success_tests': int(test_result.success_tests or 0),
                'fail_tests': int(test_result.fail_tests or 0)
            },
            'product_stats': {
                'total_products': int(product_result.total_products or 0),
                'success_products': int(product_result.success_products or 0),
                'fail_products': int(product_result.fail_products or 0),
                'success_breakdown': {
                    'always_success': int(product_result.always_success_products or 0),
                    'final_success': int(product_result.final_success_products or 0)
                },
                'fail_breakdown': {
                    'always_fail': int(product_result.always_fail_products or 0),
                    'final_fail': int(product_result.final_fail_products or 0)
                }
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
        
        logger.info(f"Integrate test product stats completed. Total products: {product_result.total_products}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching integrate test product stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500





















# 辅助函数
def parse_datetime(date_str):
    """解析日期时间字符串"""
    if not date_str:
        return None
    try:
        # 支持多种日期时间格式
        if 'T' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise ValueError(f"Invalid datetime format: {date_str}")

def populate_test_fields(test, json_data, is_update=False):
    """填充集成测试对象字段"""
    # 基本字段 - 修改字段名
    if not is_update or 'product_sn' in json_data:
        test.product_sn = json_data.get('product_sn', test.product_sn if is_update else None)
    test.integrate_test_result = json_data.get('integrate_test_result', test.integrate_test_result if is_update else 'PENDING')
    
    # 测试结果字段（是否通过测试）
    test.driver_status_result = json_data.get('driver_status_result', test.driver_status_result if is_update else None)
    test.motor_speed_result = json_data.get('motor_speed_result', test.motor_speed_result if is_update else None)
    test.ipm_temperature_result = json_data.get('ipm_temperature_result', test.ipm_temperature_result if is_update else None)
    test.dc_voltage_result = json_data.get('dc_voltage_result', test.dc_voltage_result if is_update else None)
    test.output_power_result = json_data.get('output_power_result', test.output_power_result if is_update else None)
    test.driver_software_version_result = json_data.get('driver_software_version_result', test.driver_software_version_result if is_update else None)
    test.ac_voltage_result = json_data.get('ac_voltage_result', test.ac_voltage_result if is_update else None)
    test.current_result = json_data.get('current_result', test.current_result if is_update else None)
    test.power_result = json_data.get('power_result', test.power_result if is_update else None)
    test.power_factor_result = json_data.get('power_factor_result', test.power_factor_result if is_update else None)
    test.leakage_current_result = json_data.get('leakage_current_result', test.leakage_current_result if is_update else None)
    
    # 测试数值字段（实际测试数据）
    test.driver_status = json_data.get('driver_status', test.driver_status if is_update else None)
    test.motor_speed = json_data.get('motor_speed', test.motor_speed if is_update else None)
    test.ipm_temperature = json_data.get('ipm_temperature', test.ipm_temperature if is_update else None)
    test.dc_voltage = json_data.get('dc_voltage', test.dc_voltage if is_update else None)
    test.output_power = json_data.get('output_power', test.output_power if is_update else None)
    test.driver_software_version = json_data.get('driver_software_version', test.driver_software_version if is_update else None)
    test.ac_voltage = json_data.get('ac_voltage', test.ac_voltage if is_update else None)
    test.current = json_data.get('current', test.current if is_update else None)
    test.power = json_data.get('power', test.power if is_update else None)
    test.power_factor = json_data.get('power_factor', test.power_factor if is_update else None)
    test.leakage_current = json_data.get('leakage_current', test.leakage_current if is_update else None)
    
    # 测试运行时间相关
    if 'test_runtime' in json_data:
        # 确保 test_runtime 是整数类型
        try:
            test.test_runtime = int(json_data['test_runtime']) if json_data['test_runtime'] is not None else None
        except (ValueError, TypeError):
            raise ValueError("test_runtime must be an integer (seconds)")
    elif not is_update:
        test.test_runtime = None
    
    # 时间信息
    test.start_time = parse_datetime(json_data.get('test_start_time')) if 'test_start_time' in json_data else (test.start_time if is_update else None)
    test.end_time = parse_datetime(json_data.get('test_end_time')) if 'test_end_time' in json_data else (test.end_time if is_update else None)

    # 描述信息 - 新增字段
    test.test_description = json_data.get('test_description', test.test_description if is_update else None)
    test.remark = json_data.get('remark', test.remark if is_update else None)
    
    # 网络信息 - 新增字段
    test.local_ip = json_data.get('local_ip', test.local_ip if is_update else None)
    test.public_ip = json_data.get('public_ip', test.public_ip if is_update else None)
    test.hostname = json_data.get('hostname', test.hostname if is_update else None)
    test.app_version = json_data.get('app_version', test.app_version if is_update else '1.0.0')

    test.ipm_temperature_data_id = json_data.get('ipm_temperature_data_id', test.ipm_temperature_data_id if is_update else None)

def validate_required_fields(json_data):
    """验证必填字段"""
    if 'product_sn' not in json_data or not json_data['product_sn']:
        return {'error': 'product_sn is required'}, 400
    
    if len(json_data['product_sn']) > 32:
        return {'error': 'product_sn too long (max 32 characters)'}, 400
    
    # 验证 test_runtime 如果提供的话必须是整数
    if 'test_runtime' in json_data and json_data['test_runtime'] is not None:
        try:
            int(json_data['test_runtime'])
        except (ValueError, TypeError):
            return {'error': 'test_runtime must be an integer (seconds)'}, 400
    
    return None, None



































@require_auth()
@integrate_tests_bp.route('/sn-stats', methods=['GET'])
def get_integrate_sn_stats():
    """
    获取集成测试的序列号统计信息 (产品维度)
    每个产品一行数据，测试结果=该产品最新一次测试的结果
    
    查询参数:
    - start_date: 开始日期 (YYYY-MM-DD，北京时间)
    - end_date: 结束日期 (YYYY-MM-DD，北京时间)
    - product_sn: 产品序列号筛选 (部分匹配)
    - latest_result: 筛选最新测试结果 (pass/fail)
    - sort_by: 排序字段 (product_sn, total_tests, pass_count, fail_count, pass_rate, latest_test_time, first_test_time, latest_result)
    - sort_order: 排序方向 (asc, desc，默认desc)
    - page: 页码 (默认: 1)
    - per_page: 每页记录数 (默认: 10, 最大: 100)
    
    返回格式:
    {
        "sn_stats": [
            {
                "product_sn": "序列号",
                "total_tests": 总测试次数,
                "pass_count": 成功次数,
                "fail_count": 失败次数,
                "pass_rate": 成功率百分比,
                "latest_test_time": "最新测试时间(北京时间)",
                "first_test_time": "首次测试时间(北京时间)",
                "latest_result": "最新测试结果(pass/fail)"
            }
        ],
        "pagination": {
            "page": 当前页码,
            "per_page": 每页记录数,
            "total": 总序列号数量,
            "pages": 总页数
        },
        "filters": {...}
    }
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        product_sn = request.args.get('product_sn')
        latest_result = request.args.get('latest_result')  # pass/fail
        sort_by = request.args.get('sort_by', 'latest_test_time')
        sort_order = request.args.get('sort_order', 'desc')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)

        # 验证参数
        if sort_by not in ['product_sn', 'total_tests', 'pass_count', 'fail_count', 'pass_rate', 
                          'latest_test_time', 'first_test_time', 'latest_result']:
            return jsonify({'error': f'Invalid sort_by parameter: {sort_by}'}), 400
        
        if sort_order not in ['asc', 'desc']:
            return jsonify({'error': f'Invalid sort_order parameter: {sort_order}'}), 400
        
        if latest_result and latest_result not in ['pass', 'fail']:
            return jsonify({'error': f'Invalid latest_result parameter: {latest_result}'}), 400

        # 构建 CTE 查询以优化性能
        cte_conditions = ["it.is_deleted = FALSE"]
        
        # 时间范围条件（北京时间转UTC）
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                # 北京时间转UTC（减8小时）
                if start_dt.tzinfo is None:
                    start_dt = start_dt - timedelta(hours=8)
                cte_conditions.append(f"it.create_time >= '{start_dt.isoformat()}'")
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        if end_date:
            try:
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                if 'T' not in end_date:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                # 北京时间转UTC（减8小时）
                if end_dt.tzinfo is None:
                    end_dt = end_dt - timedelta(hours=8)
                cte_conditions.append(f"it.create_time <= '{end_dt.isoformat()}'")
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 序列号筛选条件
        if product_sn:
            cte_conditions.append(f"it.product_sn LIKE '%{product_sn}%'")

        # 构建CTE查询
        cte_where_clause = " AND ".join(cte_conditions)
        
        # 排序字段映射
        sort_field_map = {
            'product_sn': 'product_sn',
            'total_tests': 'total_tests',
            'pass_count': 'pass_count',
            'fail_count': 'fail_count', 
            'pass_rate': 'pass_rate',
            'latest_test_time': 'latest_test_time',
            'first_test_time': 'first_test_time',
            'latest_result': 'latest_result'
        }
        
        # 使用board-centric CTE模式，每个产品序列号只返回一行
        stats_query = f"""
        WITH latest_test_per_board AS (
            SELECT 
                it.product_sn,
                it.integrate_test_result,
                CONVERT_TZ(it.create_time, '+00:00', '+08:00') as local_create_time,
                ROW_NUMBER() OVER (PARTITION BY it.product_sn ORDER BY it.create_time DESC) as rn
            FROM integrate_tests it
            WHERE {cte_where_clause}
              AND it.product_sn IS NOT NULL 
              AND it.product_sn != ''
        ),
        board_stats AS (
            SELECT 
                it.product_sn,
                COUNT(*) as total_tests,
                SUM(CASE WHEN it.integrate_test_result = 'pass' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN it.integrate_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count,
                ROUND(
                    (SUM(CASE WHEN it.integrate_test_result = 'pass' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                    2
                ) as pass_rate,
                MAX(CONVERT_TZ(it.create_time, '+00:00', '+08:00')) as latest_test_time,
                MIN(CONVERT_TZ(it.create_time, '+00:00', '+08:00')) as first_test_time
            FROM integrate_tests it
            WHERE {cte_where_clause}
              AND it.product_sn IS NOT NULL 
              AND it.product_sn != ''
            GROUP BY it.product_sn
        ),
        final_stats AS (
            SELECT 
                bs.*,
                lt.integrate_test_result as latest_result
            FROM board_stats bs
            JOIN latest_test_per_board lt ON bs.product_sn = lt.product_sn AND lt.rn = 1"""
        
        # 添加latest_result过滤
        if latest_result:
            stats_query += f"""
            WHERE lt.integrate_test_result = '{latest_result}'"""
        
        stats_query += f"""
        )
        SELECT * FROM final_stats
        ORDER BY {sort_field_map[sort_by]} {sort_order.upper()}
        LIMIT {per_page} OFFSET {(page - 1) * per_page}
        """
        
        # 执行统计查询
        result = db.session.execute(text(stats_query))
        sn_stats_data = [dict(row._mapping) for row in result]
        
        # 获取总数统计（用于分页） - 考虑latest_result过滤
        if latest_result:
            count_query = f"""
            WITH latest_test_per_board AS (
                SELECT 
                    it.product_sn,
                    it.integrate_test_result,
                    ROW_NUMBER() OVER (PARTITION BY it.product_sn ORDER BY it.create_time DESC) as rn
                FROM integrate_tests it
                WHERE {cte_where_clause}
                  AND it.product_sn IS NOT NULL 
                  AND it.product_sn != ''
            )
            SELECT COUNT(*) as total_sn_count 
            FROM latest_test_per_board 
            WHERE rn = 1 AND integrate_test_result = '{latest_result}'
            """
        else:
            count_query = f"""
            SELECT COUNT(DISTINCT it.product_sn) as total_sn_count
            FROM integrate_tests it
            WHERE {cte_where_clause}
              AND it.product_sn IS NOT NULL 
              AND it.product_sn != ''
            """
        
        count_result = db.session.execute(text(count_query))
        total_sn_count = count_result.scalar()
        
        # 格式化返回数据
        formatted_stats = []
        for row in sn_stats_data:
            formatted_stats.append({
                'product_sn': row['product_sn'],
                'total_tests': int(row['total_tests']),
                'pass_count': int(row['pass_count']),
                'fail_count': int(row['fail_count']),
                'pass_rate': float(row['pass_rate']),
                'latest_test_time': row['latest_test_time'].isoformat() if row['latest_test_time'] else None,
                'first_test_time': row['first_test_time'].isoformat() if row['first_test_time'] else None,
                'latest_result': row['latest_result']
            })
        
        # 构建分页信息
        total_pages = (total_sn_count + per_page - 1) // per_page
        
        response_data = {
            'sn_stats': formatted_stats,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_sn_count,
                'pages': total_pages
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'product_sn': product_sn,
                'latest_result': latest_result,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
        
        logger.info(f"Integrate test SN stats query completed. Found {len(formatted_stats)} SN records, total SNs: {total_sn_count}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching integrate test SN stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
















@require_auth()
@integrate_tests_bp.route('/time-stats', methods=['GET'])
def get_integrate_time_stats():
    """
    获取集成测试时间趋势统计信息
    
    支持的查询参数:
    - start_date: 开始日期 (格式: YYYY-MM-DD，北京时间)
    - end_date: 结束日期 (格式: YYYY-MM-DD，北京时间)
    - interval: 统计间隔 (day, week, month，默认day)
    
    返回格式:
    {
        "time_stats": [
            {
                "time_period": "2024-01-15",
                "total_tests": 25,
                "success_count": 20,
                "fail_count": 5
            }
        ],
        "filters": {
            "start_date": "2024-01-15",
            "end_date": "2024-01-21",
            "interval": "day"
        }
    }
    """
    try:
        # 获取查询参数
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        interval = request.args.get('interval', 'day').lower()
        
        # 验证时间间隔参数
        valid_intervals = ['day', 'week', 'month']
        if interval not in valid_intervals:
            return jsonify({'error': f'Invalid interval. Must be one of: {", ".join(valid_intervals)}'}), 400

        # 设置默认时间范围（如果未提供）
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # 解析时间范围并转换为UTC（前端传入北京时间）
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            
            # 北京时间转UTC（减8小时）
            start_dt = start_dt - timedelta(hours=8)
            end_dt = end_dt - timedelta(hours=8)
                
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD format'}), 400

        # 构建筛选条件
        conditions = ["it.is_deleted = FALSE"]
        conditions.append(f"it.create_time >= '{start_dt.isoformat()}'")
        conditions.append(f"it.create_time <= '{end_dt.isoformat()}'")

        # 根据间隔类型设置时间格式化（转换回北京时间显示）
        interval_formats = {
            'day': "DATE_FORMAT(CONVERT_TZ(it.create_time, '+00:00', '+08:00'), '%Y-%m-%d')",
            'week': "DATE_FORMAT(DATE_SUB(CONVERT_TZ(it.create_time, '+00:00', '+08:00'), INTERVAL WEEKDAY(CONVERT_TZ(it.create_time, '+00:00', '+08:00')) DAY), '%Y-%m-%d')",
            'month': "DATE_FORMAT(CONVERT_TZ(it.create_time, '+00:00', '+08:00'), '%Y-%m-01')"
        }
        
        time_group = interval_formats[interval]
        where_clause = " AND ".join(conditions)
        
        # 使用 CTE 构建时间趋势查询
        stats_query = f"""
        WITH filtered_tests AS (
            SELECT 
                it.integrate_test_result,
                {time_group} as time_period
            FROM integrate_tests it
            WHERE {where_clause}
        ),
        time_aggregates AS (
            SELECT 
                time_period,
                COUNT(*) as total_tests,
                SUM(CASE WHEN integrate_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN integrate_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count
            FROM filtered_tests
            GROUP BY time_period
            ORDER BY time_period ASC
        )
        SELECT * FROM time_aggregates
        """
        
        # 执行统计查询
        result = db.session.execute(text(stats_query))
        time_stats_data = [dict(row._mapping) for row in result]
        
        # 格式化返回数据
        formatted_stats = []
        for row in time_stats_data:
            formatted_stats.append({
                'time_period': str(row['time_period']),
                'total_tests': int(row['total_tests']),
                'success_count': int(row['success_count']),
                'fail_count': int(row['fail_count'])
            })
        
        response_data = {
            'time_stats': formatted_stats,
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'interval': interval
            }
        }
        
        logger.info(f"Integrate test time stats query completed. Found {len(formatted_stats)} time periods")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching integrate test time stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500