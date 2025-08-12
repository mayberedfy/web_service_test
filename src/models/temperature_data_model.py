import uuid
import ulid
from sqlalchemy import Boolean, Float, Integer, String, DateTime, Column, Text, JSON
from datetime import datetime, timezone, timedelta

from src.extensions import db 

# 辅助函数：将UTC时间转换为北京时间 (UTC+8)
def to_beijing_time(utc_dt):
    if utc_dt is None:
        return None
    beijing_tz = timezone(timedelta(hours=8))
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(beijing_tz)

# 1. 创建一个自定义的Query类，它会自动过滤
class ActiveQuery(db.Query):
    def active(self):
        return self.filter_by(is_deleted=False)

class TemperatureData(db.Model):
    __tablename__ = 'temperature_datas'

    # 启用软删除的默认查询
    query_class = ActiveQuery

    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new())) 
    product_sn = Column(String(32), nullable=False, index=True)
    
    # 测试时间相关
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    test_runtime = Column(Integer, nullable=True, comment='测试运行时长，单位：秒')
    
    # 温度采样相关
    sample_interval = Column(Integer, nullable=True, comment='采样间隔，单位：秒')
    original_temperature = Column(JSON, nullable=True, comment='原始温度数据数组')
    original_temperature_count = Column(Integer, nullable=True, comment='原始温度数据点数量')
    compensated_temperature = Column(JSON, nullable=True, comment='补偿后温度数据数组')
    
    # 温度补偿相关
    temperature_compensation_enabled = Column(Boolean, nullable=False, default=False, comment='是否启用温度补偿')
    temperature_compensation_value = Column(Float, nullable=True, comment='温度补偿值')
    temperature_compensation_duration = Column(Integer, nullable=True, comment='温度补偿持续时间，单位：秒')
    
    # 网络信息
    local_ip = Column(String(128), nullable=True)
    public_ip = Column(String(128), nullable=True)
    hostname = Column(String(255), nullable=True)
    app_version = db.Column(db.String(128), nullable=True, default='1.0.0')
    
    remark = Column(String(255), nullable=True)
    
    # 审计和软删除字段
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    delete_time = Column(DateTime, nullable=True, comment='删除时间，若未删除则为None')
    create_time = Column(DateTime, default=db.func.current_timestamp())
    update_time = Column(DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'product_sn': self.product_sn,
            
            # 测试时间相关
            'start_time': to_beijing_time(self.start_time).isoformat() if self.start_time else None,
            'end_time': to_beijing_time(self.end_time).isoformat() if self.end_time else None,
            'test_runtime': self.test_runtime,
            
            # 温度采样相关
            'sample_interval': self.sample_interval,
            'original_temperature': self.original_temperature,
            'original_temperature_count': self.original_temperature_count,
            'compensated_temperature': self.compensated_temperature,
            
            # 温度补偿相关
            'temperature_compensation_enabled': self.temperature_compensation_enabled,
            'temperature_compensation_value': self.temperature_compensation_value,
            'temperature_compensation_duration': self.temperature_compensation_duration,
            
            # 网络信息
            'local_ip': self.local_ip,
            'public_ip': self.public_ip,
            'hostname': self.hostname,
            'app_version': self.app_version,
            
            'remark': self.remark,
            
            # 审计和软删除字段
            'is_deleted': self.is_deleted,
            'delete_time': to_beijing_time(self.delete_time).isoformat() if self.delete_time else None,
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None,
        }