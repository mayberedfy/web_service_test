import uuid
import ulid
from sqlalchemy import UUID , Boolean
from datetime import datetime, timezone, timedelta

from src.extensions import db 

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
    def active(self):
        return self.filter_by(is_deleted=False)

class DriverBoardTest(db.Model):
    __tablename__ = 'driver_board_tests'

    # 启用软删除的默认查询
    query_class = ActiveQuery

    id = db.Column(db.String(26), primary_key=True, default=lambda: str(ulid.new())) 
    driver_board_sn = db.Column(db.String(32), nullable=False, index=True)
    driver_test_result = db.Column(db.String(64), nullable=False) 
    
    set_speed = db.Column(db.Integer, nullable=True, comment='设置速度，单位：RPM')

    motor_status = db.Column(db.String(64), nullable=True)
    motor_status_result = db.Column(db.String(64), nullable=True)
    motor_speed = db.Column(db.String(64), nullable=True)
    motor_speed_result = db.Column(db.String(64), nullable=True)
    ipm_temperature = db.Column(db.String(64), nullable=True)
    ipm_temperature_result = db.Column(db.String(64), nullable=True)
    dc_voltage = db.Column(db.String(64), nullable=True)
    dc_voltage_result = db.Column(db.String(64), nullable=True)
    output_power = db.Column(db.String(64), nullable=True) 
    output_power_result = db.Column(db.String(64), nullable=True) 
    driver_software_version = db.Column(db.String(64), nullable=True)
    driver_software_version_result = db.Column(db.String(64), nullable=True)

    test_runtime = db.Column(db.Integer, nullable=True, comment='测试运行时长，单位：秒')    
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    test_description = db.Column(db.String(255), nullable=True)
    general_test_remark = db.Column(db.String(255), nullable=True)

    # 修改字段长度以支持IPv6
    local_ip = db.Column(db.String(128), nullable=True)
    public_ip = db.Column(db.String(128), nullable=True)
    hostname = db.Column(db.String(255), nullable=True)
    app_version = db.Column(db.String(128), nullable=True, default='1.0.0')

    create_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_deleted = db.Column(Boolean, nullable=False, default=False, index=True)  
    delete_time = db.Column(db.DateTime, nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'driver_board_sn': self.driver_board_sn,  
            'driver_test_result': self.driver_test_result,
            
            'set_speed': self.set_speed,
            
            'motor_status': self.motor_status,
            'motor_status_result': self.motor_status_result,
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

            'test_runtime': self.test_runtime,
            'start_time': to_beijing_time(self.start_time).isoformat() if self.start_time else None,
            'end_time': to_beijing_time(self.end_time).isoformat() if self.end_time else None,
            'test_description': self.test_description,
            'general_test_remark': self.general_test_remark,

            'local_ip': self.local_ip,
            'public_ip': self.public_ip,
            'hostname': self.hostname,
            'app_version': self.app_version,

            'is_deleted': self.is_deleted,
            'delete_time': to_beijing_time(self.delete_time).isoformat() if self.delete_time else None,
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None,
        }