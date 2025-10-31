"""
音乐文件扫描与导入工具
扫描指定文件夹的音乐文件，提取元数据并写入数据库
"""
import os
import hashlib
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.config import Config
from app.utils.music_filename_parser import normalize_music_info
from app.models.music import Music
from app.services.music_service import add_music, music_exists
from app.log import logger
from app.utils.thumbnail_generator import generate_thumbnail_for_cover_uuid

# 从配置中获取支持的格式
SUPPORTED_FORMATS = Config.MUSIC_EXTS
LYRIC_FORMATS = Config.LYRICS_EXTS
COVER_FORMATS = Config.COVER_EXTS

def save_cover_file(cover_source_path: str) -> Optional[str]:
    """
    保存封面文件到统一目录，返回UUID
    
    Args:
        cover_source_path: 原始封面文件路径
    
    Returns:
        封面UUID，失败返回None
    """
    try:
        # 确保封面目录存在
        cover_dir = Path(Config.COVER_DIR)
        cover_dir.mkdir(parents=True, exist_ok=True)
        
        source_path = Path(cover_source_path)
        if not source_path.exists():
            return None
        
        # 生成UUID作为文件名
        cover_uuid = str(uuid4())
        ext = source_path.suffix.lower()
        dest_filename = f"{cover_uuid}{ext}"
        dest_path = cover_dir / dest_filename
        
        # 复制文件
        shutil.copy2(cover_source_path, dest_path)
        logger.info(f"封面已保存: {dest_filename}")
        
        # 自动生成缩略图
        generate_thumbnail_for_cover_uuid(cover_uuid)
        
        return cover_uuid
        
    except Exception as e:
        logger.error(f"保存封面文件失败 {cover_source_path}: {e}")
        return None

def save_cover_data(cover_data: bytes, mime_type: str = 'image/jpeg') -> Optional[str]:
    """
    从二进制数据保存封面文件，返回UUID
    
    Args:
        cover_data: 封面二进制数据
        mime_type: MIME类型
    
    Returns:
        封面UUID，失败返回None
    """
    try:
        # 确保封面目录存在
        cover_dir = Path(Config.COVER_DIR)
        cover_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据MIME类型确定扩展名
        ext_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/webp': '.webp',
            'image/bmp': '.bmp'
        }
        ext = ext_map.get(mime_type.lower(), '.jpg')
        
        # 生成UUID作为文件名
        cover_uuid = str(uuid4())
        dest_filename = f"{cover_uuid}{ext}"
        dest_path = cover_dir / dest_filename
        
        # 写入文件
        with open(dest_path, 'wb') as f:
            f.write(cover_data)
        
        logger.info(f"内嵌封面已保存: {dest_filename}")
        
        # 自动生成缩略图
        generate_thumbnail_for_cover_uuid(cover_uuid)
        
        return cover_uuid
        
    except Exception as e:
        logger.error(f"保存封面数据失败: {e}")
        return None

def find_cover_file(music_file_path: str) -> Optional[str]:
    """
    在同目录查找同名封面文件
    优先级：.jpg > .png > .jpeg > .webp > .bmp
    """
    music_path = Path(music_file_path)
    base_name = music_path.stem
    directory = music_path.parent
    
    for ext in COVER_FORMATS:
        cover_path = directory / f"{base_name}{ext}"
        if cover_path.exists():
            return str(cover_path)
    
    return None

def find_lyric_file(music_file_path: str) -> Optional[str]:
    """
    在同目录查找同名歌词文件
    优先级：.lrc > .txt
    """
    music_path = Path(music_file_path)
    base_name = music_path.stem
    directory = music_path.parent
    
    for ext in LYRIC_FORMATS:
        lyric_path = directory / f"{base_name}{ext}"
        if lyric_path.exists():
            return str(lyric_path)
    
    return None

