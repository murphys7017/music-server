user
我希望添加这样一个功能：添加本地音乐
客户端添加本地音乐，计算uuid和md5获取元数据文件名文件路径等信息发到服务端，服务端记录到音乐库，后续我会开发匹配音乐信息等功能补充信息。
我觉得music表应该添加一个字段设备id，如果设备是服务器，那么所有的客户端都可以获取到，如果是某个设备添加的音乐，设备id就是那个设备，只有那个设备才能获取到。各设备音乐隔离，不互通。

其中的uuid格式变为 数据类型加uuid有必要吗类似 music-xxxxx-xxxxx

文件路径隐私问题的话，客户端建立一个uuid到文件实际位置的对应库，这样封面和歌词也同样可以通过uuid来映射，当本地没有这个uuid时便从服务器端获取，有便从本地获取

先不用执行，先说说你的想法


class Music(Base):
    __tablename__ = "music"

    uuid = 《music-uuid》
    md5 = Column(String(32), unique=True, nullable=False, comment="文件MD5")
    name = Column(String(255), nullable=False, comment="音乐名称")
    author = Column(String(128), default="未知", comment="作者")
    album = Column(String(255), default="", comment="专辑")
    source = Column(String(32), default="local", comment="来源(如local、bilibili等)")
    duration = Column(Integer, default=0, comment="持续时间(秒)")
    size = Column(BigInteger, default=0, comment="文件大小(字节)")
    bitrate = Column(Integer, default=0, comment="比特率(kbps)")
    waveform = Column(Text, nullable=True, comment="音频波形数据(JSON或其他格式)")
    cover_uuid = 《cover-uuid》
    lyric = Column(Text, nullable=True, comment="歌词")
    play_count = Column(Integer, default=0, comment="播放次数")
    add_time = Column(DateTime, server_default=func.now(), comment="添加时间")
    device_id = 《新添加的》
    def __repr__(self):
        return f"<Music {self.name} by {self.author}>"

class Device(Base):
    __tablename__ = "devices"
    device_id = 《device-uuid》
    device_name = Column(String(128))  # 设备名称，如 "我的iPhone"
    device_type = Column(String(32))   # "mobile", "desktop", "web"
    owner_token = STATIC_TOKEN      # 所属用户STATIC_TOKEN
    is_online = Column(Boolean, default=False)
    last_online = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)