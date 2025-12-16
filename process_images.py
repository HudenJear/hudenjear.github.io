"""
图片处理脚本 v2.0
将源文件夹中的图片统一处理后存储到 static/imgs/photos 目录
并生成 manifest.json 索引文件

使用方法:
    python process_images.py

源文件夹结构:
    source_folder/
    ├── archive/            # 所有归档图片（按画幅/月份分类）
    │   ├── 6x6/
    │   │   ├── 2024-01/
    │   │   └── ...
    │   ├── 6x7/
    │   └── 35mm/
    ├── hero.txt            # 标记哪些图片用于Hero（每行一个图片ID）
    ├── filmlab/            # Film Lab 图片
    ├── prints/             # Prints 图片
    └── common/             # 通用图片

输出:
    static/imgs/
    ├── photos/             # 所有图片统一存储（原比例）
    │   ├── 6x6_2024-12_001.webp
    │   └── ...
    └── manifest.json       # 图片元数据索引
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
except ImportError:
    print("请先安装 Pillow: pip install Pillow")
    sys.exit(1)


# 配置
MAX_DIMENSION = 1800        # 图片长边最大像素
WEBP_QUALITY = 85           # WebP压缩质量

# 支持的图片格式
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}

# 路径配置
SCRIPT_DIR = Path(__file__).parent
TARGET_BASE = SCRIPT_DIR / "static" / "imgs"
PHOTOS_DIR = TARGET_BASE / "photos"
MANIFEST_PATH = TARGET_BASE / "manifest.json"


def ensure_directories():
    """确保目标文件夹存在"""
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {PHOTOS_DIR}")


def resize_to_max_dimension(img: Image.Image, max_dim: int) -> Image.Image:
    """
    按比例缩放图片，使长边不超过指定尺寸
    
    Args:
        img: PIL Image对象
        max_dim: 长边最大像素
    
    Returns:
        缩放后的 PIL Image对象
    """
    orig_w, orig_h = img.size
    
    # 如果图片已经小于最大尺寸，不处理
    if max(orig_w, orig_h) <= max_dim:
        return img
    
    # 计算缩放比例
    if orig_w > orig_h:
        new_w = max_dim
        new_h = int(orig_h * max_dim / orig_w)
    else:
        new_h = max_dim
        new_w = int(orig_w * max_dim / orig_h)
    
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def generate_photo_id(format_name: str, date: str, index: int) -> str:
    """生成图片ID: 格式_日期_序号"""
    return f"{format_name}_{date}_{index:03d}"


def process_single_image(src_path: Path, photo_id: str) -> dict:
    """
    处理单张图片，保存到photos目录，返回元数据
    
    Args:
        src_path: 源图片路径
        photo_id: 图片ID
    
    Returns:
        图片元数据字典，失败返回None
    """
    try:
        with Image.open(src_path) as img:
            # 转换为RGB
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # 记录原始尺寸
            orig_w, orig_h = img.size
            
            # 按比例缩放（保持原比例）
            img = resize_to_max_dimension(img, MAX_DIMENSION)
            new_w, new_h = img.size
            
            # 保存为WebP
            output_path = PHOTOS_DIR / f"{photo_id}.webp"
            img.save(output_path, "WEBP", quality=WEBP_QUALITY, method=6)
            
            print(f"  ✓ {src_path.name} -> {photo_id}.webp ({new_w}x{new_h})")
            
            return {
                "id": photo_id,
                "file": f"photos/{photo_id}.webp",
                "originalName": src_path.name,
                "width": new_w,
                "height": new_h
            }
            
    except Exception as e:
        print(f"  ✗ {src_path.name}: {e}")
        return None


def load_hero_list(src_base: Path) -> set:
    """
    加载hero.txt，获取标记为Hero的图片ID列表
    
    hero.txt格式（每行一个图片ID）:
        6x6_2024-12_001
        6x7_2024-11_003
    """
    hero_file = src_base / "hero.txt"
    hero_ids = set()
    
    if hero_file.exists():
        with open(hero_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    hero_ids.add(line)
        print(f"  已加载 {len(hero_ids)} 个Hero图片ID")
    else:
        print(f"  hero.txt 不存在，将使用所有archive图片作为Hero候选")
    
    return hero_ids


def process_archive_folder(src_folder: Path, manifest: dict, hero_ids: set):
    """
    处理archive文件夹，遍历 画幅/月份 结构
    
    Args:
        src_folder: archive源文件夹路径
        manifest: manifest字典（会被修改）
        hero_ids: Hero图片ID集合
    
    Returns:
        (success_count, fail_count)
    """
    if not src_folder.exists():
        print(f"  跳过: archive/ (文件夹不存在)")
        return 0, 0
    
    total_success = 0
    total_fail = 0
    
    # 遍历画幅文件夹
    for format_folder in sorted(src_folder.iterdir()):
        if not format_folder.is_dir():
            continue
            
        format_name = format_folder.name
        print(f"    画幅: {format_name}/")
        
        # 初始化archive索引
        if format_name not in manifest["indexes"]["archive"]:
            manifest["indexes"]["archive"][format_name] = {}
        
        # 遍历月份文件夹
        for month_folder in sorted(format_folder.iterdir()):
            if not month_folder.is_dir():
                continue
                
            month_name = month_folder.name
            print(f"      月份: {month_name}/")
            
            # 初始化月份索引
            manifest["indexes"]["archive"][format_name][month_name] = []
            
            # 处理该月份的所有图片
            index = 1
            for file_path in sorted(month_folder.iterdir()):
                if file_path.suffix.lower() not in SUPPORTED_FORMATS:
                    continue
                
                # 生成图片ID
                photo_id = generate_photo_id(format_name, month_name, index)
                
                # 处理图片
                metadata = process_single_image(file_path, photo_id)
                if metadata:
                    # 添加archive信息
                    metadata["format"] = format_name
                    metadata["date"] = month_name
                    metadata["category"] = "archive"
                    
                    # 判断是否为Hero
                    # 如果hero.txt为空，默认所有图片都可作为Hero
                    is_hero = (len(hero_ids) == 0) or (photo_id in hero_ids)
                    metadata["tags"] = ["archive"]
                    if is_hero:
                        metadata["tags"].append("hero")
                        manifest["indexes"]["hero"].append(photo_id)
                    
                    # 保存到manifest
                    manifest["photos"][photo_id] = metadata
                    manifest["indexes"]["archive"][format_name][month_name].append(photo_id)
                    
                    total_success += 1
                    index += 1
                else:
                    total_fail += 1
    
    return total_success, total_fail


def process_simple_folder(src_folder: Path, category: str, manifest: dict):
    """
    处理简单文件夹（filmlab, prints, common）
    
    Args:
        src_folder: 源文件夹路径
        category: 分类名称
        manifest: manifest字典
    
    Returns:
        (success_count, fail_count)
    """
    if not src_folder.exists():
        print(f"  跳过: {category}/ (文件夹不存在)")
        return 0, 0
    
    total_success = 0
    total_fail = 0
    
    # 初始化索引
    if category not in manifest["indexes"]:
        manifest["indexes"][category] = []
    
    index = 1
    for file_path in sorted(src_folder.iterdir()):
        if file_path.suffix.lower() not in SUPPORTED_FORMATS:
            continue
        
        # 生成图片ID
        photo_id = f"{category}_{index:03d}"
        
        # 处理图片
        metadata = process_single_image(file_path, photo_id)
        if metadata:
            metadata["category"] = category
            metadata["tags"] = [category]
            
            manifest["photos"][photo_id] = metadata
            manifest["indexes"][category].append(photo_id)
            
            total_success += 1
            index += 1
        else:
            total_fail += 1
    
    return total_success, total_fail


def save_manifest(manifest: dict):
    """保存manifest.json"""
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\n✓ manifest.json 已保存: {MANIFEST_PATH}")


def main():
    source_path = "E:\\个人主页图片文件夹"
    
    src_base = Path(source_path)
    
    if not src_base.exists():
        print(f"错误: 源文件夹不存在: {src_base}")
        sys.exit(1)
    
    print(f"源文件夹: {src_base}")
    print(f"目标文件夹: {TARGET_BASE}")
    print("-" * 50)
    
    # 创建目标文件夹
    print("\n创建文件夹结构:")
    ensure_directories()
    
    # 初始化manifest
    manifest = {
        "version": "2.0",
        "generatedAt": datetime.now().isoformat(),
        "photos": {},
        "indexes": {
            "hero": [],
            "archive": {}
        }
    }
    
    # 加载Hero列表
    print("\n加载Hero配置:")
    hero_ids = load_hero_list(src_base)
    
    total_success = 0
    total_fail = 0
    
    # 处理archive（主要图片来源）
    print("\n处理 archive/:")
    success, fail = process_archive_folder(src_base / "archive", manifest, hero_ids)
    total_success += success
    total_fail += fail
    
    # 处理其他简单文件夹
    for category in ["filmlab", "prints", "common"]:
        print(f"\n处理 {category}/:")
        success, fail = process_simple_folder(src_base / category, category, manifest)
        total_success += success
        total_fail += fail
    
    # 保存manifest
    save_manifest(manifest)
    
    # 统计信息
    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"  总图片: {total_success} 成功, {total_fail} 失败")
    print(f"  Hero图片: {len(manifest['indexes']['hero'])} 张")
    print(f"  Archive画幅: {len(manifest['indexes']['archive'])} 种")
    
    if total_success > 0:
        print(f"\n图片已保存到: {PHOTOS_DIR}")
        print(f"索引文件: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
