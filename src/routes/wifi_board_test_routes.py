from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta, timezone
import logging
import json
from sqlalchemy import func, case, text  # 添加text导入

from src.extensions import db
from src.models.wifi_board_test_model import WifiBoardTest
from src.auth.decorators import require_auth, require_role

wifi_board_tests_bp = Blueprint('wifi_board_tests_bp', __name__, url_prefix='/api/wifi_board_tests')

# 配置日志
logger = logging.getLogger(__name__)

@wifi_board_tests_bp.route('', methods=['POST'])
def create_wifi_board_test():
    """创建新的WiFi板测试记录"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        # 验证必填字段
        error, status = validate_required_fields(json_data)
        if error:
            return jsonify(error), status
        
        # logger.info(f"Creating WiFi board test for SN: {json_data['wifi_board_sn']}")
        
        new_test = WifiBoardTest()
        populate_test_fields(new_test, json_data)
        
        db.session.add(new_test)
        db.session.commit()
        
        logger.info(f"WiFi board test created successfully with ID: {new_test.id}")
        return jsonify(new_test.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error creating WiFi board test: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500






@require_auth()
@wifi_board_tests_bp.route('', methods=['GET'])
def get_all_wifi_board_tests():
    """获取所有WiFi板测试记录 (自动过滤已删除)，支持分页、排序与筛选（包括时间范围）"""
    try:
        # 分页参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 3, type=int), 100)
        
        # 排序参数
        sort_by = request.args.get('sort_by', 'update_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 普通筛选参数
        wifi_board_sn = request.args.get('wifi_board_sn')
        general_test_result = request.args.get('general_test_result')
        
        # 时间范围筛选参数（支持 YYYY-MM-DD 或 ISO 格式）
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 使用 WifiBoardTest.query 会自动过滤 is_deleted=False
        query = WifiBoardTest.query
        
        # 应用时间范围筛选（基于 create_time 字段）
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                # 如果没有时区信息，假设是北京时间，转换为UTC
                if start_dt.tzinfo is None:
                    # 假设输入是北京时间(UTC+8)，转换为UTC
                    start_dt = start_dt - timedelta(hours=8)
                query = query.filter(WifiBoardTest.create_time >= start_dt)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        if end_date:
            try:
                end_dt = parse_datetime(end_date) if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d')
                # 如果是日期格式，包含当天的所有记录
                if 'T' not in end_date:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59)
                # 如果没有时区信息，假设是北京时间，转换为UTC
                if end_dt.tzinfo is None:
                    # 假设输入是北京时间(UTC+8)，转换为UTC
                    end_dt = end_dt - timedelta(hours=8)
                query = query.filter(WifiBoardTest.create_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 应用其它筛选条件
        if wifi_board_sn:
            query = query.filter(WifiBoardTest.wifi_board_sn.like(f'%{wifi_board_sn}%'))
        if general_test_result:
            query = query.filter(WifiBoardTest.general_test_result == general_test_result)
        
        # 应用排序
        if hasattr(WifiBoardTest, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(WifiBoardTest, sort_by).desc())
            else:
                query = query.order_by(getattr(WifiBoardTest, sort_by).asc())
        
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
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'wifi_board_sn': wifi_board_sn,
                'general_test_result': general_test_result
            }
        })
    except Exception as e:
        logger.error(f"Error fetching WiFi board tests: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@require_auth()
@wifi_board_tests_bp.route('/<string:test_id>', methods=['GET'])
def get_wifi_board_test(test_id):
    """获取特定ID的WiFi板测试记录"""
    try:
        # 使用 WifiBoardTest.query 会自动过滤 is_deleted=False
        test = WifiBoardTest.query.filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'WiFi board test record not found'}), 404
        return jsonify(test.to_dict())
    except Exception as e:
        logger.error(f"Error fetching WiFi board test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@require_auth()
@wifi_board_tests_bp.route('/<string:test_id>', methods=['PUT'])
def update_wifi_board_test(test_id):
    """更新特定ID的WiFi板测试记录"""
    try:
        # 使用 WifiBoardTest.query 会自动过滤 is_deleted=False
        test = WifiBoardTest.query.filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'WiFi board test record not found'}), 404
        
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        logger.info(f"Updating WiFi board test ID: {test_id}")
        
        populate_test_fields(test, json_data, is_update=True)
        
        db.session.commit()
        
        logger.info(f"WiFi board test updated successfully: {test_id}")
        return jsonify(test.to_dict())
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error updating test {test_id}: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating WiFi board test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500




@require_auth()
@require_role('admin')
@wifi_board_tests_bp.route('/<string:test_id>', methods=['DELETE'])
def delete_wifi_board_test(test_id):
    """软删除特定ID的WiFi板测试记录"""
    try:
        # 使用 db.session.query 绕过 ActiveQuery，确保能找到记录
        test = db.session.query(WifiBoardTest).filter_by(id=test_id).first()
        if test is None:
            return jsonify({'error': 'WiFi board test record not found'}), 404
        
        if test.is_deleted:
            return jsonify({'message': 'Record already deleted'}), 200

        logger.info(f"Soft-deleting WiFi board test ID: {test_id}")
        
        # 执行软删除
        test.is_deleted = True
        test.delete_time = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"WiFi board test soft-deleted successfully: {test_id}")
        return jsonify({'message': 'WiFi board test record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting WiFi board test {test_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


















@require_auth()
@wifi_board_tests_bp.route('/stats', methods=['GET'])
def get_wifi_board_test_stats():
    """
    获取WiFi板测试统计信息
    
    支持的查询参数:
    - start_date: 开始日期 (格式: YYYY-MM-DD 或 ISO格式)
    - end_date: 结束日期 (格式: YYYY-MM-DD 或 ISO格式) 
    - wifi_board_sn: WiFi板序列号 (支持模糊匹配)
    
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
        wifi_board_sn = request.args.get('wifi_board_sn')
        general_test_result = request.args.get('general_test_result')

        # 构建基础查询，自动过滤软删除记录
        query = WifiBoardTest.query.filter(WifiBoardTest.is_deleted == False)
        
        # 应用时间范围筛选（基于create_time字段）
        if start_date:
            try:
                # 支持多种日期格式
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                # 如果没有时区信息，假设是北京时间，转换为UTC
                if start_dt.tzinfo is None:
                    # 假设输入是北京时间(UTC+8)，转换为UTC
                    start_dt = start_dt - timedelta(hours=8)
                query = query.filter(WifiBoardTest.create_time >= start_dt)
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
                query = query.filter(WifiBoardTest.create_time <= end_dt)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 应用WiFi板序列号筛选（模糊匹配）
        if wifi_board_sn:
            query = query.filter(WifiBoardTest.wifi_board_sn.like(f'%{wifi_board_sn}%'))

        if general_test_result:
            query = query.filter(WifiBoardTest.general_test_result == general_test_result)

        # 使用单次聚合查询获取所有统计数据，提高查询效率

        
        # 一次查询同时获取总数和各状态的统计
        stats_result = db.session.query(
            func.count(WifiBoardTest.id).label('total_count'),
            func.sum(case((WifiBoardTest.general_test_result == 'pass', 1), else_=0)).label('success_count'),
            func.sum(case((WifiBoardTest.general_test_result == 'fail', 1), else_=0)).label('fail_count'),
        ).filter(query.whereclause if query.whereclause is not None else True).one()
        
        # 获取详细的状态分组统计（用于breakdown）
        breakdown_stats = db.session.query(
            WifiBoardTest.general_test_result,
            func.count(WifiBoardTest.id).label('count')
        ).filter(query.whereclause if query.whereclause is not None else True
        ).group_by(WifiBoardTest.general_test_result).all()
        
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
                'wifi_board_sn': wifi_board_sn
            }
        }
        
        logger.info(f"WiFi board test stats query completed. Total: {total_count}, Success: {success_count}, Fail: {fail_count}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching WiFi board test stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500





















@require_auth()
@wifi_board_tests_bp.route('/boards-stats', methods=['GET'])
def get_wifi_board_stats():
    """
    获取WiFi板子维度的统计信息
    
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
            SUM(CASE WHEN general_test_result = 'pass' THEN 1 ELSE 0 END) as success_tests,
            SUM(CASE WHEN general_test_result = 'fail' THEN 1 ELSE 0 END) as fail_tests
        FROM wifi_board_tests 
        WHERE is_deleted = 0 {time_filter}
        """)
        
        test_result = db.session.execute(test_stats_sql, params).fetchone()
        
        # 2. 板子维度统计 - 使用窗口函数获取每个板子的最新测试结果
        board_stats_sql = text(f"""
        WITH latest_tests AS (
            SELECT 
                wifi_board_sn,
                general_test_result,
                ROW_NUMBER() OVER (PARTITION BY wifi_board_sn ORDER BY create_time DESC) as rn
            FROM wifi_board_tests 
            WHERE is_deleted = 0 {time_filter}
        ),
        board_history AS (
            SELECT 
                wifi_board_sn,
                COUNT(*) as total_tests,
                SUM(CASE WHEN general_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN general_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count
            FROM wifi_board_tests 
            WHERE is_deleted = 0 {time_filter}
            GROUP BY wifi_board_sn
        )
        SELECT 
            COUNT(DISTINCT l.wifi_board_sn) as total_boards,
            SUM(CASE WHEN l.general_test_result = 'pass' THEN 1 ELSE 0 END) as success_boards,
            SUM(CASE WHEN l.general_test_result = 'fail' THEN 1 ELSE 0 END) as fail_boards,
            -- 一直成功的板子：最新是成功且从未失败
            SUM(CASE 
                WHEN l.general_test_result = 'pass' AND h.fail_count = 0 
                THEN 1 ELSE 0 
            END) as always_success_boards,
            -- 最终成功的板子：最新是成功但有过失败
            SUM(CASE 
                WHEN l.general_test_result = 'pass' AND h.fail_count > 0 
                THEN 1 ELSE 0 
            END) as final_success_boards,
            -- 一直失败的板子：最新是失败且从未成功
            SUM(CASE 
                WHEN l.general_test_result = 'fail' AND h.success_count = 0 
                THEN 1 ELSE 0 
            END) as always_fail_boards,
            -- 最终失败的板子：最新是失败但有过成功
            SUM(CASE 
                WHEN l.general_test_result = 'fail' AND h.success_count > 0 
                THEN 1 ELSE 0 
            END) as final_fail_boards
        FROM latest_tests l
        JOIN board_history h ON l.wifi_board_sn = h.wifi_board_sn
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
        
        logger.info(f"WiFi board stats completed. Total boards: {board_result.total_boards}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching WiFi board stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500























@require_auth()
@wifi_board_tests_bp.route('/time-stats', methods=['GET'])
def get_wifi_board_time_stats():
    """
    获取WiFi板测试时间趋势统计信息
    
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
        conditions = ["wbt.is_deleted = FALSE"]
        conditions.append(f"wbt.create_time >= '{start_dt.isoformat()}'")
        conditions.append(f"wbt.create_time <= '{end_dt.isoformat()}'")

        # 根据间隔类型设置时间格式化（转换回北京时间显示）
        interval_formats = {
            'day': "DATE_FORMAT(CONVERT_TZ(wbt.create_time, '+00:00', '+08:00'), '%Y-%m-%d')",
            'week': "DATE_FORMAT(DATE_SUB(CONVERT_TZ(wbt.create_time, '+00:00', '+08:00'), INTERVAL WEEKDAY(CONVERT_TZ(wbt.create_time, '+00:00', '+08:00')) DAY), '%Y-%m-%d')",
            'month': "DATE_FORMAT(CONVERT_TZ(wbt.create_time, '+00:00', '+08:00'), '%Y-%m-01')"
        }
        
        time_group = interval_formats[interval]
        where_clause = " AND ".join(conditions)
        
        # 使用 CTE 构建时间趋势查询
        stats_query = f"""
        WITH filtered_tests AS (
            SELECT 
                wbt.general_test_result,
                {time_group} as time_period
            FROM wifi_board_tests wbt
            WHERE {where_clause}
        ),
        time_aggregates AS (
            SELECT 
                time_period,
                COUNT(*) as total_tests,
                SUM(CASE WHEN general_test_result = 'pass' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN general_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count
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
        
        logger.info(f"WiFi board time stats query completed. Found {len(formatted_stats)} time periods")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching WiFi board time stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500





































@require_auth()
@wifi_board_tests_bp.route('/sn-stats', methods=['GET'])
def get_wifi_board_sn_stats():
    """
    获取WiFi板测试的序列号统计信息 (板子维度)
    每块板子一行数据，测试结果=该板子最新一次测试的结果
    
    查询参数:
    - start_date: 开始日期 (YYYY-MM-DD，北京时间)
    - end_date: 结束日期 (YYYY-MM-DD，北京时间)
    - wifi_board_sn: WiFi板序列号筛选 (部分匹配)
    - latest_result: 筛选最新测试结果 (pass/fail)
    - sort_by: 排序字段 (wifi_board_sn, total_tests, pass_count, fail_count, pass_rate, latest_test_time, first_test_time, latest_result)
    - sort_order: 排序方向 (asc, desc，默认desc)
    - page: 页码 (默认: 1)
    - per_page: 每页记录数 (默认: 10, 最大: 100)
    
    返回格式:
    {
        "sn_stats": [
            {
                "wifi_board_sn": "序列号",
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
        wifi_board_sn = request.args.get('wifi_board_sn')
        latest_result = request.args.get('latest_result')
        sort_by = request.args.get('sort_by', 'total_tests')
        sort_order = request.args.get('sort_order', 'desc').lower()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)

        # 验证排序参数
        valid_sort_fields = {
            'wifi_board_sn': 'wifi_board_sn',
            'total_tests': 'total_tests',
            'pass_count': 'pass_count', 
            'fail_count': 'fail_count',
            'pass_rate': 'pass_rate',
            'latest_test_time': 'latest_test_time',
            'first_test_time': 'first_test_time',
            'latest_result': 'latest_result'
        }
        
        if sort_by not in valid_sort_fields:
            sort_by = 'total_tests'
        
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        # 构建 CTE 查询以优化性能（时间筛选条件，不包含latest_result）
        cte_conditions = ["wbt.is_deleted = FALSE"]
        
        # 时间范围条件（北京时间转UTC）
        if start_date:
            try:
                start_dt = parse_datetime(start_date) if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d')
                # 北京时间转UTC（减8小时）
                if start_dt.tzinfo is None:
                    start_dt = start_dt - timedelta(hours=8)
                cte_conditions.append(f"wbt.create_time >= '{start_dt.isoformat()}'")
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
                cte_conditions.append(f"wbt.create_time <= '{end_dt.isoformat()}'")
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD or ISO format'}), 400
        
        # 序列号筛选条件
        if wifi_board_sn:
            cte_conditions.append(f"wbt.wifi_board_sn LIKE '%{wifi_board_sn}%'")

        # 构建CTE查询
        cte_where_clause = " AND ".join(cte_conditions)
        
        # 板子维度统计：每块板子一行数据，基于最新测试结果筛选
        stats_query = f"""
        WITH board_all_tests AS (
            SELECT 
                wbt.wifi_board_sn,
                wbt.general_test_result,
                wbt.create_time,
                CONVERT_TZ(wbt.create_time, '+00:00', '+08:00') as local_create_time,
                ROW_NUMBER() OVER (PARTITION BY wbt.wifi_board_sn ORDER BY wbt.create_time DESC) as rn
            FROM wifi_board_tests wbt
            WHERE {cte_where_clause}
        ),
        board_latest_result AS (
            SELECT 
                wifi_board_sn,
                general_test_result as latest_result,
                local_create_time as latest_test_time
            FROM board_all_tests
            WHERE rn = 1
        ),
        board_stats AS (
            SELECT 
                bat.wifi_board_sn,
                COUNT(*) as total_tests,
                SUM(CASE WHEN bat.general_test_result = 'pass' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN bat.general_test_result = 'fail' THEN 1 ELSE 0 END) as fail_count,
                MIN(bat.local_create_time) as first_test_time,
                ROUND(
                    (SUM(CASE WHEN bat.general_test_result = 'pass' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 
                    2
                ) as pass_rate
            FROM board_all_tests bat
            WHERE bat.wifi_board_sn IS NOT NULL AND bat.wifi_board_sn != ''
            GROUP BY bat.wifi_board_sn
        )
        SELECT 
            bs.wifi_board_sn,
            bs.total_tests,
            bs.pass_count,
            bs.fail_count,
            bs.pass_rate,
            bs.first_test_time,
            blr.latest_test_time,
            blr.latest_result
        FROM board_stats bs
        JOIN board_latest_result blr ON bs.wifi_board_sn = blr.wifi_board_sn
        WHERE 1=1 {" AND blr.latest_result = '" + latest_result + "'" if latest_result else ""}
        ORDER BY {valid_sort_fields[sort_by]} {sort_order.upper()}
        LIMIT {per_page} OFFSET {(page - 1) * per_page}
        """
        
        # 执行统计查询
        result = db.session.execute(text(stats_query))
        sn_stats_data = [dict(row._mapping) for row in result]
        
        # 获取总数统计（用于分页）- 基于板子维度和最新结果筛选
        count_query = f"""
        WITH board_all_tests AS (
            SELECT 
                wbt.wifi_board_sn,
                wbt.general_test_result,
                wbt.create_time,
                ROW_NUMBER() OVER (PARTITION BY wbt.wifi_board_sn ORDER BY wbt.create_time DESC) as rn
            FROM wifi_board_tests wbt
            WHERE {cte_where_clause}
        ),
        board_latest_result AS (
            SELECT 
                wifi_board_sn,
                general_test_result as latest_result
            FROM board_all_tests
            WHERE rn = 1
              AND wifi_board_sn IS NOT NULL 
              AND wifi_board_sn != ''
        )
        SELECT COUNT(*) as total_board_count 
        FROM board_latest_result
        WHERE 1=1 {" AND latest_result = '" + latest_result + "'" if latest_result else ""}
        """
        
        count_result = db.session.execute(text(count_query))
        total_board_count = count_result.scalar()
        
        # 格式化返回数据
        formatted_stats = []
        for row in sn_stats_data:
            formatted_stats.append({
                'wifi_board_sn': row['wifi_board_sn'],
                'total_tests': int(row['total_tests']),
                'pass_count': int(row['pass_count']),
                'fail_count': int(row['fail_count']),
                'pass_rate': float(row['pass_rate']),
                'latest_test_time': row['latest_test_time'].isoformat() if row['latest_test_time'] else None,
                'first_test_time': row['first_test_time'].isoformat() if row['first_test_time'] else None,
                'latest_result': row['latest_result']
            })
        
        # 构建分页信息
        total_pages = (total_board_count + per_page - 1) // per_page
        
        response_data = {
            'sn_stats': formatted_stats,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_board_count,
                'pages': total_pages
            },
            'filters': {
                'start_date': start_date,
                'end_date': end_date,
                'wifi_board_sn': wifi_board_sn,
                'latest_result': latest_result,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        }
        
        logger.info(f"WiFi board SN stats query completed. Found {len(formatted_stats)} board records, total boards: {total_board_count}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching WiFi board SN stats: {str(e)}")
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
    """填充WiFi板测试对象字段"""
    # 基本字段
    if not is_update or 'wifi_board_sn' in json_data:
        test.wifi_board_sn = json_data.get('wifi_board_sn', test.wifi_board_sn if is_update else None)
    test.general_test_result = json_data.get('general_test_result', test.general_test_result if is_update else 'PENDING')
    
    # 旋钮测试相关
    test.knob_test_result = json_data.get('knob_test_result', test.knob_test_result if is_update else None)
    test.speed_knob_result = json_data.get('speed_knob_result', test.speed_knob_result if is_update else None)
    test.speed_knob_remark = json_data.get('speed_knob_remark', test.speed_knob_remark if is_update else None)
    test.speed_data = json.dumps(json_data.get('speed_data', test.speed_data if is_update else []))
    test.time_knob_result = json_data.get('time_knob_result', test.time_knob_result if is_update else None)
    test.time_knob_remark = json_data.get('time_knob_remark', test.time_knob_remark if is_update else None)
    test.time_data = json.dumps(json_data.get('time_data', test.time_data if is_update else []))
    test.knob_start_time = parse_datetime(json_data.get('knob_start_time')) if 'knob_start_time' in json_data else (test.knob_start_time if is_update else None)
    test.knob_end_time = parse_datetime(json_data.get('knob_end_time')) if 'knob_end_time' in json_data else (test.knob_end_time if is_update else None)
    
    # 灯光测试相关
    test.light_test_result = json_data.get('light_test_result', test.light_test_result if is_update else None)
    test.green_light_result = json_data.get('green_light_result', test.green_light_result if is_update else None)
    test.light_data = json.dumps(json_data.get('light_data', test.light_data if is_update else []))
    test.red_light_result = json_data.get('red_light_result', test.red_light_result if is_update else None)
    test.blue_light_result = json_data.get('blue_light_result', test.blue_light_result if is_update else None)
    test.light_start_time = parse_datetime(json_data.get('light_start_time')) if 'light_start_time' in json_data else (test.light_start_time if is_update else None)
    test.light_end_time = parse_datetime(json_data.get('light_end_time')) if 'light_end_time' in json_data else (test.light_end_time if is_update else None)
    
    # 网络测试相关
    test.network_test_result = json_data.get('network_test_result', test.network_test_result if is_update else None)
    test.wifi_software_version = json_data.get('wifi_software_version', test.wifi_software_version if is_update else None)
    test.wifi_software_version_data = json_data.get('wifi_software_version_data', test.wifi_software_version_data if is_update else None)
    test.mac_address = json_data.get('mac_address', test.mac_address if is_update else None)
    test.start_command_result = json_data.get('start_command_result', test.start_command_result if is_update else None)
    test.speed_command_result = json_data.get('speed_command_result', test.speed_command_result if is_update else None)
    test.stop_command_result = json_data.get('stop_command_result', test.stop_command_result if is_update else None)
    test.network_start_time = parse_datetime(json_data.get('network_start_time')) if 'network_start_time' in json_data else (test.network_start_time if is_update else None)
    test.network_end_time = parse_datetime(json_data.get('network_end_time')) if 'network_end_time' in json_data else (test.network_end_time if is_update else None)
    
    # 通用信息
    test.start_time = parse_datetime(json_data.get('start_time')) if 'start_time' in json_data else (test.start_time if is_update else None)
    test.end_time = parse_datetime(json_data.get('end_time')) if 'end_time' in json_data else (test.end_time if is_update else None)
    test.general_test_remark = json_data.get('general_test_remark', test.general_test_remark if is_update else None)
    
    # 网络信息
    test.local_ip = json_data.get('local_ip', test.local_ip if is_update else None)
    test.public_ip = json_data.get('public_ip', test.public_ip if is_update else None)
    test.hostname = json_data.get('hostname', test.hostname if is_update else None)
    test.app_version = json_data.get('app_version', test.app_version if is_update else '1.0.0')

def validate_required_fields(json_data):
    """验证必填字段"""
    if 'wifi_board_sn' not in json_data or not json_data['wifi_board_sn']:
        return {'error': 'wifi_board_sn is required'}, 400
    
    if len(json_data['wifi_board_sn']) > 32:
        return {'error': 'wifi_board_sn too long (max 32 characters)'}, 400
    
    return None, None


