"""
设备服务层
处理设备相关的业务逻辑
"""
from sqlalchemy.orm import Session
from app.models.device import Device
from app.log import logger
from datetime import datetime


def register_device(db: Session, device_data: dict) -> Device:
    """
    注册新设备
    
    Args:
        db: 数据库会话
        device_data: 设备信息字典
            - device_id: 设备UUID
            - device_name: 设备名称
            - device_type: 设备类型
            - platform: 平台信息(可选)
            - app_version: 应用版本(可选)
    
    Returns:
        Device: 创建的设备对象
    """
    # 检查设备是否已存在
    existing = db.query(Device).filter(Device.device_id == device_data["device_id"]).first()
    if existing:
        logger.info(f"设备已存在: {device_data['device_id']}")
        # 更新设备信息
        for key, value in device_data.items():
            if key != "device_id" and value is not None:
                setattr(existing, key, value)
        db.commit()
        db.refresh(existing)
        return existing
    
    # 创建新设备
    device = Device(**device_data)
    db.add(device)
    db.commit()
    db.refresh(device)
    
    logger.success(f"设备注册成功: {device.device_name} ({device.device_id})")
    return device


def get_device_list(db: Session) -> list[Device]:
    """
    获取所有设备列表
    
    Args:
        db: 数据库会话
    
    Returns:
        list[Device]: 设备列表
    """
    devices = db.query(Device).order_by(Device.created_at.desc()).all()
    return devices


def get_device_by_id(db: Session, device_id: str) -> Device | None:
    """
    根据设备ID获取设备信息
    
    Args:
        db: 数据库会话
        device_id: 设备UUID
    
    Returns:
        Device | None: 设备对象，不存在则返回None
    """
    return db.query(Device).filter(Device.device_id == device_id).first()


def delete_device(db: Session, device_id: str) -> bool:
    """
    删除设备
    注意: 此操作不会删除设备关联的音乐，需要手动从数据库处理
    
    Args:
        db: 数据库会话
        device_id: 设备UUID
    
    Returns:
        bool: 是否删除成功
    """
    device = get_device_by_id(db, device_id)
    if not device:
        logger.warning(f"设备不存在: {device_id}")
        return False
    
    # 检查是否有音乐关联
    from app.models.music import Music
    music_count = db.query(Music).filter(Music.device_id == device_id).count()
    if music_count > 0:
        logger.warning(f"设备 {device_id} 有 {music_count} 首音乐，无法删除")
        return False
    
    db.delete(device)
    db.commit()
    logger.success(f"设备删除成功: {device.device_name} ({device_id})")
    return True


def update_device_info(db: Session, device_id: str, update_data: dict) -> Device | None:
    """
    更新设备信息
    
    Args:
        db: 数据库会话
        device_id: 设备UUID
        update_data: 要更新的字段字典
    
    Returns:
        Device | None: 更新后的设备对象
    """
    device = get_device_by_id(db, device_id)
    if not device:
        logger.warning(f"设备不存在: {device_id}")
        return None
    
    for key, value in update_data.items():
        if hasattr(device, key) and key not in ["device_id", "created_at"]:
            setattr(device, key, value)
    
    db.commit()
    db.refresh(device)
    
    logger.info(f"设备信息更新成功: {device_id}")
    return device
