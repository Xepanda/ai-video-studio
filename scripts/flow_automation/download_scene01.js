const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function downloadScene01() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  const beforeTime = Date.now() - 5000;

  // Hover over the top tile on the canvas
  console.log('Hovering over top tile on canvas (x: 400, y: 200)...');
  await page.mouse.move(400, 200);
  await page.waitForTimeout(1000);

  // Take snapshot of hover state
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/tile_hover.png', Buffer.from(snap.data, 'base64'));

  // Look for any hotbar buttons or "更多选项" buttons
  const moreBtns = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button')).filter(b => {
      const label = b.getAttribute('aria-label') || '';
      const text = b.innerText || '';
      return label.includes('更多') || text.includes('more') || label.includes('more');
    }).map(b => ({
      ariaLabel: b.getAttribute('aria-label'),
      rect: b.getBoundingClientRect()
    }));
  });
  console.log('More buttons found:', moreBtns);

  // Click the more options button on the top tile
  const topTileMore = moreBtns.find(b => b.rect.y < 300 && b.rect.x < 600);
  if (topTileMore) {
    console.log('Clicking top tile more button:', topTileMore);
    await page.mouse.click(topTileMore.rect.x + topTileMore.rect.width / 2, topTileMore.rect.y + topTileMore.rect.height / 2);
  } else {
    console.log('Fallback: clicking hotbar button directly...');
    await page.evaluate(() => {
      const more = document.querySelector('flow-video-hotbar button[aria-label="更多选项"], [aria-label="更多选项"]');
      if (more) more.click();
    });
  }

  await page.waitForTimeout(1000);
  snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/menu_open.png', Buffer.from(snap.data, 'base64'));

  // Hover over "下载"
  console.log('Hovering over "下载"...');
  await page.evaluate(() => {
    const allItems = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
    const dl = allItems.find(i => (i.innerText || '').includes('下载'));
    if (dl) {
      let cur = dl;
      while (cur && !cur.classList.contains('mat-mdc-menu-item') && cur.tagName !== 'BUTTON' && cur !== document.body) {
        cur = cur.parentElement;
      }
      (cur || dl).dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      (cur || dl).dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await page.waitForTimeout(1000);

  snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/dl_submenu.png', Buffer.from(snap.data, 'base64'));

  // Click 720p or 1080p
  console.log('Clicking resolution (720p or 1080p)...');
  const clicked = await page.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
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
  console.log('Resolution click result:', clicked);

  console.log('Waiting 15s for download...');
  await page.waitForTimeout(15000);

  // Check downloads
  const checkFiles = () => {
    const footageFiles = fs.readdirSync(FOOTAGE_DIR)
      .map(f => ({ name: f, path: path.join(FOOTAGE_DIR, f), time: fs.statSync(path.join(FOOTAGE_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4'));
    const dlFiles = fs.existsSync(DOWNLOADS_DIR) ? fs.readdirSync(DOWNLOADS_DIR)
      .map(f => ({ name: f, path: path.join(DOWNLOADS_DIR, f), time: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4')) : [];
    return [...footageFiles, ...dlFiles].sort((a, b) => b.time - a.time);
  };

  const recent = checkFiles();
  console.log('Recently downloaded video files:', recent);

  if (recent.length > 0) {
    const targetPath = path.join(FOOTAGE_DIR, 'scene_01.mp4');
    fs.copyFileSync(recent[0].path, targetPath);
    console.log(`Successfully saved scene_01.mp4! Size: ${(fs.statSync(targetPath).size / 1024 / 1024).toFixed(2)} MB`);
  }

  await client.detach();
  await browser.close();
}

downloadScene01().catch(console.error);
