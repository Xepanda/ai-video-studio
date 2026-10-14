const { BrowserOperator } = require('./browser_operator');

(async () => {
  const operator = new BrowserOperator();
  await operator.init(true);
  console.log('[Test] Navigating to Wikipedia...');
  await operator.navigate('https://en.wikipedia.org/wiki/Main_Page');
  console.log('[Test] Typing search query: Artificial Intelligence...');
  await operator.smartType('input[name="search"]', 'Artificial Intelligence');
  console.log('[Test] Taking snapshot of interactive search state...');
  await operator.snapshot('D:/Projects/ai-video-studio/out/wiki_search_test.png');
  await operator.close();
  console.log('✅ 复杂外部网站自主交互测试完全成功！');
})().catch(err => {
  console.error('❌ 测试异常:', err);
  process.exit(1);
});
