import ulid
from sqlalchemy import Boolean, Text
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

# 1. 创建一个自定义的Query类，它会自动过滤
class ActiveQuery(db.Query):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 自动为所有查询应用 is_deleted=False 的过滤器
        self._criterion = self._criterion.filter_by(is_deleted=False)

class WifiTestLog(db.Model):
    """
    用于存储Wi-Fi板测试过程中的原始数据日志。
    """
    __tablename__ = 'wifi_test_logs'

    # 2. 将自定义的Query类赋给 query_class
    query_class = ActiveQuery

    # 核心字段
    id = db.Column(db.String(26), primary_key=True, default=lambda: str(ulid.new()))
    wifi_board_sn = db.Column(db.String(32), nullable=False, index=True)
    mac_address = db.Column(db.String(64), nullable=True, index=True)
    
    # 日志数据和来源信息
    raw_data = db.Column(Text, nullable=False) # 使用Text类型存储大量原始数据
    local_ip = db.Column(db.String(64), nullable=True)
    public_ip = db.Column(db.String(64), nullable=True)
    host_name = db.Column(db.String(255), nullable=True)
    app_version = db.Column(db.String(128), nullable=True, default='1.0.0')

    is_deleted = db.Column(Boolean, nullable=False, default=False, index=True)

    # 时间戳
    create_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    delete_time = db.Column(db.DateTime, nullable=True, comment='删除时间，若未删除则为None')
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        """将模型对象转换为字典，并处理时区。"""
        return {
            'id': self.id,
            'wifi_board_sn': self.wifi_board_sn,
            'mac_address': self.mac_address,
            'raw_data': self.raw_data,
            
            'local_ip': self.local_ip,
            'public_ip': self.public_ip,
            'host_name': self.host_name,
            'app_version': self.app_version,

            'is_deleted': self.is_deleted, 
            # 使用辅助函数进行转换
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'delete_time': to_beijing_time(self.delete_time).isoformat() if self.delete_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None,
        }