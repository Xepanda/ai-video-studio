const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

async function generateScene(sceneId, imageFileName, promptText) {
  console.log(`\n======================================================`);
  console.log(`[Google Flow Veo 3.1] Generating: ${sceneId}`);
  console.log(`Reference Image: ${imageFileName}`);
  console.log(`Prompt: "${promptText.slice(0, 70)}..."`);
  console.log(`======================================================`);

  const imagePath = path.join(FOOTAGE_DIR, imageFileName);
  const targetVideoPath = path.join(FOOTAGE_DIR, `${sceneId}.mp4`);

  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  if (!page) throw new Error('Flow page not found in Chrome!');

  const client = await page.context().newCDPSession(page);
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  // Step 1: Start a clean conversation session
  console.log('[Step 1] Clicking "发起新的会话"...');
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

  // Step 3: Check if image is already in media list or needs upload
  console.log(`[Step 3] Checking if ${imageFileName} exists in media list...`);
  let selected = await page.evaluate((targetName) => {
    const items = Array.from(document.querySelectorAll('*')).filter(el => 
      (el.innerText || '').trim() === targetName || 
      (el.innerText || '').includes(targetName)
    );
    if (items.length > 0) {
      const item = items[items.length - 1];
      let clickable = item;
      while (clickable && clickable.tagName !== 'BUTTON' && !clickable.classList.contains('mat-mdc-list-item') && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      (clickable || item).click();
      return true;
    }
    return false;
  }, imageFileName);

  if (!selected) {
    console.log(`[Step 3] ${imageFileName} not in list. Uploading via FileChooser...`);
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

    // Click "我同意" if modal appears
    await page.evaluate(() => {
      const agreeBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('我同意'));
      if (agreeBtn) agreeBtn.click();
    });
    await page.waitForTimeout(2000);

    // Now select the uploaded file
    await page.evaluate((targetName) => {
      const items = Array.from(document.querySelectorAll('*')).filter(el => 
        (el.innerText || '').trim() === targetName || 
        (el.innerText || '').includes(targetName)
      );
      if (items.length > 0) {
        let cur = items[items.length - 1];
        while (cur && cur.tagName !== 'BUTTON' && !cur.classList.contains('mat-mdc-list-item') && cur !== document.body) cur = cur.parentElement;
        (cur || items[items.length - 1]).click();
      }
    }, imageFileName);
    await page.waitForTimeout(1500);
  }

  // Step 4: Click "添加到提示"
  console.log('[Step 4] Clicking "添加到提示"...');
  await page.evaluate(() => {
    const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
    if (btn) btn.click();
  });
  await page.waitForTimeout(1500);

  // Step 5: Fill prompt in ProseMirror
  console.log('[Step 5] Typing prompt...');
  const editor = page.locator('.ProseMirror[contenteditable="true"]').first();
  await editor.click();
  await page.waitForTimeout(300);
  await editor.fill(promptText);
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
  await page.waitForTimeout(3000);

  // Step 7: Credit approval if prompted
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

  // Step 8: Wait for rendering to start (watch for "停止" button or analyzing state)
  console.log('[Step 8] Waiting for Veo cloud generation to start...');
  let hasStarted = false;
  for (let s = 0; s < 10; s++) {
    await page.waitForTimeout(3000);
    const status = await page.evaluate(() => {
      const stop = !!Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('停止'));
      const text = document.body.innerText;
      return stop || text.includes('Analyzing') || text.includes('scheduled');
    });
    if (status) {
      hasStarted = true;
      console.log('[Step 8] Veo generation started successfully!');
      break;
    }
  }

  // Step 9: Poll until generation finishes
  console.log('[Step 9] Polling Veo cloud generation (this typically takes 60-120 seconds)...');
  const maxCycles = 30; // 30 * 8s = 240s (4 min)
  for (let cycle = 1; cycle <= maxCycles; cycle++) {
    await page.waitForTimeout(8000);

    const isDone = await page.evaluate(() => {
      const stop = !!Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('停止'));
      const text = document.body.innerText;
      const analyzing = text.includes('Analyzing');
      const percents = text.match(/\b\d{1,3}%\b/g);
      return !stop && !analyzing && !percents;
    });

    console.log(`[Poll Cycle ${cycle}/${maxCycles}] Is rendering complete? ${isDone}`);

    if (isDone && cycle >= 2) {
      console.log('[Step 9] Veo generation finished!');
      break;
    }
  }

  await page.waitForTimeout(3000);

  // Step 10: Download the newly generated video (Top Tile)
  console.log('[Step 10] Downloading top tile video...');
  const beforeTime = Date.now() - 3000;

  // Hover top tile
  await page.mouse.move(400, 200);
  await page.waitForTimeout(600);

  // Click 3-dots on top tile
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => 
      b.getAttribute('aria-label') === '更多选项' && 
      b.getBoundingClientRect().y < 150 && 
      b.getBoundingClientRect().x < 650
    );
    if (btn) btn.click();
  });
  await page.waitForTimeout(800);

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

  console.log('[Step 10] Waiting 15s for download to complete...');
  await page.waitForTimeout(15000);

  // Check downloads
  const checkFiles = () => {
    const footageFiles = fs.readdirSync(FOOTAGE_DIR)
      .map(f => ({ name: f, path: path.join(FOOTAGE_DIR, f), time: fs.statSync(path.join(FOOTAGE_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4'));
    const dlFiles = fs.existsSync(DOWNLOADS_DIR) ? fs.readdirSync(DOWNLOADS_DIR)
      .map(f => ({ name: f, path: path.join(DOWNLOADS_DIR, f), time: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
      .filter(f => f.time >= beforeTime && f.name.endsWith('.mp4')) : [];
    return [...footageFiles, ...dlFiles].sort((a, b) => b.time - a.time);
  };

  const recent = checkFiles();
  if (recent.length > 0) {
    fs.copyFileSync(recent[0].path, targetVideoPath);
    const sizeMb = (fs.statSync(targetVideoPath).size / 1024 / 1024).toFixed(2);
    console.log(`[Success] Successfully saved ${targetVideoPath} (${sizeMb} MB)!`);
  } else {
    console.log(`[Warning] No new download detected for ${sceneId}`);
  }

  await client.detach();
  await browser.close();
  console.log(`[Task Complete] ${sceneId} finished!\n`);
}

const targetScene = process.argv[2] || 'scene_03';

const PROMPTS = {
  scene_03: {
    file: 'scene_03.jpg',
    prompt: 'Macro slow cinematic lateral tracking shot across CNC anodized aluminum chassis, laser-etched microchip glistening under cool white studio rim lighting, delicate copper heatpipes, high-tech server lab ambient drone, faint electrical hum and ventilation airflow, 1080p crisp macro focus, photorealistic depth of field'
  },
  scene_05: {
    file: 'scene_05.jpg',
    prompt: 'Cinematic slow pull-out camera movement inside moody corporate executive boardroom, dusk city skyscrapers gleaming through tall glass windows, glowing laptop screen casting subtle reflections on polished obsidian glass table, quiet corporate ambient room tone, distant muffled city rumble, 1080p cinematic documentary atmosphere'
  },
  scene_06: {
    file: 'scene_06.jpg',
    prompt: 'Atmospheric 35mm cinematic slow push-in shot from behind a young tech developer standing beside floor-to-ceiling loft window, golden sunrise light washing across room, silhouette overlooking vast futuristic morning city skyline, warm dawn ambient acoustic, peaceful room reverberation, high-end cinema lens flare, zero CGI artifacts'
  }
};

const task = PROMPTS[targetScene];
if (!task) {
  console.error(`Unknown scene: ${targetScene}`);
  process.exit(1);
}

generateScene(targetScene, task.file, task.prompt).catch(err => {
  console.error('[Error]', err);
  process.exit(1);
});
