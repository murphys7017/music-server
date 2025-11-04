"""
推荐相关服务
"""
from sqlalchemy.orm import Session
from app.models.music import Music
import random
from typing import List

def get_hot_recommendations(db: Session, limit: int = 100, pick: int = 30) -> List[Music]:
    """
    播放量由高到低排序，取前limit首，随机选pick首
    """
    musics = db.query(Music).order_by(Music.play_count.desc()).limit(limit).all()
    if len(musics) <= pick:
        return musics
    return random.sample(musics, pick)


def get_cold_recommendations(db: Session, limit: int = 200, pick: int = 15) -> List[Music]:
    """
    播放量由低到高排序，取前limit首，随机选pick首
    """
    musics = db.query(Music).order_by(Music.play_count.asc()).limit(limit).all()
    if len(musics) <= pick:
        return musics
    return random.sample(musics, pick)
