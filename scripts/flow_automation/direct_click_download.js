const { chromium } = require('playwright-core');
const fs = require('fs');

async function directDownload() {
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

  // Check what overlays or menu items are currently in DOM
  const menuResult = await flowPage.evaluate(() => {
    // Look for 1080p and 720p elements
    const elements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '1080p' || text === '720p') && el.children.length === 0;
    });

    if (elements.length > 0) {
      // Find 1080p or 720p
      const el1080 = elements.find(e => e.innerText.trim() === '1080p');
      const el720 = elements.find(e => e.innerText.trim() === '720p');
      const target = el1080 || el720;
      
      // Find the clickable button / menuitem ancestor
      let clickable = target;
      while (clickable && clickable.tagName !== 'BUTTON' && !clickable.getAttribute('role')?.includes('menuitem') && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      
      if (clickable) {
        clickable.click();
        return { clicked: true, targetText: target.innerText, tag: clickable.tagName, html: clickable.outerHTML.slice(0, 150) };
      }
      target.click();
      return { clicked: true, targetText: target.innerText, tag: target.tagName };
    }
    return { clicked: false, count: elements.length };
  });

  console.log('Direct click result:', menuResult);

  if (!menuResult.clicked) {
    console.log('Menu was not open, let us dismiss backdrops, hover, and open cleanly...');
    await flowPage.keyboard.press('Escape');
    await flowPage.waitForTimeout(500);

    // Hover tile
    await flowPage.mouse.move(400, 180);
    await flowPage.waitForTimeout(500);

    // Click more
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
        dl.click();
      }
    });
    await flowPage.waitForTimeout(1000);

    // Try clicking 1080p again
    const secondTry = await flowPage.evaluate(() => {
      const elements = Array.from(document.querySelectorAll('*')).filter(el => {
        const text = (el.innerText || '').trim();
        return (text === '1080p' || text === '720p') && el.children.length === 0;
      });
      if (elements.length > 0) {
        const target = elements.find(e => e.innerText.trim() === '1080p') || elements[0];
        let clickable = target;
        while (clickable && clickable.tagName !== 'BUTTON' && !clickable.getAttribute('role')?.includes('menuitem') && clickable !== document.body) {
          clickable = clickable.parentElement;
        }
        (clickable || target).click();
        return { clicked: true, text: target.innerText };
      }
      return { clicked: false };
    });
    console.log('Second try click result:', secondTry);
  }

  console.log('Waiting 10s for download action...');
  await flowPage.waitForTimeout(10000);

  // Take screenshot
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_after_direct_download.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/flow_after_direct_download.png');

  // Check files in footage folder
  const files = fs.readdirSync(downloadTargetDir);
  console.log('Footage dir files:', files);

  // Check user downloads folder
  const downloadsDir = process.env.USERPROFILE + '\\Downloads';
  const recentDownloads = fs.readdirSync(downloadsDir)
    .map(f => ({ name: f, time: fs.statSync(downloadsDir + '\\' + f).mtimeMs }))
    .sort((a, b) => b.time - a.time)
    .slice(0, 5);
  console.log('Recent user downloads:', recentDownloads);

  await client.detach();
  await browser.close();
}

directDownload().catch(console.error);
