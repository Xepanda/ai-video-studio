const { chromium } = require('playwright-core');
const fs = require('fs');

async function inspectEditor() {
  console.log('Connecting to Chrome CDP on http://localhost:9222...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  
  const pages = browser.contexts()[0].pages();
  const flowPage = pages.find(p => p.url().includes('flow.google.com'));
  
  if (!flowPage) {
    console.error('No Google Flow page found! Available URLs:', pages.map(p => p.url()));
    await browser.close();
    process.exit(1);
  }
  
  console.log(`Found Flow page: ${flowPage.url()} - Title: "${await flowPage.title()}"`);
  
  // Bring to front
  await flowPage.bringToFront();
  await flowPage.waitForTimeout(1000);
  
  // Inspect interactive elements first
  console.log('Inspecting DOM elements...');
  const elementsInfo = await flowPage.evaluate(() => {
    function getDetails(el) {
      const rect = el.getBoundingClientRect();
      return {
        tag: el.tagName.toLowerCase(),
        text: (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 80),
        placeholder: el.getAttribute('placeholder') || '',
        ariaLabel: el.getAttribute('aria-label') || '',
        type: el.getAttribute('type') || '',
        role: el.getAttribute('role') || '',
        id: el.id || '',
        className: (el.className || '').toString().slice(0, 50),
        visible: rect.width > 0 && rect.height > 0,
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        w: Math.round(rect.width),
        h: Math.round(rect.height)
      };
    }

    const allInputs = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"]')).map(getDetails);
    const allButtons = Array.from(document.querySelectorAll('button, [role="button"], a[role="button"]')).map(getDetails);
    const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map(getDetails);

    // Also look for potential dropzones or prompt areas
    const cards = Array.from(document.querySelectorAll('[data-testid], [aria-label]')).map(getDetails);

    return {
      allInputs,
      allButtons: allButtons.filter(b => b.visible && (b.text.length > 0 || b.ariaLabel.length > 0)),
      fileInputs,
      annotated: cards.filter(c => c.visible && (c.ariaLabel || c.text)).slice(0, 20)
    };
  });

  console.log('\n=== FILE INPUTS ===');
  console.log(JSON.stringify(elementsInfo.fileInputs, null, 2));

  console.log('\n=== INPUTS & TEXTAREAS ===');
  console.log(JSON.stringify(elementsInfo.allInputs, null, 2));

  console.log('\n=== VISIBLE BUTTONS ===');
  console.log(JSON.stringify(elementsInfo.allButtons, null, 2));

  console.log('\n=== ANNOTATED CARDS / TEST IDS ===');
  console.log(JSON.stringify(elementsInfo.annotated, null, 2));

  // Try fast screenshot with CDP directly to avoid hanging
  try {
    console.log('Capturing screenshot via CDP session...');
    const client = await flowPage.context().newCDPSession(flowPage);
    const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_editor_ready.png', Buffer.from(data, 'base64'));
    console.log('Successfully saved screenshot via CDP to D:/Projects/ai-video-studio/out/flow_editor_ready.png');
    await client.detach();
  } catch (ssErr) {
    console.warn('Screenshot via CDP warning:', ssErr.message);
  }

  await browser.close();
  console.log('\nInspection complete.');
  process.exit(0);
}

inspectEditor().catch(err => {
  console.error('Inspection failed:', err);
  process.exit(1);
});
