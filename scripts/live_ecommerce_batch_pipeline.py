#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Live E-Commerce Batch Pipeline (数据驱动版)
=============================================
依据 skills/live-ecommerce-video-editor/SKILL.md 与 docs/LIVE_ECOMMERCE_SOP.md 的标准,
将「编辑计划 JSON (plan)」一键合成为可直接发布的抖音竖屏带货短视频。

项目目录约定 (与 _template_project 一致):
  <project>/01_raw_materials/video/     原始直播素材
  <project>/02_scripts_and_docs/plans/  每个 SKU 一份 <sku_id>.plan.json
  <project>/03_intermediate/<sku_id>/   中间产物 (clips / stickers / audio)
  <project>/04_final_output/<sku_id>/   成片 + 封面

用法:
  python scripts/live_ecommerce_batch_pipeline.py --project <project_dir> --sku <sku_id> [--stage all]

plan.json 关键约定:
  * 所有时间点均「锚定到切片」: {"clip": "c03", "off": 1.2, "dur": 3.0}
    -> 实际时间轴 = 该切片在成片中的真实起点 + off, 彻底消除累积漂移。
  * clips[].zoom = 放大倍率(1.0 不放大), hflip = 镜像翻转, y_anchor = 放大锚点纵向系数。
  * split = 对称 50:50 双色/双款分屏 (居中发光分割线 + 左右胶囊标签)。
