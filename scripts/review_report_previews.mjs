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
    const colors = new Map();
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = 1;
    const context = canvas.getContext('2d');
    const rgb = color => {
      if (!colors.has(color)) {
        context.clearRect(0, 0, 1, 1);
        context.fillStyle = color;
        context.fillRect(0, 0, 1, 1);
        colors.set(color, [...context.getImageData(0, 0, 1, 1).data].slice(0, 3));
      }
      return colors.get(color);
    };
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
    const sections = [...report.querySelectorAll(':scope > header, :scope > section, :scope > footer')];
    const viewport = document.documentElement.clientWidth;
    const boundaryLines = [...report.children].filter(el => !el.matches('.report-nav')).map(el => {
      const line = getComputedStyle(el, '::before');
      return { width: parseFloat(line.width), stroke: line.borderTopWidth, offset: parseFloat(line.top), color: rgb(line.borderTopColor) };
    });
    const rails = getComputedStyle(document.body, '::before');
    const railBorders = parseFloat(rails.borderLeftWidth) + parseFloat(rails.borderRightWidth);
    const railOuterWidth = parseFloat(rails.width) + (rails.boxSizing === 'border-box' ? 0 : railBorders);
    // Published 0.2.0 portable reports predate the shared toolbar/navigation.
    // Still capture their real baseline; enforce the new layout only on "after".
    const toolbar = getComputedStyle(report.querySelector('.report-toolbar') || report);
    const undecorated = [...report.querySelectorAll('.run-summary,.question-list')].map(el => {
      const css = getComputedStyle(el);
      return { border: css.borderTopWidth, padding: el.matches('.run-summary') ? css.paddingTop : null };
    });
    const headerBoundary = getComputedStyle(report.querySelector('header') || report, '::after');
    const reportNav = report.querySelector('.report-nav');
    const nav = reportNav || report;
    const navStyle = getComputedStyle(nav);
    const navLinks = [...nav.querySelectorAll('a')].map(a => a.getBoundingClientRect());
    const layout = { canvas: rgb(getComputedStyle(document.body).backgroundColor),
      navigation: { present: Boolean(reportNav), width: nav.clientWidth, contentWidth: nav.scrollWidth,
        overflowX: navStyle.overflowX, wrap: navStyle.flexWrap,
        rows: new Set(navLinks.map(box => Math.round(box.top))).size,
        linksVisible: navLinks.every(box => box.left >= 0 && box.right <= viewport) },
      documentColor: rgb(style.backgroundColor),
      sectionPadding: sections.map(el => {
        const css = getComputedStyle(el);
        return ['Top','Right','Bottom','Left'].map(side => parseFloat(css[`padding${side}`]));
      }),
      headerBoundary: { width: parseFloat(headerBoundary.width), stroke: headerBoundary.borderTopWidth, bottom: headerBoundary.bottom },
      boundaryLines, viewport, frameColor: rgb(style.borderTopColor),
      rails: { width: parseFloat(rails.width), outerWidth: railOuterWidth,
        left: rails.borderLeftWidth, right: rails.borderRightWidth },
      toolbarPadding: [parseFloat(toolbar.paddingTop), parseFloat(toolbar.paddingBottom)], undecorated,
      display: style.display, width: box.width,
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
  assert(layout.width <= 1100, 'maximum report width');
  assert(layout.navigation.present, 'report navigation is present');
  if (layout.viewport <= 800) {
    assert.equal(layout.navigation.overflowX, 'auto', 'small-screen navigation can scroll');
    assert.equal(layout.navigation.wrap, 'nowrap');
    assert.equal(layout.navigation.rows, 1, 'small-screen navigation stays on one row');
  } else {
    assert(layout.navigation.contentWidth <= layout.navigation.width, 'desktop navigation fits without horizontal scrolling');
    assert(layout.navigation.linksVisible, 'all desktop navigation links stay visible');
  }
  if (layout.viewport >= 1200) assert.equal(layout.navigation.rows, 1, 'desktop navigation fits on one line');
  assert(layout.centered, 'horizontally centered report');
  assert(layout.sectionPadding.length > 0);
  assert(layout.sectionPadding.every(padding => padding.every(value => value >= 32 && value <= 48)), '32–48px section padding');
  assert.deepEqual(layout.documentColor, layout.canvas, 'one background inside and outside the rails');
  assert.equal(layout.rails.left, '1px');
  assert.equal(layout.rails.right, '1px');
  assert(Math.abs(layout.rails.outerWidth - layout.width) < .01, 'side rails align with the report border without duplicate strokes');
  assert.deepEqual(layout.toolbarPadding, [16, 16], 'toolbar padding matches navigation');
  assert(layout.undecorated.every(item => item.border === '0px' &&
    (item.padding === null || item.padding === '0px')), 'no redundant run-summary or question-list top borders/padding');
  assert(layout.boundaryLines.every((line, index) =>
    Math.abs(line.width - layout.viewport) < 1 && line.stroke === '1px' &&
    line.offset === (index === 0 ? -1 : 0)), 'full-width, one-pixel section boundaries');
  assert.equal(layout.headerBoundary.width, layout.viewport, 'divider spans the viewport above navigation');
  assert.equal(layout.headerBoundary.stroke, '1px');
  assert.equal(layout.headerBoundary.bottom, '-1px');
  for (const line of layout.boundaryLines) assert.deepEqual(line.color, layout.frameColor);
  const dark = layout.canvas.join(',') === '1,1,1';
  assert.deepEqual(layout.frameColor, dark ? [40, 40, 46] : [198, 203, 211]);
  assert.deepEqual(layout.borders, [1, 1, 1, 1], 'all four frame edges');
  assert(layout.topMargin >= 24 && layout.bottomMargin >= 24, 'top and bottom whitespace');
  assert.equal(layout.backgroundImage, 'none');
  assert.equal(layout.shadow, 'none');
  assert.equal(layout.radius, '0px');
}

