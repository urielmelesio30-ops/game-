const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [from, to, pr, outDir] = [+process.argv[2], +process.argv[3], process.argv[4] || '1', process.argv[5] || 'frames'];
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  page.on('console', m => console.log('console:', m.text()));
  page.on('pageerror', e => console.log('pageerror:', e.message));
  await page.goto(`http://localhost:8765/scene.html?pr=${pr}`);
  await page.waitForFunction('window.ready === true', null, { timeout: 120000 });
  fs.writeFileSync('timeline.json', JSON.stringify(await page.evaluate('window.timeline'), null, 1));
  for (let f = from; f < to; f++) {
    const t0 = Date.now();
    const url = await page.evaluate(i => window.renderAt(i), f);
    fs.writeFileSync(`${outDir}/f${String(f).padStart(4, '0')}.png`, Buffer.from(url.split(',')[1], 'base64'));
    if (f === from) console.log('frame ms', Date.now() - t0);
  }
  await browser.close();
})();
