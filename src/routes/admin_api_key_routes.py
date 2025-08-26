from flask import Blueprint, request, jsonify, g
from src.extensions import db
from src.models.admin_api_keys import ApiKey
from src.auth.decorators import require_role, require_auth
import logging

from datetime import datetime, timedelta, timezone



logger = logging.getLogger(__name__)

api_key_bp = Blueprint('api_key_bp', __name__, url_prefix='/api/api-keys')

@api_key_bp.route('', methods=['GET'])
@require_role(['admin', 'manager'])
def list_api_keys():
    """获取API密钥列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pagination = ApiKey.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'api_keys': [key.to_dict() for key in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
        
    except Exception as e:
        logger.error(f"List API keys error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500






@api_key_bp.route('', methods=['POST'])
@require_role(['admin'])
def create_api_key():
    """创建新的API密钥"""
    try:
        data = request.get_json() or {}
        key_name = data.get('key_name', '').strip()         # 如："生产环境上传密钥"
        key_description = data.get('key_description', '').strip()  # 用途和备注信息
        scope = data.get('scope', 'upload')                 # 作用域
        permissions = data.get('permissions', [])           # 具体权限
        
        if not key_name:
            return jsonify({'error': 'Key name required'}), 400
        
        # 生成新密钥
        api_key, raw_key = ApiKey.generate_key(
            name=key_name,
            description=key_description if key_description else None,
            scope=scope,
            permissions=permissions,
            created_by=g.current_user.id   # 记录创建者
        )
        
        db.session.add(api_key)
        db.session.commit()
        
        logger.info(f"API key created: {key_name} by {g.current_user.username}")
        return jsonify({
            'message': 'API key created successfully',
            'api_key': api_key.to_dict(),
            'key': raw_key  # ⚠️ 完整密钥只在创建时返回一次！
        }), 201
        
    except Exception as e:
        logger.error(f"Create API key error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@api_key_bp.route('/<key_id>', methods=['PUT'])
@require_role(['admin'])
def update_api_key(key_id):
    """更新API密钥信息"""
    try:
        api_key = ApiKey.query.get(key_id)
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        data = request.get_json() or {}
        
        # 可更新的字段
        if 'key_name' in data:
            key_name = data['key_name'].strip()
            if not key_name:
                return jsonify({'error': 'Key name cannot be empty'}), 400
            api_key.key_name = key_name
        
        if 'key_description' in data:
            key_description = data['key_description'].strip() if data['key_description'] else None
            api_key.key_description = key_description
        
        if 'scope' in data:
            valid_scopes = ['upload', 'read', 'manage']
            if data['scope'] not in valid_scopes:
                return jsonify({'error': f'Invalid scope. Must be one of: {", ".join(valid_scopes)}'}), 400
            api_key.scope = data['scope']
        
        if 'permissions' in data:
            if not isinstance(data['permissions'], list):
                return jsonify({'error': 'Permissions must be a list'}), 400
            api_key.permissions = data['permissions']
        
        if 'is_active' in data:
            api_key.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        logger.info(f"API key updated: {api_key.key_name} by {g.current_user.username}")
        return jsonify({
            'message': 'API key updated successfully',
            'api_key': api_key.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Update API key error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500


@api_key_bp.route('/<key_id>', methods=['GET'])
@require_role(['admin', 'manager'])
def get_api_key_detail(key_id):
    """获取API密钥详细信息"""
    try:
        api_key = ApiKey.query.get(key_id)
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        # 获取基本详细信息
        detail_info = api_key.to_dict()
        
        # 添加额外的状态和统计信息
        now = datetime.now(timezone.utc)
        
        # 计算创建天数
        if api_key.create_time:
            created_days_ago = (now - api_key.create_time).days
            detail_info['created_days_ago'] = created_days_ago
        
        # 计算最后使用天数
        if api_key.last_used:
            last_used_days_ago = (now - api_key.last_used).days
            detail_info['last_used_days_ago'] = last_used_days_ago
        else:
            detail_info['last_used_days_ago'] = None
        
        # 检查是否过期
        if api_key.expires_at:
            detail_info['is_expired'] = now > api_key.expires_at
        else:
            detail_info['is_expired'] = False
        
        # 状态描述
        if not api_key.is_active:
            detail_info['status'] = 'revoked'
        elif api_key.expires_at and now > api_key.expires_at:
            detail_info['status'] = 'expired'
        else:
            detail_info['status'] = 'active'
        
        # 使用频率描述
        usage_count = int(api_key.usage_count)
        if usage_count == 0:
            detail_info['usage_frequency'] = 'never_used'
        elif api_key.last_used:
            days_since_last_use = (now - api_key.last_used).days
            if days_since_last_use <= 1:
                detail_info['usage_frequency'] = 'active'
            elif days_since_last_use <= 7:
                detail_info['usage_frequency'] = 'recent'
            elif days_since_last_use <= 30:
                detail_info['usage_frequency'] = 'occasional'
            else:
                detail_info['usage_frequency'] = 'dormant'
        
        # 如果有创建者，获取创建者信息
        if api_key.created_by:
            from src.models.admin_user_model import User
            creator = User.query.get(api_key.created_by)
            if creator:
                detail_info['creator_info'] = {
                    'id': creator.id,
                    'username': creator.username,
                    'role': creator.role
                }
            else:
                detail_info['creator_info'] = {
                    'id': api_key.created_by,
                    'username': '已删除用户',
                    'role': 'unknown'
                }
        
        # 权限描述
        permissions = api_key.permissions or []
        detail_info['permissions_count'] = len(permissions)
        detail_info['has_write_permission'] = any(p in ['write', 'upload', 'manage', '*'] for p in permissions)
        detail_info['has_read_permission'] = any(p in ['read', 'upload', 'manage', '*'] for p in permissions)
        
        logger.info(f"API key detail accessed: {api_key.key_name} by {g.current_user.username}")
        return jsonify({
            'api_key': detail_info
        })
        
    except Exception as e:
        logger.error(f"Get API key detail error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@api_key_bp.route('/<key_id>', methods=['DELETE'])
@require_role(['admin', 'manager'])
def revoke_api_key(key_id):
    """撤销API密钥"""
    try:
        api_key = ApiKey.query.get(key_id)
        if not api_key:
            return jsonify({'error': 'API key not found'}), 404
        
        api_key.is_active = False
        db.session.commit()
        
        logger.info(f"API key revoked: {api_key.key_name} by {g.current_user.username}")
        return jsonify({'message': 'API key revoked successfully'})
        
    except Exception as e:
        logger.error(f"Revoke API key error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500