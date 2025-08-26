import uuid
import ulid
import secrets
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
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





class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new()))
    key_name = Column(String(128), nullable=False)                          # 密钥名称
    key_description = Column(String(512), nullable=True)                    # 密钥用途和备注信息
    key_hash = Column(String(256), nullable=False, index=True)              # 密钥哈希值，不存原文
    key_prefix = Column(String(16), nullable=False)                         # 密钥前缀(显示用)
    
    # 权限和作用域
    scope = Column(String(64), nullable=False, default='upload')    # 作用域：upload/read/manage
    permissions = Column(JSON, nullable=True, default=list)         # 具体权限列表
    allowed_ips = Column(JSON, nullable=True)  # IP白名单
    
    # 状态管理
    is_active = Column(Boolean, nullable=False, default=True)       # 是否激活
    expires_at = Column(DateTime, nullable=True)
    
    # 使用统计
    last_used = Column(DateTime, nullable=True)
    usage_count = Column(String(10), nullable=False, default='0')
    
    # 审计字段
    created_by = Column(String(26), nullable=True)  # 创建者用户ID
    create_time = Column(DateTime, default=db.func.current_timestamp())
    update_time = Column(DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    @classmethod
    def generate_key(cls, name: str, description: str = None, scope: str = 'upload', permissions: list = None, created_by: str = None) -> tuple:
        """生成新的API密钥"""
        # 生成32字节随机密钥
        key = f"hpws_{secrets.token_urlsafe(32)}"
        key_hash = generate_password_hash(key)  # 存储哈希，不存原文
        
        api_key = cls(
            key_name=name,
            key_description=description,
            key_hash=key_hash,
            key_prefix=key[:12] + "...",  # 只保存前缀用于显示
            scope=scope,
            permissions=permissions or [],
            created_by=created_by
        )
        
        return api_key, key  # 返回模型和原始密钥
    
    def verify_key(self, key: str) -> bool:
        """验证密钥"""
        return check_password_hash(self.key_hash, key)
    
    def is_valid(self) -> bool:
        """检查密钥是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True
    
    def has_permission(self, permission: str) -> bool:
        """检查是否有特定权限"""
        return permission in (self.permissions or [])
    
    def update_usage(self):
        """更新使用统计"""
        self.last_used = datetime.now(timezone.utc)
        self.usage_count = str(int(self.usage_count) + 1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key_name': self.key_name,
            'key_description': self.key_description,
            'key_prefix': self.key_prefix,
            'key_hash': self.key_hash,

            'scope': self.scope,
            'permissions': self.permissions,
            'allowed_ips': self.allowed_ips,

            'is_active': self.is_active,
            'expires_at': to_beijing_time(self.expires_at).isoformat() if self.expires_at else None,

            'last_used': to_beijing_time(self.last_used).isoformat() if self.last_used else None,
            'usage_count': self.usage_count,

            'created_by': self.created_by,
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None,
        }