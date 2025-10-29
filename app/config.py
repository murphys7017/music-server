
"""
全局配置与公共变量
"""
import os

class Config:
	# 音乐文件目录
	MUSIC_DIR = os.getenv("MUSIC_DIR", r"C:\\Users\\Administrator\\Downloads\\song\\test")
	# 静态token
	STATIC_TOKEN = os.getenv("STATIC_TOKEN", "your_static_token_here")
	# 支持的封面图片扩展名
	COVER_EXTS = [".jpg", ".jpeg", ".png", ".webp"]
	# 日志目录
	LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
	# 其他全局配置项...

# 全局变量（如需在多处共享可在此定义）
global_vars = {}

# 便于直接导入
__all__ = ["Config", "global_vars"]
