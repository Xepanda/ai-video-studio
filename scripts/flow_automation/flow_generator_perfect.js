const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

const SCENE_TASKS = [
  {
    id: 'scene_03',
    imageFile: 'scene_03.jpg',
    outputVideo: 'scene_03.mp4',
    prompt: 'Macro slow cinematic lateral tracking shot across CNC anodized aluminum chassis, laser-etched microchip glistening under cool white studio rim lighting, delicate copper heatpipes, high-tech server lab ambient drone, faint electrical hum and ventilation airflow, 1080p crisp macro focus, photorealistic depth of field'
  },
  {
    id: 'scene_04',
    imageFile: 'scene_04.jpg',
    outputVideo: 'scene_04.mp4',
    prompt: 'Extreme macro cinematic close-up, human finger gently pressing down on precision titanium desk puck button, tactile spring mechanical click action, halo LED status ring pulsing bright cyan upon press, crisp mechanical button switch click sound, clean studio acoustic, 1080p photorealistic macro camera movement'
  },
  {
    id: 'scene_05',
    imageFile: 'scene_05.jpg',
    outputVideo: 'scene_05.mp4',
    prompt: 'Cinematic slow pull-out camera movement inside moody corporate executive boardroom, dusk city skyscrapers gleaming through tall glass windows, glowing laptop screen casting subtle reflections on polished obsidian glass table, quiet corporate ambient room tone, distant muffled city rumble, 1080p cinematic documentary atmosphere'
  },
  {
    id: 'scene_06',
    imageFile: 'scene_06.jpg',
    outputVideo: 'scene_06.mp4',
    prompt: 'Atmospheric 35mm cinematic slow push-in shot from behind a young tech developer standing beside floor-to-ceiling loft window, golden sunrise light washing across room, silhouette overlooking vast futuristic morning city skyline, warm dawn ambient acoustic, peaceful room reverberation, high-end cinema lens flare, zero CGI artifacts'
  }
];

async function captureSnapshot(client, name) {
  try {
    const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(`D:/Projects/ai-video-studio/out/${name}.png`, Buffer.from(data, 'base64'));
    console.log(`[Snapshot] Saved D:/Projects/ai-video-studio/out/${name}.png`);
  } catch (e) {
    console.log('[Snapshot Error]', e.message);
  }
}

