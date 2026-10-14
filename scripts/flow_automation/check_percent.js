const { chromium } = require('playwright-core');
const fs = require('fs');

async function checkPercent() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  const text = await page.evaluate(() => {
    return document.body.innerText;
  });

  const percentMatches = text.match(/\b\d{1,3}%\b/g);
  console.log('Current percent matches on page:', percentMatches);

  const snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/current_render_progress.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot to out/current_render_progress.png');

  await browser.close();
}

checkPercent().catch(console.error);
