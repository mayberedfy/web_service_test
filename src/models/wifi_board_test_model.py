import uuid
import ulid # Import ulid
from sqlalchemy import UUID # Changed back to generic UUID

from src.extensions import db # Import the db instance

class WifiBoardTest(db.Model):
    __tablename__ = 'wifi_board_tests'

    id = db.Column(db.String(26), primary_key=True, default=lambda: str(ulid.new())) # Use ULID
    wifi_board_sn = db.Column(db.String(32), nullable=False)
    general_test_result = db.Column(db.String(64), nullable=False) 
    
    knob_test_result = db.Column(db.String(64), nullable=True)
    speed_knob_result = db.Column(db.String(64), nullable=True)
    speed_knob_remark = db.Column(db.String(64), nullable=True)
    time_knob_result = db.Column(db.String(64), nullable=True)
    time_knob_remark = db.Column(db.String(64), nullable=True)
    knob_start_time = db.Column(db.DateTime, nullable=True)
    knob_end_time = db.Column(db.DateTime, nullable=True)

    light_test_result = db.Column(db.String(64), nullable=True)
    green_light_result = db.Column(db.String(64), nullable=True)
    red_light_result = db.Column(db.String(64), nullable=True)
    blue_light_result = db.Column(db.String(64), nullable=True)
    light_start_time = db.Column(db.DateTime, nullable=True)
    light_end_time = db.Column(db.DateTime, nullable=True)

    network_test_result = db.Column(db.String(64), nullable=True)
    wifi_software_version = db.Column(db.String(32), nullable=True)
    mac_address = db.Column(db.String(64), nullable=True)
    start_command_result = db.Column(db.String(64), nullable=True)
    speed_command_result = db.Column(db.String(64), nullable=True)
    stop_command_result = db.Column(db.String(64), nullable=True)
    network_start_time = db.Column(db.DateTime, nullable=True)
    network_end_time = db.Column(db.DateTime, nullable=True)

    test_ip_address = db.Column(db.String(32), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    general_test_remark = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': str(self.id) if self.id else None,
            'wifi_board_sn': self.wifi_board_sn,
            'general_test_result': self.general_test_result,
            
            # 旋钮测试相关
            'knob_test_result': self.knob_test_result,
            'speed_knob_result': self.speed_knob_result,
            'speed_knob_remark': self.speed_knob_remark,
            'time_knob_result': self.time_knob_result,
            'time_knob_remark': self.time_knob_remark,
            'knob_start_time': self.knob_start_time.isoformat() if self.knob_start_time else None,
            'knob_end_time': self.knob_end_time.isoformat() if self.knob_end_time else None,
            
            # 灯光测试相关
            'light_test_result': self.light_test_result,
            'green_light_result': self.green_light_result,
            'red_light_result': self.red_light_result,
            'blue_light_result': self.blue_light_result,
            'light_start_time': self.light_start_time.isoformat() if self.light_start_time else None,
            'light_end_time': self.light_end_time.isoformat() if self.light_end_time else None,
            
            # 网络测试相关
            'network_test_result': self.network_test_result,
            'wifi_software_version': self.wifi_software_version,
            'mac_address': self.mac_address,
            'start_command_result': self.start_command_result,
            'speed_command_result': self.speed_command_result,
            'stop_command_result': self.stop_command_result,
            'network_start_time': self.network_start_time.isoformat() if self.network_start_time else None,
            'network_end_time': self.network_end_time.isoformat() if self.network_end_time else None,
            
            # 通用信息
            'test_ip_address': self.test_ip_address,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'general_test_remark': self.general_test_remark
        }