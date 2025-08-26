import uuid
import ulid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from werkzeug.security import generate_password_hash, check_password_hash
from src.extensions import db
from datetime import datetime, timezone, timedelta


# 辅助函数：将UTC时间转换为北京时间 (UTC+8)
def to_beijing_time(utc_dt):
    if utc_dt is None:
        return None
    # 创建一个代表北京时间的时区对象
    beijing_tz = timezone(timedelta(hours=8))
    # 将无时区的UTC时间强制指定为UTC时区，然后转换为北京时间
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(beijing_tz)



class User(db.Model):
    __tablename__ = 'users'
    
    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=True, index=True)
    password_hash = Column(String(256), nullable=False)
    
    # 角色权限
    role = Column(String(32), nullable=False, default='viewer')  # admin, manager, operator, viewer
    permissions = Column(JSON, nullable=True, default=list)  # 具体权限列表
    
    # 状态管理
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    
    # 安全字段
    last_login = Column(DateTime, nullable=True)
    login_count = Column(String(10), nullable=False, default='0')
    failed_login_attempts = Column(String(10), nullable=False, default='0')
    locked_until = Column(DateTime, nullable=True)
    
    # 审计字段
    created_by = Column(String(26), nullable=True)
    create_time = Column(DateTime, default=db.func.current_timestamp())
    update_time = Column(DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def set_password(self, password: str):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        if self.role == 'admin':
            return True
        return permission in (self.permissions or [])
    
    def has_role(self, role: str) -> bool:
        """检查是否有特定角色"""
        if isinstance(role, list):
            return self.role in role
        return self.role == role
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'permissions': self.permissions,
            'is_active': self.is_active,
            
            'last_login': to_beijing_time(self.last_login).isoformat() if self.last_login else None,
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None
        }