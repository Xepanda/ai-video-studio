const { chromium } = require('playwright-core');

async function inspectVideoTile() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Hover over the video tile first so hover overlays become visible
  console.log('Hovering over video tile (x: 400, y: 180)...');
  await flowPage.mouse.move(400, 180);
  await flowPage.waitForTimeout(1000);

  const tileButtons = await flowPage.evaluate(() => {
    const videoTile = document.querySelector('flow-video-tile') || document.querySelector('.container');
    const buttons = Array.from(document.querySelectorAll('flow-video-hotbar button, .footer-overlay-has-progress-bar button, .footer-overlay-has-progress-bar [role="button"], flow-video-tile button')).map(b => ({
      tag: b.tagName,
      text: (b.innerText || '').trim(),
      ariaLabel: b.getAttribute('aria-label'),
      title: b.getAttribute('title'),
      className: b.className
    }));

    return { buttons };
  });

  console.log('Video tile hover buttons:');
  console.log(JSON.stringify(tileButtons, null, 2));

  await browser.close();
}

inspectVideoTile().catch(console.error);
