const { chromium } = require('playwright-core');

async function inspectCards() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  const cardDetails = await flowPage.evaluate(() => {
    // Find all items on the canvas
    const tiles = Array.from(document.querySelectorAll('.virtual-item-container > * , .tiles-container *')).filter(el => {
      const rect = el.getBoundingClientRect();
      return rect.width > 150 && rect.height > 100;
    }).map(el => ({
      tag: el.tagName,
      className: el.className,
      rect: { x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y, w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height },
      html: el.outerHTML.slice(0, 300)
    }));

    return tiles;
  });

  console.log('Detected canvas tiles:');
  console.log(JSON.stringify(cardDetails, null, 2));

  await browser.close();
}

inspectCards().catch(console.error);