async function checkNavigation(page) {
  const nav = page.locator('.report-nav');
  if (!await nav.evaluate(el => el.scrollWidth > el.clientWidth)) return { scrollable: false };
  const links = nav.locator('a');
  await nav.focus();
  assert.notEqual(await nav.evaluate(el => getComputedStyle(el).outlineStyle), 'none');
  await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(120);
  assert(await nav.evaluate(el => el.scrollLeft > 0), 'navigation scrolls with arrow keys');
  await nav.evaluate(el => { el.scrollLeft = 0; });
  await links.first().focus();
  for (let index = 1; index < await links.count(); index++) await page.keyboard.press('Tab');
  const last = links.last();
  assert(await last.evaluate(el => el === document.activeElement), 'Tab reaches the last navigation link');
  const revealed = () => last.evaluate(el => {
    const a = el.getBoundingClientRect(), b = el.closest('nav').getBoundingClientRect();
    return a.left >= b.left && a.right <= b.right;
  });
  // Scroll the focusable region if native link focus leaves a label partly clipped.
  for (let attempt = 0; !await revealed() && attempt < 30; attempt++) {
    await nav.focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(120);
  }
  await last.focus();
  assert(await revealed(), 'keyboard scrolling reveals the full final navigation label');
  assert.notEqual(await last.evaluate(el => getComputedStyle(el).outlineStyle), 'none');
  const scrollLeft = await nav.evaluate(el => el.scrollLeft);
  await page.evaluate(() => { document.activeElement?.blur(); window.scrollTo(0, 0); });
  await nav.evaluate(el => { el.scrollLeft = 0; });
  return { scrollable: true, keyboardScroll: true, lastLinkRevealed: true, scrollLeft };
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
        if (phase === after) checks.navigationInteraction = await checkNavigation(page);
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
          await themedPage.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
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
          await themedPage.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
          await themedPage.screenshot({ path: path.join(captureDir, `${name}-light-${width}.png`) });
          if (width === 1440) {
            await themedPage.emulateMedia({ media: 'print' });
            await themedPage.pdf({ path: path.join(captureDir, `${name}-light.pdf`), format: 'A4' });
            await themedPage.emulateMedia({ media: 'screen' });
          }
          light.navigationInteraction = await checkNavigation(themedPage);
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
      checks.navigationInteraction = await checkNavigation(page);
      assert.equal(checks.overflow, false);
      records.push({ phase: after, name: relative.split('/')[1], width, probe: 'layout', ...checks });
    }
    await page.close();
  }
  await layoutContext.close();
} finally { await browser.close(); }
await fs.writeFile(path.join(root, 'browser', 'checks.json'), JSON.stringify(records, null, 2) + '\n');
console.log(`PASS: ${records.length} offline browser checks, including JavaScript-disabled and dark/light views`);
