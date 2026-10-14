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

async function pollCompletion() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  const maxAttempts = 24; // 24 * 10s = 4 minutes
  let completed = false;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`[Attempt ${attempt}/${maxAttempts}] Checking Veo rendering progress...`);

    const status = await flowPage.evaluate(() => {
      const allButtons = Array.from(document.querySelectorAll('button, [role="button"]'));
      const stopBtn = allButtons.find(b => {
        const text = (b.innerText || '').trim();
        const label = (b.getAttribute('aria-label') || '').trim();
        return text.includes('停止') || label.includes('停止') || label.includes('stop');
      });
      const isGenerating = !!stopBtn;

      // Look for all video elements
      const videos = Array.from(document.querySelectorAll('video')).map(v => ({
        src: v.src || v.currentSrc,
        duration: v.duration,
        w: v.videoWidth,
        h: v.videoHeight,
        paused: v.paused
      }));

      // Look for media tiles on the main canvas
      const tiles = Array.from(document.querySelectorAll('.media-card, .grid-item, .tile, mat-card')).map(c => ({
        text: (c.innerText || '').trim().replace(/\s+/g, ' '),
        className: c.className
      }));

      // Look for download buttons or menu items
      const downloadButtons = Array.from(document.querySelectorAll('button, a')).filter(el => {
        const text = (el.innerText || '').toLowerCase();
        const label = (el.getAttribute('aria-label') || '').toLowerCase();
        return text.includes('下载') || text.includes('download') || label.includes('下载') || label.includes('download');
      }).map(el => ({
        tag: el.tagName,
        text: (el.innerText || '').trim(),
        label: el.getAttribute('aria-label'),
        href: el.getAttribute('href')
      }));

      // Find any newly created conversation responses
      const lastMessages = Array.from(document.querySelectorAll('.chat-message, .conversation-turn, [role="article"]')).slice(-3).map(m => m.innerText.slice(0, 100));

      return {
        isGenerating,
        videos,
        downloadButtons,
        tilesCount: tiles.length,
        lastMessages
      };
    });

    console.log(`[Attempt ${attempt}] isGenerating: ${status.isGenerating}, videos: ${status.videos.length}, downloads: ${status.downloadButtons.length}`);

    // Take screenshot periodically
    if (attempt % 2 === 1 || !status.isGenerating) {
      const client = await flowPage.context().newCDPSession(flowPage);
      const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(`D:/Projects/ai-video-studio/out/flow_render_progress_${attempt}.png`, Buffer.from(data, 'base64'));
      console.log(`Saved screenshot out/flow_render_progress_${attempt}.png`);
      await client.detach();
    }

    // Check if video is found
    if (status.videos.length > 0) {
      const validVideo = status.videos.find(v => v.src && v.src.length > 10);
      if (validVideo) {
        console.log('Video detected!', validVideo);
        if (!validVideo.src.startsWith('blob:')) {
          console.log('Direct video link! Downloading...');
          await downloadFile(validVideo.src, 'D:/Projects/ai-video-studio/public/footage/meta_muse_apple/scene_02.mp4');
          console.log('Successfully saved to public/footage/meta_muse_apple/scene_02.mp4');
          completed = true;
          break;
        }
      }
    }

    if (!status.isGenerating && attempt >= 2) {
      console.log('Veo generation finished (stop button disappeared)!');
      completed = true;
      break;
    }

    await flowPage.waitForTimeout(10000);
  }

  await browser.close();
  console.log('Polling finished. Completed:', completed);
}

pollCompletion().catch(console.error);
