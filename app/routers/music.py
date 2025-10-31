"""
音乐相关API路由
提供音乐列表查询、搜索、播放、封面等接口
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pathlib import Path
from urllib.parse import unquote
from pydantic import BaseModel

from app.config import Config
from app.database import get_db
from app.models.music import Music
from app.services import music_service
from app.log import logger

router = APIRouter(prefix="/music", tags=["music"])


# Pydantic 模型定义
class MusicAddRequest(BaseModel):
    """客户端添加音乐请求"""
    uuid: str
    md5: str
    device_id: str
    name: str
    author: str = "未知"
    album: str = ""
    source: str = "local"
    duration: int = 0
    size: int = 0
    bitrate: int = 0
    file_format: str | None = None
    local_path: str | None = None  # 服务端本地文件路径
    cover_uuid: str | None = None
    lyric: str | None = None


@router.post("/add")
async def add_music(
    request: MusicAddRequest,
    db: Session = Depends(get_db)
):
    """
    客户端添加音乐（仅上传元数据）
    
    - **uuid**: 音乐UUID（客户端生成）
    - **md5**: 文件MD5
    - **device_id**: 设备ID
    - **name**: 歌曲名
    - **author**: 艺术家
    - **其他元数据**: 专辑、时长、比特率等
    
    注意：(md5, device_id) 必须唯一
    """
    try:
        music = music_service.add_music_from_client(db, request.dict())
        
        return {
            "code": 200,
            "message": "音乐添加成功",
            "data": {
                "uuid": music.uuid,
                "name": music.name,
                "author": music.author,
                "device_id": music.device_id,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加音乐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_music(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    device_id: Optional[str] = Query(None, description="设备ID（不传则返回所有设备的音乐）"),
    db: Session = Depends(get_db)
):
    """
    分页查询音乐列表
    支持按设备过滤
    
    - **page**: 页码
    - **page_size**: 每页数量
    - **device_id**: 设备ID（可选）
      - 不传：返回所有音乐
      - "server"：仅服务器音乐
      - 其他：指定设备的音乐
    """
    try:
        # 使用新的服务层函数，支持设备过滤
        result = music_service.query_music_by_device(
            db=db,
            device_id=device_id,
            page=page,
            page_size=page_size
        )
        
        # 序列化为JSON
        music_list = []
        for music in result['list']:
            music_dict = music_service.music_to_json(music)
            # 添加播放URL
            music_dict['play_url'] = f"/music/play/{music.uuid}"
            # 添加封面和缩略图URL
            cover_uuid = getattr(music, 'cover_uuid', None)
            if cover_uuid:
                music_dict['cover_url'] = f"/music/cover/{cover_uuid}"
                music_dict['thumbnail_url'] = f"/music/thumbnail/{cover_uuid}"
            else:
                music_dict['cover_url'] = None
                music_dict['thumbnail_url'] = None
            # list接口不返回歌词
            music_dict.pop('lyric', None)
            music_list.append(music_dict)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": result['total'],
                "page": page,
                "page_size": page_size,
                "list": music_list
            }
        }
    except Exception as e:
        logger.error(f"查询音乐列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_music(
    keyword: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    device_id: Optional[str] = Query(None, description="设备ID（不传则搜索所有设备）"),
    db: Session = Depends(get_db)
):
    """
    模糊搜索音乐
    支持按歌名、作者、专辑搜索（OR逻辑）
    支持按设备过滤
    """
    try:
        # 使用新的服务层函数，支持设备过滤
        result = music_service.fuzzy_query_music_by_device(
            db=db,
            device_id=device_id,
            name=keyword,
            author=keyword,
            album=keyword,
            page=page,
            page_size=page_size
        )
        
        # 序列化结果
        music_list = []
        for music in result['list']:
            music_dict = music_service.music_to_json(music)
            music_dict['play_url'] = f"/music/play/{music.uuid}"
            cover_uuid = getattr(music, 'cover_uuid', None)
            if cover_uuid:
                music_dict['cover_url'] = f"/music/cover/{cover_uuid}"
                music_dict['thumbnail_url'] = f"/music/thumbnail/{cover_uuid}"
            else:
                music_dict['cover_url'] = None
                music_dict['thumbnail_url'] = None
            # search接口不返回歌词
            music_dict.pop('lyric', None)
            music_list.append(music_dict)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": result['total'],
                "page": page,
                "page_size": page_size,
                "list": music_list
            }
        }
    except Exception as e:
        logger.error(f"搜索音乐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/lyric")
async def search_music_by_lyric(
    keyword: str = Query(..., description="歌词关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    根据歌词内容搜索音乐
    只搜索包含歌词的音乐
    """
    try:
        # 调用服务层函数
        result = music_service.search_music_by_lyric(
            db=db,
            lyric_keyword=keyword,
            page=page,
            page_size=page_size
        )
        
        # 序列化结果
        music_list = []
        for music in result['list']:
            music_dict = music_service.music_to_json(music)
            music_dict['play_url'] = f"/music/play/{music.uuid}"
            cover_uuid = getattr(music, 'cover_uuid', None)
            if cover_uuid:
                music_dict['cover_url'] = f"/music/cover/{cover_uuid}"
                music_dict['thumbnail_url'] = f"/music/thumbnail/{cover_uuid}"
            else:
                music_dict['cover_url'] = None
                music_dict['thumbnail_url'] = None
            # 歌词搜索接口保留歌词（方便高亮显示匹配部分）
            music_list.append(music_dict)
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": result['total'],
                "page": page,
                "page_size": page_size,
                "keyword": keyword,
                "list": music_list
            }
        }
    except Exception as e:
        logger.error(f"根据歌词搜索音乐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail/{uuid}")
