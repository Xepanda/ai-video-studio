const { chromium } = require('playwright-core');
const fs = require('fs');

async function testAddClick() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  
  console.log('Clicking 在提示框中添加素材...');
  const addBtn = page.locator('button[aria-label="在提示框中添加素材"]').first();
  await addBtn.click();
  await page.waitForTimeout(1000);
  
  const client = await page.context().newCDPSession(page);
  const snap = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_add_menu.png', Buffer.from(snap.data, 'base64'));
  console.log('Saved screenshot: out/flow_add_menu.png');
  
  const menuItems = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], button')).map(el => ({
      text: (el.innerText || '').trim().replace(/\s+/g, ' '),
      ariaLabel: el.getAttribute('aria-label')
    })).filter(i => i.text || i.ariaLabel);
  });
  console.log('Menu items:', JSON.stringify(menuItems, null, 2));
  await browser.close();
}
testAddClick().catch(console.error);
