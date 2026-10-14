const { chromium } = require('playwright-core');

async function inspectApprove() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  const items = await flowPage.evaluate(() => {
    return Array.from(document.querySelectorAll('*')).filter(el => {
      const text = (el.innerText || '').trim();
      return (text.includes('批准') || text.includes('Approve')) && el.children.length === 0;
    }).map(el => ({
      tag: el.tagName,
      parentTag: el.parentElement ? el.parentElement.tagName : null,
      parentParentTag: el.parentElement && el.parentElement.parentElement ? el.parentElement.parentElement.tagName : null,
      text: el.innerText,
      className: el.className,
      rect: el.getBoundingClientRect()
    }));
  });

  console.log('Approve candidates:', JSON.stringify(items, null, 2));
  await browser.close();
}

inspectApprove().catch(console.error);
