const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function clickTileMenu() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  const beforeTime = Date.now() - 3000;

  // Hover over the tile first so the hotbar/pill is visible
  console.log('Hovering over tile at x: 400, y: 200...');
  await page.mouse.move(400, 200);
  await page.waitForTimeout(800);

  // Click the 3-dots button at x: 580, y: 120
  console.log('Clicking 3-dots button at x: 580, y: 120...');
  await page.mouse.click(580, 120);
  await page.waitForTimeout(1000);

  // Take screenshot of opened menu
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/tile_menu_open.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/tile_menu_open.png');

  // Find all items in the menu
  const menuItems = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, div')).filter(el => {
      const text = (el.innerText || '').trim();
      return text.includes('下载') || text.includes('Download');
    }).map(el => ({
      text: el.innerText,
      className: el.className,
      rect: el.getBoundingClientRect()
    }));
  });
  console.log('Download menu items:', menuItems);

  if (menuItems.length > 0) {
    const dlItem = menuItems[0];
    console.log('Hovering over download menu item at:', dlItem.rect.x + dlItem.rect.width / 2, dlItem.rect.y + dlItem.rect.height / 2);
    await page.mouse.move(dlItem.rect.x + dlItem.rect.width / 2, dlItem.rect.y + dlItem.rect.height / 2);
    await page.waitForTimeout(1000);

    snap = await client.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('D:/Projects/ai-video-studio/out/dl_submenu_open.png', Buffer.from(snap.data, 'base64'));
    console.log('Saved screenshot: out/dl_submenu_open.png');

    // Click 720p or 1080p
    console.log('Finding and clicking 720p / 1080p...');
    const clickedRes = await page.evaluate(() => {
      const allElements = Array.from(document.querySelectorAll('*')).filter(el => {
        const text = (el.innerText || '').trim();
        return (text === '720p' || text === '1080p') && el.children.length === 0;
      });
      if (allElements.length > 0) {
        let clickable = allElements[0];
        while (clickable && clickable.tagName !== 'BUTTON' && !clickable.getAttribute('role')?.includes('menuitem') && clickable !== document.body) {
          clickable = clickable.parentElement;
        }
        (clickable || allElements[0]).click();
        return true;
      }
      return false;
    });
    console.log('Clicked resolution item:', clickedRes);

    console.log('Waiting 15s for download to finish...');
    await page.waitForTimeout(15000);

    // Look for new file
    const footageFiles = fs.readdirSync(FOOTAGE_DIR)
      .map(f => ({ name: f, path: path.join(FOOTAGE_DIR, f), time: fs.statSync(path.join(FOOTAGE_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4'));
    const dlFiles = fs.existsSync(DOWNLOADS_DIR) ? fs.readdirSync(DOWNLOADS_DIR)
      .map(f => ({ name: f, path: path.join(DOWNLOADS_DIR, f), time: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4')) : [];
    const allRecent = [...footageFiles, ...dlFiles].sort((a, b) => b.time - a.time);
    console.log('Recent downloaded files:', allRecent);

    if (allRecent.length > 0) {
      const target = path.join(FOOTAGE_DIR, 'scene_01.mp4');
      fs.copyFileSync(allRecent[0].path, target);
      console.log(`Saved scene_01.mp4 successfully! Size: ${(fs.statSync(target).size / 1024 / 1024).toFixed(2)} MB`);
    }
  }

  await client.detach();
  await browser.close();
}

clickTileMenu().catch(console.error);
