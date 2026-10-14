const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const FOOTAGE_DIR = 'D:\\Projects\\ai-video-studio\\public\\footage\\meta_muse_apple';
const DOWNLOADS_DIR = path.join(process.env.USERPROFILE, 'Downloads');

const SCENE_TASKS = [
  {
    id: 'scene_01',
    imageFile: 'scene_01.jpg',
    outputVideo: 'scene_01.mp4',
    prompt: 'Slow gentle cinematic push-in shot, morning golden hour sunlight softly shifting across warm oak wood desk, steam gently curling from coffee ceramic mug, subtle screen reflection of mobile interface on phone screen, soft room tone, quiet ambient morning breeze, 1080p photorealistic cinema lighting, smooth 35mm film motion'
  },
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

async function uploadImage(flowPage, client, imagePath) {
  console.log(`[Upload] Starting upload process for ${path.basename(imagePath)}...`);

  // Check if sidebar upload button is visible
  const isUploadVisible = await flowPage.evaluate(() => {
    const btn = document.querySelector('button.sidebar-upload-btn') || 
                Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('上传媒体内容'));
    return btn && btn.offsetParent !== null;
  });

  if (!isUploadVisible) {
    console.log('[Upload] Add menu not open. Clicking 在提示框中添加素材 button...');
    await flowPage.evaluate(() => {
      const addBtn = document.querySelector('button.add-menu-trigger') ||
                     document.querySelector('button[aria-label="在提示框中添加素材"]');
      if (addBtn) addBtn.click();
    });
    await flowPage.waitForTimeout(1500);
  }

  console.log('[Upload] Intercepting filechooser and clicking 上传媒体内容...');
  const [fileChooser] = await Promise.all([
    flowPage.waitForEvent('filechooser', { timeout: 15000 }),
    flowPage.evaluate(() => {
      const btn = document.querySelector('button.sidebar-upload-btn') || 
                  Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('上传媒体内容'));
      if (btn) btn.click();
    })
  ]);

  console.log(`[Upload] Intercepted filechooser! Setting file: ${imagePath}`);
  await fileChooser.setFiles(imagePath);
  console.log('[Upload] File set sent. Waiting 5s for upload to process...');
  await flowPage.waitForTimeout(5000);
}

async function handleAgreementsAndAttach(flowPage, client) {
  // Check for "我同意" agreement modal
  const hasAgreeModal = await flowPage.evaluate(() => {
    const agreeBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('我同意'));
    if (agreeBtn) {
      agreeBtn.click();
      return true;
    }
    return false;
  });

  if (hasAgreeModal) {
    console.log('[Modal] Clicked "我同意" button on agreement dialog.');
    await flowPage.waitForTimeout(3000);
  }

  // Wait for "添加到提示" button to be ready
  console.log('[Process] Waiting for "添加到提示" button...');
  for (let cycle = 0; cycle < 10; cycle++) {
    const attached = await flowPage.evaluate(() => {
      const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                  Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
      if (btn && !btn.disabled) {
        btn.click();
        return true;
      }
      return false;
    });

    if (attached) {
      console.log('[Process] Clicked "添加到提示" successfully!');
      await flowPage.waitForTimeout(2000);
      return true;
    }
    await flowPage.waitForTimeout(2000);
  }

  console.log('[Warning] "添加到提示" button was not clicked within timeout.');
  return false;
}

async function injectPromptAndGenerate(flowPage, client, promptText) {
  console.log('[Prompt] Locating ProseMirror editor...');
  const promptEditor = flowPage.locator('.ProseMirror[contenteditable="true"]').first();
  await promptEditor.click();
  await flowPage.waitForTimeout(600);

  console.log(`[Prompt] Typing prompt: "${promptText.slice(0, 50)}..."`);
  await promptEditor.fill(promptText);
  await flowPage.waitForTimeout(1000);

  // Capture snapshot before generating
  await captureSnapshot(client, 'prompt_injected_ready');

  // Click start generation button
  console.log('[Generate] Clicking 开始生成 button...');
  const clickedGen = await flowPage.evaluate(() => {
    const genBtn = document.querySelector('button.generate-icon-button') ||
                   document.querySelector('button[aria-label="开始生成"]');
    if (genBtn && !genBtn.disabled) {
      genBtn.click();
      return true;
    }
    return false;
  });

  if (!clickedGen) {
    console.log('[Generate] Using locator fallback for 开始生成...');
    const genBtn = flowPage.locator('button.generate-icon-button, button[aria-label="开始生成"]').first();
    await genBtn.click();
  }

  console.log('[Generate] Clicked generate button. Waiting 3s for credit modal...');
  await flowPage.waitForTimeout(3500);

  // Check for credit approval modal (一律批准 / 批准)
  const approved = await flowPage.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, [role="button"], span'));
    const approveBtn = buttons.find(b => {
      const text = (b.innerText || '').trim();
      return text.includes('一律批准') || text === '批准';
    });
    if (approveBtn) {
      let clickable = approveBtn;
      while (clickable && clickable.tagName !== 'BUTTON' && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      (clickable || approveBtn).click();
      return true;
    }
    return false;
  });

  if (approved) {
    console.log('[Approve] Credit modal approved (15 credits deducted)!');
    await flowPage.waitForTimeout(3000);
  } else {
    console.log('[Approve] No credit modal appeared (may have auto-approved).');
  }
}

