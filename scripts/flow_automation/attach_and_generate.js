const { chromium } = require('playwright-core');
const fs = require('fs');

async function attachAndGenerate() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  // Wait a few seconds for media processing to finish
  console.log('Waiting 6s for media upload and processing...');
  await flowPage.waitForTimeout(6000);

  // Take snapshot of current state
  const client = await flowPage.context().newCDPSession(flowPage);
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_ready_to_attach.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/flow_ready_to_attach.png');

  // Check the state of "添加到提示" button
  const addToPromptBtn = flowPage.locator('button:has-text("添加到提示")').first();
  const isAddVisible = await addToPromptBtn.isVisible();
  console.log('Is "添加到提示" button visible?', isAddVisible);

  if (isAddVisible) {
    // If enabled or clickable, click it
    console.log('Clicking "添加到提示"...');
    await addToPromptBtn.click({ timeout: 5000 }).catch(e => console.log('Click error:', e.message));
    await flowPage.waitForTimeout(2000);
  }

  // Now locate the prompt input (ProseMirror contenteditable div)
  console.log('Locating prompt input box...');
  const promptEditor = flowPage.locator('.ProseMirror[contenteditable="true"]').first();
  await promptEditor.click();
  await flowPage.waitForTimeout(500);

  const motionPrompt = 'Gentle slow panning shot across modern sunlit studio desk, human fingers delicately typing code on aluminum keyboard, terminal text scrolling naturally in background, soft morning sunlight shifting across oak wood, 1080p photorealistic motion, smooth 35mm cinema movement, zero CGI glow';
  
  console.log('Typing motion prompt...');
  // Type the prompt into ProseMirror
  await promptEditor.fill(motionPrompt);
  await flowPage.waitForTimeout(1000);

  // Check state before clicking generate
  snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_prompt_filled.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/flow_prompt_filled.png');

  // Check generate button
  const generateBtn = flowPage.locator('button[aria-label="开始生成"], button.generate-icon-button').first();
  const isGenEnabled = await generateBtn.isEnabled();
  console.log('Is generate button enabled?', isGenEnabled);

  if (isGenEnabled) {
    console.log('Clicking 开始生成 button...');
    await generateBtn.click();
    console.log('Generation triggered!');
    await flowPage.waitForTimeout(4000);
    snap = await client.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_generating.png', Buffer.from(snap.data, 'base64'));
    console.log('Saved screenshot: out/flow_generating.png');
  } else {
    console.log('Generate button not yet enabled, let us inspect details:');
    const details = await flowPage.evaluate(() => {
      const pm = document.querySelector('.ProseMirror');
      const gen = document.querySelector('button[aria-label="开始生成"]');
      return {
        promptText: pm ? pm.innerText : null,
        genClasses: gen ? gen.className : null,
        genDisabled: gen ? gen.hasAttribute('disabled') : null
      };
    });
    console.log('Details:', details);
  }

  await client.detach();
  await browser.close();
  console.log('Attach and generate test complete.');
}

attachAndGenerate().catch(console.error);
