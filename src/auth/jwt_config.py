from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
from datetime import timedelta
from src.models.admin_user_model import User

jwt = JWTManager()

def init_jwt(app):
    """初始化JWT配置"""
    app.config.setdefault('JWT_SECRET_KEY', app.config.get('SECRET_KEY'))
    app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=2))
    app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=7))
    
    jwt.init_app(app)

def create_tokens_for_user(user: User):
    """为用户创建访问令牌"""
    additional_claims = {
        'role': user.role,                      # 角色信息
        'permissions': user.permissions or [],  # 权限列表
        'username': user.username
    }
    
    # 创建访问令牌（短期，2小时）
    access_token = create_access_token(
        identity=user.id,
        additional_claims=additional_claims
    )
    
    # 创建刷新令牌（长期，7天）
    refresh_token = create_refresh_token(identity=user.id)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }