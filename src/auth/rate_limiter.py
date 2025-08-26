from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=None,
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)

def init_limiter(app):
    """初始化速率限制"""
    limiter.init_app(app)