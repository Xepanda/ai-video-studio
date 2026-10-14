const { chromium } = require('playwright-core');
const fs = require('fs');

async function download720p() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  const client = await flowPage.context().newCDPSession(flowPage);
  const downloadTargetDir = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: downloadTargetDir
  });

  // Track any downloads via network or events
  let downloadedUrl = null;
  flowPage.on('response', async (res) => {
    const url = res.url();
    const type = res.headers()['content-type'] || '';
    if (url.includes('.mp4') || type.includes('video') || (url.includes('googleusercontent') && type.includes('octet-stream'))) {
      console.log('===> DETECTED VIDEO DOWNLOAD URL:', url);
      downloadedUrl = url;
    }
  });

  console.log('Hovering tile and opening more menu...');
  await flowPage.mouse.move(400, 180);
  await flowPage.waitForTimeout(500);

  await flowPage.evaluate(() => {
    const more = document.querySelector('flow-video-hotbar button[aria-label="更多选项"]');
    if (more) more.click();
  });
  await flowPage.waitForTimeout(800);

  // Hover 下载
  await flowPage.evaluate(() => {
    const allItems = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"]'));
    const dl = allItems.find(i => (i.innerText || '').includes('下载'));
    if (dl) {
      dl.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      dl.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await flowPage.waitForTimeout(800);

  // Click 720p
  console.log('Clicking 720p menu item...');
  const clicked720 = await flowPage.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return text === '720p' && el.children.length === 0;
    });
    if (elements.length > 0) {
      let clickable = elements[0];
      while (clickable && clickable.tagName !== 'BUTTON' && !clickable.getAttribute('role')?.includes('menuitem') && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      (clickable || elements[0]).click();
      return true;
    }
    return false;
  });

  console.log('Clicked 720p result:', clicked720);
  console.log('Waiting 10s for download to finish...');
  await flowPage.waitForTimeout(10000);

  // Check footage folder
  const files = fs.readdirSync(downloadTargetDir);
  console.log('Files in footage folder:', files);

  // Check downloads folder
  const downloadsDir = process.env.USERPROFILE + '\\Downloads';
  const recentDownloads = fs.readdirSync(downloadsDir)
    .map(f => ({ name: f, time: fs.statSync(downloadsDir + '\\' + f).mtimeMs }))
    .sort((a, b) => b.time - a.time)
    .slice(0, 5);
  console.log('Recent user downloads:', recentDownloads);

  await client.detach();
  await browser.close();
}

download720p().catch(console.error);