async function waitForVeoRender(flowPage, client, sceneId) {
  console.log(`[Render] Polling Veo 3.1 rendering progress for ${sceneId}...`);
  const maxWaitCycles = 35; // 35 * 8s = 280s (~4.5 min)

  for (let cycle = 1; cycle <= maxWaitCycles; cycle++) {
    await flowPage.waitForTimeout(8000);

    const state = await flowPage.evaluate(() => {
      const allButtons = Array.from(document.querySelectorAll('button, [role="button"]'));
      const stopBtn = allButtons.find(b => {
        const text = (b.innerText || '').trim();
        const label = (b.getAttribute('aria-label') || '').trim();
        return text.includes('停止') || label.includes('停止') || label.toLowerCase().includes('stop');
      });
      const isGenerating = !!stopBtn;

      const videos = Array.from(document.querySelectorAll('video')).map(v => ({
        src: v.src || v.currentSrc,
        duration: v.duration
      }));

      return {
        isGenerating,
        videosCount: videos.length
      };
    });

    console.log(`[Render Cycle ${cycle}/${maxWaitCycles}] isGenerating: ${state.isGenerating}, videosOnPage: ${state.videosCount}`);

    if (cycle % 3 === 0) {
      await captureSnapshot(client, `render_progress_${sceneId}_c${cycle}`);
    }

    if (!state.isGenerating && cycle >= 2) {
      console.log(`[Render Complete] Veo generation finished for ${sceneId}!`);
      await flowPage.waitForTimeout(4000);
      await captureSnapshot(client, `render_done_${sceneId}`);
      return true;
    }
  }
  return false;
}

async function downloadGeneratedVideo(flowPage, client, outputPath) {
  console.log(`[Download] Starting download to ${outputPath}...`);
  const targetDir = path.dirname(outputPath);
  const targetFileName = path.basename(outputPath);

  await client.send('Page.setDownloadBehavior', {
    behavior: 'allow',
    downloadPath: targetDir
  });

  const beforeTime = Date.now() - 5000;

  // Hover over the video hotbar to reveal more options
  await flowPage.mouse.move(300, 100);
  await flowPage.waitForTimeout(600);

  console.log('[Download] Clicking 更多选项 button on hotbar...');
  const clickedMore = await flowPage.evaluate(() => {
    const more = document.querySelector('flow-video-hotbar button[aria-label="更多选项"]');
    if (more) {
      more.click();
      return true;
    }
    return false;
  });

  if (!clickedMore) {
    console.log('[Download] Hotbar more button not found directly, trying generic more-options button...');
    await flowPage.locator('button[aria-label="更多选项"]').first().click().catch(() => {});
  }

  await flowPage.waitForTimeout(800);

  // Hover over "下载"
  console.log('[Download] Hovering over 下载 menu item...');
  await flowPage.evaluate(() => {
    const allItems = Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button'));
    const dl = allItems.find(i => (i.innerText || '').includes('下载'));
    if (dl) {
      dl.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      dl.dispatchEvent(new MouseEvent('mouseover', { bubbles: true }));
    }
  });
  await flowPage.waitForTimeout(800);

  // Click 720p or 1080p
  console.log('[Download] Clicking resolution menu item...');
  const clickedRes = await flowPage.evaluate(() => {
    const elements = Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text === '720p' || text === '1080p') && el.children.length === 0;
    });
    if (elements.length > 0) {
      let clickable = elements[0];
      while (clickable && clickable.tagName !== 'BUTTON' && !clickable.getAttribute('role')?.includes('menuitem') && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      (clickable || elements[0]).click();
      return true;
    }
    return false;
  });

  console.log(`[Download] Click resolution result: ${clickedRes}`);
  console.log('[Download] Waiting 15s for download stream to complete...');
  await flowPage.waitForTimeout(15000);

  // Find the newly downloaded MP4 file
  const findDownloadedFile = () => {
    // Check targetDir
    if (fs.existsSync(targetDir)) {
      const files = fs.readdirSync(targetDir)
        .filter(f => f.endsWith('.mp4') && f !== targetFileName)
        .map(f => ({ path: path.join(targetDir, f), mtime: fs.statSync(path.join(targetDir, f)).mtimeMs }))
        .filter(f => f.mtime >= beforeTime)
        .sort((a, b) => b.mtime - a.mtime);
      if (files.length > 0) return files[0].path;
    }
    // Check Downloads dir
    if (fs.existsSync(DOWNLOADS_DIR)) {
      const dlFiles = fs.readdirSync(DOWNLOADS_DIR)
        .filter(f => f.endsWith('.mp4'))
        .map(f => ({ path: path.join(DOWNLOADS_DIR, f), mtime: fs.statSync(path.join(DOWNLOADS_DIR, f)).mtimeMs }))
        .filter(f => f.mtime >= beforeTime)
        .sort((a, b) => b.mtime - a.mtime);
      if (dlFiles.length > 0) return dlFiles[0].path;
    }
    return null;
  };

  const foundFile = findDownloadedFile();
  if (foundFile) {
    console.log(`[Download Success] Found downloaded file: ${foundFile}`);
    fs.copyFileSync(foundFile, outputPath);
    const sizeMb = (fs.statSync(outputPath).size / 1024 / 1024).toFixed(2);
    console.log(`[Download Success] Saved to target: ${outputPath} (${sizeMb} MB)`);
    return true;
  } else {
    console.log('[Download Warning] Could not detect downloaded file automatically.');
    return false;
  }
}

