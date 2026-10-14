const { chromium } = require('playwright-core');
const fs = require('fs');

async function pollGen() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  for (let cycle = 1; cycle <= 30; cycle++) {
    await page.waitForTimeout(10000);

    const state = await page.evaluate(() => {
      const allText = document.body.innerText;
      const stopBtn = Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('停止'));
      const isGenerating = !!stopBtn;

      // Check if there is an approval button like "批准" or "一律批准"
      const approveBtn = Array.from(document.querySelectorAll('button')).find(b => 
        (b.innerText || '').includes('批准') || (b.innerText || '').includes('一律批准')
      );

      // Check for any progress percentage
      const percentMatches = allText.match(/\b\d{1,3}%\b/g);

      // Check total videos in DOM
      const videoElements = document.querySelectorAll('video').length;

      return {
        isGenerating,
        hasApproveBtn: !!approveBtn,
        approveBtnText: approveBtn?.innerText,
        percentMatches,
        videoElements
      };
    });

    console.log(`[Cycle ${cycle}/30] Generating: ${state.isGenerating}, Approve: ${state.hasApproveBtn} (${state.approveBtnText}), Percents: ${state.percentMatches}`);

    // If an approval button appears, click it automatically!
    if (state.hasApproveBtn) {
      console.log('Approve button appeared! Clicking it...');
      await page.evaluate(() => {
        const approveBtn = Array.from(document.querySelectorAll('button')).find(b => 
          (b.innerText || '').includes('一律批准') || (b.innerText || '').includes('批准')
        );
        if (approveBtn) approveBtn.click();
      });
      await page.waitForTimeout(2000);
    }

    if (cycle % 3 === 0 || !state.isGenerating) {
      const snap = await client.send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(`D:/Projects/ai-video-studio/out/poll_cycle_${cycle}.png`, Buffer.from(snap.data, 'base64'));
      console.log(`Saved screenshot out/poll_cycle_${cycle}.png`);
    }

    if (!state.isGenerating && cycle >= 2 && !state.hasApproveBtn) {
      console.log('Generation completed (stop button disappeared)!');
      break;
    }
  }

  await client.detach();
  await browser.close();
}

pollGen().catch(console.error);
