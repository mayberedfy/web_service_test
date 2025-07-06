from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

from src.extensions import db
from src.models.wifi_test_log_model import WifiTestLog

wifi_test_logs_bp = Blueprint('wifi_test_logs_bp', __name__, url_prefix='/api/wifi_test_logs')

# 配置日志
logger = logging.getLogger(__name__)

@wifi_test_logs_bp.route('', methods=['POST'])
def create_wifi_test_log():
    """创建新的WiFi测试日志"""
    try:
        json_data = request.get_json()
        if not json_data:
            return jsonify({'error': 'No input data provided'}), 400

        # 验证必填字段
        if 'wifi_board_sn' not in json_data or 'raw_data' not in json_data:
            return jsonify({'error': 'wifi_board_sn and raw_data are required'}), 400

        logger.info(f"Creating WiFi test log for SN: {json_data['wifi_board_sn']}")

        new_log = WifiTestLog(
            wifi_board_sn=json_data['wifi_board_sn'],
            raw_data=json_data['raw_data'],
            mac_address=json_data.get('mac_address'),
            local_ip=json_data.get('local_ip'),
            public_ip=json_data.get('public_ip'),
            host_name=json_data.get('host_name')
        )

        db.session.add(new_log)
        db.session.commit()

        logger.info(f"WiFi test log created successfully with ID: {new_log.id}")
        return jsonify(new_log.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating WiFi test log: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@wifi_test_logs_bp.route('', methods=['GET'])
def get_all_wifi_test_logs():
    """获取所有WiFi测试日志（默认不包含已删除的）"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        sort_by = request.args.get('sort_by', 'create_time')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 筛选参数
        wifi_board_sn = request.args.get('wifi_board_sn')
        mac_address = request.args.get('mac_address')
        
        # 使用模型的默认查询（已过滤 is_deleted=False）
        query = WifiTestLog.query

        # 应用筛选
        if wifi_board_sn:
            query = query.filter(WifiTestLog.wifi_board_sn.like(f'%{wifi_board_sn}%'))
        if mac_address:
            query = query.filter(WifiTestLog.mac_address.like(f'%{mac_address}%'))

        # 应用排序
        if hasattr(WifiTestLog, sort_by):
            if sort_order.lower() == 'desc':
                query = query.order_by(getattr(WifiTestLog, sort_by).desc())
            else:
                query = query.order_by(getattr(WifiTestLog, sort_by).asc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'data': [log.to_dict() for log in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        logger.error(f"Error fetching WiFi test logs: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@wifi_test_logs_bp.route('/<string:log_id>', methods=['GET'])
def get_wifi_test_log(log_id):
    """获取特定ID的WiFi测试日志"""
    try:
        # WifiTestLog.query 会自动过滤已删除的
        log = WifiTestLog.query.filter_by(id=log_id).first()
        if log is None:
            return jsonify({'error': 'WiFi test log not found'}), 404
        return jsonify(log.to_dict())
    except Exception as e:
        logger.error(f"Error fetching WiFi test log {log_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@wifi_test_logs_bp.route('/<string:log_id>', methods=['DELETE'])
def delete_wifi_test_log(log_id):
    """软删除特定ID的WiFi测试日志"""
    try:
        # 使用 session.query 绕过默认的 is_deleted=False 过滤器，确保能找到记录
        log = db.session.query(WifiTestLog).filter_by(id=log_id, is_deleted=False).first()
        if log is None:
            return jsonify({'error': 'WiFi test log not found or already deleted'}), 404

        logger.info(f"Soft-deleting WiFi test log ID: {log_id}")
        
        # 执行软删除
        log.is_deleted = True
        log.delete_time = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"WiFi test log soft-deleted successfully: {log_id}")
        return jsonify({'message': 'WiFi test log record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting WiFi test log {log_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500