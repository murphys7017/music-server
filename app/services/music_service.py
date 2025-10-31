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


# ============ 客户端音乐管理 ============

def add_music_from_client(db: Session, music_data: Dict[str, Any]) -> Music:
    """
    客户端添加音乐（仅元数据，无文件）
    
    Args:
        db: 数据库会话
        music_data: 音乐元数据字典，必须包含:
            - uuid: 音乐UUID（客户端生成）
            - md5: 文件MD5
            - device_id: 设备ID
            - name, author, album 等元数据
    
    Returns:
        Music: 创建的音乐对象
    
    Raises:
        ValueError: 如果缺少必要字段或 (md5, device_id) 已存在
    """
    # 验证必要字段
    required_fields = ["uuid", "md5", "device_id", "name"]
    for field in required_fields:
        if field not in music_data:
            raise ValueError(f"缺少必要字段: {field}")
    
    # 检查 (md5, device_id) 是否已存在
    existing = db.query(Music).filter(
        Music.md5 == music_data["md5"],
        Music.device_id == music_data["device_id"]
    ).first()
    
    if existing:
        raise ValueError(f"该设备已存在相同MD5的音乐: {existing.uuid}")
    
    # 创建音乐记录
    music = Music(**music_data)
    db.add(music)
    db.commit()
    db.refresh(music)
    
    return music


def query_music_by_device(
    db: Session,
    device_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """
    按设备ID查询音乐列表（分页）
    
    Args:
        db: 数据库会话
        device_id: 设备ID，None表示查询所有设备的音乐
        page: 页码
        page_size: 每页数量
    
    Returns:
        dict: {'total': 总数, 'list': 音乐列表}
    """
    q = db.query(Music)
    
    if device_id:
        q = q.filter(Music.device_id == device_id)
    
    total = q.count()
    items = q.offset((page-1)*page_size).limit(page_size).all()
    
    return {"total": total, "list": items}


def delete_music_by_device(db: Session, uuid: str, device_id: str) -> bool:
    """
    删除指定设备的音乐
    
    Args:
        db: 数据库会话
        uuid: 音乐UUID
        device_id: 设备ID（用于权限验证）
    
    Returns:
        bool: 是否删除成功
    """
    music = db.query(Music).filter(
        Music.uuid == uuid,
        Music.device_id == device_id
    ).first()
    
    if not music:
        return False
    
    db.delete(music)
    db.commit()
    return True


def fuzzy_query_music_by_device(
    db: Session,
    device_id: Optional[str] = None,
    name: Optional[str] = None,
    author: Optional[str] = None,
    album: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """
    按设备ID模糊搜索音乐
    
    Args:
        db: 数据库会话
        device_id: 设备ID，None表示搜索所有设备
        name, author, album: 搜索关键词（OR逻辑）
        page, page_size: 分页参数
    
    Returns:
        dict: {'total': 总数, 'list': 音乐列表}
    """
    q = db.query(Music)
    
    # 设备过滤
    if device_id:
        q = q.filter(Music.device_id == device_id)
    
    # 构建 OR 条件
    conditions = []
    if name:
        conditions.append(Music.name.like(f"%{name}%"))
    if author:
        conditions.append(Music.author.like(f"%{author}%"))
    if album:
        conditions.append(Music.album.like(f"%{album}%"))
    
    if conditions:
        q = q.filter(or_(*conditions))
    
    total = q.count()
    items = q.offset((page-1)*page_size).limit(page_size).all()
    
    return {"total": total, "list": items}
