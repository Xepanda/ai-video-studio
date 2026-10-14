const { chromium } = require('playwright-core');
const fs = require('fs');

async function listMedia() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  const items = await page.evaluate(() => {
    // Look for all video cards / tiles / hotbars
    const hotbars = Array.from(document.querySelectorAll('flow-video-hotbar, flow-media-tile, .media-card, mat-card')).map(el => {
      const text = (el.innerText || '').trim();
      const rect = el.getBoundingClientRect();
      return { text, rect };
    });

    const allTexts = Array.from(document.querySelectorAll('.video-title, .title, .media-title, span, p')).filter(el => {
      const t = el.innerText || '';
      return t.includes('chassis') || t.includes('aluminum') || t.includes('button') || t.includes('Steam') || t.includes('Fingers') || t.includes('typing');
    }).map(el => ({ text: el.innerText.trim(), rect: el.getBoundingClientRect() }));

    return { hotbars, allTexts };
  });

  console.log('Items found:', JSON.stringify(items, null, 2));
  await browser.close();
}

listMedia().catch(console.error);
