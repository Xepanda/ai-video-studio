const { chromium } = require('playwright-core');

async function checkPromptBar() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  
  const promptDetails = await flowPage.evaluate(() => {
    const inputs = Array.from(document.querySelectorAll('textarea, input, [contenteditable="true"]')).map(el => ({
      tag: el.tagName,
      placeholder: el.placeholder || el.getAttribute('placeholder'),
      ariaLabel: el.getAttribute('aria-label'),
      className: el.className,
      rect: { x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y, w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height }
    }));
    
    const fileInputs = Array.from(document.querySelectorAll('input[type="file"]')).map(el => ({
      name: el.name,
      id: el.id,
      accept: el.accept,
      className: el.className
    }));

    const addButtons = Array.from(document.querySelectorAll('button')).filter(el => {
      const label = el.getAttribute('aria-label') || '';
      const text = el.innerText || '';
      return label.includes('添加素材') || text.includes('add') || label.includes('添加');
    }).map(el => ({
      text: el.innerText,
      ariaLabel: el.getAttribute('aria-label'),
      rect: { x: el.getBoundingClientRect().x, y: el.getBoundingClientRect().y, w: el.getBoundingClientRect().width, h: el.getBoundingClientRect().height }
    }));

    return { inputs, fileInputs, addButtons };
  });

  console.log(JSON.stringify(promptDetails, null, 2));
  await browser.close();
}

checkPromptBar().catch(console.error);
