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
async function inspect(page) {
  return page.evaluate(() => {
    const missingAnchors = [...document.querySelectorAll('a[href^="#"]')]
      .filter(a => !document.getElementById(a.hash.slice(1))).map(a => a.hash);
    const rgb = s => s.match(/[\d.]+/g)?.slice(0, 3).map(Number);
    const luminance = c => c.map(v => v / 255).map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
      .reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
    const contrasts = [];
    for (const el of document.querySelectorAll('h1,h2,h3,p,a,button,td,th,summary,dt,dd,.status,.meta,.prompt,.question-id')) {
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
    const report = document.querySelector('main');
    const box = report.getBoundingClientRect();
    const style = getComputedStyle(report);
    const singleColumn = [...document.querySelectorAll('main,.comparison,.runs,.diagnosis-grid,.metadata,.composition,.question-list')]
      .filter(el => el.checkVisibility()).every(el => {
        const css = getComputedStyle(el);
        return css.display !== 'grid' || css.gridTemplateColumns.trim().split(/\s+/).length === 1;
      });
    const layout = { display: style.display, width: box.width,
      centered: Math.abs(box.left - (document.documentElement.clientWidth - box.right)) < 1,
      padding: ['Top','Right','Bottom','Left'].map(side => parseFloat(style[`padding${side}`])),
      borders: ['Top','Right','Bottom','Left'].map(side => parseFloat(style[`border${side}Width`])),
      topMargin: box.top + scrollY,
      bottomMargin: document.documentElement.scrollHeight - (box.bottom + scrollY),
      backgroundImage: getComputedStyle(document.body).backgroundImage,
      shadow: style.boxShadow, radius: style.borderRadius, singleColumn };
    return { layout, overflow: document.documentElement.scrollWidth > innerWidth,
      missingAnchors, contrasts, fonts: document.fonts.check('16px Geist'),
      details: document.querySelectorAll('details').length,
      background: getComputedStyle(document.body).backgroundColor };
  });
}

function assertLayout(layout) {
  assert.equal(layout.display, 'grid');
  assert(layout.singleColumn, 'one column at every screen width');
  assert(layout.width <= 900, 'maximum report width');
  assert(layout.centered, 'horizontally centered report');
  assert(layout.padding.every(value => value >= 32 && value <= 48), '32–48px inner padding');
  assert.deepEqual(layout.borders, [1, 1, 1, 1], 'all four frame edges');
  assert(layout.topMargin >= 24 && layout.bottomMargin >= 24, 'top and bottom whitespace');
  assert.equal(layout.backgroundImage, 'none');
  assert.equal(layout.shadow, 'none');
  assert.equal(layout.radius, '0px');
}

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
        const checks = await inspect(page);
        if (phase === after) assert.equal(await page.locator('#theme-toggle').isVisible(), false);
        if (phase === after) {
          assertLayout(checks.layout);
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
        if (phase === after) {
          const themed = await browser.newContext({ javaScriptEnabled: true, offline: true,
            viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
          const themedPage = await themed.newPage();
          const themeErrors = [], themeRequests = [];
          themedPage.on('pageerror', e => themeErrors.push(String(e)));
          themedPage.on('console', m => { if (m.type() === 'error') themeErrors.push(m.text()); });
          themedPage.on('request', r => { if (/^https?:/.test(r.url())) themeRequests.push(r.url()); });
          await themedPage.goto(pathToFileURL(path.join(root, relative)).href);
          await themedPage.evaluate(() => document.fonts.ready);
          const toggle = themedPage.locator('#theme-toggle');
          assert(await toggle.isVisible());
          assert.equal(await toggle.getAttribute('aria-pressed'), 'false');
          await themedPage.screenshot({ path: path.join(captureDir, `${name}-dark-${width}.png`) });
          await toggle.focus();
          await themedPage.keyboard.press('Enter');
          assert.equal(await toggle.getAttribute('aria-pressed'), 'true');
          assert.equal(await toggle.innerText(), 'Dark mode');
          assert.equal(await themedPage.locator('html').getAttribute('data-theme'), 'light');
          const light = await inspect(themedPage);
          assert.deepEqual(light.contrasts, [], `${name}/${width}: light theme contrast`);
          assert.equal(light.overflow, false);
          assertLayout(light.layout);
          await themedPage.evaluate(() => document.activeElement?.blur());
          await themedPage.screenshot({ path: path.join(captureDir, `${name}-light-${width}.png`) });
          if (width === 1440) {
            await themedPage.emulateMedia({ media: 'print' });
            await themedPage.pdf({ path: path.join(captureDir, `${name}-light.pdf`), format: 'A4' });
            await themedPage.emulateMedia({ media: 'screen' });
          }
          await toggle.click();
          assert.equal(await toggle.getAttribute('aria-pressed'), 'false');
          assert.equal(await themedPage.locator('html').getAttribute('data-theme'), 'dark');
          assert.deepEqual(themeErrors, []);
          assert.deepEqual(themeRequests, []);
          records.push({ phase, name, width, theme: 'light', ...light,
            errors: themeErrors, requests: themeRequests });
          await themed.close();
        }
      }
    }
  }
  const manifest = JSON.parse(await fs.readFile(path.join(root, after, 'manifest.json')));
  const layoutContext = await browser.newContext({ javaScriptEnabled: false, offline: true });
  for (const relative of Object.keys(manifest)) {
    const page = await layoutContext.newPage();
    await page.goto(pathToFileURL(path.join(root, relative)).href);
    for (const width of [320, 768, 900, 1920]) {
      await page.setViewportSize({ width, height: 1000 });
      const checks = await inspect(page);
      assertLayout(checks.layout);
      assert.equal(checks.overflow, false);
      records.push({ phase: after, name: relative.split('/')[1], width, probe: 'layout', ...checks });
    }
    await page.close();
  }
  await layoutContext.close();
} finally { await browser.close(); }
await fs.writeFile(path.join(root, 'browser', 'checks.json'), JSON.stringify(records, null, 2) + '\n');
console.log(`PASS: ${records.length} offline browser checks, including JavaScript-disabled and dark/light views`);
