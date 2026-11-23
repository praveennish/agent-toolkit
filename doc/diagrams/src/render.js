// Renders the SVG sources in this folder to PNG files in the parent folder.
//   node render.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  for (const name of ['architecture', 'component', 'sequence', 'code-map-kubernetes', 'code-map-docker']) {
    const svgPath = path.join(__dirname, `${name}.svg`);
    const svg = fs.readFileSync(svgPath, 'utf8');
    const w = parseInt(svg.match(/width="(\d+)"/)[1], 10);
    const h = parseInt(svg.match(/height="(\d+)"/)[1], 10);
    const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 2 });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.locator('svg').first().screenshot({ path: path.join(__dirname, '..', `${name}.png`) });
    await page.close();
    console.log(`rendered ${name}.png (${w}x${h} @2x)`);
  }
  await browser.close();
})();
