/**
 * render_pdf.js — generate the slide deck PDF from slides.html using Puppeteer.
 *
 * Usage:
 *   npm install                    # one-time, installs puppeteer
 *   node slides/render_pdf.js      # writes output/food-delivery-domain.pdf
 *
 * If you don't want to install Puppeteer, the HTML is print-ready —
 * just open slides/slides.html in Chrome and File → Print → Save as PDF
 * with these settings:
 *   - Layout: Landscape
 *   - Paper size: A4
 *   - Margins: None
 *   - Background graphics: ON
 */

const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer');

(async () => {
  const slidesPath = path.resolve(__dirname, 'slides.html');
  const outDir = path.resolve(__dirname, '..', 'output');
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });
  const outPath = path.resolve(outDir, 'food-delivery-domain.pdf');

  console.log(`→ launching headless Chromium`);
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  console.log(`→ loading ${slidesPath}`);
  await page.goto('file://' + slidesPath, { waitUntil: 'networkidle0' });

  // Hide the screen-only nav before printing
  await page.addStyleTag({ content: '.nav { display: none !important; }' });

  console.log(`→ rendering PDF`);
  await page.pdf({
    path: outPath,
    width: '297mm',
    height: '210mm',
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 },
  });

  await browser.close();
  const sizeKb = (fs.statSync(outPath).size / 1024).toFixed(1);
  console.log(`✓ wrote ${outPath} (${sizeKb} KB)`);
})().catch((err) => {
  console.error('✗ render failed:', err);
  process.exit(1);
});
