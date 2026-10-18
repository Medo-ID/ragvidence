// Optional browser review tooling; no report or Python runtime dependency.
// PLAYWRIGHT_MODULE must identify an existing Playwright installation.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
const { chromium } = await import(pathToFileURL(process.env.PLAYWRIGHT_MODULE).href);
const root = path.resolve(process.argv[2] || 'verification/ci/report-design');
const browser = await chromium.launch({ headless: true });
const records = [];
const after = process.argv[3] || 'after';
try {
  for (const phase of ['before', after]) {
    const manifest = JSON.parse(await fs.readFile(path.join(root, phase, 'manifest.json')));
    for (const relative of Object.keys(manifest)) {
      const name = relative.split('/')[1];
      for (const width of [1440, 390]) {
        const context = await browser.newContext({ javaScriptEnabled: false, offline: true,
          viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
        const page = await context.newPage();
        const errors = [], requests = [];
        page.on('pageerror', e => errors.push(String(e)));
        page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
        page.on('request', r => { if (/^https?:/.test(r.url())) requests.push(r.url()); });
        await page.goto(pathToFileURL(path.join(root, relative)).href);
        await page.evaluate(() => document.fonts.ready);
        const checks = await page.evaluate(() => {
          const missingAnchors = [...document.querySelectorAll('a[href^="#"]')]
            .filter(a => !document.getElementById(a.hash.slice(1))).map(a => a.hash);
          const rgb = s => s.match(/[\d.]+/g)?.slice(0, 3).map(Number);
          const luminance = c => c.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
            .reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
          const contrasts = [];
          for (const el of document.querySelectorAll('h1,h2,h3,p,a,td,th,summary,dt,dd,.status,.meta')) {
            if (!el.checkVisibility() || !el.textContent.trim()) continue;
            const style = getComputedStyle(el);
            let parent = el, background;
            while (parent) {
              const bg = getComputedStyle(parent).backgroundColor;
              if (!bg.endsWith(', 0)') && bg !== 'transparent') { background = rgb(bg); break; }
              parent = parent.parentElement;
            }
            if (!background) continue;
            const fg = luminance(rgb(style.color)), bg = luminance(background);
            const ratio = (Math.max(fg, bg) + .05) / (Math.min(fg, bg) + .05);
            const large = parseFloat(style.fontSize) >= 24 ||
              (parseFloat(style.fontSize) >= 18.66 && parseFloat(style.fontWeight) >= 700);
            if (ratio < (large ? 3 : 4.5)) contrasts.push({ text: el.textContent.trim().slice(0, 50), ratio });
          }
          return { overflow: document.documentElement.scrollWidth > innerWidth,
            missingAnchors, contrasts, fonts: document.fonts.check('16px Geist'),
            details: document.querySelectorAll('details').length,
            background: getComputedStyle(document.body).backgroundColor };
        });
        if (phase === after) {
          assert.equal(checks.overflow, false, `${name}/${width}: viewport overflow`);
          assert.deepEqual(checks.missingAnchors, []);
          assert.deepEqual(checks.contrasts, [], `${name}/${width}: contrast`);
          assert(checks.fonts);
          const scroll = page.locator('.scroll').first();
          if (await scroll.count() && await scroll.evaluate(e => e.scrollWidth > e.clientWidth)) {
            await scroll.focus();
            await page.keyboard.press('ArrowRight');
            await page.waitForTimeout(120);
            assert(await scroll.evaluate(e => e.scrollLeft > 0), 'keyboard table scrolling');
            await scroll.evaluate(e => { e.scrollLeft = 0; });
          }
          assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior), 'auto');
          const summary = page.locator('summary').filter({ visible: true }).first();
          if (await summary.count()) {
            await summary.focus();
            await page.keyboard.press('Enter');
            assert(await summary.evaluate(e => e.parentElement.open), 'keyboard disclosure');
            const focus = await summary.evaluate(e => getComputedStyle(e).outlineStyle);
            assert.notEqual(focus, 'none', 'visible focus');
            await page.keyboard.press('Enter');
          }
        }
        await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo(0, 0); });
        const captureDir = path.join(root, 'browser', phase);
        await fs.mkdir(captureDir, { recursive: true });
        await page.screenshot({ path: path.join(captureDir, `${name}-${width}.png`), fullPage: true });
        await page.screenshot({ path: path.join(captureDir, `${name}-overview-${width}.png`) });
        if (phase === after && width === 1440) {
          // Print the untouched, CLOSED disclosures: do not use script to open them.
          await page.emulateMedia({ media: 'print' });
          const print = await page.evaluate(() => ({
            closed: [...document.querySelectorAll('details')].filter(d => !d.open).length,
            hidden: [...document.querySelectorAll('details')].filter(d =>
              getComputedStyle(d, '::details-content').contentVisibility === 'hidden').length,
            pre: [...document.querySelectorAll('pre')].map(e => e.textContent),
            body: document.body.innerText,
          }));
          assert.equal(print.hidden, 0, `${name}: print disclosure hidden`);
          await fs.writeFile(path.join(captureDir, `${name}-print-content.json`), JSON.stringify(print, null, 2));
          await page.screenshot({ path: path.join(captureDir, `${name}-print.png`) });
          await page.pdf({ path: path.join(captureDir, `${name}.pdf`), format: 'A4', printBackground: false });
          await page.emulateMedia({ media: 'screen' });
          // Inspect every expanded state as well as the default view.
          await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
          await page.screenshot({ path: path.join(captureDir, `${name}-expanded.png`), fullPage: true });
        }
        if (phase === after && width === 390) {
          await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
          assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
          await page.screenshot({ path: path.join(captureDir, `${name}-expanded-390.png`), fullPage: true });
        }
        assert.deepEqual(errors, [], `${name}: console errors`);
        assert.deepEqual(requests, [], `${name}: network requests`);
        records.push({ phase, name, width, ...checks, errors, requests });
        await context.close();
      }
    }
  }
} finally { await browser.close(); }
await fs.writeFile(path.join(root, 'browser', 'checks.json'), JSON.stringify(records, null, 2) + '\n');
console.log(`PASS: ${records.length} offline, JavaScript-disabled browser reviews`);
