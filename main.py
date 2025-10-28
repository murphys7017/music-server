from urllib.parse import unquote

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import FileResponse
import os

app = FastAPI()
MUSIC_DIR = r"C:\Users\Administrator\Downloads\song\test"
STATIC_TOKEN = "your_static_token_here"  # 请替换为你自己的token
COVER_EXTS = [".jpg", ".jpeg", ".png", ".webp"]

from fastapi import Query
import mimetypes

async def verify_token(request: Request):
    pass  # token 校验已暂时关闭

@app.get("/music/list")
async def list_music(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    files = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".wav", ".flac"))]
    total = len(files)
    start = (page - 1) * page_size
    end = start + page_size
    page_files = files[start:end]
    music_list = []
    for f in page_files:
        file_path = os.path.join(MUSIC_DIR, f)
        stat = os.stat(file_path)
        ext = os.path.splitext(f)[1].lower()
        mime = mimetypes.types_map.get(ext, "application/octet-stream")
        # 查找同名封面图片
        base_name = os.path.splitext(f)[0]
        cover_url = None
        for cext in COVER_EXTS:
            cover_path = os.path.join(MUSIC_DIR, base_name + cext)
            if os.path.isfile(cover_path):
                cover_url = f"/music/cover/{base_name + cext}"
                break
        music_list.append({
            "name": f,
            "url": f"/music/play/{f}",
            "size": stat.st_size,
            "type": mime,
            "duration": None,  # 可后续补充
            "cover": cover_url
        })
    return music_list
@app.get("/music/cover/{covername}")
async def get_cover(covername: str):
    covername = unquote(covername)
    cover_path = os.path.join(MUSIC_DIR, covername)
    if not os.path.isfile(cover_path):
        raise HTTPException(status_code=404, detail="Cover not found")
    ext = os.path.splitext(covername)[1].lower()
    if ext in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif ext == ".png":
        media_type = "image/png"
    elif ext == ".webp":
        media_type = "image/webp"
    else:
        media_type = "application/octet-stream"
    return FileResponse(cover_path, media_type=media_type, filename=covername)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": music_list
    }

@app.get("/music/play/{filename}")
async def play_music(filename: str):
    filename = unquote(filename)
    file_path = os.path.join(MUSIC_DIR, filename)
    print(f"Playing music: {file_path}")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".mp3":
        media_type = "audio/mpeg"
    elif ext == ".flac":
        media_type = "audio/flac"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(file_path, media_type=media_type, filename=filename)
