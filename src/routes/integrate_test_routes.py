from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import logging

from src.extensions import db
from src.models.integrate_test_model import IntegrateTest

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
        
        # 使用 IntegrateTest.query 会自动过滤 is_deleted=False
        query = IntegrateTest.query
        
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