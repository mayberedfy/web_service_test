from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import logging
import json

from src.extensions import db
from src.models.wifi_board_test_model import WifiBoardTest

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
        
        logger.info(f"Creating WiFi board test for SN: {json_data['wifi_board_sn']}")
        
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

@wifi_board_tests_bp.route('', methods=['GET'])
def get_all_wifi_board_tests():
    """获取所有WiFi板测试记录 (自动过滤已删除)"""
    try:
        # 添加分页支持
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 5, type=int), 100)
        
        # 添加排序支持
        sort_by = request.args.get('sort_by', 'update_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 添加筛选支持
        wifi_board_sn = request.args.get('wifi_board_sn')
        general_test_result = request.args.get('general_test_result')
        
        # 使用 WifiBoardTest.query 会自动过滤 is_deleted=False
        query = WifiBoardTest.query
        
        # 应用筛选条件
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
            }
        })
    except Exception as e:
        logger.error(f"Error fetching WiFi board tests: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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