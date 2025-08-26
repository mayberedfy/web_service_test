import functools
import logging
from flask import request, jsonify, current_app, g
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from werkzeug.security import check_password_hash
from src.models.admin_user_model import User
from src.models.admin_api_keys import ApiKey

logger = logging.getLogger(__name__)

def require_api_key(permissions=None):


    """API密钥认证装饰器"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            
            # 第1步：从请求头提取API密钥
            auth_header = request.headers.get('Authorization', '')
            api_key = None
            
            # 支持多种格式
            if auth_header.startswith('Bearer '):
                api_key = auth_header.split(' ', 1)[1]
            elif auth_header.startswith('ApiKey '):
                api_key = auth_header.split(' ', 1)[1]
            else:
                api_key = request.headers.get('X-API-Key')
            
            if not api_key:
                logger.warning(f"Missing API key from {request.remote_addr}")
                return jsonify({'error': 'API key required'}), 401
            
            # 第2步：验证API密钥
            key_record = None
            for key_obj in ApiKey.query.filter_by(is_active=True).all():
                if key_obj.verify_key(api_key) and key_obj.is_valid():
                    key_record = key_obj
                    break
            
            if not key_record:
                logger.warning(f"Invalid API key from {request.remote_addr}")
                return jsonify({'error': 'Invalid API key'}), 401
            
            # 第3步：检查权限
            if permissions:
                required_perms = permissions if isinstance(permissions, list) else [permissions]
                for perm in required_perms:
                    if not key_record.has_permission(perm):
                        logger.warning(f"Insufficient permissions for API key {key_record.key_name}")
                        return jsonify({'error': 'Insufficient permissions'}), 403
            
            # 第4步：更新使用统计
            key_record.update_usage()
            
            # 第5步：保存到请求上下文
            g.api_key = key_record
            
            return f(*args, **kwargs)
        return wrapper
    return decorator






def require_auth():
    """JWT认证装饰器"""
    def decorator(f):
        @functools.wraps(f)
        @jwt_required()                 # Flask-JWT-Extended 提供的基础验证

        def wrapper(*args, **kwargs):
            
            # 第1步：从JWT token中提取用户ID
            user_id = get_jwt_identity()
            
            # 第2步：从数据库查询用户信息
            user = User.query.get(user_id)
            
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive'}), 401
            
            # 第3步：保存到请求上下文供后续使用
            g.current_user = user
            
            return f(*args, **kwargs)
        return wrapper
    return decorator






def require_role(roles):
    """角色权限装饰器"""
    def decorator(f):
        @functools.wraps(f)
        @require_auth()     # 先验证JWT
        def wrapper(*args, **kwargs):
            user = g.current_user
            required_roles = roles if isinstance(roles, list) else [roles]
            
            if not user.has_role(required_roles):
                logger.warning(f"User {user.username} attempted to access {request.endpoint} without proper role")
                return jsonify({'error': 'Insufficient role permissions'}), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator








def require_permission(permissions):
    """权限装饰器"""
    def decorator(f):
        @functools.wraps(f)
        @require_auth()
        def wrapper(*args, **kwargs):
            user = g.current_user
            required_perms = permissions if isinstance(permissions, list) else [permissions]
            
            for perm in required_perms:
                if not user.has_permission(perm):
                    logger.warning(f"User {user.username} attempted to access {request.endpoint} without permission {perm}")
                    return jsonify({'error': f'Permission {perm} required'}), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator