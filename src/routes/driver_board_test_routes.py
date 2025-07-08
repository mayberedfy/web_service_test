from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import logging

from src.extensions import db
from src.models.driver_board_test_model import DriverBoardTest

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
        
        # 使用 DriverBoardTest.query 会自动过滤 is_deleted=False
        query = DriverBoardTest.query
        
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
            test.set_speed = int(json_data['set_speed']) if json_data['set_speed'] is not None else None
        except (ValueError, TypeError):
            raise ValueError("set_speed must be an integer (RPM)")
    elif not is_update:
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


    # 测试运行时间相关
    if 'set_speed' in json_data:
        # 确保 set_speed 是整数类型
        try:
            test.set_speed = int(json_data['set_speed']) if json_data['set_speed'] is not None else None
        except (ValueError, TypeError):
            raise ValueError("set_speed must be an integer (RPM)")
    elif not is_update:
        print("set_speed not found in json_data, setting to None", flush=True)
        test.set_speed = None

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