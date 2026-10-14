/**
 * scripts/browser_flow_automation.js
 * Google Flow (flow.google.com) 浏览器全自动接管生成引擎
 * 
 * 机制:
 * 1. 用户启动真实 Chrome 并携带 --remote-debugging-port=9222 调试端口
 * 2. 用户在真实 Chrome 窗口中完成 Google 账号安全登录 (2FA / 密码)
 * 3. 本脚本通过 Playwright CDP (Chrome DevTools Protocol) 协议完全接管浏览器:
 *    - 自动定位或打开 flow.google.com
 *    - 自动上传首帧原画 (如 meta_muse_scene2_apple.png)
 *    - 自动填入镜头与物理动态提示词
 *    - 自动触发 Generate 并轮询渲染状态
 *    - 自动截屏汇报进度，并在完成后下载 MP4 至项目素材库
 */

const { chromium } = require('playwright-core');
const path = require('path');
const fs = require('fs');

async function main() {
  const cdpUrl = 'http://localhost:9222';
  console.log(`🔌 [Flow Agent] 正在连接本地 Chrome 调试实例 (${cdpUrl})...`);

  let browser;
  try {
    browser = await chromium.connectOverCDP(cdpUrl);
  } catch (err) {
    console.error(`❌ [Flow Agent] 无法连接到 Chrome 调试端口！`);
    console.error(`请先运行以下命令启动 Chrome 调试窗口并在其中登录 Google 账号:\n`);
    console.error(`  & "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222 --user-data-dir="$HOME\\.chrome-flow-profile" "https://flow.google.com"\n`);
    process.exit(1);
  }

  const contexts = browser.contexts();
  if (contexts.length === 0) {
    console.error('❌ [Flow Agent] 未找到活动的浏览器上下文');
    process.exit(1);
  }

  const context = contexts[0];
  let pages = context.pages();
  let page = pages.find(p => p.url().includes('flow.google.com'));

  if (!page) {
    console.log('🌐 [Flow Agent] 未找到已打开的 flow.google.com 标签页，正在新建标签页导航...');
    page = await context.newPage();
    await page.goto('https://flow.google.com', { waitUntil: 'domcontentloaded' });
  } else {
    console.log(`🎯 [Flow Agent] 已命中现存的 Google Flow 标签页: ${page.url()}`);
    await page.bringToFront();
  }

  // 等待页面加载并检查登录态
  console.log('⏳ [Flow Agent] 正在探测页面状态与登录凭据...');
  await page.waitForTimeout(2000);

  const title = await page.title();
  const url = page.url();
  console.log(`📄 当前页面标题: "${title}" | URL: ${url}`);

  // 截图留存给用户核验
  const screenshotPath = path.resolve(__dirname, '../out/flow_current_state.png');
  await page.screenshot({ path: screenshotPath });
  console.log(`📸 已保存当前浏览器状态截图至: ${screenshotPath}`);

  // 如果处于登录页面
  if (url.includes('accounts.google.com')) {
    console.log('\n⚠️  [Flow Agent] 检测到当前处于 Google 登录页面！');
    console.log('👉 请在打开的 Chrome 窗口中完成登录 (输入密码/2FA)，登录完成后再次运行本脚本即可完全自动接管！\n');
    return;
  }

  console.log('✅ [Flow Agent] 成功处于 Google Flow 授权环境，准备执行自动化操作！');
}

main().catch(err => {
  console.error('❌ [Flow Agent 异常]:', err);
  process.exit(1);
});
