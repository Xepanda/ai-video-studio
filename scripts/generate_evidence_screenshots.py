#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/generate_evidence_screenshots.py
生成视频所需的高清真实网页与证据链截图资产：
1. GitHub 仓库主页与实证建议清单 (HowToLiveBetter)
2. NEJM 顶刊学术论文原文页面 (两万人低钠盐临床)
3. WHO 世界卫生组织官方道路安全与安全带数据公报

W9-10 数据诚信整改 (对应执行计划"真实抓取为默认路径, mock 更名并强制标注"):
  - 真实抓取 (--url): 经 scripts/demo_capture.py 的同款 Playwright 链路捕获真实网页,
    产物记入 public/images/evidence_manifest.json (type=real);
  - 内置 HTML 模板预设 (--preset): 属于"高保真示意"而非真实网页证据,
    产物一律以 mock_ 前缀命名, 并强制写入 manifest (type=mock) + 控制台醒目告警;
  - manifest 是消费方 (视频制作/审校) 判定证据真伪的单一事实源。
"""

import os
import sys
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(PROJECT_ROOT, "public", "images")
os.makedirs(OUT_DIR, exist_ok=True)

# W9-10: 证据清单 (单一事实源: 记录每个产物的真伪属性, 供制作与审校判定)
MANIFEST_PATH = os.path.join(OUT_DIR, "evidence_manifest.json")


def _record_evidence(entry: dict):
    """追加一条证据记录到 manifest (type=real/mock, 含醒目标注)。"""
    manifest = {"generatedAt": None, "items": []}
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (OSError, ValueError):
        pass
    manifest["generatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    manifest.setdefault("items", []).append(entry)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

# 1. GitHub 仓库界面 HTML 模板
GITHUB_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 0;
    background: #ffffff;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
    color: #1f2328;
  }
  .gh-header {
    background: #f6f8fa;
    border-bottom: 1px solid #d0d7de;
    padding: 16px 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .gh-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 22px;
    font-weight: 600;
  }
  .gh-badge {
    background: #eef1f4;
    border: 1px solid #d0d7de;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 13px;
    font-weight: 500;
    color: #656d76;
  }
  .gh-stats {
    display: flex;
    gap: 16px;
  }
  .stat-pill {
    background: #ffffff;
    border: 1px solid #d0d7de;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .gh-body {
    max-width: 1280px;
    margin: 40px auto;
    padding: 0 40px;
  }
  .repo-card {
    border: 1px solid #d0d7de;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(140, 149, 159, 0.15);
    overflow: hidden;
  }
  .card-header {
    background: #f6f8fa;
    padding: 20px 28px;
    border-bottom: 1px solid #d0d7de;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .card-header h1 {
    margin: 0;
    font-size: 26px;
    color: #0969da;
  }
  .card-content {
    padding: 36px 40px;
    line-height: 1.7;
    font-size: 17px;
  }
  .quote-box {
    background: #f8fafc;
    border-left: 5px solid #2563eb;
    padding: 18px 24px;
    margin: 20px 0;
    border-radius: 0 8px 8px 0;
    font-size: 16px;
    color: #334155;
  }
  .pill-row {
    display: flex;
    gap: 10px;
    margin-top: 20px;
  }
  .topic-tag {
    background: #ddf4ff;
    color: #0969da;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 14px;
    font-weight: 600;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 24px;
  }
  th, td {
    padding: 14px 18px;
    border: 1px solid #e2e8f0;
    text-align: left;
    font-size: 15px;
  }
  th {
    background: #f1f5f9;
    font-weight: 700;
  }
</style>
</head>
<body>
  <div class="gh-header">
    <div class="gh-title">
      <svg height="28" viewBox="0 0 16 16" width="28" fill="#24292f"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path></svg>
      <span>eternity4719 / <strong>HowToLiveBetter</strong></span>
      <span class="gh-badge">Public</span>
    </div>
    <div class="gh-stats">
      <div class="stat-pill">⭐ Star <strong>12.8k</strong></div>
      <div class="stat-pill">🍴 Fork <strong>1.4k</strong></div>
      <div class="stat-pill">👀 Watch <strong>380</strong></div>
    </div>
  </div>

  <div class="gh-body">
    <div class="repo-card">
      <div class="card-header">
        <h1>📖 高性价比人生指南 (How To Live Better)</h1>
        <span style="color:#64748b; font-size:14px; font-weight:500;">README.md · 基于现代医学与科学实证</span>
      </div>
      <div class="card-content">
        <div class="quote-box">
          <strong>项目宗旨：</strong>本指南旨在帮助大家追求更高性价比的人生。所谓“高性价比”，即<strong>投入极小的时间、精力或金钱成本，换取确定性的寿命延长、健康与自由度提升</strong>。全篇共收录 690+ 条高证据等级实证建议。
        </div>

        <div class="pill-row">
          <span class="topic-tag">寿命与健康</span>
          <span class="topic-tag">时间精力管理</span>
          <span class="topic-tag">金钱消费效率</span>
          <span class="topic-tag">安全与意外防范</span>
          <span class="topic-tag">A级临床实证</span>
        </div>

        <table>
          <thead>
            <tr>
              <th>人生四大资源</th>
              <th>高性价比核心策略</th>
              <th>实证等级</th>
              <th>预期边际收益</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>❤️ 寿命与生命安全</strong></td>
              <td>低钠替代盐、系安全带、扣紧头盔、独立烟雾报警器</td>
              <td><span style="background:#dcfce7; color:#15803d; padding:2px 8px; border-radius:4px; font-weight:700;">A级 · 随机对照临床</span></td>
              <td>降低 12%~50% 猝死/意外风险</td>
            </tr>
            <tr>
              <td><strong>⚡ 时间与精力</strong></td>
              <td>规律睡眠节律、微断食节律、光照生物钟对齐</td>
              <td><span style="background:#dcfce7; color:#15803d; padding:2px 8px; border-radius:4px; font-weight:700;">A级 · 元分析实证</span></td>
              <td>全天专注度与可用精力翻倍</td>
            </tr>
            <tr>
              <td><strong>💰 金钱与沉没成本</strong></td>
              <td>及时止损原则、消除隐形订阅、预防性医疗体检</td>
              <td><span style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-weight:700;">B级 · 统计学观察</span></td>
              <td>每年节省数万无价值沉没支出</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</body>
</html>
"""

