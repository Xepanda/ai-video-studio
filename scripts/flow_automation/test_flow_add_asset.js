const { chromium } = require('playwright-core');
const fs = require('fs');

async function testAddAsset() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  
  console.log('Clicking 在提示框中添加素材 button...');
  const addBtn = flowPage.locator('button[aria-label="在提示框中添加素材"]').first();
  await addBtn.click();
  await flowPage.waitForTimeout(1000);

  // Check what menus or dialogs appeared
  const menuItems = await flowPage.evaluate(() => {
    const items = Array.from(document.querySelectorAll('[role="menuitem"], [role="option"], .mat-mdc-menu-item, button, input[type="file"]')).map(el => ({
      tag: el.tagName,
      type: el.type,
      text: (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' '),
      ariaLabel: el.getAttribute('aria-label'),
      className: el.className,
      visible: el.getBoundingClientRect().width > 0
    }));
    return items.filter(i => i.visible && (i.text || i.type === 'file'));
  });

  console.log('Visible menu items / inputs after clicking add:');
  console.log(JSON.stringify(menuItems.slice(0, 20), null, 2));

  // Take screenshot of popup menu
  const client = await flowPage.context().newCDPSession(flowPage);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_add_menu.png', Buffer.from(data, 'base64'));
  console.log('Saved screenshot to D:/Projects/ai-video-studio/out/flow_add_menu.png');
  await client.detach();

  await browser.close();
}

testAddAsset().catch(console.error);
