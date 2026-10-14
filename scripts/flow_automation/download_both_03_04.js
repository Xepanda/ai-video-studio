const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function downloadBoth() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  // ==========================================
  // 1. Download Scene 04 (Top Tile)
  // ==========================================
  console.log('--- Downloading Scene 04 (Top Tile) ---');
  let beforeTime = Date.now() - 3000;

  // Hover top tile
  await page.mouse.move(400, 200);
  await page.waitForTimeout(600);

  // Click 3-dots on top tile
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => 
      b.getAttribute('aria-label') === '更多选项' && 
      b.getBoundingClientRect().y < 150 && 
      b.getBoundingClientRect().x < 650
    );
    if (btn) btn.click();
  });
  await page.waitForTimeout(800);

  // Hover "下载"
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
    const dl = all.find(el => (el.innerText || '').includes('下载'));
    if (dl) {
      let cur = dl;
      while (cur && !cur.classList.contains('mat-mdc-menu-item') && cur !== document.body) cur = cur.parentElement;
      (cur || dl).dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      (cur || dl).dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await page.waitForTimeout(800);

  // Click resolution (720p or 1080p)
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
    });
    if (all.length > 0) {
      let cur = all[0];
      while (cur && cur.tagName !== 'BUTTON' && !cur.getAttribute('role')?.includes('menuitem') && cur !== document.body) cur = cur.parentElement;
      (cur || all[0]).click();
    }
  });
  console.log('Clicked download for Scene 04, waiting 15s...');
  await page.waitForTimeout(15000);

  const checkFiles = (timeThreshold) => {
    const footageFiles = fs.readdirSync(FOOTAGE_DIR)
      .map(f => ({ name: f, path: path.join(FOOTAGE_DIR, f), time: fs.statSync(path.join(FOOTAGE_DIR, f)).mtimeMs }))
      .filter(f => f.time >= timeThreshold && f.name.endsWith('.mp4'));
    const dlFiles = fs.existsSync(DOWNLOADS_DIR) ? fs.readdirSync(DOWNLOADS_DIR)
      .map(f => ({ name: f, path: path.join(DOWNLOADS_DIR, f), time: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
      .filter(f => f.time >= timeThreshold && f.name.endsWith('.mp4')) : [];
    return [...footageFiles, ...dlFiles].sort((a, b) => b.time - a.time);
  };

  let dl04 = checkFiles(beforeTime);
  console.log('Scene 04 downloaded files:', dl04);
  if (dl04.length > 0) {
    const target04 = path.join(FOOTAGE_DIR, 'scene_04.mp4');
    fs.copyFileSync(dl04[0].path, target04);
    console.log(`Saved scene_04.mp4 successfully! Size: ${(fs.statSync(target04).size / 1024 / 1024).toFixed(2)} MB`);
  }

  // ==========================================
  // 2. Download Scene 03 (3rd Tile)
  // ==========================================
  console.log('\n--- Downloading Scene 03 (3rd Tile) ---');
  beforeTime = Date.now() - 3000;

  // Hover 3rd tile (around y: 720)
  await page.mouse.move(400, 720);
  await page.waitForTimeout(600);

  // Find the more options button for the 3rd tile (y between 550 and 700)
  const clickedTile3 = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => 
      b.getAttribute('aria-label') === '更多选项' && 
      b.getBoundingClientRect().y > 500 && 
      b.getBoundingClientRect().y < 700 &&
      b.getBoundingClientRect().x < 650
    );
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  console.log('Clicked 3rd tile more button:', clickedTile3);
  await page.waitForTimeout(800);

  // Hover "下载"
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
    const dl = all.find(el => (el.innerText || '').includes('下载'));
    if (dl) {
      let cur = dl;
      while (cur && !cur.classList.contains('mat-mdc-menu-item') && cur !== document.body) cur = cur.parentElement;
      (cur || dl).dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      (cur || dl).dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await page.waitForTimeout(800);

  // Click resolution (720p or 1080p)
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
    });
    if (all.length > 0) {
      let cur = all[0];
      while (cur && cur.tagName !== 'BUTTON' && !cur.getAttribute('role')?.includes('menuitem') && cur !== document.body) cur = cur.parentElement;
      (cur || all[0]).click();
    }
  });
  console.log('Clicked download for Scene 03, waiting 15s...');
  await page.waitForTimeout(15000);

  let dl03 = checkFiles(beforeTime);
  console.log('Scene 03 downloaded files:', dl03);
  if (dl03.length > 0) {
    const target03 = path.join(FOOTAGE_DIR, 'scene_03.mp4');
    fs.copyFileSync(dl03[0].path, target03);
    console.log(`Saved scene_03.mp4 successfully! Size: ${(fs.statSync(target03).size / 1024 / 1024).toFixed(2)} MB`);
  }

  await client.detach();
  await browser.close();
}

downloadBoth().catch(console.error);
