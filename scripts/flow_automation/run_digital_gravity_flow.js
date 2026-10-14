const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\digital_gravity';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

const SCENES_CONFIG = [
  {
    index: 1,
    name: 'Scene 01 (Morning Workspace / Awakening Screen)',
    image: 'scene_01.jpg',
    target: 'scene_01.mp4',
    prompt: 'Atmospheric cinematic slow push-in shot of minimalist tech workspace desk in morning golden light, gentle warm steam slowly rising from ceramic coffee mug, hand gently tapping MacBook trackpad, glowing laptop screen, peaceful morning studio acoustic, quiet room tone, 1080p documentary atmosphere'
  },
  {
    index: 2,
    name: 'Scene 02 (Fiber Optic Server Rack / Digital Gravity)',
    image: 'scene_02.jpg',
    target: 'scene_02.mp4',
    prompt: 'Macro cinematic slow pan across high-tech data center server rack, glowing cyan and amber fiber optic cables pulsing with moving light data streams, server cooling fans low hum, deep datacenter white noise ambient acoustic, crisp industrial glass reflections, zero CGI artifacts'
  },
  {
    index: 3,
    name: 'Scene 03 (Dual Monitor Night Coding / Autonomous Agent)',
    image: 'scene_03.jpg',
    target: 'scene_03.mp4',
    prompt: 'Moody cinematic camera movement inside dark developer office at night, dual monitor screens displaying streaming terminal code lines, developer fingers typing on mechanical keyboard, crisp tactile switch clicking acoustic, quiet room reverberation, high-end cinema lens flare'
  },
  {
    index: 4,
    name: 'Scene 04 (Precision Microchip Soldering / Verifiable Code)',
    image: 'scene_04.jpg',
    target: 'scene_04.mp4',
    prompt: 'Macro cinematic slow push-in shot of precision soldering iron touching microchip on dark motherboard, tiny delicate wisp of solder smoke rising upward, glowing copper traces and brushed aluminum heatsink reflections, subtle electrical sizzle acoustic, ultra sharp macro focus'
  },
  {
    index: 5,
    name: 'Scene 05 (Executive Boardroom / Critical Privacy Defense)',
    image: 'scene_05.jpg',
    target: 'scene_05.mp4',
    prompt: 'Cinematic slow pull-out camera movement inside executive corporate boardroom at twilight dusk, floor-to-ceiling glass windows overlooking glowing city skyscrapers, dark polished conference table reflecting digital screens with complex network security graphs, quiet corporate ambient room tone, distant muffled city rumble'
  },
  {
    index: 6,
    name: 'Scene 06 (Dawn Loft Skyline / Deep Dive Call to Action)',
    image: 'scene_06.jpg',
    target: 'scene_06.mp4',
    prompt: 'Atmospheric 35mm cinematic slow push-in shot from behind a young tech developer standing beside floor-to-ceiling loft window, golden sunrise light washing across room with beautiful lens flare, silhouette overlooking vast futuristic morning city skyline, warm dawn ambient acoustic, peaceful room reverberation'
  }
];

