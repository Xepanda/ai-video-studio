const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function monitorAndDownload() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  console.log('Monitoring rendering state...');
  for (let i = 1; i <= 25; i++) {
    await page.waitForTimeout(10000);

    const snap = await client.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(`D:/Projects/ai-video-studio/out/monitor_progress_${i}.png`, Buffer.from(snap.data, 'base64'));

    const state = await page.evaluate(() => {
      const stopBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('停止'));
      const text = document.body.innerText;
      const percents = text.match(/\b\d{1,3}%\b/g);
      const isAnalyzing = text.includes('Analyzing');
      return {
        hasStop: !!stopBtn,
        percents,
        isAnalyzing
      };
    });

    console.log(`[Cycle ${i}/25] Stop: ${state.hasStop}, Percents: ${state.percents}, Analyzing: ${state.isAnalyzing}`);

    // If no percentages and no stop button, rendering is likely finished!
    if (!state.hasStop && !state.percents && !state.isAnalyzing && i >= 3) {
      console.log('Rendering finished!');
      break;
    }
  }

  await client.detach();
  await browser.close();
}

monitorAndDownload().catch(console.error);
