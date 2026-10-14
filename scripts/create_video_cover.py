#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/create_video_cover.py
合成包含视觉吸引力大字排版的专业视频封面 (1920x1080)
"""

import os
import sys
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC_IMAGE = r"C:\Users\ePanda\.gemini\antigravity\brain\8cadcb22-6c45-487a-b888-0e1dd8fdc796\how_to_live_better_cover_1791984912050.jpg"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(PUBLIC_DIR, exist_ok=True)

# 1. 复制纯净版封面
clean_out = os.path.join(OUT_DIR, "cover_clean.jpg")
shutil.copy(SRC_IMAGE, clean_out)
shutil.copy(SRC_IMAGE, os.path.join(PUBLIC_DIR, "cover_clean.jpg"))

# 2. 制作带大标题包装的高点击率 Bilibili / 视频号 封面
img = Image.open(SRC_IMAGE).convert("RGBA")
W, H = img.size  # 1920, 1080

overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

# 字体加载
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
font_top = ImageFont.truetype(FONT_BOLD, 36)
font_main = ImageFont.truetype(FONT_BOLD, 84)
font_sub = ImageFont.truetype(FONT_BOLD, 36)

# 顶部分类小标
top_badge_text = "开源硬核循证 · 第一期"
top_badge_bbox = font_top.getbbox(top_badge_text)
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
draw.text((tb_x + 28, tb_y - 2), top_badge_text, font=font_top, fill=(37, 99, 235, 255))

# 主标题两行排版 (大字冲击力)
line1 = "几乎零成本"
line2 = "换回十年寿命！"

m_y1 = 170
m_y2 = 280

# 文本阴影与发光效果
for offset_x, offset_y in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, 4)]:
    draw.text((tb_x + offset_x, m_y1 + offset_y), line1, font=font_main, fill=(255, 255, 255, 200))
    draw.text((tb_x + offset_x, m_y2 + offset_y), line2, font=font_main, fill=(255, 255, 255, 200))

draw.text((tb_x, m_y1), line1, font=font_main, fill=(15, 23, 42, 255)) # 深岩黑
draw.text((tb_x, m_y2), line2, font=font_main, fill=(225, 29, 72, 255)) # 醒目朱红高光

# 底部亮点标签
tags = ["690条顶级医学实证", "NEJM两万人低钠盐研究", "零意志力避坑"]
tag_x = tb_x
tag_y = 410

for tag in tags:
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
