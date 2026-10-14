const { chromium } = require('playwright-core');
const fs = require('fs');

async function testSubmit() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  // First, check the chips in the container:
  // We want only scene_01.jpg, so let's check what chips are inside
  const chips = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.media-chip, .attachment-chip, flow-media-chip, [role="button"]')).map(el => ({
      text: el.innerText,
      className: el.className,
      rect: el.getBoundingClientRect()
    })).filter(el => el.rect.y > 600 && el.rect.y < 850 && el.rect.x > 650);
  });
  console.log('Chips found:', chips);

  // Find the generate button
  const genBtn = page.locator('button.generate-icon-button, button[aria-label="开始生成"]').first();
  const box = await genBtn.boundingBox();
  console.log('Generate button box:', box);

  if (box) {
    console.log(`Clicking physically at center: ${box.x + box.width / 2}, ${box.y + box.height / 2}`);
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForTimeout(3000);
  }

  const snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/after_submit_click.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/after_submit_click.png');

  // Check what messages or dialogs appeared
  const dialogText = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.mat-mdc-dialog-container, .dialog, .modal, [role="dialog"], .chat-message')).map(el => el.innerText.slice(0, 200));
  });
  console.log('Dialogs/Messages:', dialogText);

  await browser.close();
}

testSubmit().catch(console.error);
