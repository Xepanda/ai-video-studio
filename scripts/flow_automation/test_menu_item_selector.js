const { chromium } = require('playwright-core');
const fs = require('fs');

async function downloadVideoPrecision() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Configure CDP download behavior
  const client = await flowPage.context().newCDPSession(flowPage);
  const downloadTargetDir = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: downloadTargetDir
  });

  // Track network responses
  flowPage.on('response', async (res) => {
    const url = res.url();
    const type = res.headers()['content-type'] || '';
    if (url.includes('.mp4') || type.includes('video') || (url.includes('googleusercontent') && type.includes('octet-stream'))) {
      console.log('===> DOWNLOAD NETWORK EVENT:', url, type);
    }
  });

  // Move to video tile, hover, click more
  console.log('Hovering video tile (x: 400, y: 180)...');
  await flowPage.mouse.move(400, 180);
  await flowPage.waitForTimeout(600);

  const moreBtn = flowPage.locator('flow-video-hotbar button[aria-label="更多选项"]').first();
  await moreBtn.click();
  await flowPage.waitForTimeout(800);

  console.log('Hovering "下载" menu item...');
  const dlItem = flowPage.locator('.mat-mdc-menu-item:has-text("下载"), [role="menuitem"]:has-text("下载")').first();
  await dlItem.hover();
  await flowPage.waitForTimeout(800);

  // Dump all menu items currently in DOM
  const menuList = await flowPage.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"]')).map(el => ({
      text: el.innerText.trim().replace(/\s+/g, ' '),
      tag: el.tagName,
      className: el.className
    }));
    return items;
  });
  console.log('Currently visible menu items in DOM:', menuList);

  // Locate the 720p or 1080p item specifically within .mat-mdc-menu-item
  const target720 = flowPage.locator('.mat-mdc-menu-item:has-text("720p"), [role="menuitem"]:has-text("720p")').first();
  const target1080 = flowPage.locator('.mat-mdc-menu-item:has-text("1080p"), [role="menuitem"]:has-text("1080p")').first();

  let targetToClick = target1080;
  if (await target1080.isVisible()) {
    console.log('Found 1080p menu item! Clicking 1080p...');
  } else if (await target720.isVisible()) {
    console.log('1080p not visible, using 720p menu item! Clicking 720p...');
    targetToClick = target720;
  } else {
    console.log('Neither 1080p nor 720p menu item visible!');
  }

  // Click target
  await targetToClick.click({ force: true });
  console.log('Clicked download target! Waiting 15s to observe download files...');
  await flowPage.waitForTimeout(15000);

  // Check downloaded files in target directory
  const files = fs.readdirSync(downloadTargetDir);
  console.log('Files in directory:', files);

  // Also check User Downloads directory
  const downloadsDir = process.env.USERPROFILE + '\\Downloads';
  const recentDownloads = fs.readdirSync(downloadsDir)
    .map(f => ({ name: f, time: fs.statSync(downloadsDir + '\\' + f).mtimeMs }))
    .sort((a, b) => b.time - a.time)
    .slice(0, 5);
  console.log('Recent in Downloads:', recentDownloads);

  await client.detach();
  await browser.close();
}

downloadVideoPrecision().catch(console.error);
