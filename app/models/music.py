from sqlalchemy import Column, String, Integer, DateTime, Text, BigInteger, Boolean, Index
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from app.database import Base

class Music(Base):
    __tablename__ = "music"

    uuid = Column(CHAR(36), primary_key=True, comment="唯一ID")
    md5 = Column(String(32), nullable=False, comment="文件MD5")
    device_id = Column(CHAR(36), nullable=False, default="server", index=True, comment="所属设备ID")
    name = Column(String(255), nullable=False, comment="音乐名称")
    author = Column(String(128), default="未知", comment="作者")
    album = Column(String(255), default="", comment="专辑")
    source = Column(String(32), default="local", comment="来源(如local、bilibili等)")
    duration = Column(Integer, default=0, comment="持续时间(秒)")
    size = Column(BigInteger, default=0, comment="文件大小(字节)")
    bitrate = Column(Integer, default=0, comment="比特率(kbps)")
    file_format = Column(String(16), nullable=True, comment="文件格式(mp3/flac/wav等)")
    local_path = Column(String(500), nullable=True, comment="服务端本地文件路径(仅device_id=server时使用)")
    waveform = Column(Text, nullable=True, comment="音频波形数据(JSON或其他格式)")
    cover_uuid = Column(CHAR(36), nullable=True, comment="封面图片UUID")
    lyric = Column(Text, nullable=True, comment="歌词")
    play_count = Column(Integer, default=0, comment="播放次数")
    is_matched = Column(Boolean, default=False, comment="是否已匹配音乐信息")
    add_time = Column(DateTime, server_default=func.now(), comment="添加时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 联合唯一索引: (md5, device_id)
    __table_args__ = (
        Index('idx_md5_device', 'md5', 'device_id', unique=True),
    )

    def __repr__(self):
        return f"<Music {self.name} by {self.author}>"
