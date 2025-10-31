"""
Music表相关服务
"""
from sqlalchemy.orm import Session
from app.models.music import Music
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from uuid import uuid4
import json

# 自动建表（如未开启）
from app.database import engine, Base
Base.metadata.create_all(bind=engine)

# 单个插入

def add_music(db: Session, music_data: Dict[str, Any]) -> Music:
    # 若未传uuid则自动生成
    if not music_data.get("uuid"):
        music_data["uuid"] = str(uuid4())
    music = Music(**music_data)
    db.add(music)
    db.commit()
    db.refresh(music)
    return music

# 批量插入

def add_musics(db: Session, musics_data: List[Dict[str, Any]]) -> List[Music]:
    for data in musics_data:
        if not data.get("uuid"):
            data["uuid"] = str(uuid4())
    musics = [Music(**data) for data in musics_data]
    db.add_all(musics)
    db.commit()
    return musics

# 单个修改

def update_music(db: Session, uuid: str, update_data: Dict[str, Any]) -> Optional[Music]:
    music = db.query(Music).filter(Music.uuid == uuid).first()
    if not music:
        return None
    for k, v in update_data.items():
        setattr(music, k, v)
    db.commit()
    db.refresh(music)
    return music

# 批量修改（根据uuid列表）

def update_musics(db: Session, updates: List[Dict[str, Any]]) -> int:
    count = 0
    for upd in updates:
        uuid = upd.get("uuid")
        if not uuid:
            continue
        music = db.query(Music).filter(Music.uuid == uuid).first()
        if not music:
            continue
        for k, v in upd.items():
            if k != "uuid":
                setattr(music, k, v)
        count += 1
    db.commit()
    return count

# 根据uuid判断是否存在

def music_exists(db: Session, uuid: str) -> bool:
    return db.query(Music).filter(Music.uuid == uuid).first() is not None

# 根据uuid获取

def get_music_by_uuid(db: Session, uuid: str) -> Optional[Music]:
    return db.query(Music).filter(Music.uuid == uuid).first()

# 支持分页的多条件精确查询

def query_music(db: Session, name: Optional[str] = None, author: Optional[str] = None, album: Optional[str] = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    q = db.query(Music)
    if name:
        q = q.filter(Music.name == name)
    if author:
        q = q.filter(Music.author == author)
    if album:
        q = q.filter(Music.album == album)
    total = q.count()
    items = q.offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "list": items}

# 支持分页的多条件模糊查询

def fuzzy_query_music(db: Session, name: Optional[str] = None, author: Optional[str] = None, album: Optional[str] = None, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    q = db.query(Music)
    
    # 构建 OR 条件列表
    conditions = []
    if name:
        conditions.append(Music.name.like(f"%{name}%"))
    if author:
        conditions.append(Music.author.like(f"%{author}%"))
    if album:
        conditions.append(Music.album.like(f"%{album}%"))
    
    # 如果有条件，使用 or_ 组合
    if conditions:
        q = q.filter(or_(*conditions))
    
    total = q.count()
    items = q.offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "list": items}

# 根据歌词搜索音乐

def search_music_by_lyric(db: Session, lyric_keyword: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
    """
    根据歌词内容搜索音乐
    
    Args:
        db: 数据库会话
        lyric_keyword: 歌词关键词
        page: 页码
        page_size: 每页数量
        
    Returns:
        dict: {'total': 总数, 'list': 音乐列表}
    """
    q = db.query(Music)
    
    # 只搜索有歌词的音乐
    q = q.filter(Music.lyric.isnot(None))
    q = q.filter(Music.lyric != "")
    q = q.filter(Music.lyric.like(f"%{lyric_keyword}%"))
    
    total = q.count()
    items = q.offset((page-1)*page_size).limit(page_size).all()
    return {"total": total, "list": items}

# 批量删除

def delete_musics(db: Session, uuids: List[str]) -> int:
    count = db.query(Music).filter(Music.uuid.in_(uuids)).delete(synchronize_session=False)
    db.commit()
    return count

# 序列化为json

def music_to_json(music: Music) -> Dict[str, Any]:
    return {c.name: getattr(music, c.name) for c in music.__table__.columns}

# 批量序列化

def musics_to_json(musics: List[Music]) -> List[Dict[str, Any]]:
    return [music_to_json(m) for m in musics]

# 从json转换为Music对象

def json_to_music(data: Dict[str, Any]) -> Music:
    return Music(**data)
