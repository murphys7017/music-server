"""
缩略图生成工具
为封面图片生成小体积的缩略图
"""
from pathlib import Path
from typing import Optional
from PIL import Image
import io

from app.config import Config
from app.log import logger


def generate_thumbnail(
    cover_path: Path,
    thumbnail_path: Path,
    size: Optional[tuple] = None,
    quality: Optional[int] = None
) -> bool:
    """
    生成缩略图
    
    Args:
        cover_path: 原始封面图片路径
        thumbnail_path: 缩略图保存路径
        size: 缩略图尺寸 (width, height)，默认使用Config配置
        quality: JPEG压缩质量 (1-100)，默认使用Config配置
        
    Returns:
        bool: 是否成功生成
    """
    try:
        if not cover_path.exists():
            logger.warning(f"封面文件不存在: {cover_path}")
            return False
        
        # 使用配置的默认值
        if size is None:
            size = Config.THUMBNAIL_SIZE
        if quality is None:
            quality = Config.THUMBNAIL_QUALITY
        
        # 打开图片
        with Image.open(cover_path) as img:
            # 转换为RGB模式（某些PNG有透明通道）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 生成缩略图（保持宽高比）
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # 确保目标目录存在
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存为JPEG格式（体积小）
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
        logger.info(f"生成缩略图成功: {thumbnail_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"生成缩略图失败 {cover_path}: {e}")
        return False


def generate_thumbnail_for_cover_uuid(cover_uuid: str) -> bool:
    """
    根据cover_uuid生成缩略图
    
    Args:
        cover_uuid: 封面UUID
        
    Returns:
        bool: 是否成功生成
    """
    cover_dir = Path(Config.COVER_DIR)
    thumbnail_dir = Path(Config.THUMBNAIL_DIR)
    
    # 查找原始封面文件
    cover_path = None
    for ext in Config.COVER_EXTS:
        test_path = cover_dir / f"{cover_uuid}{ext}"
        if test_path.exists():
            cover_path = test_path
            break
    
    if not cover_path:
        logger.warning(f"未找到封面文件: {cover_uuid}")
        return False
    
    # 缩略图统一使用.jpg扩展名
    thumbnail_path = thumbnail_dir / f"{cover_uuid}.jpg"
    
    # 如果缩略图已存在，跳过
    if thumbnail_path.exists():
        logger.debug(f"缩略图已存在: {thumbnail_path.name}")
        return True
    
    return generate_thumbnail(cover_path, thumbnail_path)


def batch_generate_thumbnails(cover_dir: Optional[Path] = None) -> dict:
    """
    批量生成缩略图
    
    Args:
        cover_dir: 封面目录，默认使用Config.COVER_DIR
        
    Returns:
        dict: 统计信息 {'total': 总数, 'success': 成功数, 'skipped': 跳过数, 'failed': 失败数}
    """
    if cover_dir is None:
        cover_dir = Path(Config.COVER_DIR)
    
    thumbnail_dir = Path(Config.THUMBNAIL_DIR)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'failed': 0
    }
    
    # 遍历所有封面文件
    for cover_path in cover_dir.iterdir():
        if not cover_path.is_file():
            continue
        
        # 检查是否为支持的图片格式
        if cover_path.suffix.lower() not in Config.COVER_EXTS:
            continue
        
        stats['total'] += 1
        
        # 缩略图路径（统一使用.jpg）
        thumbnail_path = thumbnail_dir / f"{cover_path.stem}.jpg"
        
        # 如果缩略图已存在，跳过
        if thumbnail_path.exists():
            stats['skipped'] += 1
            logger.debug(f"缩略图已存在，跳过: {thumbnail_path.name}")
            continue
        
        # 生成缩略图
        if generate_thumbnail(cover_path, thumbnail_path):
            stats['success'] += 1
        else:
            stats['failed'] += 1
    
    logger.info(
        f"批量生成缩略图完成: "
        f"总数={stats['total']}, "
        f"成功={stats['success']}, "
        f"跳过={stats['skipped']}, "
        f"失败={stats['failed']}"
    )
    
    return stats


def get_thumbnail_path(cover_uuid: str) -> Optional[Path]:
    """
    获取缩略图路径（如果存在）
    
    Args:
        cover_uuid: 封面UUID
        
    Returns:
        Path: 缩略图路径，如果不存在返回None
    """
    thumbnail_dir = Path(Config.THUMBNAIL_DIR)
    thumbnail_path = thumbnail_dir / f"{cover_uuid}.jpg"
    
    if thumbnail_path.exists():
        return thumbnail_path
    
    return None


if __name__ == "__main__":
    # 测试：批量生成所有缩略图
    print("开始批量生成缩略图...")
    stats = batch_generate_thumbnails()
    print(f"\n生成完成！")
    print(f"总计: {stats['total']}")
    print(f"成功: {stats['success']}")
    print(f"跳过: {stats['skipped']}")
    print(f"失败: {stats['failed']}")