async function generateSingleScene(sceneConf) {
  console.log('\n======================================================');
  console.log(`Generating ${sceneConf.name}`);
  console.log('======================================================');

  const imagePath = path.join(FOOTAGE_DIR, sceneConf.image);
  const targetPath = path.join(FOOTAGE_DIR, sceneConf.target);

  if (!fs.existsSync(imagePath)) {
    throw new Error(`Base image not found: ${imagePath}`);
  }

  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  if (!page) {
    throw new Error('Google Flow page not found in Chrome on port 9222');
  }

  const client = await page.context().newCDPSession(page);
  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: FOOTAGE_DIR
  });

  // 1. Fresh session
  console.log('[Step 1] Starting fresh session...');
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label="发起新的会话"]');
    if (btn) btn.click();
  });
  await page.waitForTimeout(2500);

  // 2. Open Add Media Menu
  console.log('[Step 2] Opening add media menu...');
  await page.evaluate(() => {
    const addBtn = document.querySelector('button.add-menu-trigger') ||
                   document.querySelector('button[aria-label="在提示框中添加素材"]');
    if (addBtn) addBtn.click();
  });
  await page.waitForTimeout(1500);

  // 3. Upload file
  console.log(`[Step 3] Uploading ${sceneConf.image}...`);
  const [fileChooser] = await Promise.all([
    page.waitForEvent('filechooser', { timeout: 15000 }),
    page.evaluate(() => {
      const btn = document.querySelector('button.sidebar-upload-btn') || 
                  Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('上传媒体内容'));
      if (btn) btn.click();
    })
  ]);
  await fileChooser.setFiles(imagePath);
  console.log('[Step 3] Upload complete, waiting 6s for processing...');
  await page.waitForTimeout(6000);

  // Agreement modal
  await page.evaluate(() => {
    const agreeBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('我同意'));
    if (agreeBtn) agreeBtn.click();
  });
  await page.waitForTimeout(2000);

  // 4. Click "添加到提示"
  console.log('[Step 4] Clicking "添加到提示"...');
  await page.evaluate(() => {
    const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
    if (btn) btn.click();
  });
  await page.waitForTimeout(1500);

  // 5. Fill prompt
  console.log('[Step 5] Typing prompt into ProseMirror...');
  const editor = page.locator('.ProseMirror[contenteditable="true"]').first();
  await editor.click();
  await page.waitForTimeout(300);
  await editor.fill(sceneConf.prompt);
  await page.waitForTimeout(1000);

  // 6. Submit prompt
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

  // 7. Credit approval
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

  // 8. Dynamic wait for cloud Veo 3.1 render (up to 150s)
  console.log('[Step 8] Waiting for cloud Veo 3.1 render to complete...');
  let isDone = false;
  for (let cycle = 1; cycle <= 22; cycle++) {
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
    console.log(`[Cycle ${cycle}/22] Elapsed ${cycle * 7}s | Has top 3-dots: ${status.hasTopBtn} | Has percentage: ${status.hasPercent}`);
    if (status.hasTopBtn && !status.hasPercent && cycle >= 5) {
      console.log('Veo 3.1 cloud render confirmed complete!');
      isDone = true;
      break;
    }
  }

  // 9. Download newly rendered top tile
  console.log('[Step 9] Downloading top tile...');
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
  await page.waitForTimeout(1000);

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

  console.log('Waiting 16s for download to complete...');
  await page.waitForTimeout(16000);

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
  console.log(`Downloaded candidate files for ${sceneConf.name}:`, dl);
  if (dl.length > 0) {
    fs.copyFileSync(dl[0].path, targetPath);
    console.log(`Saved ${sceneConf.target} successfully! Size: ${(fs.statSync(targetPath).size / 1024 / 1024).toFixed(2)} MB`);
  } else {
    console.warn(`⚠️ Warning: No new download detected for ${sceneConf.name}`);
  }

  await client.detach();
  await browser.close();
  console.log(`[Complete] ${sceneConf.name} finished!`);
}

async function main() {
  const args = process.argv.slice(2);
  let targetScene = null;
  const sceneIdx = args.indexOf('--scene');
  if (sceneIdx !== -1 && args[sceneIdx + 1]) {
    targetScene = parseInt(args[sceneIdx + 1], 10);
  }

  if (targetScene) {
    const conf = SCENES_CONFIG.find(s => s.index === targetScene);
    if (!conf) {
      console.error(`Invalid scene index: ${targetScene}. Available: 1..6`);
      process.exit(1);
    }
    await generateSingleScene(conf);
  } else if (args.includes('--all')) {
    console.log('Starting batch generation for all 6 scenes...');
    for (const conf of SCENES_CONFIG) {
      await generateSingleScene(conf);
      console.log('Cooling down 5s before next scene...');
      await new Promise(r => setTimeout(r, 5000));
    }
    console.log('ALL 6 SCENES GENERATED SUCCESSFULLY!');
  } else {
    console.log('Usage: node scripts/run_digital_gravity_flow.js [--scene 1..6 | --all]');
  }
}

main().catch(err => {
  console.error('Execution failed:', err);
  process.exit(1);
});
