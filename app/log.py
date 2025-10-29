# app/log.py
"""
全局日志模块，基于 loguru
"""
from loguru import logger
import sys
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger.remove()
# 控制台输出
logger.add(sys.stdout, level="INFO", format="[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {message}")

# 文件输出，自动分割、保留10天
logger.add(
	os.path.join(LOG_DIR, "app_{time:YYYYMMDD}.log"),
	rotation="10 MB",
	retention="10 days",
	level="INFO",
	encoding="utf-8",
	format="[{time:YYYY-MM-DD HH:mm:ss}] [{level}] {message}"
)

# 捕获未处理异常
def log_exception(exc_type, exc_value, exc_traceback):
	logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

import sys as _sys
_sys.excepthook = log_exception

__all__ = ["logger"]
