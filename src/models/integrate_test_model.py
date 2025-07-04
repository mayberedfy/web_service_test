import uuid
import ulid
from sqlalchemy import UUID # Changed back to generic UUID

from src.extensions import db 

class IntegrateTest(db.Model):
    __tablename__ = 'integrate_tests'

    id = db.Column(db.String(26), primary_key=True, default=lambda: str(ulid.new())) 
    integrate_sn = db.Column(db.String(32), nullable=False)
    general_test_result = db.Column(db.String(64), nullable=False) 
    
    # 记录是否通过测试
    motor_status_result = db.Column(db.String(64), nullable=True)
    motor_speed_result = db.Column(db.String(64), nullable=True)
    ipm_temperature_result = db.Column(db.String(64), nullable=True)
    dc_voltage_result = db.Column(db.String(64), nullable=True)
    output_power_result = db.Column(db.String(64), nullable=True) 
    driver_software_version_result = db.Column(db.String(64), nullable=True)
    power_ac_voltage_result = db.Column(db.String(64), nullable=True)
    power_current_result = db.Column(db.String(64), nullable=True)
    power_power_result = db.Column(db.String(64), nullable=True)
    power_power_factor_result = db.Column(db.String(64), nullable=True)
    leakage_current_result = db.Column(db.String(64), nullable=True)

    # 记录最终的测试结果
    motor_status = db.Column(db.String(64), nullable=True)
    motor_speed = db.Column(db.String(64), nullable=True)
    ipm_temperature = db.Column(db.String(64), nullable=True)
    dc_voltage = db.Column(db.String(64), nullable=True)
    output_power = db.Column(db.String(64), nullable=True) 
    driver_software_version = db.Column(db.String(64), nullable=True)
    power_ac_voltage = db.Column(db.String(64), nullable=True)
    power_current = db.Column(db.String(64), nullable=True)
    power_power = db.Column(db.String(64), nullable=True)
    power_power_factor = db.Column(db.String(64), nullable=True)
    leakage_current = db.Column(db.String(64), nullable=True)

    test_runtime = db.Column(db.Integer, nullable=True, comment='测试运行时长，单位：秒')
    test_ip_address = db.Column(db.String(32), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    general_test_remark = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'integrate_sn': self.integrate_sn,  # 修正字段名
            'general_test_result': self.general_test_result,
            
            # 测试结果字段（是否通过测试）
            'motor_status_result': self.motor_status_result,
            'motor_speed_result': self.motor_speed_result,
            'ipm_temperature_result': self.ipm_temperature_result,
            'dc_voltage_result': self.dc_voltage_result,
            'output_power_result': self.output_power_result,
            'driver_software_version_result': self.driver_software_version_result,
            'power_ac_voltage_result': self.power_ac_voltage_result,
            'power_current_result': self.power_current_result,
            'power_power_result': self.power_power_result,
            'power_power_factor_result': self.power_power_factor_result,
            'leakage_current_result': self.leakage_current_result,
            
            # 测试数值字段（实际测试数据）
            'motor_status': self.motor_status,
            'motor_speed': self.motor_speed,
            'ipm_temperature': self.ipm_temperature,
            'dc_voltage': self.dc_voltage,
            'output_power': self.output_power,
            'driver_software_version': self.driver_software_version,
            'power_ac_voltage': self.power_ac_voltage,
            'power_current': self.power_current,
            'power_power': self.power_power,
            'power_power_factor': self.power_power_factor,
            'leakage_current': self.leakage_current,
            
            # 测试时间和运行信息
            'test_runtime': self.test_runtime,  # 整数类型，单位：秒
            'test_ip_address': self.test_ip_address,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'general_test_remark': self.general_test_remark
        }