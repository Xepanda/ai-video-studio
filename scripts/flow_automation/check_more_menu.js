const { chromium } = require('playwright-core');
const fs = require('fs');

async function checkMoreMenu() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const flowPage = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));

  console.log('Hovering over video tile...');
  await flowPage.mouse.move(400, 180);
  await flowPage.waitForTimeout(500);

  console.log('Clicking 更多选项 button on the video hotbar...');
  const moreBtn = flowPage.locator('flow-video-hotbar button[aria-label="更多选项"]').first();
  await moreBtn.click();
  await flowPage.waitForTimeout(1000);

  const menuItems = await flowPage.evaluate(() => {
    return Array.from(document.querySelectorAll('.mat-mdc-menu-item, [role="menuitem"], .mat-menu-panel *')).filter(el => {
      const text = (el.innerText || '').trim();
      return text.length > 0 && el.children.length <= 1;
    }).map(el => ({
      tag: el.tagName,
      text: el.innerText.trim(),
      ariaLabel: el.getAttribute('aria-label'),
      className: el.className
    }));
  });

  console.log('Menu items:');
  console.log(JSON.stringify(menuItems, null, 2));

  // Take screenshot of opened menu
  const client = await flowPage.context().newCDPSession(flowPage);
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_video_more_menu.png', Buffer.from(data, 'base64'));
  console.log('Saved screenshot: out/flow_video_more_menu.png');
  await client.detach();

  await browser.close();
}

checkMoreMenu().catch(console.error);
