from fastapi import FastAPI
from app.routers import music
from app.database import engine, Base
from app.log import logger

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Music Server", version="1.0.0")

# 注册路由
app.include_router(music.router, prefix="/music", tags=["music"])

@app.get("/")
async def root():
    return {"message": "Music Server API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Music Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
