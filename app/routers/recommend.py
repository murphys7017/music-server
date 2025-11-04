"""
推荐相关API
"""

from fastapi import APIRouter, Depends
from fastapi import Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services import recommend_service, music_service
from app.config import Config
from app.log import logger

router = APIRouter(prefix="/recommend", tags=["recommend"])

@router.get("/mymusic/hot")
def recommend_hot_music(
    db: Session = Depends(get_db),
    pick: int = Query(30, ge=1, le=100, description="推荐数量，最大100")
):
    """
    热门推荐：播放量高→低，前100随机取30首，返回与/music/list相同格式
    """
    try:
        musics = recommend_service.get_hot_recommendations(db, pick=pick)
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
            # 推荐接口不返回歌词
            music_dict.pop('lyric', None)
            music_list.append(music_dict)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": len(music_list),
                "list": music_list
            }
        }
    except Exception as e:
        logger.error(f"推荐热门音乐失败: {e}")
        return {"code": 500, "message": str(e), "data": None}

@router.get("/mymusic/cold")
def recommend_cold_music(
    db: Session = Depends(get_db),
    pick: int = Query(15, ge=1, le=200, description="推荐数量，最大200")
):
    """
    冷门推荐：播放量低→高，前200随机取15首，返回与/music/list相同格式
    """
    try:
        musics = recommend_service.get_cold_recommendations(db, pick=pick)
        music_list = []
        for music in musics:
            music_dict = music_service.music_to_json(music)
            music_dict['play_url'] = f"/music/play/{music.uuid}"
            cover_uuid = getattr(music, 'cover_uuid', None)
            if cover_uuid:
                music_dict['cover_url'] = f"/music/cover/{cover_uuid}"
                music_dict['thumbnail_url'] = f"/music/thumbnail/{cover_uuid}"
            else:
                music_dict['cover_url'] = None
                music_dict['thumbnail_url'] = None
            music_dict.pop('lyric', None)
            music_list.append(music_dict)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "total": len(music_list),
                "list": music_list
            }
        }
    except Exception as e:
        logger.error(f"推荐冷门音乐失败: {e}")
        return {"code": 500, "message": str(e), "data": None}
