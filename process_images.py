"""
图片处理脚本
将源文件夹中的图片处理后复制到 static/imgs 目录

使用方法:
    python process_images.py <源文件夹路径>

源文件夹结构应与目标结构相同:
    source_folder/
    ├── hero/           # Hero轮播图片，也作为Highlights的数据源
    ├── archive/        # 归档图片
    │   ├── 6x6/        # 胶片画幅分类
    │   │   ├── 2024-01/
    │   │   ├── 2024-02/
    │   │   └── ...
    │   ├── 6x7/
    │   ├── 35mm/
    │   └── ...
    ├── filmlab/
    ├── prints/
    └── common/
"""

import os
import sys
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    sys.exit(1)


# 各分类的目标尺寸配置 (宽, 高)
SIZE_CONFIG = {
    "hero": (800, 800),        # 正方形 1:1，也作为Highlights数据源
    "archive": (120, 120),     # 小缩略图
    "filmlab": (400, 530),     # 竖向
    "prints": (400, 530),      # 竖向
    "common": None,            # 不调整尺寸
}

# 支持的图片格式
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}

# 目标文件夹路径
SCRIPT_DIR = Path(__file__).parent
TARGET_BASE = SCRIPT_DIR / "static" / "imgs"


def ensure_directories():
    """
    确保所有目标文件夹存在
    """
    for category in SIZE_CONFIG.keys():
        folder = TARGET_BASE / category
        folder.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {folder}")


def resize_image(img: Image.Image, target_size: tuple, fit_mode: str = "cover") -> Image.Image:
    """
    调整图片尺寸
    
    Args:
        img: PIL Image对象
        target_size: (宽, 高) 目标尺寸
        fit_mode: 
            - "cover": 裁剪填充（保持比例，裁剪多余部分）
            - "contain": 缩放适应（保持比例，可能有留白）
    
    Returns:
        调整后的 PIL Image对象
    """
    target_w, target_h = target_size
    orig_w, orig_h = img.size
    
    if fit_mode == "cover":
        # 计算缩放比例，取较大值以填满目标区域
        scale = max(target_w / orig_w, target_h / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)
        
        # 缩放
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 居中裁剪
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))
    
    elif fit_mode == "contain":
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
    
    return img


def process_image(src_path: Path, dst_path: Path, target_size: tuple = None, quality: int = 85):
    """
    处理单张图片
    
    Args:
        src_path: 源图片路径
        dst_path: 目标图片路径
        target_size: 目标尺寸，None则不调整
        quality: JPEG压缩质量 (1-100)
    """
    try:
        with Image.open(src_path) as img:
            # 转换为RGB（处理RGBA等格式）
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 调整尺寸
            if target_size:
                img = resize_image(img, target_size, fit_mode="cover")
            
            # 确保目标目录存在
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存为WebP
            output_path = dst_path.with_suffix(".webp")
            img.save(output_path, "WEBP", quality=quality, method=6)
            
            print(f"  ✓ {src_path.name} -> {output_path.name}")
            return True
            
    except Exception as e:
        print(f"  ✗ {src_path.name}: {e}")
        return False


def process_folder(src_folder: Path, category: str, sub_folder: str = None):
    """
    处理一个分类文件夹中的所有图片
    
    Args:
        src_folder: 源分类文件夹路径
        category: 分类名称
        sub_folder: 子文件夹名称（用于archive的月份子文件夹）
    """
    if not src_folder.exists():
        print(f"  跳过: {category}/ (文件夹不存在)")
        return 0, 0
    
    target_size = SIZE_CONFIG.get(category)
    
    # 确定目标文件夹路径
    if sub_folder:
        dst_folder = TARGET_BASE / category / sub_folder
    else:
        dst_folder = TARGET_BASE / category
    
    success_count = 0
    fail_count = 0
    
    for file_path in src_folder.iterdir():
        if file_path.suffix.lower() in SUPPORTED_FORMATS:
            dst_path = dst_folder / file_path.name
            if process_image(file_path, dst_path, target_size):
                success_count += 1
            else:
                fail_count += 1
    
    return success_count, fail_count


def process_archive(src_folder: Path):
    """
    处理archive文件夹，支持 胶片画幅/月份 两层子文件夹结构
    
    结构示例:
        archive/
        ├── 6x6/
        │   ├── 2024-01/
        │   ├── 2024-02/
        ├── 6x7/
        │   ├── 2024-01/
        └── 35mm/
            ├── 2024-01/
    
    Args:
        src_folder: archive源文件夹路径
    
    Returns:
        (success_count, fail_count)
    """
    if not src_folder.exists():
        print(f"  跳过: archive/ (文件夹不存在)")
        return 0, 0
    
    total_success = 0
    total_fail = 0
    
    # 第一层：胶片画幅文件夹 (6x6, 6x7, 35mm等)
    for format_folder in sorted(src_folder.iterdir()):
        if format_folder.is_dir():
            print(f"    画幅: {format_folder.name}/")
            
            # 第二层：月份文件夹 (2024-01, 2024-02等)
            for month_folder in sorted(format_folder.iterdir()):
                if month_folder.is_dir():
                    print(f"      月份: {month_folder.name}/")
                    # 目标路径: archive/画幅/月份/
                    sub_path = f"{format_folder.name}/{month_folder.name}"
                    success, fail = process_folder(month_folder, "archive", sub_path)
                    total_success += success
                    total_fail += fail
    
    return total_success, total_fail


def main():
    source_path="E:\个人主页图片文件夹"
    # if len(sys.argv) < 2:
    #     print(__doc__)
    #     print("错误: 请提供源文件夹路径")
    #     print("示例: python process_images.py D:\\my_photos")
    #     sys.exit(1)
    
    src_base = Path(source_path)
    
    if not src_base.exists():
        print(f"错误: 源文件夹不存在: {src_base}")
        sys.exit(1)
    
    print(f"源文件夹: {src_base}")
    print(f"目标文件夹: {TARGET_BASE}")
    print("-" * 50)
    
    # 创建目标文件夹结构
    print("\n创建文件夹结构:")
    ensure_directories()
    
    total_success = 0
    total_fail = 0
    
    for category in SIZE_CONFIG.keys():
        print(f"\n处理 {category}/:")
        src_folder = src_base / category
        
        # archive使用特殊处理（支持月份子文件夹）
        if category == "archive":
            success, fail = process_archive(src_folder)
        else:
            success, fail = process_folder(src_folder, category)
        
        total_success += success
        total_fail += fail
    
    print("\n" + "=" * 50)
    print(f"处理完成! 成功: {total_success}, 失败: {total_fail}")
    
    if total_success > 0:
        print(f"\n图片已保存到: {TARGET_BASE}")


if __name__ == "__main__":
    main()
