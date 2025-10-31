"""
设备管理 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.services import device_service
from app.log import logger
from typing import Dict, Any

router = APIRouter(prefix="/device")


# Pydantic 模型定义
class DeviceRegisterRequest(BaseModel):
    """设备注册请求"""
    device_id: str
    device_name: str
    device_type: str  # mobile/desktop/web
    platform: str | None = None  # iOS/Android/Windows/macOS/Linux
    app_version: str | None = None


class DeviceUpdateRequest(BaseModel):
    """设备更新请求"""
    device_name: str | None = None
    device_type: str | None = None
    platform: str | None = None
    app_version: str | None = None


# 辅助函数
def device_to_dict(device) -> Dict[str, Any]:
    """将设备对象转换为字典"""
    return {
        "device_id": device.device_id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "platform": device.platform,
        "app_version": device.app_version,
        "created_at": device.created_at.isoformat() if device.created_at else None,
        "updated_at": device.updated_at.isoformat() if device.updated_at else None,
    }


@router.post("/register", summary="注册设备")
async def register_device(
    request: DeviceRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    注册新设备或更新已存在的设备信息
    
    - **device_id**: 设备UUID (客户端生成)
    - **device_name**: 设备名称，如 "我的iPhone"
    - **device_type**: 设备类型 (mobile/desktop/web)
    - **platform**: 平台信息 (iOS/Android/Windows/macOS/Linux)
    - **app_version**: 客户端版本号
    """
    try:
        device = device_service.register_device(db, request.dict())
        return {
            "code": 200,
            "message": "设备注册成功",
            "data": device_to_dict(device)
        }
    except Exception as e:
        logger.error(f"设备注册失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", summary="获取设备列表")
async def get_device_list(db: Session = Depends(get_db)):
    """
    获取所有已注册设备列表
    """
    try:
        devices = device_service.get_device_list(db)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": len(devices),
                "list": [device_to_dict(device) for device in devices]
            }
        }
    except Exception as e:
        logger.error(f"获取设备列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{device_id}", summary="获取设备详情")
async def get_device_detail(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    根据设备ID获取设备详细信息
    """
    device = device_service.get_device_by_id(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    
    return {
        "code": 200,
        "message": "success",
        "data": device_to_dict(device)
    }


@router.put("/{device_id}", summary="更新设备信息")
async def update_device(
    device_id: str,
    request: DeviceUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新设备信息
    """
    try:
        # 过滤掉 None 值
        update_data = {k: v for k, v in request.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="没有提供需要更新的字段")
        
        device = device_service.update_device_info(db, device_id, update_data)
        if not device:
            raise HTTPException(status_code=404, detail="设备不存在")
        
        return {
            "code": 200,
            "message": "设备信息更新成功",
            "data": device_to_dict(device)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新设备信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{device_id}", summary="删除设备")
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    删除设备
    
    注意：只能删除没有关联音乐的设备
    """
    try:
        success = device_service.delete_device(db, device_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="设备不存在或有关联音乐，无法删除。请先从数据库手动删除关联音乐。"
            )
        
        return {
            "code": 200,
            "message": "设备删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除设备失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