def read_lyric_file(lyric_path: str) -> str:
    """读取歌词文件内容"""
    try:
        with open(lyric_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        try:
            with open(lyric_path, 'r', encoding='gbk') as f:
                return f.read()
        except Exception as e:
            logger.error(f"读取歌词文件失败 {lyric_path}: {e}")
            return ""
    except Exception as e:
        logger.error(f"读取歌词文件失败 {lyric_path}: {e}")
        return ""

def calculate_file_md5(file_path: str, chunk_size: int = 8192) -> str:
    """计算文件MD5值"""
    md5_hash = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        logger.error(f"计算MD5失败 {file_path}: {e}")
        return ""

def extract_audio_metadata(file_path: str) -> Dict[str, Any]:
    """
    使用mutagen提取音频元数据
    返回包含title, artist, album, duration, bitrate, cover, lyric等信息的字典
    """
    metadata = {}
    try:
        from mutagen._file import File as MutagenFile
        
        audio = MutagenFile(file_path)
        
        if audio is None:
            return metadata
        
        # 提取基本信息
        if hasattr(audio, 'info'):
            # 时长（秒）
            metadata['duration'] = int(getattr(audio.info, 'length', 0))
            # 比特率（kbps）
            metadata['bitrate'] = int(getattr(audio.info, 'bitrate', 0) / 1000)
        
        # 提取标签信息
        tags = audio.tags if audio.tags else {}
        
        # 不同格式的标签键名可能不同
        # MP3 (ID3)
        if hasattr(tags, 'get'):
            metadata['title'] = str(tags.get('TIT2', [''])[0]) if 'TIT2' in tags else ''
            metadata['artist'] = str(tags.get('TPE1', [''])[0]) if 'TPE1' in tags else ''
            metadata['album'] = str(tags.get('TALB', [''])[0]) if 'TALB' in tags else ''
            
            # 提取歌词 (ID3)
            if 'USLT' in tags:
                uslt = tags.get('USLT')
                if uslt:
                    metadata['lyric'] = str(uslt[0]) if isinstance(uslt, list) else str(uslt)
            
            # 提取封面 (ID3)
            if 'APIC:' in tags or any(k.startswith('APIC') for k in tags.keys()):
                for key in tags.keys():
                    if key.startswith('APIC'):
                        apic = tags[key]
                        if hasattr(apic, 'data'):
                            metadata['cover_data'] = apic.data
                            metadata['cover_mime'] = apic.mime if hasattr(apic, 'mime') else 'image/jpeg'
                            logger.info(f"找到内嵌封面 (ID3)")
                            break
        
        # FLAC/OGG/MP4等使用字典式标签
        if isinstance(tags, dict):
            metadata['title'] = tags.get('title', [''])[0] if 'title' in tags else ''
            metadata['artist'] = tags.get('artist', [''])[0] if 'artist' in tags else ''
            metadata['album'] = tags.get('album', [''])[0] if 'album' in tags else ''
            metadata['lyric'] = tags.get('lyrics', [''])[0] if 'lyrics' in tags else ''
        
        # FLAC 特殊处理封面
        if hasattr(audio, 'pictures') and audio.pictures:
            picture = audio.pictures[0]
            metadata['cover_data'] = picture.data
            metadata['cover_mime'] = picture.mime
            logger.info(f"找到内嵌封面 (FLAC)")
        
    except ImportError:
        logger.warning("未安装mutagen库，无法提取音频元数据。建议: uv add mutagen")
    except Exception as e:
        logger.error(f"提取音频元数据失败 {file_path}: {e}")
    
    return metadata

def scan_music_file(file_path: str, source: str = 'local') -> Optional[Dict[str, Any]]:
    """
    扫描单个音乐文件，综合文件名和元数据提取信息
    
    Args:
        file_path: 音频文件完整路径
        source: 音乐来源（local, bilibili等）
    
    Returns:
        包含Music模型所需字段的字典，失败返回None
    """
    try:
        file_path_obj = Path(file_path)
        
        # 检查文件是否存在且为支持的格式
        if not file_path_obj.exists() or file_path_obj.suffix.lower() not in SUPPORTED_FORMATS:
            return None
        
        # 获取文件基本信息
        file_size = file_path_obj.stat().st_size
        filename = file_path_obj.name
        file_format = file_path_obj.suffix.lower().lstrip('.')  # 获取文件格式（不带点）
        
        # 计算MD5
        file_md5 = calculate_file_md5(file_path)
        if not file_md5:
            logger.warning(f"无法计算MD5，跳过文件: {filename}")
            return None
        
        # 提取音频元数据
        audio_metadata = extract_audio_metadata(file_path)
        
        # 使用文件名解析工具规范化信息
        normalized = normalize_music_info(filename, audio_metadata)
        
        # 处理歌词：优先使用内嵌歌词，其次使用外部歌词文件
        final_lyric = ""
        
        # 1. 优先使用内嵌歌词
        if audio_metadata.get('lyric'):
            final_lyric = audio_metadata['lyric']
            logger.info(f"使用内嵌歌词")
        else:
            # 2. 如果没有内嵌歌词，查找外部歌词文件
            lyric_file = find_lyric_file(file_path)
            if lyric_file:
                final_lyric = read_lyric_file(lyric_file)
                logger.info(f"找到外部歌词文件: {Path(lyric_file).name}")
        
        # 更新到metadata中
        audio_metadata['lyric'] = final_lyric
        
        # 处理封面：优先使用内嵌封面，其次使用外部封面文件
        cover_uuid = None
        
        # 1. 检查是否有内嵌封面
        if audio_metadata.get('cover_data'):
            cover_uuid = save_cover_data(
                audio_metadata['cover_data'],
                audio_metadata.get('cover_mime', 'image/jpeg')
            )
        
        # 2. 如果没有内嵌封面，查找外部封面文件
        if not cover_uuid:
            cover_file = find_cover_file(file_path)
            if cover_file:
                logger.info(f"找到外部封面文件: {Path(cover_file).name}")
                cover_uuid = save_cover_file(cover_file)
        
        # 构建Music模型数据
        music_data = {
            'uuid': str(uuid4()),
            'md5': file_md5,
            'device_id': 'server',  # 服务端音乐
            'name': normalized['name'],
            'author': normalized['author'],
            'album': normalized.get('album', '') or audio_metadata.get('album', ''),
            'source': source,
            'duration': audio_metadata.get('duration', 0),
            'size': file_size,
            'bitrate': audio_metadata.get('bitrate', 0),
            'file_format': file_format,  # 文件格式
            'local_path': str(file_path_obj.absolute()),  # 服务端本地路径
            'waveform': None,  # 波形数据可后续生成
            'cover_uuid': cover_uuid,  # 封面UUID
            'lyric': audio_metadata.get('lyric', ''),
            'play_count': 0,
        }
        
        # 将额外信息存储到某个字段（可选）
        extra_parts = []
        if normalized.get('version'):
            extra_parts.append(normalized['version'])
        if normalized.get('type'):
            extra_parts.append(normalized['type'])
        if normalized.get('style'):
            extra_parts.append(normalized['style'])
        if normalized.get('mix'):
            extra_parts.append(normalized['mix'])
        
        # 可以将extra信息追加到name或存储到专门字段
        # 这里选择保留在name中（可根据需求调整）
        if extra_parts and normalized.get('extra_info'):
            extra_parts.append(normalized['extra_info'])
        
        return music_data
        
    except Exception as e:
        logger.error(f"扫描音乐文件失败 {file_path}: {e}")
        return None

def is_better_quality(new_music: Dict[str, Any], old_music: Music) -> bool:
    """
    比较两个音乐文件的质量，判断新文件是否更好
    比较标准：
    1. 比特率更高
    2. 文件大小更大
    3. 时长差异不大（避免错误匹配）
    """
    # 时长差异超过5秒，可能不是同一首歌
    if abs(new_music['duration'] - old_music.duration) > 5:
        return False
    
    # 比特率更高
    if new_music['bitrate'] > old_music.bitrate:
        return True
    
    # 比特率相同，文件更大
    if new_music['bitrate'] == old_music.bitrate and new_music['size'] > old_music.size:
        return True
    
    return False

def merge_music_info(new_music: Dict[str, Any], old_music: Music) -> Dict[str, Any]:
    """
    合并新旧音乐信息，保留更完整的数据
    """
    merged = new_music.copy()
    
    # 如果新数据某些字段为空，使用旧数据
    if not merged.get('album') and old_music.album is not None:
        merged['album'] = old_music.album
    
    if not merged.get('lyric') and old_music.lyric is not None:
        merged['lyric'] = old_music.lyric
    
    if not merged.get('cover_uuid') and old_music.cover_uuid is not None:
        merged['cover_uuid'] = old_music.cover_uuid
    
    # 保留播放次数
    merged['play_count'] = old_music.play_count
    
    # 保留UUID
    merged['uuid'] = old_music.uuid
    
    return merged

def scan_and_import_folder(
    folder_path: str, 
    db: Session, 
    source: str = 'local',
    skip_existing: bool = True,
    upgrade_quality: bool = True
) -> Dict[str, Any]:
    """
    扫描文件夹内所有音乐文件并导入数据库（不递归子目录）
    
    Args:
        folder_path: 文件夹路径
        db: 数据库会话
        source: 音乐来源标识
        skip_existing: 是否跳过已存在的文件（根据MD5判断）
        upgrade_quality: 是否用高质量版本替换低质量版本
    
    Returns:
        统计信息字典 {total, success, skipped, failed, upgraded}
    """
    stats = {
        'total': 0,
        'success': 0,
        'skipped': 0,
        'failed': 0,
        'upgraded': 0,
        'files': []
    }
    
    try:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            logger.error(f"文件夹不存在或不是目录: {folder_path}")
            return stats
        
        # 遍历文件夹内所有文件（不递归）
        for file_path in folder.iterdir():
            if not file_path.is_file():
                continue
            
            # 检查是否为支持的音频格式
            if file_path.suffix.lower() not in SUPPORTED_FORMATS:
                continue
            
            stats['total'] += 1
            logger.info(f"正在处理: {file_path.name}")
            
            # 扫描文件
            music_data = scan_music_file(str(file_path), source)
            if not music_data:
                stats['failed'] += 1
                logger.warning(f"扫描失败: {file_path.name}")
                continue
            
            # 检查是否已存在（根据MD5）
            existing_by_md5 = db.query(Music).filter(
                Music.md5 == music_data['md5'],
                Music.device_id == 'server'  # 只检查服务端音乐
            ).first()
            if existing_by_md5:
                # 更新可能缺失的信息（封面、歌词等）
                updated = False
                
                # 更新封面（如果原记录没有封面，但现在找到了）
                if existing_by_md5.cover_uuid is None and music_data.get('cover_uuid'):
                    existing_by_md5.cover_uuid = music_data['cover_uuid']
                    updated = True
                    logger.info(f"更新封面UUID: {music_data['cover_uuid']}")
                
                # 更新歌词（如果原记录没有歌词，但现在找到了）
                current_lyric = getattr(existing_by_md5, 'lyric', None)
                if (current_lyric is None or current_lyric == '') and music_data.get('lyric'):
                    existing_by_md5.lyric = music_data['lyric']
                    updated = True
                    logger.info(f"更新歌词信息")
                
                # 更新专辑（如果原记录没有专辑，但现在找到了）
                current_album = getattr(existing_by_md5, 'album', None)
                if (current_album is None or current_album == '') and music_data.get('album'):
                    existing_by_md5.album = music_data['album']
                    updated = True
                    logger.info(f"更新专辑: {music_data['album']}")
                
                # 更新比特率和时长（如果原记录为0）
                current_bitrate = getattr(existing_by_md5, 'bitrate', 0)
                if current_bitrate == 0 and music_data.get('bitrate', 0) > 0:
                    existing_by_md5.bitrate = music_data['bitrate']
                    updated = True
                
                current_duration = getattr(existing_by_md5, 'duration', 0)
                if current_duration == 0 and music_data.get('duration', 0) > 0:
                    existing_by_md5.duration = music_data['duration']
                    updated = True
                
                if updated:
                    try:
                        db.commit()
                        stats['upgraded'] += 1
                        stats['files'].append(f"{existing_by_md5.name} (已更新)")
                        logger.info(f"信息已更新: {existing_by_md5.name}")
                        continue
                    except Exception as e:
                        db.rollback()
                        logger.error(f"更新信息失败: {e}")
                
                # 如果没有可更新的信息，则跳过
                if skip_existing:
                    stats['skipped'] += 1
                    logger.info(f"文件MD5已存在且无需更新，跳过: {file_path.name}")
                    continue
            
            # 检查是否有同名同作者的歌曲（可能是不同质量版本）
            if upgrade_quality:
                existing_by_name = db.query(Music).filter(
                    Music.name == music_data['name'],
                    Music.author == music_data['author']
                ).first()
                
                if existing_by_name and not existing_by_md5:
                    # 判断是否是更高质量的版本
                    if is_better_quality(music_data, existing_by_name):
                        logger.info(f"发现高质量版本，升级: {music_data['name']} (比特率: {existing_by_name.bitrate}kbps -> {music_data['bitrate']}kbps)")
                        
                        # 合并信息
                        merged_data = merge_music_info(music_data, existing_by_name)
                        
                        # 更新数据库记录
                        try:
                            for key, value in merged_data.items():
                                if key != 'uuid':  # uuid不更新
                                    setattr(existing_by_name, key, value)
                            db.commit()
                            stats['upgraded'] += 1
                            stats['files'].append(f"{music_data['name']} (已升级)")
                            logger.info(f"升级成功: {music_data['name']}")
                            continue
                        except Exception as e:
                            db.rollback()
                            stats['failed'] += 1
                            logger.error(f"升级失败 {file_path.name}: {e}")
                            continue
                    else:
                        # 新版本质量不如旧版本，跳过
                        stats['skipped'] += 1
                        logger.info(f"已存在更高质量版本，跳过: {file_path.name}")
                        continue
            
            # 写入数据库
            try:
                music = add_music(db, music_data)
                stats['success'] += 1
                stats['files'].append(music.name)
                logger.info(f"导入成功: {music.name} by {music.author}")
            except Exception as e:
                stats['failed'] += 1
                logger.error(f"数据库写入失败 {file_path.name}: {e}")
        
        logger.info(f"扫描完成! 总计:{stats['total']}, 成功:{stats['success']}, 升级:{stats['upgraded']}, 跳过:{stats['skipped']}, 失败:{stats['failed']}")
        
    except Exception as e:
        logger.error(f"扫描文件夹失败: {e}")
    
    return stats

# 使用示例
if __name__ == "__main__":
    import sys
    from app.database import SessionLocal
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python -m app.utils.music_scanner <文件夹路径>")
        print("\n示例:")
        print("  python -m app.utils.music_scanner D:/Music")
        print("  python -m app.utils.music_scanner \"C:/Users/YourName/Music/我的收藏\"")
        sys.exit(1)
    
    # 获取文件夹路径
    folder_path = sys.argv[1]
    
    # 检查路径是否存在
    if not Path(folder_path).exists():
        print(f"❌ 错误: 路径不存在: {folder_path}")
        sys.exit(1)
    
    if not Path(folder_path).is_dir():
        print(f"❌ 错误: 不是文件夹: {folder_path}")
        sys.exit(1)
    
    print("=" * 60)
    print(f"🎵 音乐文件扫描与导入工具")
    print("=" * 60)
    print(f"📁 扫描目录: {folder_path}")
    print(f"🎼 支持格式: {', '.join(SUPPORTED_FORMATS)}")
    print(f"💾 数据库: MySQL")
    print("=" * 60)
    print()
    
    # 创建数据库会话
    db = SessionLocal()
    try:
        # 扫描并导入
        result = scan_and_import_folder(
            folder_path, 
            db, 
            source='local',
            skip_existing=True,
            upgrade_quality=True
        )
        
        # 输出结果
        print()
        print("=" * 60)
        print("📊 扫描结果统计")
        print("=" * 60)
        print(f"  📂 扫描文件数: {result['total']}")
        print(f"  ✅ 导入成功: {result['success']}")
        print(f"  ⬆️  质量升级: {result['upgraded']}")
        print(f"  ⏭️  跳过: {result['skipped']}")
        print(f"  ❌ 失败: {result['failed']}")
        print("=" * 60)
        
        if result['files']:
            print()
            print("🎼 成功处理的歌曲:")
            for name in result['files'][:20]:  # 只显示前20首
                print(f"  • {name}")
            if len(result['files']) > 20:
                print(f"  ... 以及其他 {len(result['files']) - 20} 首歌曲")
        
        print()
        print("✨ 完成!")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()