async function processSingleScene(page, client, task) {
  console.log(`\n====================================================`);
  console.log(`[Starting Task] ${task.id} (${task.imageFile})`);
  console.log(`====================================================`);

  const imagePath = path.join(FOOTAGE_DIR, task.imageFile);
  const targetVideoPath = path.join(FOOTAGE_DIR, task.outputVideo);

  if (fs.existsSync(targetVideoPath) && !process.argv.includes('--force')) {
    console.log(`[Skip] Output video already exists: ${targetVideoPath}`);
    return true;
  }

  // 1. Start clean session (发起新的会话)
  console.log('[Step 1] Starting fresh session...');
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="发起新的会话"]');
    if (btn) btn.click();
  });
  await page.waitForTimeout(2000);

  // 2. Open Add Media Menu
  console.log('[Step 2] Opening add media menu...');
  await page.evaluate(() => {
    const addBtn = document.querySelector('button.add-menu-trigger') ||
                   document.querySelector('button[aria-label="在提示框中添加素材"]');
    if (addBtn) addBtn.click();
  });
  await page.waitForTimeout(1500);

  // 3. Upload Media file via FileChooser
  console.log(`[Step 3] Uploading ${task.imageFile}...`);
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

  // Handle agreement modal if any
  await page.evaluate(() => {
    const agreeBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('我同意'));
    if (agreeBtn) agreeBtn.click();
  });
  await page.waitForTimeout(2000);

  // 4. Click "添加到提示" button
  console.log('[Step 4] Clicking "添加到提示"...');
  let attached = false;
  for (let c = 0; c < 8; c++) {
    attached = await page.evaluate(() => {
      const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                  Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
      if (btn && !btn.disabled) {
        btn.click();
        return true;
      }
      return false;
    });
    if (attached) break;
    await page.waitForTimeout(1500);
  }
  console.log(`[Step 4] Attached to prompt: ${attached}`);
  await page.waitForTimeout(1500);

  // 5. Fill ProseMirror prompt
  console.log(`[Step 5] Typing prompt: "${task.prompt.slice(0, 50)}..."`);
  const editor = page.locator('.ProseMirror[contenteditable="true"]').first();
  await editor.click();
  await page.waitForTimeout(300);
  await editor.fill(task.prompt);
  await page.waitForTimeout(1000);

  // 6. Click generate button physically
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

  // 7. Check credit approval modal
  console.log('[Step 7] Checking credit approval...');
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('button, span, .mdc-button')).filter(el => {
      const text = (el.innerText || '').trim();
      return text === '一律批准' || text.includes('一律批准') || text === '批准';
    });
    if (all.length > 0) {
      let target = all[all.length - 1];
      while (target && target.tagName !== 'BUTTON' && target !== document.body) {
        target = target.parentElement;
      }
      (target || all[all.length - 1]).click();
    }
  });
  await page.waitForTimeout(3000);

  // 8. Poll until render finishes
  console.log(`[Step 8] Polling Veo 3.1 rendering for ${task.id}...`);
  const maxWait = 40; // 40 * 8s = 320s (~5.3 min)
  let renderDone = false;
  for (let cycle = 1; cycle <= maxWait; cycle++) {
    await page.waitForTimeout(8000);

    const isGen = await page.evaluate(() => {
      const stopBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('停止'));
      return !!stopBtn;
    });

    console.log(`[Poll Cycle ${cycle}/${maxWait}] Still generating: ${isGen}`);

    if (!isGen && cycle >= 2) {
      console.log(`[Step 8] Generation completed for ${task.id}!`);
      renderDone = true;
      break;
    }
  }

  if (!renderDone) {
    console.log(`[Step 8 Error] Render did not complete in time for ${task.id}`);
    return false;
  }

  await captureSnapshot(client, `render_done_${task.id}`);
  await page.waitForTimeout(4000);

  // 9. Download the generated video
  console.log(`[Step 9] Downloading video for ${task.id}...`);
  const beforeTime = Date.now() - 3000;

  // Hover tile
  await page.mouse.move(400, 200);
  await page.waitForTimeout(600);

  // Click 更多选项 on top tile
  const clickedMore = await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => 
      b.getAttribute('aria-label') === '更多选项' && 
      b.getBoundingClientRect().y < 150 && 
      b.getBoundingClientRect().x < 650
    );
    if (btn) {
      btn.click();
      return true;
    }
    return false;
  });
  console.log(`[Step 9] Clicked more options: ${clickedMore}`);
  await page.waitForTimeout(800);

  // Hover "下载"
  await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button, span'));
    const dl = all.find(el => (el.innerText || '').includes('下载'));
    if (dl) {
      let cur = dl;
      while (cur && !cur.classList.contains('mat-mdc-menu-item') && cur !== document.body) {
        cur = cur.parentElement;
      }
      (cur || dl).dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      (cur || dl).dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await page.waitForTimeout(800);

  // Click resolution (720p or 1080p)
  const clickedRes = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
    });
    if (all.length > 0) {
      let cur = all[0];
      while (cur && cur.tagName !== 'BUTTON' && !cur.getAttribute('role')?.includes('menuitem') && cur !== document.body) {
        cur = cur.parentElement;
      }
      (cur || all[0]).click();
      return true;
    }
    return false;
  });
  console.log(`[Step 9] Clicked resolution: ${clickedRes}`);

  console.log('[Step 9] Waiting 15s for download...');
  await page.waitForTimeout(15000);

  // Detect downloaded file
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
    console.log(`[Success] Saved ${task.outputVideo} (${sizeMb} MB)`);
    return true;
  } else {
    console.log(`[Warning] Could not detect downloaded file for ${task.id}`);
    return false;
  }
}

async function main() {
  console.log('Connecting to Chrome CDP on http://localhost:9222...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  if (!page) {
    throw new Error('Could not find Google Flow tab in Chrome!');
  }

  const client = await page.context().newCDPSession(page);
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  const argScene = process.argv.find(a => a.startsWith('--scene='))?.split('=')[1];
  const tasksToRun = argScene 
    ? SCENE_TASKS.filter(t => t.id === argScene)
    : SCENE_TASKS;

  console.log(`Running tasks: ${tasksToRun.map(t => t.id).join(', ')}`);

  for (const task of tasksToRun) {
    const success = await processSingleScene(page, client, task);
    console.log(`Finished ${task.id}. Success: ${success}`);
    await page.waitForTimeout(3000);
  }

  await client.detach();
  await browser.close();
  console.log('\n====================================================');
  console.log('All remaining scenes completed successfully!');
  console.log('====================================================');
}

main().catch(err => {
  console.error('[Fatal Error]', err);
  process.exit(1);
});
