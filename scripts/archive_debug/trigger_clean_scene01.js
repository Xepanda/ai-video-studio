const { chromium } = require('playwright-core');
const fs = require('fs');

async function triggerScene01() {
  console.log('Connecting to Chrome CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  // Step 1: Click "发起新的会话" (edit_square) to get a clean canvas and prompt bar
  console.log('Starting fresh session (发起新的会话)...');
  await page.evaluate(() => {
    const newChatBtn = document.querySelector('button[aria-label="发起新的会话"]');
    if (newChatBtn) newChatBtn.click();
  });
  await page.waitForTimeout(2000);

  // Step 2: Open add media menu
  console.log('Opening add media menu...');
  await page.evaluate(() => {
    const addBtn = document.querySelector('button.add-menu-trigger') ||
                   document.querySelector('button[aria-label="在提示框中添加素材"]');
    if (addBtn) addBtn.click();
  });
  await page.waitForTimeout(1500);

  // Step 3: Select scene_01.jpg from list
  console.log('Selecting scene_01.jpg...');
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('*')).filter(el => 
      (el.innerText || '').trim() === 'scene_01.jpg' || 
      (el.innerText || '').includes('scene_01.jpg')
    );
    const item = items[items.length - 1];
    if (item) {
      let clickable = item;
      while (clickable && clickable.tagName !== 'BUTTON' && !clickable.classList.contains('mat-mdc-list-item') && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      (clickable || item).click();
    }
  });
  await page.waitForTimeout(1200);

  // Step 4: Click "添加到提示"
  console.log('Clicking "添加到提示"...');
  await page.evaluate(() => {
    const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
    if (btn) btn.click();
  });
  await page.waitForTimeout(1500);

  // Step 5: Fill ProseMirror prompt
  const scene01Prompt = 'Slow gentle cinematic push-in shot, morning golden hour sunlight softly shifting across warm oak wood desk, steam gently curling from coffee ceramic mug, subtle screen reflection of mobile interface on phone screen, soft room tone, quiet ambient morning breeze, 1080p photorealistic cinema lighting, smooth 35mm film motion';
  console.log('Typing prompt into ProseMirror...');
  const editor = page.locator('.ProseMirror[contenteditable="true"]').first();
  await editor.click();
  await page.waitForTimeout(400);
  await editor.fill(scene01Prompt);
  await page.waitForTimeout(1000);

  // Capture snapshot before clicking generate
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/scene01_ready_to_gen.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/scene01_ready_to_gen.png');

  // Step 6: Click "开始生成" (generate-icon-button)
  console.log('Clicking 开始生成 button...');
  await page.evaluate(() => {
    const genBtn = document.querySelector('button.generate-icon-button') ||
                   document.querySelector('button[aria-label="开始生成"]');
    if (genBtn) genBtn.click();
  });
  await page.waitForTimeout(4000);

  // Step 7: Check for "一律批准" / "批准" credit dialog
  console.log('Checking for credit approval dialog...');
  const approved = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('button, span, .mdc-button')).filter(el => {
      const text = (el.innerText || '').trim();
      return text === '一律批准' || text.includes('一律批准') || text === '批准';
    });
    if (all.length > 0) {
      let target = all[all.length - 1]; // pick the most recent dialog button
      while (target && target.tagName !== 'BUTTON' && target !== document.body) {
        target = target.parentElement;
      }
      (target || all[0]).click();
      return true;
    }
    return false;
  });

  console.log('Credit dialog clicked result:', approved);
  await page.waitForTimeout(4000);

  // Snapshot after generation started
  snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/scene01_generating.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/scene01_generating.png');

  await client.detach();
  await browser.close();
  console.log('Scene 01 triggered successfully!');
}

triggerScene01().catch(console.error);
