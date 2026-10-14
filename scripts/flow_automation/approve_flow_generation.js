const { chromium } = require('playwright-core');
const fs = require('fs');

async function approveGeneration() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  console.log('Clicking "一律批准"...');
  const target = flowPage.locator('text=一律批准').first();
  await target.click();
  console.log('Clicked "一律批准"!');

  console.log('Waiting 6s to observe generation starting...');
  await flowPage.waitForTimeout(6000);

  // Take screenshot
  const client = await flowPage.context().newCDPSession(flowPage);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_after_approved.png', Buffer.from(data, 'base64'));
  console.log('Saved screenshot to out/flow_after_approved.png');
  await client.detach();

  await browser.close();
  console.log('Done.');
}

approveGeneration().catch(console.error);