async function main() {
  console.log('====================================================');
  console.log('Google Flow (Veo 3.1) Batch Video Generation Pipeline');
  console.log('====================================================');

  console.log('Connecting to Chrome CDP on http://localhost:9222...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  if (!flowPage) {
    throw new Error('Could not find Google Flow tab in Chrome! Please open flow.google.com.');
  }

  console.log(`Connected to Google Flow page: ${await flowPage.title()} (${flowPage.url()})`);
  const client = await flowPage.context().newCDPSession(flowPage);

  // Check specific task filter via CLI argument, e.g. --scene=scene_01
  const argScene = process.argv.find(a => a.startsWith('--scene='))?.split('=')[1];
  const tasksToRun = argScene 
    ? SCENE_TASKS.filter(t => t.id === argScene)
    : SCENE_TASKS;

  console.log(`Total tasks to execute: ${tasksToRun.length}`);

  for (let i = 0; i < tasksToRun.length; i++) {
    const task = tasksToRun[i];
    console.log(`\n----------------------------------------------------`);
    console.log(`[Task ${i + 1}/${tasksToRun.length}] Processing ${task.id}...`);
    console.log(`----------------------------------------------------`);

    const imagePath = path.join(FOOTAGE_DIR, task.imageFile);
    const outputPath = path.join(FOOTAGE_DIR, task.outputVideo);

    if (fs.existsSync(outputPath) && !process.argv.includes('--force')) {
      console.log(`[Skip] Video already exists: ${outputPath}`);
      continue;
    }

    // Step 1: Upload Image
    await uploadImage(flowPage, client, imagePath);

    // Step 2: Confirm agreement and attach
    const attached = await handleAgreementsAndAttach(flowPage, client);
    if (!attached) {
      console.log('[Warning] Attach might have had issues, proceeding with caution...');
    }

    // Step 3: Inject prompt & click generate
    await injectPromptAndGenerate(flowPage, client, task.prompt);

    // Step 4: Wait for Veo render
    const rendered = await waitForVeoRender(flowPage, client, task.id);
    if (!rendered) {
      console.log(`[Error] Render timed out for ${task.id}`);
      continue;
    }

    // Step 5: Download video
    await downloadGeneratedVideo(flowPage, client, outputPath);

    console.log(`[Task Complete] Finished processing ${task.id}!`);
    await flowPage.waitForTimeout(4000);
  }

  await client.detach();
  await browser.close();
  console.log('\n====================================================');
  console.log('All Flow batch video generation tasks completed!');
  console.log('====================================================');
}

main().catch(err => {
  console.error('[Fatal Error]', err);
  process.exit(1);
});
