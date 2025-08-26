from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from datetime import datetime, timedelta, timezone
from src.extensions import db
from src.models.admin_user_model import User
from src.auth.jwt_config import create_tokens_for_user
from src.auth.decorators import require_auth, require_role
from src.auth.rate_limiter import limiter
import logging
from flask import g

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")  # 登录速率限制
def login():
    """用户登录"""
    try:
        data = request.get_json() or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # 第1步：验证用户存在性
        user = User.query.filter_by(username=username).first()
        
        if not user:
            logger.warning(f"Login attempt with non-existent username: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # 第2步：检查账户激活状态
        if not user.is_active:
            logger.warning(f"Login attempt with inactive account: {username}")
            return jsonify({'error': 'Account is inactive'}), 403
        
        # 第3步：检查账户锁定状态
        if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
            return jsonify({'error': 'Account is temporarily locked'}), 423
        
        # 第4步：验证密码
        if not user.check_password(password):
            # 增加失败尝试次数
            user.failed_login_attempts = str(int(user.failed_login_attempts) + 1)
            
            # 超过5次失败，锁定30分钟
            if int(user.failed_login_attempts) >= 5:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
                logger.warning(f"Account locked due to failed attempts: {username}")
            
            db.session.commit()
            logger.warning(f"Failed login attempt for user: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # 第5步：登录成功，生成JWT令牌
        user.failed_login_attempts = '0' # 重置失败计数
        user.locked_until = None
        user.last_login = datetime.now(timezone.utc)
        user.login_count = str(int(user.login_count) + 1)
        db.session.commit()
        
        # 生成令牌
        tokens = create_tokens_for_user(user)
        
        logger.info(f"Successful login for user: {username}")
        return jsonify({
            'message': 'Login successful',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'user': user.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500








@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        tokens = create_tokens_for_user(user)
        return jsonify({
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500













@auth_bp.route('/me', methods=['GET'])
@require_auth()
def get_current_user():
    """获取当前用户信息"""
    return jsonify(g.current_user.to_dict())






@auth_bp.route('/change-password', methods=['POST'])
@require_auth()
@require_role('admin')
def change_password():
    """修改密码"""
    try:
        from flask import g
        data = request.get_json() or {}
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old password and new password required'}), 400
        
        user = g.current_user
        
        # 验证旧密码
        if not user.check_password(old_password):
            return jsonify({'error': 'Invalid old password'}), 400
        
        # 设置新密码
        user.set_password(new_password)
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        logger.error(f"Change password error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    









# 1. 基础版本（客户端清除为主）
@auth_bp.route('/logout', methods=['POST'])
@require_auth()
def logout():
    """用户登出"""
    try:
        user = g.current_user
        
        # 1. 记录登出日志
        logger.info(f"User logout: {user.username}")
        
        # 2. 更新用户最后活动时间（可选）
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()
        
        # 3. 返回成功响应（客户端负责清除token）
        return jsonify({
            'message': 'Logout successful',
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    




# 2. 完整版本（服务端token撤销）
# 如果你想实现更安全的token撤销机制，logout接口还应该做：
# @auth_bp.route('/logout', methods=['POST'])
# @require_auth()
# def logout():
#     """用户登出（完整版本）"""
#     try:
#         user = g.current_user
        
#         # 1. 获取当前token信息
#         from flask_jwt_extended import get_jwt
#         jwt_claims = get_jwt()
#         access_jti = jwt_claims.get('jti')  # JWT唯一标识符
        
#         # 2. 将token加入黑名单（如果实现了token黑名单系统）
#         if access_jti:
#             from src.models.token_blacklist import TokenBlacklist
#             TokenBlacklist.revoke_token(
#                 jti=access_jti,
#                 user_id=user.id,
#                 token_type='access',
#                 expires_at=datetime.fromtimestamp(jwt_claims.get('exp')),
#                 reason='logout'
#             )
        
#         # 3. 检查是否需要撤销所有设备的token
#         revoke_all_devices = request.get_json().get('revoke_all_devices', False)
#         if revoke_all_devices:
#             # 方式1：更新用户的token撤销时间
#             user.tokens_revoked_at = datetime.now(timezone.utc)
#
#             # 方式2：或者更新token版本号
#             # user.token_version = str(int(user.token_version or 0) + 1)
        
#         # 4. 记录审计日志（如果实现了审计系统）
#         try:
#             from src.models.admin_audit_log import AuditLog, AuditAction, ResourceType
#             AuditLog.log_action(
#                 user=user,
#                 action=AuditAction.LOGOUT,
#                 resource_type=ResourceType.USER,
#                 description="用户登出",
#                 status='success'
#             )
#         except:
#             pass  # 审计失败不影响登出功能
        
#         # 5. 更新数据库
#         db.session.commit()
        
#         # 6. 记录系统日志
#         logger.info(f"User logout successful: {user.username}, token revoked: {access_jti[:8] if access_jti else 'none'}...")
        
#         return jsonify({
#             'message': 'Logout successful',
#             'revoked_tokens': 1 if access_jti else 0,
#             'timestamp': datetime.now(timezone.utc).isoformat()
#         })
        
#     except Exception as e:
#         logger.error(f"Logout error: {str(e)}")
#         db.session.rollback()
#         return jsonify({'error': 'Internal server error'}), 500