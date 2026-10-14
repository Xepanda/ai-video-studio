const { chromium } = require('playwright-core');
const fs = require('fs');

async function triggerDownload() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Look for the "下载" menu item
  console.log('Locating "下载" item in menu...');
  let downloadItem = flowPage.locator('text=下载').first();

  if (!await downloadItem.isVisible()) {
    console.log('"下载" not visible yet, opening more menu first...');
    await flowPage.mouse.move(400, 180);
    await flowPage.waitForTimeout(500);
    const moreBtn = flowPage.locator('flow-video-hotbar button[aria-label="更多选项"]').first();
    await moreBtn.click();
    await flowPage.waitForTimeout(1000);
    downloadItem = flowPage.locator('text=下载').first();
  }

  console.log('Hovering over "下载" to check submenu...');
  await downloadItem.hover();
  await flowPage.waitForTimeout(1000);

  // Take screenshot of submenu
  const client = await flowPage.context().newCDPSession(flowPage);
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_download_submenu.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved submenu screenshot: out/flow_download_submenu.png');

  // Check what submenu items appeared
  const subOptions = await flowPage.evaluate(() => {
    return Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text.includes('MP4') || text.includes('1080') || text.includes('720') || text.includes('原画') || text.includes('视频')) && el.children.length === 0;
    }).map(el => ({
      tag: el.tagName,
      text: el.innerText.trim(),
      className: el.className
    }));
  });
  console.log('Submenu options:', subOptions);

  // Click the best download option or "下载" directly with download listener
  const targetOption = flowPage.locator('text=MP4, text=1080p, text=下载视频, text=下载').last();
  
  console.log('Setting up download listener and clicking target download option...');
  try {
    const downloadPromise = flowPage.waitForEvent('download', { timeout: 15000 });
    await targetOption.click();
    const download = await downloadPromise;
    const destPath = 'D:/Projects/ai-video-studio/public/footage/meta_muse_apple/scene_02.mp4';
    await download.saveAs(destPath);
    console.log('SUCCESS! Downloaded video saved to:', destPath);
    const stats = fs.statSync(destPath);
    console.log(`File size: ${(stats.size / 1024 / 1024).toFixed(2)} MB`);
  } catch (err) {
    console.error('Download event catch:', err.message);
  }

  await client.detach();
  await browser.close();
  console.log('Done.');
}

triggerDownload().catch(console.error);
