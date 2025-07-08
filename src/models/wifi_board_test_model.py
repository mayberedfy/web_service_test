import uuid
import ulid
from sqlalchemy import UUID, Boolean # Changed back to generic UUID
from datetime import datetime, timezone, timedelta

from src.extensions import db # Import the db instance

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

class WifiBoardTest(db.Model):
    __tablename__ = 'wifi_board_tests'

    # 启用软删除的默认查询
    query_class = ActiveQuery

    id = db.Column(db.String(26), primary_key=True, default=lambda: str(ulid.new())) # Use ULID
    wifi_board_sn = db.Column(db.String(32), nullable=False, index=True)
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
    wifi_software_version = db.Column(db.String(64), nullable=True)
    mac_address = db.Column(db.String(64), nullable=True)
    start_command_result = db.Column(db.String(64), nullable=True)
    speed_command_result = db.Column(db.String(64), nullable=True)
    stop_command_result = db.Column(db.String(64), nullable=True)
    network_start_time = db.Column(db.DateTime, nullable=True)
    network_end_time = db.Column(db.DateTime, nullable=True)


    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    general_test_remark = db.Column(db.String(255), nullable=True)

    # --- 使用更安全的字段长度 ---
    local_ip = db.Column(db.String(128), nullable=True)
    public_ip = db.Column(db.String(128), nullable=True)
    hostname = db.Column(db.String(255), nullable=True)

    # 新增审计和软删除字段
    create_time = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_deleted = db.Column(Boolean, nullable=False, default=False, index=True)  
    delete_time = db.Column(db.DateTime, nullable=True)
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

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
            'knob_start_time': to_beijing_time(self.knob_start_time).isoformat() if self.knob_start_time else None,
            'knob_end_time': to_beijing_time(self.knob_end_time).isoformat() if self.knob_end_time else None,
            
            # 灯光测试相关
            'light_test_result': self.light_test_result,
            'green_light_result': self.green_light_result,
            'red_light_result': self.red_light_result,
            'blue_light_result': self.blue_light_result,
            'light_start_time': to_beijing_time(self.light_start_time).isoformat() if self.light_start_time else None,
            'light_end_time': to_beijing_time(self.light_end_time).isoformat() if self.light_end_time else None,
            
            # 网络测试相关
            'network_test_result': self.network_test_result,
            'wifi_software_version': self.wifi_software_version,
            'mac_address': self.mac_address,
            'start_command_result': self.start_command_result,
            'speed_command_result': self.speed_command_result,
            'stop_command_result': self.stop_command_result,
            'network_start_time': to_beijing_time(self.network_start_time).isoformat() if self.network_start_time else None,
            'network_end_time': to_beijing_time(self.network_end_time).isoformat() if self.network_end_time else None,
            
            # 通用信息
            
            'start_time': to_beijing_time(self.start_time).isoformat() if self.start_time else None,
            'end_time': to_beijing_time(self.end_time).isoformat() if self.end_time else None,
            'general_test_remark': self.general_test_remark,
            
            'local_ip': self.local_ip,
            'public_ip': self.public_ip,
            'hostname': self.hostname,


            # 审计和软删除字段
            'is_deleted': self.is_deleted,
            'delete_time': to_beijing_time(self.delete_time).isoformat() if self.delete_time else None,
            'create_time': to_beijing_time(self.create_time).isoformat() if self.create_time else None,
            'update_time': to_beijing_time(self.update_time).isoformat() if self.update_time else None,
        }