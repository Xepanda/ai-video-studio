#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/create_video_cover.py
合成包含视觉吸引力大字排版的专业视频封面 (1920x1080)

配置方式 (环境变量或命令行参数):
  AVS_COVER_SRC   封面底图绝对路径 (必填; 原硬编码个人目录路径已移除)
  AVS_COVER_FONT  粗体中文字体路径 (可选; 默认按 Windows/Linux 常见字体自动探测)
  --src / --badge / --line1 / --line2 / --tags  命令行覆盖默认文案
"""

import os
import sys
import shutil
import argparse
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

# 封面底图: AVS_COVER_SRC 环境变量 > --src 参数 (原硬编码个人 .gemini 路径已移除)
SRC_IMAGE = os.environ.get("AVS_COVER_SRC", "")

# 粗体中文字体候选 (按优先级探测, 覆盖 Windows / Linux / macOS)
_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def resolve_font() -> str:
    """解析可用粗体字体: AVS_COVER_FONT > 内置候选探测, 全部缺失时返回空串由调用方报错。"""
    env_font = os.environ.get("AVS_COVER_FONT", "")
    if env_font and os.path.exists(env_font):
        return env_font
    for candidate in _FONT_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return ""


def create_cover(
    src_image: str,
    badge_text: str = "开源硬核循证 · 第一期",
    line1: str = "几乎零成本",
    line2: str = "换回十年寿命！",
    tags=None,
) -> str:
    """生成带大标题包装的高点击率封面, 返回成片绝对路径。"""
    if not src_image or not os.path.exists(src_image):
        raise FileNotFoundError(
            f"封面底图不存在: {src_image!r}。请设置 AVS_COVER_SRC 环境变量或传入 --src 指定底图绝对路径。"
        )

    font_path = resolve_font()
    if not font_path:
        raise FileNotFoundError(
            "未找到可用中文字体。请设置 AVS_COVER_FONT 指向一个 .ttf/.ttc 粗体字体文件。"
        )
    font_top = ImageFont.truetype(font_path, 36)
    font_main = ImageFont.truetype(font_path, 84)
    font_sub = ImageFont.truetype(font_path, 36)

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    # 1. 复制纯净版封面
    clean_out = os.path.join(OUT_DIR, "cover_clean.jpg")
    shutil.copy(src_image, clean_out)
    shutil.copy(src_image, os.path.join(PUBLIC_DIR, "cover_clean.jpg"))

    # 2. 制作带大标题包装的高点击率 Bilibili / 视频号 封面
    img = Image.open(src_image).convert("RGBA")
    W, H = img.size

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 顶部分类小标
    top_badge_bbox = font_top.getbbox(badge_text)
    tb_w = top_badge_bbox[2] - top_badge_bbox[0] + 36
    tb_h = top_badge_bbox[3] - top_badge_bbox[1]
    tb_x = 90
    tb_y = 80

    # 绘制顶部胶囊条
    draw.rounded_rectangle(
        [tb_x - 18, tb_y - 10, tb_x + tb_w + 18, tb_y + tb_h + 12],
        radius=16,
        fill=(255, 255, 255, 245),
        outline=(218, 224, 233, 255),
        width=2
    )
    # 蓝色指示点
    draw.ellipse([tb_x, tb_y + 11, tb_x + 16, tb_y + 27], fill=(37, 99, 235, 255))
    draw.text((tb_x + 28, tb_y - 2), badge_text, font=font_top, fill=(37, 99, 235, 255))

    # 主标题两行排版 (大字冲击力)
    m_y1 = 170
    m_y2 = 280

    # 文本阴影与发光效果
    for offset_x, offset_y in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 4)]:
        draw.text((tb_x + offset_x, m_y1 + offset_y), line1, font=font_main, fill=(255, 255, 255, 200))
        draw.text((tb_x + offset_x, m_y2 + offset_y), line2, font=font_main, fill=(255, 255, 255, 200))

    draw.text((tb_x, m_y1), line1, font=font_main, fill=(15, 23, 42, 255))  # 深岩黑
    draw.text((tb_x, m_y2), line2, font=font_main, fill=(225, 29, 72, 255))  # 醒目朱红高光

    # 底部亮点标签
    tag_list = tags if tags else ["690条顶级医学实证", "NEJM两万人低钠盐研究", "零意志力避坑"]
    tag_x = tb_x
    tag_y = 410

    for tag in tag_list:
        t_bbox = font_sub.getbbox(tag)
        t_w = t_bbox[2] - t_bbox[0]
        t_h = t_bbox[3] - t_bbox[1]

        draw.rounded_rectangle(
            [tag_x, tag_y, tag_x + t_w + 32, tag_y + t_h + 20],
            radius=14,
            fill=(255, 255, 255, 245),
            outline=(203, 213, 225, 240),
            width=2
        )
        draw.text((tag_x + 16, tag_y + 8), tag, font=font_sub, fill=(30, 41, 59, 255))
        tag_x += t_w + 48

    # 合成图层
    final_img = Image.alpha_composite(img, overlay).convert("RGB")

    out_with_title = os.path.join(OUT_DIR, "cover_with_title.jpg")
    final_img.save(out_with_title, quality=95)
    final_img.save(os.path.join(PUBLIC_DIR, "cover_with_title.jpg"), quality=95)

    # 默认主封面
    shutil.copy(out_with_title, os.path.join(OUT_DIR, "cover.jpg"))
    shutil.copy(out_with_title, os.path.join(PUBLIC_DIR, "cover.jpg"))

    print("✅ 封面生成并保存完成:")
    print(f"  1. 纯净画作版: {clean_out}")
    print(f"  2. 大标题营销版: {out_with_title}")
    print(f"  3. 默认封面: {os.path.join(OUT_DIR, 'cover.jpg')}")
    return out_with_title


def main():
    parser = argparse.ArgumentParser(description="专业视频封面合成 (1920x1080)")
    parser.add_argument("--src", default=SRC_IMAGE, help="封面底图绝对路径 (或设置 AVS_COVER_SRC)")
    parser.add_argument("--badge", default="开源硬核循证 · 第一期", help="顶部分类小标文案")
    parser.add_argument("--line1", default="几乎零成本", help="主标题第一行")
    parser.add_argument("--line2", default="换回十年寿命！", help="主标题第二行")
    parser.add_argument("--tags", nargs="*", default=None, help="底部亮点标签 (空格分隔多个)")
    args = parser.parse_args()

    try:
        create_cover(
            src_image=args.src,
            badge_text=args.badge,
            line1=args.line1,
            line2=args.line2,
            tags=args.tags,
        )
    except (FileNotFoundError, OSError) as e:
        print(f"❌ [Cover Error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
