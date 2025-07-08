import uuid
import ulid
from sqlalchemy import Boolean, Float, Integer, String, DateTime, Column
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 自动为所有查询应用 is_deleted=False 的过滤器
        self._criterion = self._criterion.filter_by(is_deleted=False)

class IntegrateTest(db.Model):
    __tablename__ = 'integrate_tests'

    # 启用软删除的默认查询
    query_class = ActiveQuery

    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new())) 
    product_sn = Column(String(32), nullable=False, index=True) # 添加索引
    integrate_test_result = Column(String(64), nullable=False) 

    # 记录最终的测试结果
    driver_status = Column(String(64), nullable=True)
    driver_status_result = Column(String(64), nullable=True)

    motor_speed = Column(String(64), nullable=True)
    motor_speed_result = Column(String(64), nullable=True)

    ipm_temperature = Column(String(64), nullable=True)
    ipm_temperature_result = Column(String(64), nullable=True)

    dc_voltage = Column(String(64), nullable=True)
    dc_voltage_result = Column(String(64), nullable=True)

    output_power = Column(String(64), nullable=True) 
    output_power_result = Column(String(64), nullable=True) 

    driver_software_version = Column(String(64), nullable=True)
    driver_software_version_result = Column(String(64), nullable=True)

    ac_voltage = Column(String(64), nullable=True)
    ac_voltage_result = Column(String(64), nullable=True)

    current = Column(String(64), nullable=True)
    current_result = Column(String(64), nullable=True)

    power = Column(String(64), nullable=True)
    power_result = Column(String(64), nullable=True)

    power_factor = Column(String(64), nullable=True)
    power_factor_result = Column(String(64), nullable=True)

    leakage_current = Column(String(64), nullable=True)
    leakage_current_result = Column(String(64), nullable=True)

    # --- 时间和描述信息 ---
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    test_runtime = Column(Integer, nullable=True)
    test_description = Column(String(255), nullable=True)
    remark = Column(String(255), nullable=True)

    # --- 使用更安全的字段长度 ---
    local_ip = Column(String(128), nullable=True)
    public_ip = Column(String(128), nullable=True)
    hostname = Column(String(255), nullable=True)


    ipm_temperature_data_id = Column(String(64), nullable=True)
    # --- 审计和软删除字段 ---
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    delete_time = Column(DateTime, nullable=True, comment='删除时间，若未删除则为None')
    create_time = Column(DateTime, default=db.func.current_timestamp())
    update_time = Column(DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'product_sn': self.product_sn, 
            'integrate_test_result': self.integrate_test_result,             

            'driver_status': self.driver_status,
            'driver_status_result': self.driver_status_result,
            'motor_speed': self.motor_speed,
            'motor_speed_result': self.motor_speed_result,
            'ipm_temperature': self.ipm_temperature,
            'ipm_temperature_result': self.ipm_temperature_result,
            'dc_voltage': self.dc_voltage,
            'dc_voltage_result': self.dc_voltage_result,
            'output_power': self.output_power,
            'output_power_result': self.output_power_result,
            'driver_software_version': self.driver_software_version,
            'driver_software_version_result': self.driver_software_version_result,
            'ac_voltage': self.ac_voltage,
            'ac_voltage_result': self.ac_voltage_result,
            'current': self.current,
            'current_result': self.current_result,
            'power': self.power,
            'power_result': self.power_result,
            'power_factor': self.power_factor,
            'power_factor_result': self.power_factor_result,
            'leakage_current': self.leakage_current,
            'leakage_current_result': self.leakage_current_result,

            'start_time': to_beijing_time(self.start_time).isoformat() if self.start_time else None,
            'end_time': to_beijing_time(self.end_time).isoformat() if self.end_time else None,
            'test_runtime': self.test_runtime,  
            'test_description': self.test_description,
            'remark': self.remark,

            'local_ip': self.local_ip,
            'public_ip': self.public_ip,
            'hostname': self.hostname,
            'ipm_temperature_data_id': self.ipm_temperature_data_id,

            'is_deleted': self.is_deleted,
            'delete_time': to_beijing_time(self.delete_time).isoformat() if self.delete_time else None,
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None,

        }