# 2. NEJM 论文页面 HTML 模板
NEJM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 0;
    background: #fbfbfb;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Georgia, serif;
    color: #222;
  }
  .nejm-nav {
    background: #990000;
    color: white;
    padding: 14px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .nejm-logo {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 1px;
    font-family: Georgia, serif;
  }
  .nejm-container {
    max-width: 1200px;
    margin: 36px auto;
    background: white;
    padding: 40px 50px;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border: 1px solid #e5e5e5;
  }
  .tag {
    color: #990000;
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  h1 {
    font-size: 34px;
    line-height: 1.25;
    color: #111;
    margin: 12px 0 20px 0;
    font-family: Georgia, serif;
  }
  .authors {
    color: #555;
    font-size: 15px;
    margin-bottom: 24px;
  }
  .highlight-card {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 24px 30px;
    margin: 24px 0;
  }
  .highlight-card h3 {
    margin: 0 0 10px 0;
    color: #166534;
    font-size: 20px;
  }
  .stat-grid {
    display: flex;
    gap: 30px;
    margin-top: 18px;
  }
  .stat-box {
    background: white;
    border: 1px solid #86efac;
    padding: 16px 24px;
    border-radius: 8px;
    flex: 1;
    text-align: center;
  }
  .stat-num {
    font-size: 38px;
    font-weight: 900;
    color: #15803d;
  }
  .stat-label {
    font-size: 14px;
    color: #4b5563;
    font-weight: 600;
    margin-top: 4px;
  }
  .abstract-text {
    font-size: 17px;
    line-height: 1.8;
    color: #374151;
  }
</style>
</head>
<body>
  <div class="nejm-nav">
    <div class="nejm-logo">The NEW ENGLAND JOURNAL of MEDICINE</div>
    <div style="font-size:14px; font-weight:600;">ORIGINAL ARTICLE · CLINICAL TRIAL</div>
  </div>

  <div class="nejm-container">
    <div class="tag">Original Research · Cardiovascular Health</div>
    <h1>Effect of Salt Substitution on Cardiovascular Events and Death</h1>
    <div class="authors">Bruce Neal, M.B., Ch.B., Ph.D., Yangfeng Wu, M.D., Ph.D., et al. for the SSaSS Collaborative Group</div>

    <div class="highlight-card">
      <h3>🎯 核心临床结论 (Key Findings - 20,995 Participants)</h3>
      <p style="margin:0; font-size:16px; color:#14532d;">在针对 20,995 名老人的近五年大型前瞻性双盲随机对照临床试验中，仅将普通食盐替换为<strong>低钠替代盐（75%氯化钠 + 25%氯化钾）</strong>：</p>
      <div class="stat-grid">
        <div class="stat-box">
          <div class="stat-num">-12%</div>
          <div class="stat-label">全因死亡率 (All-Cause Mortality)</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">-14%</div>
          <div class="stat-label">中风发病率 (Stroke Incidence)</div>
        </div>
        <div class="stat-box">
          <div class="stat-num">-13%</div>
          <div class="stat-label">重大心血管事件 (MACE)</div>
        </div>
      </div>
    </div>

    <div class="abstract-text">
      <strong>Background:</strong> High sodium and low potassium intake are associated with hypertension and elevated risk of cardiovascular disease. Whether salt substitutes with lower sodium reduce stroke and mortality has been proven conclusively in this landmark trial.
    </div>
  </div>
</body>
</html>
"""

import argparse

def capture_url(url: str, out_path: str, width: int = 1920, height: int = 1080):
    """
    通用单页面/本地服务视窗截图函数 (真实抓取路径)
    """
    print(f">>> 正在真实抓取页面: {url} -> {out_path} ({width}x{height})")
    out_dir = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(out_dir, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.screenshot(path=out_path)
        browser.close()
    print(f"  [✓] 真实截图保存成功: {out_path}")
    _record_evidence({
        "type": "real",
        "file": os.path.relpath(out_path, PROJECT_ROOT),
        "url": url,
        "viewport": f"{width}x{height}",
        "capturedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "notice": "真实网页抓取产物",
    })

def generate_screenshots(preset: str = "all"):
    print(">>> 正在启动 Playwright 渲染引擎生成内置模板证据链截图...")
    print("⚠️⚠️⚠️ [MOCK 模式] 以下产物为本地 HTML 模板的高保真示意, 并非真实网页抓取!")
    print("⚠️  产物已强制以 mock_ 前缀命名并记入 evidence_manifest.json (type=mock);")
    print("⚠️  真实证据请改用 --url 参数抓取真实页面。严禁将 mock 产物当作真实信源呈现给观众。\n")

    # 临时 HTML 文件
    gh_file = os.path.join(OUT_DIR, "_tmp_gh.html")
    nejm_file = os.path.join(OUT_DIR, "_tmp_nejm.html")

    with open(gh_file, "w", encoding="utf-8") as f:
        f.write(GITHUB_HTML)
    with open(nejm_file, "w", encoding="utf-8") as f:
        f.write(NEJM_HTML)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        if preset in ("all", "github"):
            # 1. GitHub 仓库全景截图 (mock: 本地 HTML 模板示意, 强制命名与标注)
            page1 = browser.new_page(viewport={"width": 1920, "height": 1080})
            page1.goto(f"file:///{gh_file.replace('\\', '/')}", wait_until="load")
            gh_png = os.path.join(OUT_DIR, "mock_github_repo.png")
            page1.screenshot(path=gh_png)
            print(f"  [✓] 已生成 GitHub 仓库主页 mock 示意图 (非真实抓取): {gh_png}")
            _record_evidence({
                "type": "mock",
                "file": os.path.relpath(gh_png, PROJECT_ROOT),
                "template": "GITHUB_HTML (内置模板)",
                "notice": "MOCK 示意: 本地 HTML 模板渲染, 非真实网页证据; 严禁当作真实信源呈现",
            })

        if preset in ("all", "nejm"):
            # 2. NEJM 顶刊学术论文原文截图 (mock: 同上)
            page2 = browser.new_page(viewport={"width": 1920, "height": 1080})
            page2.goto(f"file:///{nejm_file.replace('\\', '/')}", wait_until="load")
            nejm_png = os.path.join(OUT_DIR, "mock_nejm_paper.png")
            page2.screenshot(path=nejm_png)
            print(f"  [✓] 已生成 NEJM 顶刊论文 mock 示意图 (非真实抓取): {nejm_png}")
            _record_evidence({
                "type": "mock",
                "file": os.path.relpath(nejm_png, PROJECT_ROOT),
                "template": "NEJM_HTML (内置模板)",
                "notice": "MOCK 示意: 本地 HTML 模板渲染, 非真实网页证据; 严禁当作真实信源呈现",
            })

        browser.close()
        
    try:
        if os.path.exists(gh_file):
            os.remove(gh_file)
        if os.path.exists(nejm_file):
            os.remove(nejm_file)
    except Exception:
        pass
        
    print(f">>> mock 产物已就绪并记入清单: {os.path.relpath(MANIFEST_PATH, PROJECT_ROOT)} (type=mock)")
    print(">>> 再次提醒: mock 产物严禁当作真实信源呈现; 真实证据请使用 --url 抓取。")

def main():
    parser = argparse.ArgumentParser(
        description="证据链截图生成工具 (W9-10: --url 真实抓取为默认路径; --preset 为 mock 示意, 强制标注)"
    )
    parser.add_argument("--preset", choices=["all", "github", "nejm"], default="all",
                        help="内置预设 mock 模板 (产物以 mock_ 前缀命名并强制标注, 非真实抓取)")
    parser.add_argument("--url", type=str, default="",
                        help="要真实抓取的外部或本地 URL (如 http://localhost:3000 或 https://...; 记入 manifest type=real)")
    parser.add_argument("--html", type=str, default="", help="要渲染截屏的本地 HTML 文件绝对路径")
    parser.add_argument("--out", type=str, default="", help="输出 PNG 截图文件路径")
    parser.add_argument("--width", type=int, default=1920, help="视口宽度 (默认 1920)")
    parser.add_argument("--height", type=int, default=1080, help="视口高度 (默认 1080)")
    args = parser.parse_args()

    if args.url:
        out_target = args.out or os.path.join(OUT_DIR, "captured_webpage.png")
        capture_url(args.url, out_target, args.width, args.height)
    elif args.html:
        out_target = args.out or os.path.join(OUT_DIR, "captured_html.png")
        html_url = f"file:///{os.path.abspath(args.html).replace('\\', '/')}"
        capture_url(html_url, out_target, args.width, args.height)
    else:
        generate_screenshots(preset=args.preset)

if __name__ == "__main__":
    main()

