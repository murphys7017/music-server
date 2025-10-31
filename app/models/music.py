from sqlalchemy import Column, String, Integer, DateTime, Text, BigInteger
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from app.database import Base

class Music(Base):
    __tablename__ = "music"

    uuid = Column(CHAR(36), primary_key=True, comment="唯一ID")
    md5 = Column(String(32), unique=True, nullable=False, comment="文件MD5")
    name = Column(String(255), nullable=False, comment="音乐名称")
    author = Column(String(128), default="未知", comment="作者")
    album = Column(String(255), default="", comment="专辑")
    source = Column(String(32), default="local", comment="来源(如local、bilibili等)")
    duration = Column(Integer, default=0, comment="持续时间(秒)")
    size = Column(BigInteger, default=0, comment="文件大小(字节)")
    bitrate = Column(Integer, default=0, comment="比特率(kbps)")
    waveform = Column(Text, nullable=True, comment="音频波形数据(JSON或其他格式)")
    cover_uuid = Column(CHAR(36), nullable=True, comment="封面图片UUID")
    lyric = Column(Text, nullable=True, comment="歌词")
    play_count = Column(Integer, default=0, comment="播放次数")
    add_time = Column(DateTime, server_default=func.now(), comment="添加时间")

    def __repr__(self):
        return f"<Music {self.name} by {self.author}>"
