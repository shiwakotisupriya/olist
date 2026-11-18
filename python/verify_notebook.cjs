// Inspect the generated notebook HTML in an isolated headless browser.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const root = path.resolve(__dirname, '..');
  fs.mkdirSync(path.join(root, 'tmp'), {recursive:true});
  const browser = await chromium.launch({channel:'msedge',headless:true});
  const page = await browser.newPage({viewport:{width:1400,height:1000},deviceScaleFactor:1});
  await page.goto('file:///' + path.join(root,'docs/notebook_preview.html').replaceAll('\\','/'));
  await page.screenshot({path:path.join(root,'tmp/notebook_top.png')});
  const cells=page.locator('.jp-MarkdownCell');
  const results=page.getByText('Chronological evaluation',{exact:false}).first();
  await results.scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(root,'tmp/notebook_results.png')});
  const figure=page.locator('.jp-OutputArea-output img').first();
  await figure.scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(root,'tmp/notebook_chart.png')});
  console.log(JSON.stringify({markdownCells:await cells.count(),figures:await page.locator('.jp-OutputArea-output img').count(),title:await page.title()}));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
