from flask import Blueprint, jsonify, request
from datetime import datetime, timezone
import logging

from src.extensions import db
from src.models.temperature_data_model import TemperatureData

temperature_data_bp = Blueprint('temperature_data_bp', __name__, url_prefix='/api/temperature_data')

# 配置日志
logger = logging.getLogger(__name__)

@temperature_data_bp.route('', methods=['POST'])
def create_temperature_data():
    """创建新的温度数据记录"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        # 验证必填字段
        error, status = validate_required_fields(json_data)
        if error:
            return jsonify(error), status
        
        logger.info(f"Creating temperature data for product SN: {json_data['product_sn']}")
        
        new_data = TemperatureData()
        populate_data_fields(new_data, json_data)
        
        db.session.add(new_data)
        db.session.commit()
        
        logger.info(f"Temperature data created successfully with ID: {new_data.id}")
        return jsonify(new_data.to_dict()), 201
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected error creating temperature data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@temperature_data_bp.route('', methods=['GET'])
def get_all_temperature_data():
    """获取所有温度数据记录 (自动过滤已删除)"""
    try:
        # 添加分页支持
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        # 添加排序支持
        sort_by = request.args.get('sort_by', 'update_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 添加筛选支持
        product_sn = request.args.get('product_sn')
        temperature_compensation_enabled = request.args.get('temperature_compensation_enabled')
        
        # 使用 TemperatureData.query 会自动过滤 is_deleted=False
        query = TemperatureData.query
        
        # 应用筛选条件
        if product_sn:
            query = query.filter(TemperatureData.product_sn.like(f'%{product_sn}%'))
        if temperature_compensation_enabled is not None:
            # 处理布尔值参数
            is_enabled = temperature_compensation_enabled.lower() in ['true', '1', 'yes']
            query = query.filter(TemperatureData.temperature_compensation_enabled == is_enabled)
        
        # 应用排序
        if hasattr(TemperatureData, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(TemperatureData, sort_by).desc())
            else:
                query = query.order_by(getattr(TemperatureData, sort_by).asc())
        
        # 分页查询
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'data': [data.to_dict() for data in pagination.items],
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
        logger.error(f"Error fetching temperature data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@temperature_data_bp.route('/<string:data_id>', methods=['GET'])
def get_temperature_data(data_id):
    """获取特定ID的温度数据记录"""
    try:
        # 使用 TemperatureData.query 会自动过滤 is_deleted=False
        data = TemperatureData.query.filter_by(id=data_id).first()
        if data is None:
            return jsonify({'error': 'Temperature data record not found'}), 404
        return jsonify(data.to_dict())
    except Exception as e:
        logger.error(f"Error fetching temperature data {data_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@temperature_data_bp.route('/<string:data_id>', methods=['PUT'])
def update_temperature_data(data_id):
    """更新特定ID的温度数据记录"""
    try:
        # 使用 TemperatureData.query 会自动过滤 is_deleted=False
        data = TemperatureData.query.filter_by(id=data_id).first()
        if data is None:
            return jsonify({'error': 'Temperature data record not found'}), 404
        
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400
        
        logger.info(f"Updating temperature data ID: {data_id}")
        
        populate_data_fields(data, json_data, is_update=True)
        
        db.session.commit()
        
        logger.info(f"Temperature data updated successfully: {data_id}")
        return jsonify(data.to_dict())
        
    except ValueError as e:
        db.session.rollback()
        logger.error(f"Validation error updating data {data_id}: {str(e)}")
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating temperature data {data_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@temperature_data_bp.route('/<string:data_id>', methods=['DELETE'])
def delete_temperature_data(data_id):
    """软删除特定ID的温度数据记录"""
    try:
        # 使用 db.session.query 绕过 ActiveQuery，确保能找到记录
        data = db.session.query(TemperatureData).filter_by(id=data_id).first()
        if data is None:
            return jsonify({'error': 'Temperature data record not found'}), 404
        
        if data.is_deleted:
            return jsonify({'message': 'Record already deleted'}), 200

        logger.info(f"Soft-deleting temperature data ID: {data_id}")
        
        # 执行软删除
        data.is_deleted = True
        data.delete_time = datetime.now(timezone.utc)
        
        db.session.commit()
        
        logger.info(f"Temperature data soft-deleted successfully: {data_id}")
        return jsonify({'message': 'Temperature data record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting temperature data {data_id}: {str(e)}")
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

def populate_data_fields(data, json_data, is_update=False):
    """填充温度数据对象字段"""
    # 基本字段
    if not is_update or 'product_sn' in json_data:
        data.product_sn = json_data.get('product_sn', data.product_sn if is_update else None)
    
    # 时间相关字段
    data.start_time = parse_datetime(json_data.get('test_start_time')) if 'test_start_time' in json_data else (data.start_time if is_update else None)
    data.end_time = parse_datetime(json_data.get('test_end_time')) if 'test_end_time' in json_data else (data.end_time if is_update else None)
    
    # 数值字段
    data.test_runtime = json_data.get('test_runtime', data.test_runtime if is_update else None)
    data.sample_interval = json_data.get('sample_interval', data.sample_interval if is_update else None)
    data.original_temperature_count = json_data.get('original_temperature_count', data.original_temperature_count if is_update else None)
    data.temperature_compensation_value = json_data.get('temperature_compensation_value', data.temperature_compensation_value if is_update else None)
    data.temperature_compensation_duration = json_data.get('temperature_compensation_duration', data.temperature_compensation_duration if is_update else None)
    
    # 温度数据数组
    data.original_temperature = json_data.get('original_temperature', data.original_temperature if is_update else None)
    data.compensated_temperature = json_data.get('compensated_temperature', data.compensated_temperature if is_update else None)
    
    # 布尔字段
    data.temperature_compensation_enabled = json_data.get('temperature_compensation_enabled', data.temperature_compensation_enabled if is_update else False)
    
    # 网络信息
    data.local_ip = json_data.get('local_ip', data.local_ip if is_update else None)
    data.public_ip = json_data.get('public_ip', data.public_ip if is_update else None)
    data.hostname = json_data.get('hostname', data.hostname if is_update else None)
    data.app_version = json_data.get('app_version', data.app_version if is_update else '1.0.0')
    
    # 备注
    data.remark = json_data.get('remark', data.remark if is_update else None)

def validate_required_fields(json_data):
    """验证必填字段"""
    if 'product_sn' not in json_data or not json_data['product_sn']:
        return {'error': 'product_sn is required'}, 400
    
    if len(json_data['product_sn']) > 32:
        return {'error': 'product_sn too long (max 32 characters)'}, 400
    
    # 验证数字字段
    if 'test_runtime' in json_data and json_data['test_runtime'] is not None:
        try:
            int(json_data['test_runtime'])
        except (ValueError, TypeError):
            return {'error': 'test_runtime must be an integer (seconds)'}, 400
    
    if 'sample_interval' in json_data and json_data['sample_interval'] is not None:
        try:
            int(json_data['sample_interval'])
        except (ValueError, TypeError):
            return {'error': 'sample_interval must be an integer (seconds)'}, 400
    
    if 'temperature_compensation_value' in json_data and json_data['temperature_compensation_value'] is not None:
        try:
            float(json_data['temperature_compensation_value'])
        except (ValueError, TypeError):
            return {'error': 'temperature_compensation_value must be a number'}, 400
    
    if 'temperature_compensation_duration' in json_data and json_data['temperature_compensation_duration'] is not None:
        try:
            int(json_data['temperature_compensation_duration'])
        except (ValueError, TypeError):
            return {'error': 'temperature_compensation_duration must be an integer (seconds)'}, 400
    
    return None, None