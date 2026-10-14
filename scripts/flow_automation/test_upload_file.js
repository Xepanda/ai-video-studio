const { chromium } = require('playwright-core');
const fs = require('fs');

async function testUpload() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  
  const targetImage = 'D:/Projects/ai-video-studio/public/footage/meta_muse_apple/scene_02.jpg';
  console.log('Target image:', targetImage);

  // Check if fileChooser event is fired on clicking '上传媒体内容'
  console.log('Waiting for filechooser event and clicking 上传媒体内容...');
  
  const uploadBtn = flowPage.locator('button:has-text("上传媒体内容")').first();
  
  const [fileChooser] = await Promise.all([
    flowPage.waitForEvent('filechooser', { timeout: 10000 }),
    uploadBtn.click()
  ]);

  console.log('FileChooser intercepted! Setting files...');
  await fileChooser.setFiles(targetImage);

  console.log('Files set! Waiting 5s to observe upload progress...');
  await flowPage.waitForTimeout(5000);

  // Take screenshot
  const client = await flowPage.context().newCDPSession(flowPage);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_after_upload.png', Buffer.from(data, 'base64'));
  console.log('Saved screenshot to D:/Projects/ai-video-studio/out/flow_after_upload.png');
  await client.detach();

  await browser.close();
  console.log('Done test upload!');
}

testUpload().catch(console.error);