async def get_music_detail(
    uuid: str,
    db: Session = Depends(get_db)
):
    """
    获取音乐详细信息
    """
    try:
        music = music_service.get_music_by_uuid(db, uuid)
        if not music:
            raise HTTPException(status_code=404, detail="Music not found")
        
        music_dict = music_service.music_to_json(music)
        music_dict['play_url'] = f"/music/play/{music.uuid}"
        cover_uuid = getattr(music, 'cover_uuid', None)
        if cover_uuid:
            music_dict['cover_url'] = f"/music/cover/{cover_uuid}"
            music_dict['thumbnail_url'] = f"/music/thumbnail/{cover_uuid}"
        else:
            music_dict['cover_url'] = None
            music_dict['thumbnail_url'] = None
        
        return {
            "code": 200,
            "message": "success",
            "data": music_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取音乐详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/play/{uuid}")
async def play_music(
    uuid: str,
    db: Session = Depends(get_db)
):
    """
    播放音乐（音频流）
    根据UUID从数据库查找音乐文件并返回流
    
    工作流程：
    1. 服务端音乐（device_id="server"）：直接使用 local_path 播放
    2. 客户端音乐（其他 device_id）：
       - 客户端应优先检查本地映射表
       - 本地没有时，可以调用此接口从服务器获取（如果服务器有副本）
    """
    try:
        # 从数据库获取音乐信息
        music = music_service.get_music_by_uuid(db, uuid)
        if not music:
            raise HTTPException(status_code=404, detail="Music not found")
        
        file_path = None
        
        # 优先使用 local_path（适用于服务端音乐和有本地副本的客户端音乐）
        local_path_value = getattr(music, 'local_path', None)
        if local_path_value:
            file_path = Path(local_path_value)
            if not file_path.exists():
                logger.warning(f"local_path 指向的文件不存在: {local_path_value}")
                file_path = None
        
        # 如果没有找到文件
        if not file_path:
            device_id = getattr(music, 'device_id', 'server')
            if device_id == 'server':
                # 服务端音乐但没有 local_path，尝试在 MUSIC_DIR 查找
                music_dir = Path(Config.MUSIC_DIR)
                
                for ext in Config.MUSIC_EXTS:
                    possible_names = [
                        f"{music.name} - {music.author}{ext}",
                        f"{music.name}-{music.author}{ext}",
                        f"{music.author} - {music.name}{ext}",
                    ]
                    for name in possible_names:
                        test_path = music_dir / name
                        if test_path.exists():
                            file_path = test_path
                            break
                    if file_path:
                        break
                
                if not file_path:
                    logger.error(f"服务端音乐文件未找到: {music.name} - {music.author} (UUID: {uuid})")
                    raise HTTPException(status_code=404, detail="Music file not found on server")
            else:
                # 客户端音乐，服务器没有副本
                logger.info(f"客户端音乐，服务器无副本: {music.name} (device_id: {device_id})")
                raise HTTPException(
                    status_code=404,
                    detail=f"Music file not available on server (device_id: {device_id})"
                )
        
        # 更新播放次数
        current_count = getattr(music, 'play_count', 0)
        setattr(music, 'play_count', current_count + 1)
        db.commit()
        
        # 确定MIME类型
        ext = file_path.suffix.lower()
        mime_map = {
            '.mp3': 'audio/mpeg',
            '.flac': 'audio/flac',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.wma': 'audio/x-ms-wma'
        }
        media_type = mime_map.get(ext, 'application/octet-stream')
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=file_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"播放音乐失败 {uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cover/{cover_uuid}")
async def get_cover(cover_uuid: str):
    """
    获取封面图片
    根据cover_uuid返回封面文件
    """
    try:
        cover_uuid = unquote(cover_uuid)
        
        # 在封面目录查找文件
        cover_dir = Path(Config.COVER_DIR)
        
        # 尝试所有可能的扩展名
        cover_path = None
        for ext in Config.COVER_EXTS:
            test_path = cover_dir / f"{cover_uuid}{ext}"
            if test_path.exists():
                cover_path = test_path
                break
        
        if not cover_path or not cover_path.exists():
            raise HTTPException(status_code=404, detail="Cover not found")
        
        # 确定MIME类型
        ext = cover_path.suffix.lower()
        mime_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.bmp': 'image/bmp'
        }
        media_type = mime_map.get(ext, 'application/octet-stream')
        
        return FileResponse(
            path=str(cover_path),
            media_type=media_type,
            filename=cover_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取封面失败 {cover_uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lyric/{uuid}")
async def get_lyric(
    uuid: str,
    db: Session = Depends(get_db)
):
    """
    获取歌词
    """
    try:
        music = music_service.get_music_by_uuid(db, uuid)
        if not music:
            raise HTTPException(status_code=404, detail="Music not found")
        
        return {
            "code": 200,
            "message": "success",
            "data": {
                "uuid": music.uuid,
                "name": music.name,
                "author": music.author,
                "lyric": music.lyric or ""
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取歌词失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thumbnail/{cover_uuid}")
async def get_thumbnail(cover_uuid: str):
    """
    获取缩略图
    根据cover_uuid返回缩略图文件（小体积JPEG格式）
    """
    try:
        from urllib.parse import unquote
        cover_uuid = unquote(cover_uuid)
        
        # 在缩略图目录查找文件（统一为.jpg格式）
        thumbnail_dir = Path(Config.THUMBNAIL_DIR)
        thumbnail_path = thumbnail_dir / f"{cover_uuid}.jpg"
        
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(
            path=str(thumbnail_path),
            media_type='image/jpeg',
            filename=thumbnail_path.name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缩略图失败 {cover_uuid}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{uuid}")
async def delete_music(
    uuid: str,
    device_id: str = Query(..., description="设备ID（用于权限验证）"),
    db: Session = Depends(get_db)
):
    """
    删除音乐
    
    - **uuid**: 音乐UUID
    - **device_id**: 设备ID（用于验证权限，只能删除该设备的音乐）
    
    注意：仅删除数据库记录，不删除本地文件（客户端负责删除本地文件）
    """
    try:
        success = music_service.delete_music_by_device(db, uuid, device_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="音乐不存在或无权删除（device_id不匹配）"
            )
        
        return {
            "code": 200,
            "message": "音乐删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除音乐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
