"""
批量生成缩略图工具
为所有已存在的封面图片生成缩略图
"""
from app.utils.thumbnail_generator import batch_generate_thumbnails
from app.log import logger

if __name__ == "__main__":
    print("=" * 60)
    print("🖼️  批量生成缩略图工具")
    print("=" * 60)
    print()
    
    try:
        logger.info("开始批量生成缩略图...")
        stats = batch_generate_thumbnails()
        
        print()
        print("=" * 60)
        print("📊 生成结果统计")
        print("=" * 60)
        print(f"  📂 封面总数: {stats['total']}")
        print(f"  ✅ 生成成功: {stats['success']}")
        print(f"  ⏭️  已存在跳过: {stats['skipped']}")
        print(f"  ❌ 生成失败: {stats['failed']}")
        print("=" * 60)
        print()
        
        if stats['success'] > 0:
            print(f"✨ 成功生成 {stats['success']} 个缩略图!")
        elif stats['total'] == 0:
            print("⚠️  封面目录中没有图片文件")
        elif stats['skipped'] == stats['total']:
            print("ℹ️  所有缩略图都已存在，无需重新生成")
        
        if stats['failed'] > 0:
            print(f"⚠️  {stats['failed']} 个图片生成失败，请查看日志")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
