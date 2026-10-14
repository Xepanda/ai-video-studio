const { chromium } = require('playwright-core');
const fs = require('fs');

async function confirmUpload() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  console.log('Clicking "我同意" button...');
  const agreeBtn = flowPage.locator('button:has-text("我同意")').first();
  if (await agreeBtn.isVisible()) {
    await agreeBtn.click();
    console.log('Clicked "我同意"!');
  } else {
    console.log('"我同意" button not visible.');
  }

  // Wait 8s for image processing/upload
  console.log('Waiting for image upload to process...');
  await flowPage.waitForTimeout(8000);

  // Take screenshot
  const client = await flowPage.context().newCDPSession(flowPage);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_after_agree.png', Buffer.from(data, 'base64'));
  console.log('Saved screenshot to D:/Projects/ai-video-studio/out/flow_after_agree.png');
  await client.detach();

  await browser.close();
  console.log('Done confirm upload.');
}

confirmUpload().catch(console.error);
