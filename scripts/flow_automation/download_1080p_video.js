const { chromium } = require('playwright-core');
const fs = require('fs');

async function download1080p() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Configure CDP download behavior so any browser-triggered download goes directly to our folder
  const client = await flowPage.context().newCDPSession(flowPage);
  const downloadTargetDir = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: downloadTargetDir
  });
  console.log('Set CDP download behavior to:', downloadTargetDir);

  // Monitor network responses for video
  flowPage.on('response', async (res) => {
    const url = res.url();
    const type = res.headers()['content-type'] || '';
    if (url.includes('.mp4') || type.includes('video') || (url.includes('googleusercontent') && type.includes('octet-stream'))) {
      console.log('==> Detected potential video download URL:', url, 'type:', type);
    }
  });

  // Ensure menu is open
  let opt1080 = flowPage.locator('text=1080p').first();
  if (!await opt1080.isVisible()) {
    console.log('Opening menu...');
    await flowPage.mouse.move(400, 180);
    await flowPage.waitForTimeout(500);
    const moreBtn = flowPage.locator('flow-video-hotbar button[aria-label="更多选项"]').first();
    await moreBtn.click();
    await flowPage.waitForTimeout(800);
    const dlMenu = flowPage.locator('text=下载').first();
    await dlMenu.hover();
    await flowPage.waitForTimeout(800);
    opt1080 = flowPage.locator('text=1080p').first();
  }

  console.log('Clicking 1080p option...');
  await opt1080.click();
  console.log('Clicked 1080p! Waiting 15s for download to complete...');
  await flowPage.waitForTimeout(15000);

  // Check files in folder
  const files = fs.readdirSync(downloadTargetDir);
  console.log('Files in footage folder:', files);

  await client.detach();
  await browser.close();
}

download1080p().catch(console.error);
