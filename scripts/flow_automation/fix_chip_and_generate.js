const { chromium } = require('playwright-core');
const fs = require('fs');

async function fixChip() {
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages().find(p => p.url().includes('flow.google.com'));
  const client = await page.context().newCDPSession(page);

  // Look for the close button on the chip inside prompt bar
  const chipCloseBtns = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button, mat-icon, .close-btn')).filter(el => {
      const text = (el.innerText || '').trim();
      const label = (el.getAttribute('aria-label') || '').trim();
      const rect = el.getBoundingClientRect();
      return (text === 'close' || label.includes('close') || label.includes('删除') || label.includes('移除')) && rect.y > 600;
    }).map(el => ({
      text: el.innerText,
      ariaLabel: el.getAttribute('aria-label'),
      rect: el.getBoundingClientRect()
    }));
  });

  console.log('Chip close buttons:', chipCloseBtns);

  if (chipCloseBtns.length > 0) {
    console.log('Clicking chip close button to remove wrong media chip...');
    await page.mouse.click(chipCloseBtns[0].rect.x + chipCloseBtns[0].rect.width / 2, chipCloseBtns[0].rect.y + chipCloseBtns[0].rect.height / 2);
    await page.waitForTimeout(1000);
  }

  // Now, click the top tile on the canvas (scene_01.jpg)!
  // Or open add media menu and select scene_01.jpg!
  console.log('Clicking "+" button in prompt bar to attach scene_01.jpg...');
  const addBtn = page.locator('button.add-menu-trigger, button[aria-label="在提示框中添加素材"]').first();
  await addBtn.click();
  await page.waitForTimeout(1500);

  // In the add menu, find the item for "scene_01.jpg" and click it!
  const clickedScene01 = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('.mat-mdc-list-item, .resource-item, [role="listitem"], .item-container, div, span'));
    const scene1Item = items.find(i => (i.innerText || '').includes('scene_01.jpg') && i.children.length < 3);
    if (scene1Item) {
      let clickable = scene1Item;
      while (clickable && clickable.tagName !== 'BUTTON' && !clickable.classList.contains('mat-mdc-list-item') && clickable !== document.body) {
        clickable = clickable.parentElement;
      }
      (clickable || scene1Item).click();
      return true;
    }
    return false;
  });
  console.log('Clicked scene_01 item in list:', clickedScene01);
  await page.waitForTimeout(1500);

  // Click "添加到提示" button
  console.log('Clicking "添加到提示"...');
  await page.evaluate(() => {
    const btn = document.querySelector('button.detail-add-to-prompt-btn') ||
                Array.from(document.querySelectorAll('button')).find(b => (b.innerText || '').includes('添加到提示'));
    if (btn) btn.click();
  });
  await page.waitForTimeout(1500);

  // Capture snapshot
  const { data } = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('D:/Projects/ai-video-studio/out/flow_after_attach_scene01.png', Buffer.from(data, 'base64'));
  console.log('Saved snapshot to out/flow_after_attach_scene01.png');

  await browser.close();
}

fixChip().catch(console.error);
