const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function screenshotSlides(inputPath, outputDir) {
  const data = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const results = [];
  for (const slide of data.slides) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 2 });
    await page.setContent(slide.html_content, { waitUntil: 'networkidle0' });

    const outputPath = path.join(outputDir, `slide_${slide.page_number}.png`);
    await page.screenshot({ path: outputPath, fullPage: false });
    results.push({ page_number: slide.page_number, path: outputPath });
    await page.close();
  }

  await browser.close();
  console.log(JSON.stringify(results));
}

const args = process.argv.slice(2);
if (args.length < 2) {
  console.error('Usage: node screenshot.js <input.json> <output_dir>');
  process.exit(1);
}
screenshotSlides(args[0], args[1]).catch(e => { console.error(e); process.exit(1); });
