const { chromium } = require('playwright-core');
const fs = require('fs');

async function trackTile() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Get info about canvas tiles
  const tileInfo = await flowPage.evaluate(() => {
    // Look for all elements that might contain percentage or progress
    const allTextNodes = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return /\d+%\s*$/.test(text) || text.includes('%');
    }).map(el => ({
      tag: el.tagName,
      text: el.innerText.trim(),
      className: el.className
    }));

    // Check video tags
    const videos = Array.from(document.querySelectorAll('video')).map(v => ({
      src: v.src || v.currentSrc,
      duration: v.duration,
      w: v.videoWidth,
      h: v.videoHeight
    }));

    // Check all cards on canvas
    const cards = Array.from(document.querySelectorAll('.canvas-item, .media-item, .card, [class*="tile"], [class*="card"]')).map(c => ({
      tag: c.tagName,
      className: c.className,
      text: (c.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 50)
    }));

    return { allTextNodes: allTextNodes.slice(0, 10), videos, cards: cards.slice(0, 10) };
  });

  console.log('Tile inspection:', JSON.stringify(tileInfo, null, 2));

  // Take screenshot
  const client = await flowPage.context().newCDPSession(flowPage);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_tile_status.png', Buffer.from(data, 'base64'));
  console.log('Saved screenshot: out/flow_tile_status.png');
  await client.detach();

  await browser.close();
}

trackTile().catch(console.error);
