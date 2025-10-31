from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import music, device
from app.database import engine, Base
from app.log import logger
from app.core.scheduler import get_scheduler
from app.config import Config
from app.middleware.auth import TokenAuthMiddleware

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Music Server", version="1.0.0")

# 添加 CORS 中间件（允许跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,  # 从配置读取允许的源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头
)
logger.info(f"CORS 中间件已启用 / CORS middleware enabled (origins: {Config.CORS_ORIGINS})")

# 添加认证中间件
app.add_middleware(TokenAuthMiddleware)
logger.info("Token 认证中间件已启用 / Token authentication middleware enabled")

# 注册路由
app.include_router(music.router, tags=["music"])
app.include_router(device.router, tags=["device"])
logger.info("路由已注册 / Routers registered")

# 启动调度器
scheduler = get_scheduler()
logger.info("定时任务调度器已启动 / Scheduler started")

@app.get("/")
async def root():
    return {"message": "Music Server API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Music Server...")
    uvicorn.run(
        "main:app",  # 使用字符串格式，而不是直接传入 app 对象
        host=Config.SERVER_HOST, 
        port=Config.SERVER_PORT, 
        reload=Config.RELOAD  # 通过配置控制是否启用热重载
    )
