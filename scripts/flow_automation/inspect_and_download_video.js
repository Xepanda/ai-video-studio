const { chromium } = require('playwright-core');
const fs = require('fs');
const https = require('https');
const http = require('http');

async function downloadFile(url, destPath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(destPath);
    const client = url.startsWith('https') ? https : http;
    client.get(url, (response) => {
      if (response.statusCode >= 300 && response.statusCode < 400 && response.headers.location) {
        return downloadFile(response.headers.location, destPath).then(resolve).catch(reject);
      }
      response.pipe(file);
      file.on('finish', () => {
        file.close(resolve);
      });
    }).on('error', (err) => {
      fs.unlink(destPath, () => {});
      reject(err);
    });
  });
}

async function inspectAndDownload() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Listen to network requests for any mp4 or video media
  flowPage.on('response', async (response) => {
    const url = response.url();
    const contentType = response.headers()['content-type'] || '';
    if (contentType.includes('video') || url.includes('.mp4') || (url.includes('googleusercontent.com') && url.includes('video'))) {
      console.log('Detected video network response:', url, contentType);
    }
  });

  // Hover or click the video tile (first tile with play_circle or mat-icon play_circle)
  console.log('Locating video tile on canvas...');
  const tile = flowPage.locator('.tile-row, .virtual-item-container, [class*="tile"]').first();
  await tile.hover();
  await flowPage.waitForTimeout(1000);

  // Take screenshot of hover state
  const client = await flowPage.context().newCDPSession(flowPage);
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_tile_hover.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved hover screenshot: out/flow_tile_hover.png');

  // Click on the tile to open preview / player modal
  console.log('Clicking the video tile...');
  await tile.click();
  await flowPage.waitForTimeout(2000);

  snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_video_opened.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved opened screenshot: out/flow_video_opened.png');

  // Inspect DOM for video element, download button, or direct src
  const modalInfo = await flowPage.evaluate(() => {
    const videos = Array.from(document.querySelectorAll('video')).map(v => ({
      src: v.src || v.currentSrc,
      duration: v.duration,
      w: v.videoWidth,
      h: v.videoHeight
    }));

    const buttons = Array.from(document.querySelectorAll('button, a, [role="button"]')).map(b => ({
      tag: b.tagName,
      text: (b.innerText || '').trim(),
      ariaLabel: b.getAttribute('aria-label'),
      href: b.getAttribute('href'),
      visible: b.getBoundingClientRect().width > 0
    })).filter(b => b.visible && (b.text || b.ariaLabel));

    return { videos, buttons };
  });

  console.log('Modal Info:');
  console.log('Videos:', JSON.stringify(modalInfo.videos, null, 2));
  console.log('Action Buttons:', JSON.stringify(modalInfo.buttons.filter(b => {
    const s = ((b.text || '') + ' ' + (b.ariaLabel || '')).toLowerCase();
    return s.includes('下载') || s.includes('download') || s.includes('export') || s.includes('导出') || s.includes('more') || s.includes('更多');
  }), null, 2));

  // If video src found and is HTTP/HTTPS
  if (modalInfo.videos.length > 0 && modalInfo.videos[0].src && modalInfo.videos[0].src.startsWith('http')) {
    const videoUrl = modalInfo.videos[0].src;
    console.log('Found video URL:', videoUrl);
    const dest = 'D:/Projects/ai-video-studio/public/footage/meta_muse_apple/scene_02.mp4';
    await downloadFile(videoUrl, dest);
    console.log('Successfully saved to:', dest);
  }

  await client.detach();
  await browser.close();
  console.log('Done.');
}

inspectAndDownload().catch(console.error);
