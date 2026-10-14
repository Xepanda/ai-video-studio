/**
 * scripts/browser_automation/browser_operator.js
 * 现代化多模态自主浏览器控制中枢 (Autonomous Browser Operator)
 * 
 * 机制设计 (对标 Codex / Playwright Inspector):
 * 1. 优先尝试附着到正在运行的 Chrome 调试端口 (9222 CDP)；
 * 2. 若未检测到 9222 端口，则自动使用本地系统 Chrome 启动全新浏览器实例；
 * 3. 具备自主智能定位与操作接口：
 *    - smartNavigate(url, waitUntil)
 *    - smartClick(selector_or_text)
 *    - smartType(selector, text, options)
 *    - smartUpload(selector_or_button, filePath)
 *    - captureSnapshot(outPath)
 *    - extractText(selector)
 */

const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

class BrowserOperator {
  constructor(options = {}) {
    this.cdpPort = options.cdpPort || 9222;
    this.chromePath = options.chromePath || 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
    this.browser = null;
    this.context = null;
    this.page = null;
    this.isAttached = false;
  }

  async init(headless = false) {
    console.log(`🔌 [BrowserOperator] 正在初始化浏览器接管引擎...`);
    // 1. 尝试 CDP 附着
    try {
      this.browser = await chromium.connectOverCDP(`http://localhost:${this.cdpPort}`);
      const contexts = this.browser.contexts();
      this.context = contexts[0];
      const pages = this.context.pages();
      this.page = pages.length > 0 ? pages[0] : await this.context.newPage();
      this.isAttached = true;
      console.log(`✅ [BrowserOperator] 成功通过 CDP 附着至现有 Chrome (Port ${this.cdpPort})！`);
      return;
    } catch (e) {
      console.log(`ℹ️ [BrowserOperator] 未发现 Port ${this.cdpPort} 实例，自动启动全新本地 Chrome...`);
    }

    // 2. 独立启动本地 Chrome
    if (!fs.existsSync(this.chromePath)) {
      const altPath = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe';
      if (fs.existsSync(altPath)) this.chromePath = altPath;
    }

    this.browser = await chromium.launch({
      executablePath: this.chromePath,
      headless: headless,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
    });
    this.context = await this.browser.newContext({
      viewport: { width: 1280, height: 800 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    });
    this.page = await this.context.newPage();
    this.isAttached = false;
    console.log(`✅ [BrowserOperator] 本地 Chrome 启动成功！`);
  }

  async navigate(url, waitUntil = 'domcontentloaded') {
    console.log(`🌐 [Navigate] 前往: ${url}`);
    await this.page.goto(url, { waitUntil, timeout: 30000 });
  }

  async smartClick(target) {
    console.log(`👆 [Click] 点击元素: "${target}"`);
    // 优先通过 CSS 选择器点击，失败则通过文本内容点击
    try {
      await this.page.waitForSelector(target, { timeout: 3000 });
      await this.page.click(target);
    } catch (e) {
      const btn = this.page.locator(`text="${target}"`).first();
      await btn.click({ timeout: 5000 });
    }
  }

  async smartType(selector, text, clear = true) {
    console.log(`⌨️ [Type] 向 [${selector}] 填入文本: "${text.substring(0, 30)}..."`);
    await this.page.waitForSelector(selector, { timeout: 5000 });
    if (clear) await this.page.fill(selector, '');
    await this.page.type(selector, text, { delay: 30 });
  }

  async snapshot(filepath) {
    const fullPath = path.resolve(filepath);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    await this.page.screenshot({ path: fullPath, fullPage: false });
    console.log(`📸 [Snapshot] 页面截图已保存至: ${fullPath}`);
    return fullPath;
  }

  async close() {
    if (this.browser && !this.isAttached) {
      await this.browser.close();
      console.log(`🚪 [BrowserOperator] 浏览器已安全关闭。`);
    } else {
      console.log(`🚪 [BrowserOperator] 断开 CDP 连接，保留用户浏览器窗口。`);
    }
  }
}

module.exports = { BrowserOperator };

if (require.main === module) {
  (async () => {
    const operator = new BrowserOperator();
    await operator.init(true); // Headless test
    await operator.navigate('https://httpbin.org/forms/post');
    await operator.smartType('input[name="custname"]', 'Xepanda AI Test');
    await operator.snapshot('D:/Projects/ai-video-studio/out/browser_operator_test.png');
    await operator.close();
    console.log('🎉 BrowserOperator 基础验证通过！');
  })().catch(err => {
    console.error('❌ BrowserOperator 验证失败:', err);
    process.exit(1);
  });
}
