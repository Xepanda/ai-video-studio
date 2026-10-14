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

async function monitorGeneration() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  const maxAttempts = 30; // 30 * 10s = 5 minutes max
  let completed = false;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    console.log(`[Attempt ${attempt}/${maxAttempts}] Checking generation status...`);
    
    // Check if video element exists or stop button disappeared
    const status = await flowPage.evaluate(() => {
      const allButtons = Array.from(document.querySelectorAll('button, [role="button"]'));
      const stopBtn = allButtons.find(b => {
        const text = (b.innerText || '').trim();
        const label = (b.getAttribute('aria-label') || '').trim();
        return text.includes('停止') || label.includes('停止') || label.includes('stop');
      });
      const isGenerating = !!stopBtn;

      // Look for video elements
      const videos = Array.from(document.querySelectorAll('video')).map(v => ({
        src: v.src || v.currentSrc,
        duration: v.duration,
        w: v.videoWidth,
        h: v.videoHeight,
        paused: v.paused
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

      // Look for generated media in DOM (cards, thumbnails, img, video)
      const mediaThumbnails = Array.from(document.querySelectorAll('img, video, canvas')).map(m => ({
        tag: m.tagName,
        src: (m.src || m.currentSrc || '').slice(0, 100)
      })).filter(m => m.src.length > 0);

      return {
        isGenerating,
        videos,
        downloadButtons,
        mediaCount: mediaThumbnails.length
      };
    });

    console.log(`Status [attempt ${attempt}]: isGenerating=${status.isGenerating}, videos=${status.videos.length}, downloads=${status.downloadButtons.length}, media=${status.mediaCount}`);

    // Capture screenshot every 30s
    if (attempt % 3 === 1 || attempt === maxAttempts) {
      const client = await flowPage.context().newCDPSession(flowPage);
      const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(`D:/Projects/ai-video-studio/out/flow_gen_progress_${attempt}.png`, Buffer.from(data, 'base64'));
      console.log(`Saved screenshot out/flow_gen_progress_${attempt}.png`);
      await client.detach();
    }

    if (status.videos.length > 0 && status.videos.some(v => v.src && v.src.length > 5 && !v.src.startsWith('blob:null'))) {
      console.log('Found video elements!', status.videos);
      const validVideo = status.videos.find(v => v.src && !v.src.startsWith('blob:'));
      if (validVideo) {
        console.log('Direct video URL found:', validVideo.src);
        await downloadFile(validVideo.src, 'D:/Projects/ai-video-studio/public/footage/meta_muse_apple/scene_02.mp4');
        console.log('Saved direct video to public/footage/meta_muse_apple/scene_02.mp4');
        completed = true;
        break;
      } else {
        console.log('Blob video detected. Inspecting video details...');
      }
    }

    if (!status.isGenerating && attempt >= 2) {
      console.log('Generation stop button is gone! Generation likely completed.');
      const client = await flowPage.context().newCDPSession(flowPage);
      const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_gen_finished.png', Buffer.from(data, 'base64'));
      console.log('Saved out/flow_gen_finished.png');
      await client.detach();
      completed = true;
      break;
    }

    await flowPage.waitForTimeout(10000);
  }

  await browser.close();
  console.log('Monitor run completed. Result:', { completed });
}

monitorGeneration().catch(console.error);
