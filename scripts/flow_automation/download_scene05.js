const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function downloadTopTile() {
  const targetPath = path.join(FOOTAGE_DIR, 'scene_05.mp4');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  const beforeTime = Date.now() - 5000;

  console.log('Hovering over top tile...');
  await page.mouse.move(400, 200);
  await page.waitForTimeout(1000);

  console.log('Clicking 3-dots on top tile...');
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => 
      b.getAttribute('aria-label') === '更多选项' && 
      b.getBoundingClientRect().y < 160 && 
      b.getBoundingClientRect().x < 650
    );
    if (btn) btn.click();
    else console.log('3-dots button not found');
  });
  await page.waitForTimeout(1000);

  console.log('Hovering 下载 menu item...');
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
    const dl = all.find(el => (el.innerText || '').includes('下载'));
    if (dl) {
      let cur = dl;
      while (cur && !cur.classList.contains('mat-mdc-menu-item') && cur !== document.body) cur = cur.parentElement;
      (cur || dl).dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      (cur || dl).dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    } else {
      console.log('下载 menu item not found');
    }
  });
  await page.waitForTimeout(1000);

  console.log('Clicking resolution (720p or 1080p)...');
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
    });
    if (all.length > 0) {
      let cur = all[0];
      while (cur && cur.tagName !== 'BUTTON' && !cur.getAttribute('role')?.includes('menuitem') && cur !== document.body) cur = cur.parentElement;
      (cur || all[0]).click();
    } else {
      console.log('Resolution button not found');
    }
  });

  console.log('Waiting 15s for download...');
  await page.waitForTimeout(15000);

  const checkFiles = () => {
    const footageFiles = fs.readdirSync(FOOTAGE_DIR)
      .map(f => ({ name: f, path: path.join(FOOTAGE_DIR, f), time: fs.statSync(path.join(FOOTAGE_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4'));
    const dlFiles = fs.existsSync(DOWNLOADS_DIR) ? fs.readdirSync(DOWNLOADS_DIR)
      .map(f => ({ name: f, path: path.join(DOWNLOADS_DIR, f), time: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4')) : [];
    return [...footageFiles, ...dlFiles].sort((a, b) => b.time - a.time);
  };

  const dl = checkFiles();
  console.log('Downloaded files:', dl);
  if (dl.length > 0) {
    fs.copyFileSync(dl[0].path, targetPath);
    console.log(`Saved scene_05.mp4 successfully! Size: ${(fs.statSync(targetPath).size / 1024 / 1024).toFixed(2)} MB`);
  }

  await client.detach();
  await browser.close();
}

downloadTopTile().catch(console.error);
