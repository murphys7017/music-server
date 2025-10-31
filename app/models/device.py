"""
设备模型
用于管理客户端设备信息
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from app.database import Base


class Device(Base):
    """设备信息表"""
    __tablename__ = "devices"

    device_id = Column(CHAR(36), primary_key=True, comment="设备UUID")
    device_name = Column(String(128), nullable=False, comment="设备名称")
    device_type = Column(String(32), nullable=False, comment="设备类型(mobile/desktop/web)")
    platform = Column(String(32), nullable=True, comment="平台信息(iOS/Android/Windows/macOS/Linux)")
    app_version = Column(String(32), nullable=True, comment="客户端版本")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Device {self.device_name} ({self.device_type})>"
