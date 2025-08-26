from flask import Blueprint, jsonify, request
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy import func, case, text  # 确保导入了 text

from src.extensions import db
from src.models.driver_board_test_model import DriverBoardTest

from src.auth.decorators import require_auth, require_role




driver_board_tests_bp = Blueprint('driver_board_tests_bp', __name__, url_prefix='/api/driver_board_tests')

# 配置日志
logger = logging.getLogger(__name__)





@driver_board_tests_bp.route('', methods=['POST'])
def create_driver_board_test():
    """创建新的驱动板测试记录"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        # 验证必填字段
        error, status = validate_required_fields(json_data)
        if error:
            return jsonify(error), status
        
        logger.info(f"Creating driver board test for SN: {json_data['driver_board_sn']}")
        
        new_test = DriverBoardTest()
        populate_test_fields(new_test, json_data)
        
        db.session.add(new_test)
        db.session.commit()
        
        logger.info(f"Driver board test created successfully with ID: {new_test.id}")
        return jsonify(new_test.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error creating driver board test: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500













@require_auth()
@driver_board_tests_bp.route('', methods=['GET'])
def get_all_driver_board_tests():
    """获取所有驱动板测试记录 (自动过滤已删除)"""
    try:
        # 添加分页支持
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 添加排序支持
        sort_by = request.args.get('sort_by', 'update_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 修复字段名称
        driver_board_sn = request.args.get('driver_board_sn')
        driver_test_result = request.args.get('driver_test_result')

        # 时间范围筛选参数（支持 YYYY-MM-DD 或 ISO 格式）
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 使用 DriverBoardTest.query 会自动过滤 is_deleted=False
        query = DriverBoardTest.query
        
        # 应用时间范围筛选（基于 create_time 字段）
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(DriverBoardTest.create_time >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        if end_date:
            try:
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                # 如果是日期格式，包含当天的所有记录
                if 'T' not in end_date:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(DriverBoardTest.create_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400




        # 应用筛选条件
        if driver_board_sn:
            query = query.filter(DriverBoardTest.driver_board_sn.like(f'%{driver_board_sn}%'))
        if driver_test_result:
            query = query.filter(DriverBoardTest.driver_test_result == driver_test_result)
        
        # 应用排序
        if hasattr(DriverBoardTest, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(DriverBoardTest, sort_by).desc())
            else:
                query = query.order_by(getattr(DriverBoardTest, sort_by).asc())
        
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
        logger.error(f"Error fetching driver board tests: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
















@require_auth()
@driver_board_tests_bp.route('/<string:test_id>', methods=['GET'])
def get_driver_board_test(test_id):
    """获取特定ID的驱动板测试记录"""
    try:
        # 使用 DriverBoardTest.query 会自动过滤 is_deleted=False
        test = DriverBoardTest.query.filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'Driver board test record not found'}), 404
        return jsonify(test.to_dict())
    except Exception as e:
        logger.error(f"Error fetching driver board test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@driver_board_tests_bp.route('/<string:test_id>', methods=['PUT'])
def update_driver_board_test(test_id):
    """更新特定ID的驱动板测试记录"""
    try:
        # 使用 DriverBoardTest.query 会自动过滤 is_deleted=False
        test = DriverBoardTest.query.filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'Driver board test record not found'}), 404
        
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        logger.info(f"Updating driver board test ID: {test_id}")
        
        populate_test_fields(test, json_data, is_update=True)
        
        db.session.commit()
        
        logger.info(f"Driver board test updated successfully: {test_id}")
        return jsonify(test.to_dict())
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error updating test {test_id}: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating driver board test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500







@require_role('admin')
@driver_board_tests_bp.route('/<string:test_id>', methods=['DELETE'])
def delete_driver_board_test(test_id):
    """软删除特定ID的驱动板测试记录"""
    try:
        # 使用 db.session.query 绕过 ActiveQuery，确保能找到记录
        test = db.session.query(DriverBoardTest).filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'Driver board test record not found'}), 404
        
        if test.is_deleted:
            return jsonify({'message': 'Record already deleted'}), 200

        logger.info(f"Soft-deleting driver board test ID: {test_id}")
        
        # 执行软删除
        test.is_deleted = True
        test.delete_time = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Driver board test soft-deleted successfully: {test_id}")
        return jsonify({'message': 'Driver board test record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting driver board test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500











@require_auth()
@driver_board_tests_bp.route('/stats', methods=['GET'])
def get_driver_board_test_stats():
    """
    获取驱动板测试统计信息
    
    支持的查询参数:
    - start_date: 开始日期 (格式: YYYY-MM-DD 或 ISO格式)
    - end_date: 结束日期 (格式: YYYY-MM-DD 或 ISO格式) 
    - driver_board_sn: 驱动板序列号 (支持模糊匹配)
    
    返回格式:
    {
        "total_count": 总记录数,
        "success_count": 成功记录数,
        "fail_count": 失败记录数,
        "other_count": 其他状态记录数,
        "breakdown": {"pass": 10, "fail": 5},
        "filters": {...}
    }
    """
    try:
        # 获取可选的筛选条件
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        driver_board_sn = request.args.get('driver_board_sn')
        driver_test_result = request.args.get('driver_test_result')

        # 构建基础查询，自动过滤软删除记录
        query = DriverBoardTest.query.filter(DriverBoardTest.is_deleted == False)
        
        # 应用时间范围筛选（基于create_time字段）
        if start_date:
            try:
                # 支持多种日期格式
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                # 如果没有时区信息，假设是北京时间，转换为UTC
                if start_dt.tzinfo is None:
                    # 假设输入是北京时间(UTC+8)，转换为UTC
                    start_dt = start_dt - timedelta(hours=8)
                query = query.filter(DriverBoardTest.create_time >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        if end_date:
            try:
                # 结束日期加1天，确保包含当天的所有记录
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                if 'T' not in end_date:  # 如果是日期格式，则包含当天23:59:59
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                # 如果没有时区信息，假设是北京时间，转换为UTC
                if end_dt.tzinfo is None:
                    # 假设输入是北京时间(UTC+8)，转换为UTC
                    end_dt = end_dt - timedelta(hours=8)
                query = query.filter(DriverBoardTest.create_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 应用驱动板序列号筛选（模糊匹配）
        if driver_board_sn:
            query = query.filter(DriverBoardTest.driver_board_sn.like(f'%{driver_board_sn}%'))

        if driver_test_result:
            query = query.filter(DriverBoardTest.driver_test_result == driver_test_result)

        # 使用单次聚合查询获取所有统计数据，提高查询效率
        # 一次查询同时获取总数和各状态的统计
        stats_result = db.session.query(
            func.count(DriverBoardTest.id).label('total_count'),
            func.sum(case((DriverBoardTest.driver_test_result == 'pass', 1), else_=0)).label('success_count'),
            func.sum(case((DriverBoardTest.driver_test_result == 'fail', 1), else_=0)).label('fail_count'),
        ).filter(query.whereclause if query.whereclause is not None else True).one()
        
        # 获取详细的状态分组统计（用于breakdown）
        breakdown_stats = db.session.query(
            DriverBoardTest.driver_test_result,
            func.count(DriverBoardTest.id).label('count')
        ).filter(query.whereclause if query.whereclause is not None else True
        ).group_by(DriverBoardTest.driver_test_result).all()
        
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
                'driver_board_sn': driver_board_sn
            }
        }
        
        logger.info(f"Driver board test stats query completed. Total: {total_count}, Success: {success_count}, Fail: {fail_count}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching driver board test stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500









@require_auth()
@driver_board_tests_bp.route('/boards-stats', methods=['GET'])
def get_driver_board_stats():
    """
    获取驱动板子维度的统计信息
    
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
        "board_stats": {
            "total_boards": 总板子数,
            "success_boards": 成功板子数,
            "fail_boards": 失败板子数,
            "success_breakdown": {
                "always_success": 一直成功的板子数,
                "final_success": 最终成功的板子数(有过失败)
            },
            "fail_breakdown": {
                "always_fail": 一直失败的板子数,
                "final_fail": 最终失败的板子数(有过成功)
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
            SUM(CASE WHEN driver_test_result = 'pass' THEN 1 ELSE 0 END) as success_tests,
            SUM(CASE WHEN driver_test_result = 'fail' THEN 1 ELSE 0 END) as fail_tests
        FROM driver_board_tests 
        WHERE is_deleted = 0 {time_filter}
        """)
        
        test_result = db.session.execute(test_stats_sql, params).fetchone()
        
        # 2. 板子维度统计 - 使用窗口函数获取每个板子的最新测试结果
        board_stats_sql = text(f"""
        WITH latest_tests AS (
            SELECT 
                driver_board_sn,
                driver_test_result,
                ROW_NUMBER() OVER (PARTITION BY driver_board_sn ORDER BY create_time DESC) as rn
            FROM driver_board_tests 
            WHERE is_deleted = 0 {time_filter}
        ),
        board_history AS (
            SELECT 
                driver_board_sn,
                COUNT(*) as total_tests,
                SUM(CASE WHEN driver_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN driver_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count
            FROM driver_board_tests 
            WHERE is_deleted = 0 {time_filter}
            GROUP BY driver_board_sn
        )
        SELECT 
            COUNT(DISTINCT l.driver_board_sn) as total_boards,
            SUM(CASE WHEN l.driver_test_result = 'pass' THEN 1 ELSE 0 END) as success_boards,
            SUM(CASE WHEN l.driver_test_result = 'fail' THEN 1 ELSE 0 END) as fail_boards,
            -- 一直成功的板子：最新是成功且从未失败
            SUM(CASE 
                WHEN l.driver_test_result = 'pass' AND h.fail_count = 0 
                THEN 1 ELSE 0 
            END) as always_success_boards,
            -- 最终成功的板子：最新是成功但有过失败
            SUM(CASE 
                WHEN l.driver_test_result = 'pass' AND h.fail_count > 0 
                THEN 1 ELSE 0 
            END) as final_success_boards,
            -- 一直失败的板子：最新是失败且从未成功
            SUM(CASE 
                WHEN l.driver_test_result = 'fail' AND h.success_count = 0 
                THEN 1 ELSE 0 
            END) as always_fail_boards,
            -- 最终失败的板子：最新是失败但有过成功
            SUM(CASE 
                WHEN l.driver_test_result = 'fail' AND h.success_count > 0 
                THEN 1 ELSE 0 
            END) as final_fail_boards
        FROM latest_tests l
        JOIN board_history h ON l.driver_board_sn = h.driver_board_sn
        WHERE l.rn = 1
        """)
        
        board_result = db.session.execute(board_stats_sql, params).fetchone()
        
        # 构建返回结果
        response_data = {
            'test_stats': {
                'total_tests': int(test_result.total_tests or 0),
                'success_tests': int(test_result.success_tests or 0),
                'fail_tests': int(test_result.fail_tests or 0)
            },
            'board_stats': {
                'total_boards': int(board_result.total_boards or 0),
                'success_boards': int(board_result.success_boards or 0),
                'fail_boards': int(board_result.fail_boards or 0),
                'success_breakdown': {
                    'always_success': int(board_result.always_success_boards or 0),
                    'final_success': int(board_result.final_success_boards or 0)
                },
                'fail_breakdown': {
                    'always_fail': int(board_result.always_fail_boards or 0),
                    'final_fail': int(board_result.final_fail_boards or 0)
                }
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date
            }
        }
        
        logger.info(f"Driver board stats completed. Total boards: {board_result.total_boards}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching driver board stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


















@require_auth()
@driver_board_tests_bp.route('/sn-stats', methods=['GET'])
def get_driver_board_sn_stats():
    """
    获取驱动板测试的序列号统计信息
    包含每个序列号的测试次数、成功率、最新测试时间等
    
    查询参数:
    - start_date: 开始日期 (YYYY-MM-DD，北京时间)
    - end_date: 结束日期 (YYYY-MM-DD，北京时间)
    - driver_board_sn: 驱动板序列号筛选 (部分匹配)
    - driver_test_result: 测试结果筛选 (pass/fail)
    - page: 页码 (默认: 1)
    - per_page: 每页记录数 (默认: 10, 最大: 100)
    
    返回格式:
    {
        "sn_stats": [
            {
                "driver_board_sn": "序列号",
                "total_tests": 总测试次数,
                "success_count": 成功次数,
                "fail_count": 失败次数,
                "success_rate": 成功率百分比,
                "latest_test_time": "最新测试时间(北京时间)",
                "first_test_time": "首次测试时间(北京时间)"
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
        driver_board_sn = request.args.get('driver_board_sn')
        driver_test_result = request.args.get('driver_test_result')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)

        # 构建 CTE 查询以优化性能
        cte_conditions = ["dbt.is_deleted = FALSE"]
        
        # 时间范围条件（北京时间转UTC）
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                # 北京时间转UTC（减8小时）
                if start_dt.tzinfo is None:
                    start_dt = start_dt - timedelta(hours=8)
                cte_conditions.append(f"dbt.create_time >= '{start_dt.isoformat()}'")
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
                cte_conditions.append(f"dbt.create_time <= '{end_dt.isoformat()}'")
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 序列号筛选条件
        if driver_board_sn:
            cte_conditions.append(f"dbt.driver_board_sn LIKE '%{driver_board_sn}%'")
        
        if driver_test_result:
            cte_conditions.append(f"dbt.driver_test_result = '{driver_test_result}'")

        # 构建CTE查询
        cte_where_clause = " AND ".join(cte_conditions)
        
        # 使用 CTE 和窗口函数进行高效聚合统计（返回北京时间）
        stats_query = f"""
        WITH filtered_tests AS (
            SELECT 
                dbt.driver_board_sn,
                dbt.driver_test_result,
                CONVERT_TZ(dbt.create_time, '+00:00', '+08:00') as local_create_time
            FROM driver_board_tests dbt
            WHERE {cte_where_clause}
        ),
        sn_aggregates AS (
            SELECT 
                driver_board_sn,
                COUNT(*) as total_tests,
                SUM(CASE WHEN driver_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN driver_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count,
                MAX(local_create_time) as latest_test_time,
                MIN(local_create_time) as first_test_time,
                ROUND(
                    (SUM(CASE WHEN driver_test_result = 'pass' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                    2
                ) as success_rate
            FROM filtered_tests
            WHERE driver_board_sn IS NOT NULL AND driver_board_sn != ''
            GROUP BY driver_board_sn
            ORDER BY total_tests DESC, success_rate DESC
            LIMIT {per_page} OFFSET {(page - 1) * per_page}
        )
        SELECT * FROM sn_aggregates
        """
        
        # 执行统计查询
        result = db.session.execute(text(stats_query))
        sn_stats_data = [dict(row._mapping) for row in result]
        
        # 获取总数统计（用于分页）
        count_query = f"""
        WITH filtered_tests AS (
            SELECT DISTINCT dbt.driver_board_sn
            FROM driver_board_tests dbt
            WHERE {cte_where_clause}
              AND dbt.driver_board_sn IS NOT NULL 
              AND dbt.driver_board_sn != ''
        )
        SELECT COUNT(*) as total_sn_count FROM filtered_tests
        """
        
        count_result = db.session.execute(text(count_query))
        total_sn_count = count_result.scalar()
        
        # 格式化返回数据
        formatted_stats = []
        for row in sn_stats_data:
            formatted_stats.append({
                'driver_board_sn': row['driver_board_sn'],
                'total_tests': int(row['total_tests']),
                'success_count': int(row['success_count']),
                'fail_count': int(row['fail_count']),
                'success_rate': float(row['success_rate']),
                'latest_test_time': row['latest_test_time'].isoformat() if row['latest_test_time'] else None,
                'first_test_time': row['first_test_time'].isoformat() if row['first_test_time'] else None
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
                'driver_board_sn': driver_board_sn,
                'driver_test_result': driver_test_result
            }
        }
        
        logger.info(f"Driver board SN stats query completed. Found {len(formatted_stats)} SN records, total SNs: {total_sn_count}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching driver board SN stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500














@require_auth()
@driver_board_tests_bp.route('/time-stats', methods=['GET'])
def get_driver_board_time_stats():
    """
    获取驱动板测试时间趋势统计信息
    
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
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
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
        conditions = ["dbt.is_deleted = FALSE"]
        conditions.append(f"dbt.create_time >= '{start_dt.isoformat()}'")
        conditions.append(f"dbt.create_time <= '{end_dt.isoformat()}'")

        # 根据间隔类型设置时间格式化（转换回北京时间显示）
        interval_formats = {
            'day': "DATE_FORMAT(CONVERT_TZ(dbt.create_time, '+00:00', '+08:00'), '%Y-%m-%d')",
            'week': "DATE_FORMAT(DATE_SUB(CONVERT_TZ(dbt.create_time, '+00:00', '+08:00'), INTERVAL WEEKDAY(CONVERT_TZ(dbt.create_time, '+00:00', '+08:00')) DAY), '%Y-%m-%d')",
            'month': "DATE_FORMAT(CONVERT_TZ(dbt.create_time, '+00:00', '+08:00'), '%Y-%m-01')"
        }
        
        time_group = interval_formats[interval]
        where_clause = " AND ".join(conditions)
        
        # 使用 CTE 构建时间趋势查询
        stats_query = f"""
        WITH filtered_tests AS (
            SELECT 
                dbt.driver_test_result,
                {time_group} as time_period
            FROM driver_board_tests dbt
            WHERE {where_clause}
        ),
        time_aggregates AS (
            SELECT 
                time_period,
                COUNT(*) as total_tests,
                SUM(CASE WHEN driver_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN driver_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count
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
        
        logger.info(f"Driver board time stats query completed. Found {len(formatted_stats)} time periods")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching driver board time stats: {str(e)}")
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
    """填充驱动板测试对象字段"""
    # 基本字段
    if not is_update or 'driver_board_sn' in json_data:
        test.driver_board_sn = json_data.get('driver_board_sn', test.driver_board_sn if is_update else None)
    # 修正字段名称
    test.driver_test_result = json_data.get('driver_test_result', test.driver_test_result if is_update else 'PENDING')
    
    # 设置速度
    if 'set_speed' in json_data:
        try:       
            # 确保 set_speed 是整数类型
            test.set_speed = int(json_data['set_speed']) if json_data['set_speed'] is not None else None
        except (ValueError, TypeError):
            raise ValueError("set_speed must be an integer (RPM)")
    elif not is_update:
        print("set_speed not found in json_data, setting to None", flush=True)
        test.set_speed = None

    
    # 测试数值字段（实际测试数据）
    test.motor_status = json_data.get('motor_status', test.motor_status if is_update else None)
    test.motor_speed = json_data.get('motor_speed', test.motor_speed if is_update else None)
    test.ipm_temperature = json_data.get('ipm_temperature', test.ipm_temperature if is_update else None)
    test.dc_voltage = json_data.get('dc_voltage', test.dc_voltage if is_update else None)
    test.output_power = json_data.get('output_power', test.output_power if is_update else None)
    test.driver_software_version = json_data.get('driver_software_version', test.driver_software_version if is_update else None)
    
    # 测试结果字段（是否通过测试）
    test.motor_status_result = json_data.get('motor_status_result', test.motor_status_result if is_update else None)
    test.motor_speed_result = json_data.get('motor_speed_result', test.motor_speed_result if is_update else None)
    test.ipm_temperature_result = json_data.get('ipm_temperature_result', test.ipm_temperature_result if is_update else None)
    test.dc_voltage_result = json_data.get('dc_voltage_result', test.dc_voltage_result if is_update else None)
    test.output_power_result = json_data.get('output_power_result', test.output_power_result if is_update else None)
    test.driver_software_version_result = json_data.get('driver_software_version_result', test.driver_software_version_result if is_update else None)
    
    # 测试运行时间相关
    if 'test_runtime' in json_data:
        # 确保 test_runtime 是整数类型
        try:
            test.test_runtime = int(json_data['test_runtime']) if json_data['test_runtime'] is not None else None
        except (ValueError, TypeError):
            raise ValueError("test_runtime must be an integer (seconds)")
    elif not is_update:
        test.test_runtime = None




    # 通用信息
    test.start_time = parse_datetime(json_data.get('start_time')) if 'start_time' in json_data else (test.start_time if is_update else None)
    test.end_time = parse_datetime(json_data.get('end_time')) if 'end_time' in json_data else (test.end_time if is_update else None)
    
    # 描述信息
    test.test_description = json_data.get('test_description', test.test_description if is_update else None)
    test.general_test_remark = json_data.get('general_test_remark', test.general_test_remark if is_update else None)
    
    # 网络信息
    test.local_ip = json_data.get('local_ip', test.local_ip if is_update else None)
    test.public_ip = json_data.get('public_ip', test.public_ip if is_update else None)
    test.hostname = json_data.get('hostname', test.hostname if is_update else None)
    test.app_version = json_data.get('app_version', test.app_version if is_update else '1.0.0')


    
def validate_required_fields(json_data):
    """验证必填字段"""
    if 'driver_board_sn' not in json_data or not json_data['driver_board_sn']:
        return {'error': 'driver_board_sn is required'}, 400
    
    if len(json_data['driver_board_sn']) > 32:
        return {'error': 'driver_board_sn too long (max 32 characters)'}, 400
    
    # 验证数字字段
    if 'test_runtime' in json_data and json_data['test_runtime'] is not None:
        try:
            int(json_data['test_runtime'])
        except (ValueError, TypeError):
            return {'error': 'test_runtime must be an integer (seconds)'}, 400
    
    if 'set_speed' in json_data and json_data['set_speed'] is not None:
        try:
            int(json_data['set_speed'])
        except (ValueError, TypeError):
            return {'error': 'set_speed must be an integer (RPM)'}, 400
    
    return None, None