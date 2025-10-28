# app/config.py
"""
全局配置文件，存储公共配置项
"""

import os

# 音乐文件目录
MUSIC_DIR = os.getenv("MUSIC_DIR", r"C:\\Users\\Administrator\\Downloads\\song\\test")

# 静态token
STATIC_TOKEN = os.getenv("STATIC_TOKEN", "your_static_token_here")

# 支持的封面图片扩展名
COVER_EXTS = [".jpg", ".jpeg", ".png", ".webp"]

# 其他全局配置可在此添加