"""
import os
import sys
import json
import wave
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_HEAVY = "C:/Windows/Fonts/simhei.ttf" if os.name == "nt" else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MSYH = "C:/Users/ePanda/.workbuddy/binaries/python/envs/liveclip/Lib/site-packages"  # placeholder no-op
FONT_MSYH = "C:/Windows/Fonts/msyhbd.ttc" if os.name == "nt" else FONT_HEAVY

OUT_W, OUT_H, FPS = 1080, 1920, 30
ASS_HL = "&H0000E6FF&"   # 亮黄高亮 (BGR)
ASS_WHITE = "&H00FFFFFF&"


def run(cmd, cwd=None, desc=""):
    print(f"[RUN] {desc or cmd[0]} ...", flush=True)
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         encoding="utf-8", errors="replace", cwd=cwd)
    if res.returncode != 0:
        print(res.stderr[-2000:])
        raise RuntimeError(f"FAILED: {desc or ' '.join(cmd[:6])}")
    return res.stdout


def ffprobe_duration(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", path], desc=f"probe {os.path.basename(path)}")
    return float(out.strip())


# ----------------------------------------------------------------------------
# 视觉资产
# ----------------------------------------------------------------------------

def gen_boom(path, duration=1.2, sr=48000):
    """45Hz~90Hz 带阻尼衰减的 Sub-Bass 冲击音效 (SKILL.md §6.2)"""
    if os.path.exists(path):
        return path
    t = np.linspace(0, duration, int(sr * duration), False)
    freq = np.linspace(90, 45, len(t))
    wavef = np.sin(2 * np.pi * freq * t)
    env = np.exp(-4.5 * t)
    audio = (wavef * env * 32767 * 0.9).astype(np.int16)
    with wave.open(path, "w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(np.column_stack((audio, audio)).flatten().tobytes())
    print(f"[ASSET] boom -> {path}")
    return path


def _glow_box(draw, x0, y0, x1, y1, radius=28, glow=12):
    for r in range(glow, 0, -3):
        alpha = int(24 * (glow - r) / glow)
        draw.rounded_rectangle([x0 - r, y0 - r, x1 + r, y1 + r], radius=radius + r, fill=(0, 0, 0, alpha))


def gen_sticker(item, path):
    """挂角利益点徽章 (低带宽 y=1400, 避开人脸与字幕安全区)"""
    canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f_tag = ImageFont.truetype(FONT_MSYH, 26)
    f_title = ImageFont.truetype(FONT_MSYH, 38)
    f_desc = ImageFont.truetype(FONT_MSYH, 28)

    box_w, box_h = 780, 126
    x0, y0 = (OUT_W - box_w) // 2, 1400
    x1, y1 = x0 + box_w, y0 + box_h
    _glow_box(d, x0, y0, x1, y1)
    d.rounded_rectangle([x0, y0, x1, y1], radius=24, fill=(15, 18, 26, 225))
    d.rounded_rectangle([x0, y0, x1, y1], radius=24, outline=(255, 255, 255, 80), width=2)

    tag = item["tag"]
    tb = d.textbbox((0, 0), tag, font=f_tag)
    tw = tb[2] - tb[0] + 24
    tx0, ty0 = x0 + 18, y0 + 16
    d.rounded_rectangle([tx0, ty0, tx0 + tw, ty0 + 36], radius=10, fill=tuple(item["tag_bg"]))
    d.text((tx0 + 12, ty0 + 3), tag, font=f_tag, fill=(255, 255, 255))

    d.text((tx0 + tw + 15, y0 + 12), item["title"], font=f_title, fill=tuple(item.get("title_color", (255, 255, 255))))
    d.text((x0 + 20, y0 + 72), item["desc"], font=f_desc, fill=tuple(item.get("desc_color", (255, 220, 100))))
    canvas.save(path, "PNG")
    print(f"[ASSET] sticker {os.path.basename(path)}")


def gen_hook_card(cfg, path):
    """黄金 3 秒超大标题卡 (胸前带 y=1140~1316, 绝不遮挡面部)"""
    canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f_title = ImageFont.truetype(FONT_MSYH, 62)
    f_sub = ImageFont.truetype(FONT_MSYH, 36)

    box_w, box_h = 980, 176
    x0, y0 = (OUT_W - box_w) // 2, 1140
    x1, y1 = x0 + box_w, y0 + box_h
    _glow_box(d, x0, y0, x1, y1, radius=30, glow=20)
    d.rounded_rectangle([x0, y0, x1, y1], radius=30, fill=(220, 18, 38, 248))
    d.rounded_rectangle([x0, y0, x1, y1], radius=30, outline=(255, 225, 60, 255), width=5)
    d.rounded_rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], radius=26, outline=(255, 255, 255, 120), width=2)

    title = cfg["title"]
    tb = d.textbbox((0, 0), title, font=f_title)
    tx, ty = (OUT_W - (tb[2] - tb[0])) // 2, y0 + 16
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            if dx or dy:
                d.text((tx + dx, ty + dy), title, font=f_title, fill=(0, 0, 0, 230))
    d.text((tx, ty), title, font=f_title, fill=(255, 245, 60))

    sub_w, sub_h = 780, 52
    sx0, sy0 = (OUT_W - sub_w) // 2, y0 + 104
    d.rounded_rectangle([sx0, sy0, sx0 + sub_w, sy0 + sub_h], radius=16,
                        fill=(15, 18, 28, 230), outline=(255, 255, 255, 140), width=2)
    sub = cfg["sub"]
    sb = d.textbbox((0, 0), sub, font=f_sub)
    sx, sy = (OUT_W - (sb[2] - sb[0])) // 2, sy0 + 6
    d.text((sx + 2, sy + 2), sub, font=f_sub, fill=(0, 0, 0, 220))
    d.text((sx, sy), sub, font=f_sub, fill=(255, 255, 255))
    canvas.save(path, "PNG")
    print(f"[ASSET] hook card -> {path}")


def gen_split_overlay(cfg, path):
    """对称分屏遮罩: 中央发光分割线 + 左右胶囊标签"""
    canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f_tag = ImageFont.truetype(FONT_MSYH, 32)
    for r in range(6, 0, -2):
        d.line([(OUT_W // 2, 0), (OUT_W // 2, OUT_H)], fill=(255, 255, 255, int(40 * (8 - r) / 8)), width=r * 2)
    d.line([(OUT_W // 2, 0), (OUT_W // 2, OUT_H)], fill=(255, 215, 0, 235), width=6)
    y0 = 1420
    for side, tag in (("left", cfg["left_tag"]), ("right", cfg["right_tag"])):
        x0 = 150 if side == "left" else 690
        d.rounded_rectangle([x0, y0, x0 + 240, y0 + 66], radius=16, fill=(15, 20, 30, 225),
                            outline=(255, 255, 255, 140), width=2)
        tb = d.textbbox((0, 0), tag, font=f_tag)
        d.text((x0 + (240 - (tb[2] - tb[0])) // 2, y0 + 14), tag, font=f_tag, fill=(255, 255, 255))
    canvas.save(path, "PNG")
    print(f"[ASSET] split overlay -> {path}")


def gen_cta(cfg, path):
    """尾部 2~3s 下单引导气泡 (左下角, 避开平台底部 UI)"""
    canvas = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(FONT_MSYH, 40)
    text = cfg["text"]
    tb = d.textbbox((0, 0), text, font=f)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad = 28
    x0, y0 = 40, 1408
    x1, y1 = x0 + tw + pad * 2 + 56, y0 + th + 44
    _glow_box(d, x0, y0, x1, y1, radius=22)
    d.rounded_rectangle([x0, y0, x1, y1], radius=22, fill=(220, 18, 38, 240),
                        outline=(255, 225, 60, 255), width=4)
    d.text((x0 + pad, y0 + 20), text, font=f, fill=(255, 255, 255))
    # 手绘指向箭头 (指向左下小黄车)
    ax, ay = x1 - 40, (y0 + y1) // 2
    d.line([(ax + 18, ay - 16), (ax - 8, ay + 12)], fill=(255, 235, 60), width=7)
    d.polygon([(ax - 22, ay + 18), (ax + 2, ay + 14), (ax - 4, ay - 4)], fill=(255, 235, 60))
    canvas.save(path, "PNG")
    print(f"[ASSET] cta badge -> {path}")


# ----------------------------------------------------------------------------
# ASS 字幕
# ----------------------------------------------------------------------------

def _ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _highlight(text, keywords):
    out = text
    for kw in keywords or []:
        if kw and kw in out:
            out = out.replace(kw, f"{{\\c{ASS_HL}&}}{kw}{{\\c{ASS_WHITE}&}}")
    return out


def gen_ass(events, path, tl_json=None):
    """字幕事件锚定切片; 若提供实测 timeline 则先解析为绝对时间"""
    if tl_json is not None:
        resolved = []
        for ev in events:
            t0 = tl(tl_json, ev["clip"], ev.get("off", 0.0))
            resolved.append({**ev, "t0": t0, "t1": round(t0 + ev.get("dur", 0), 3)})
        events = resolved
    lines = [
        "[Script Info]", "Title: Douyin Fashion Subtitles", "ScriptType: v4.00+",
        "WrapStyle: 0", "ScaledBorderAndShadow: yes", "YCbCr Matrix: TV.709",
        f"PlayResX: {OUT_W}", f"PlayResY: {OUT_H}", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: DouyinSubtitle,Microsoft YaHei,52,&H00FFFFFF,&H000000FF,&H00121216,&H80000000,-1,0,0,0,"
        "100,100,1,0,1,4.5,2.0,2,40,40,240,1",
        "", "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for ev in events:
        txt = _highlight(ev["text"], ev.get("hl"))
        lines.append(f"Dialogue: 0,{_ass_time(ev['t0'])},{_ass_time(ev['t1'])},DouyinSubtitle,,0,0,0,,{txt}")
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[ASSET] subtitles {len(events)} events -> {path}")


# ----------------------------------------------------------------------------
# 渲染
# ----------------------------------------------------------------------------

def base_chain(clip):
    """1088x1920 -> 居中裁 1080 -> 可选 hflip / 推镜 zoom -> 统一 fps"""
    z = clip.get("zoom", 1.0)
    ya = clip.get("y_anchor", 0.35)
    parts = [f"crop={OUT_W}:{OUT_H}:(iw-{OUT_W})/2:0"]
    if clip.get("hflip"):
        parts.append("hflip")
    if z and z > 1.0:
        parts.append(f"crop=w=iw/{z}:h=ih/{z}:x=(iw-iw/{z})/2:y=(ih-ih/{z})*{ya},scale={OUT_W}:{OUT_H}")
    parts.append(f"fps={FPS},setsar=1")
    return ",".join(parts)


def render_clips(plan, src_root, work):
    clips_dir = os.path.join(work, "clips")
    os.makedirs(clips_dir, exist_ok=True)
    ordered = [c["id"] for c in plan["clips"]]
    sp = plan.get("split")
    if sp:
        after = sp.get("after")
        idx = ordered.index(after) + 1 if after in ordered else len(ordered)
        ordered.insert(idx, sp["id"])
    for c in plan["clips"]:
        out = os.path.join(clips_dir, f"{c['id']}.mp4")
        if os.path.exists(out):
            continue
        src = os.path.join(src_root, c["src"].replace("/", os.sep))
        fade = 0.05
        af = f"afade=t=in:st=0:d={fade},afade=t=out:st={max(0.0, c['dur'] - fade):.3f}:d={fade}"
        run(["ffmpeg", "-y", "-ss", f"{c['st']}", "-t", f"{c['dur']}", "-i", src,
             "-vf", base_chain(c), "-af", af,
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out],
            desc=f"clip {c['id']} ({c['dur']}s zoom={c.get('zoom', 1.0)}{' hflip' if c.get('hflip') else ''})")
    sp = plan.get("split")
    if sp:
        out = os.path.join(clips_dir, f"{sp['id']}.mp4")
        if not os.path.exists(out):
            dur = sp["dur"]
            ol = os.path.join(work, "split_overlay.png")
            fade = 0.05
            lx = sp["left"].get("crop_x", 160); rx = sp["right"].get("crop_x", 160)
            fc = (
                f"[0:v]fps={FPS},crop=540:{OUT_H}:{lx}:0[vl];"
                f"[1:v]fps={FPS},crop=540:{OUT_H}:{rx}:0[vr];"
                f"[vl][vr]hstack[vs];[vs][2:v]overlay=0:0:format=auto[vout]"
            )
            lsrc = os.path.join(src_root, sp["left"]["src"].replace("/", os.sep))
            rsrc = os.path.join(src_root, sp["right"]["src"].replace("/", os.sep))
            run(["ffmpeg", "-y",
                 "-ss", f"{sp['left']['st']}", "-t", f"{dur}", "-i", lsrc,
                 "-ss", f"{sp['right']['st']}", "-t", f"{dur}", "-i", rsrc,
                 "-loop", "1", "-t", f"{dur}", "-i", ol,
                 "-filter_complex", fc, "-map", "[vout]", "-map", "0:a",
                 "-af", f"afade=t=in:st=0:d={fade},afade=t=out:st={dur - fade:.3f}:d={fade}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", out],
                desc=f"split clip {sp['id']}")
    # 实测时长 -> 时间轴 (按最终成片顺序)
    by_id = {c["id"]: c for c in plan["clips"]}
    if plan.get("split"):
        by_id[plan["split"]["id"]] = plan["split"]
    timeline, acc = {}, 0.0
    for cid in ordered:
        d = ffprobe_duration(os.path.join(clips_dir, f"{cid}.mp4"))
        timeline[cid] = {"start": round(acc, 3), "dur": round(d, 3)}
        acc += d
    with open(os.path.join(work, "timeline.json"), "w", encoding="utf-8") as f:
        json.dump(timeline, f, ensure_ascii=False, indent=2)
    print(f"[TIMELINE] total {acc:.2f}s")
    return timeline


def tl(tl_json, clip_id, off=0.0):
    e = tl_json[clip_id]
    return round(e["start"] + off, 3)


def resolve(events, tl_json, key="clip", get_off=lambda e: e.get("off", 0.0), get_end=None):
    out = []
    for e in events:
        t0 = tl(tl_json, e[key], get_off(e))
        t1 = tl(tl_json, e[key], get_end(e)) if get_end else t0 + e.get("dur", 0)
        out.append((t0, t1, e))
    return out


def ordered_ids(plan):
    ids = [c["id"] for c in plan["clips"]]
    sp = plan.get("split")
    if sp:
        idx = ids.index(sp["after"]) + 1 if sp.get("after") in ids else len(ids)
        ids.insert(idx, sp["id"])
    return ids


def assemble(plan, work, out_dir, sku_id):
    clips_dir = os.path.join(work, "clips")
    tl_json = json.load(open(os.path.join(work, "timeline.json"), encoding="utf-8"))
    ids = ordered_ids(plan)

    total = round(tl_json[ids[-1]]["start"] + tl_json[ids[-1]]["dur"], 3)

    concat = os.path.join(work, "concat_list.txt")
    with open(concat, "w", encoding="utf-8") as f:
        for cid in ids:
            f.write(f"file '{os.path.join(clips_dir, cid + '.mp4').replace(os.sep, '/')}'\n")

    # overlay 时间窗 (clip 锚定)
    windows = []
    if plan.get("hook_card"):
        hc = plan["hook_card"]
        windows.append((os.path.join(work, "hook_card.png"),
                        tl(tl_json, hc["clip"], hc.get("off", 0.0)),
                        tl(tl_json, hc["clip"], hc.get("off", 0.0) + hc.get("dur", 2.0))))
    for st in plan.get("stickers", []):
        windows.append((os.path.join(work, "stickers", st["file"]),
                        tl(tl_json, st["clip"], st.get("off", 0.0)),
                        tl(tl_json, st["clip"], st.get("off", 0.0) + st.get("dur", 0))))
    if plan.get("cta"):
        cta = plan["cta"]
        windows.append((os.path.join(work, "cta.png"),
                        max(0.0, total - cta.get("dur", 2.5)), total + 1))

    inputs = ["-f", "concat", "-safe", "0", "-i", concat]
    for p, a, b in windows:
        inputs += ["-loop", "1", "-t", f"{total + 1}", "-i", p]
    inputs += ["-i", os.path.join(work, "boom.wav")]

    fc = []
    prev = "0:v"
    for i, (p, a, b) in enumerate(windows, start=1):
        nxt = f"v{i}"
        fc.append(f"[{prev}][{i}:v]overlay=0:0:enable='between(t,{a},{b})'[{nxt}]")
        prev = nxt
    fc.append(f"[{prev}]subtitles={os.path.basename(plan['subtitle']['file'])}[vout]")

    b = plan.get("boom", {})
    w_boom = b.get("volume", 0.45)
    fc.append(f"[{len(windows) + 1}:a]volume={w_boom}[hit]")
    fc.append(f"[0:a][hit]amix=inputs=2:duration=first:weights='1.0 1.0'[amix]")
    fade_st = max(0.0, total - 0.25)
    fc.append(f"[amix]afade=t=out:st={fade_st}:d=0.25[aout]")

    out_mp4 = os.path.join(out_dir, f"{sku_id}_final.mp4")
    run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc),
         "-map", "[vout]", "-map", "[aout]",
         "-t", f"{total}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
         "-movflags", "+faststart", out_mp4],
        cwd=work, desc=f"ASSEMBLE {sku_id} ({total:.1f}s)")
    return out_mp4, total


def gen_cover(plan, src_root, out_dir, sku_id):
    cfg = plan["cover"]
    if not cfg:
        return None
    src = os.path.join(src_root, cfg["src"].replace("/", os.sep))
    frame = os.path.join(out_dir, f"{sku_id}_cover_frame.jpg")
    run(["ffmpeg", "-y", "-ss", f"{cfg['t']}", "-i", src, "-frames:v", "1",
         "-vf", f"crop={OUT_W}:{OUT_H}:(iw-{OUT_W})/2:0", "-q:v", "2", frame],
        desc=f"cover frame @{cfg['t']}s")
    base = Image.open(frame).convert("RGBA")
    ov = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f_h1 = ImageFont.truetype(FONT_HEAVY, 66)
    f_sub = ImageFont.truetype(FONT_MSYH, 34)
    f_tag = ImageFont.truetype(FONT_HEAVY, 46)
    f_price = ImageFont.truetype(FONT_HEAVY, 64)
    f_desc = ImageFont.truetype(FONT_MSYH, 32)

    # 中部大标题 (y=1150~1430, 本批素材人脸普遍占满上半屏, 避开面部)
    d.rounded_rectangle([40, 1150, 1040, 1430], radius=30, fill=(215, 20, 35, 245),
                        outline=(255, 225, 110, 255), width=6)
    d.text((OUT_W // 2, 1245), cfg["title"], font=f_h1,
           fill=(255, 240, 85), anchor="mm", stroke_width=4, stroke_fill=(110, 10, 10))
    d.rounded_rectangle([140, 1340, 940, 1400], radius=24, fill=(18, 18, 22, 230),
                        outline=(255, 215, 0, 220), width=3)
    d.text((OUT_W // 2, 1370), cfg["sub"], font=f_sub, fill=(255, 255, 255), anchor="mm")

    # 底部福利腰封 (y=1550~1780)
    d.rectangle([0, 1550, OUT_W, 1780], fill=(12, 12, 16, 230))
    d.rounded_rectangle([60, 1585, 330, 1665], radius=16, fill=(230, 30, 45, 255))
    d.text((195, 1625), cfg["tag"], font=f_tag, fill=(255, 255, 255), anchor="mm")
    d.text((365, 1622), cfg["price"], font=f_price, fill=(255, 235, 60),
           stroke_width=3, stroke_fill=(150, 20, 20))
    d.text((OUT_W // 2, 1723), cfg["points"], font=f_desc, fill=(255, 235, 120), anchor="mm")

    out = os.path.join(out_dir, f"{sku_id}_cover_default.jpg")
    Image.alpha_composite(base, ov).convert("RGB").save(out, quality=95)
    print(f"[COVER] -> {out}")
    return out


# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--sku", required=True)
    ap.add_argument("--stage", default="all", choices=["all", "assets", "clips", "assemble", "cover"])
    args = ap.parse_args()

    proj = os.path.abspath(args.project)
    src_root = os.path.join(proj, "01_raw_materials", "video")
    docs = os.path.join(proj, "02_scripts_and_docs")
    work = os.path.join(proj, "03_intermediate", args.sku)
    out_dir = os.path.join(proj, "04_final_output", args.sku)
    for p in (work, os.path.join(work, "stickers"), out_dir):
        os.makedirs(p, exist_ok=True)

    plan = json.load(open(os.path.join(docs, "plans", f"{args.sku}.plan.json"), encoding="utf-8"))
    sku = plan["sku_id"]

    if args.stage in ("all", "assets"):
        gen_boom(os.path.join(work, "boom.wav"))
        for it in plan.get("assets", {}).get("stickers", []):
            gen_sticker(it, os.path.join(work, "stickers", f"{it['id']}.png"))
        if plan.get("hook_card"):
            gen_hook_card(plan["assets"]["hook_card"], os.path.join(work, "hook_card.png"))
        if plan.get("split"):
            gen_split_overlay(plan["assets"]["split_overlay"], os.path.join(work, "split_overlay.png"))
        if plan.get("cta"):
            gen_cta(plan["cta"], os.path.join(work, "cta.png"))

    if args.stage in ("all", "clips"):
        render_clips(plan, src_root, work)

    if args.stage in ("all", "assemble"):
        tl_json = json.load(open(os.path.join(work, "timeline.json"), encoding="utf-8"))
        gen_ass(plan["subtitle"]["events"], os.path.join(work, plan["subtitle"]["file"]), tl_json)
        mp4, total = assemble(plan, work, out_dir, sku)
        print(f"[DONE] {mp4} ({total:.2f}s)")

    if args.stage in ("all", "cover"):
        gen_cover(plan, src_root, out_dir, sku)


if __name__ == "__main__":
    main()
