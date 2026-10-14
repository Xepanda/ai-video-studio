const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function runScene06() {
  console.log('======================================================');
  console.log('Generating Scene 06 (Dawn Skyline / Contemplative Developer)');
  console.log('======================================================');

  const imagePath = path.join(FOOTAGE_DIR, 'scene_06.jpg');
  const targetPath = path.join(FOOTAGE_DIR, 'scene_06.mp4');
  const prompt = 'Atmospheric 35mm cinematic slow push-in shot from behind a young tech developer standing beside floor-to-ceiling loft window, golden sunrise light washing across room, silhouette overlooking vast futuristic morning city skyline, warm dawn ambient acoustic, peaceful room reverberation, high-end cinema lens flare, zero CGI artifacts';

  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  // Step 1: Clean session
  console.log('[Step 1] Starting fresh session...');
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="发起新的会话"]');
    if (btn) btn.click();
  });
  await page.waitForTimeout(2000);

  // Step 2: Open Add Media Menu
  console.log('[Step 2] Opening add media menu...');
  await page.evaluate(() => {
    const addBtn = document.querySelector('button.add-menu-trigger') ||
                   document.querySelector('button[aria-label="在提示框中添加素材"]');
    if (addBtn) addBtn.click();
  });
  await page.waitForTimeout(1500);

  // Step 3: Upload scene_06.jpg via FileChooser
  console.log('[Step 3] Uploading scene_06.jpg...');
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 15000 }),
    page.evaluate(() => {
      const btn = document.querySelector('button.sidebar-upload-btn') || 
                  Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('上传媒体内容'));
      if (btn) btn.click();
    })
  ]);
  await fileChooser.setFiles(imagePath);
  console.log('[Step 3] File uploaded, waiting 6s for processing...');
  await page.waitForTimeout(6000);

  // Agreement modal if prompted
  await page.evaluate(() => {
    const agreeBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('我同意'));
    if (agreeBtn) agreeBtn.click();
  });
  await page.waitForTimeout(2000);

  // Step 4: Click "添加到提示"
  console.log('[Step 4] Clicking "添加到提示"...');
  await page.evaluate(() => {
    const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
    if (btn) btn.click();
  });
  await page.waitForTimeout(1500);

  // Step 5: Fill prompt
  console.log('[Step 5] Typing prompt into ProseMirror...');
  const editor = page.locator('.ProseMirror[contenteditable="true"]').first();
  await editor.click();
  await page.waitForTimeout(300);
  await editor.fill(prompt);
  await page.waitForTimeout(1000);

  // Step 6: Submit prompt
  console.log('[Step 6] Submitting prompt...');
  const genBtn = page.locator('button.generate-icon-button, button[aria-label="开始生成"]').first();
  const box = await genBtn.boundingBox();
  if (box) {
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  } else {
    await page.evaluate(() => {
      const b = document.querySelector('button.generate-icon-button') || document.querySelector('button[aria-label="开始生成"]');
      if (b) b.click();
    });
  }
  await page.waitForTimeout(3500);

  // Step 7: Credit approval
  console.log('[Step 7] Checking credit approval...');
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('button, span, .mdc-button')).filter(el => {
      const text = (el.innerText || '').trim();
      return text === '一律批准' || text.includes('一律批准') || text === '批准';
    });
    if (all.length > 0) {
      let cur = all[all.length - 1];
      while (cur && cur.tagName !== 'BUTTON' && cur !== document.body) cur = cur.parentElement;
      (cur || all[all.length - 1]).click();
    }
  });

  // Step 8: Polling rendering progress until complete (up to 150 seconds)
  console.log('[Step 8] Waiting for cloud Veo 3.1 render to complete...');
  let isDone = false;
  for (let cycle = 1; cycle <= 20; cycle++) {
    await page.waitForTimeout(7000);
    const status = await page.evaluate(() => {
      const topBtn = Array.from(document.querySelectorAll('button')).find(b => 
        b.getAttribute('aria-label') === '更多选项' && 
        b.getBoundingClientRect().y < 160 && 
        b.getBoundingClientRect().x < 650
      );
      const hasPercent = Array.from(document.querySelectorAll('*')).some(el => {
        const t = (el.innerText || '').trim();
        return /^\d{1,2}%$/.test(t) && el.children.length === 0;
      });
      return { hasTopBtn: Boolean(topBtn), hasPercent };
    });
    console.log(`[Cycle ${cycle}/20] Elapsed ${cycle * 7}s | Has top 3-dots: ${status.hasTopBtn} | Has percentage: ${status.hasPercent}`);
    if (status.hasTopBtn && !status.hasPercent && cycle >= 4) {
      console.log('Veo 3.1 cloud render confirmed complete!');
      isDone = true;
      break;
    }
  }

  // Check state with snapshot
  let snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/scene06_after_wait.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/scene06_after_wait.png');

  // Step 9: Download newly rendered top tile
  console.log('[Step 9] Downloading top tile (Scene 06)...');
  const beforeTime = Date.now() - 5000;

  // Hover top tile
  await page.mouse.move(400, 200);
  await page.waitForTimeout(800);

  // Click 3-dots on top tile
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => 
      b.getAttribute('aria-label') === '更多选项' && 
      b.getBoundingClientRect().y < 160 && 
      b.getBoundingClientRect().x < 650
    );
    if (btn) btn.click();
  });
  await page.waitForTimeout(1000);

  // Hover "下载"
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
    const dl = all.find(el => (el.innerText || '').includes('下载'));
    if (dl) {
      let cur = dl;
      while (cur && !cur.classList.contains('mat-mdc-menu-item') && cur !== document.body) cur = cur.parentElement;
      (cur || dl).dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      (cur || dl).dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await page.waitForTimeout(800);

  // Click resolution (720p or 1080p)
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
    });
    if (all.length > 0) {
      let cur = all[0];
      while (cur && cur.tagName !== 'BUTTON' && !cur.getAttribute('role')?.includes('menuitem') && cur !== document.body) cur = cur.parentElement;
      (cur || all[0]).click();
    }
  });

  console.log('Waiting 15s for download to complete...');
  await page.waitForTimeout(15000);

  const checkFiles = () => {
    const footageFiles = fs.readdirSync(FOOTAGE_DIR)
      .map(f => ({ name: f, path: path.join(FOOTAGE_DIR, f), time: fs.statSync(path.join(FOOTAGE_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4'));
    const dlFiles = fs.existsSync(DOWNLOADS_DIR) ? fs.readdirSync(DOWNLOADS_DIR)
      .map(f => ({ name: f, path: path.join(DOWNLOADS_DIR, f), time: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4')) : [];
    return [...footageFiles, ...dlFiles].sort((a, b) => b.time - a.time);
  };

  const dl = checkFiles();
  console.log('Downloaded files for Scene 06:', dl);
  if (dl.length > 0) {
    fs.copyFileSync(dl[0].path, targetPath);
    console.log(`Saved scene_06.mp4 successfully! Size: ${(fs.statSync(targetPath).size / 1024 / 1024).toFixed(2)} MB`);
  }

  await client.detach();
  await browser.close();
  console.log('Scene 06 process complete!');
}

runScene06().catch(console.error);
