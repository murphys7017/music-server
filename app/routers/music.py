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

from app.config import Config
from app.database import get_db
from app.models.music import Music
from app.services import music_service
from app.log import logger

router = APIRouter(prefix="/music", tags=["music"])


@router.get("/list")
async def list_music(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    分页查询音乐列表
    返回音乐的完整信息，包括封面UUID、歌词等
    """
    try:
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询总数
        total = db.query(Music).count()
        
        # 查询当前页数据
        musics = db.query(Music).offset(offset).limit(page_size).all()
        
        # 序列化为JSON
        music_list = []
        for music in musics:
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
                "total": total,
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
    db: Session = Depends(get_db)
):
    """
    模糊搜索音乐
    支持按歌名、作者、专辑搜索
    """
    try:
        # 模糊查询
        result = music_service.fuzzy_query_music(
            db=db,
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
    """
    try:
        # 从数据库获取音乐信息
        music = music_service.get_music_by_uuid(db, uuid)
        if not music:
            raise HTTPException(status_code=404, detail="Music not found")
        
        # 构建文件路径（暂时使用MUSIC_DIR，后续可以根据source字段处理）
        # 这里需要根据实际存储方式调整
        # 如果音乐文件存储路径在数据库中，可以添加file_path字段
        # 目前先按照原始文件名在MUSIC_DIR查找
        music_dir = Path(Config.MUSIC_DIR)
        
        # 尝试查找文件（这里需要优化，应该在数据库存储完整路径）
        file_path = None
        for ext in Config.MUSIC_EXTS:
            # 尝试多种可能的文件名格式
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
        
        if not file_path or not file_path.exists():
            logger.error(f"音乐文件未找到: {music.name} - {music.author}")
            raise HTTPException(status_code=404, detail="Music file not found")
        
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
