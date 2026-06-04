#!/usr/bin/env node
/**
 * audit.mjs — самопроверка HTML-презентации скилла `presentation`.
 *
 * ДВА РЕЖИМА:
 *  • С браузером (puppeteer/playwright) — полная проверка ГЕОМЕТРИИ + структуры:
 *    переполнение (верт/гор), наезжание текста, НЕДОЗАПОЛНЕНИЕ слайда, отсутствие
 *    рамки .fr / номера .pg, повтор форм подряд, плейсхолдеры, протёкший текст,
 *    (опц.) сверка чисел с реестром плана.
 *  • БЕЗ браузера (фолбэк) — статическая проверка по тексту HTML: .fr/.pg,
 *    повтор форм, плейсхолдеры. ГЕОМЕТРИЯ НЕ ПРОВЕРЯЕТСЯ (об этом громко сообщается).
 *
 * ЗАПУСК:
 *   node audit.mjs <deck.html>                  обычный аудит
 *   node audit.mjs <deck.html> --plan <plan.md> + сверка чисел деки с «Реестром данных»
 *   node audit.mjs <deck.html> --json           машинный вывод (JSON)
 *   node audit.mjs --selftest                    только проверить, доступен ли браузер
 *
 * КОДЫ ВЫХОДА: 0 чисто · 1 есть FAIL · 2 ошибка вызова · 3 (только --selftest) браузера нет.
 * ЗАВИСИМОСТИ: Node 18+; для геометрии — puppeteer | puppeteer-core+Chrome | playwright.
 */

import { pathToFileURL } from 'node:url';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const JSON_OUT = args.includes('--json');
const SELFTEST = args.includes('--selftest');
const planIdx = args.indexOf('--plan');
const planPath = planIdx >= 0 ? args[planIdx + 1] : null;
const file = args.find((a, i) => !a.startsWith('--') && args[i - 1] !== '--plan');

// ── общие хелперы (Node-сторона) ────────────────────────────────────────────────
const PLACEHOLDER_RE = /(lorem|ipsum|\bxxxx\b|\bTODO\b|\bTBD\b|\bN\/A\b|placeholder|заглушка|\bOption [ABC]\b|тут будет|вставь|МЕСТО ПОД|подпись к метрике|Категория [АБВГ]|одной фразой|Заголовок-?вывод|Заголовок раздела|deck_stage)/i;
function numTokens(text) {
  return new Set((text || '').match(/\d[\d.,]*\d|\d+/g) || []);
}

// ── поиск системного Chrome ─────────────────────────────────────────────────────
function findChrome() {
  if (process.env.PUPPETEER_EXECUTABLE_PATH) return process.env.PUPPETEER_EXECUTABLE_PATH;
  const c = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ];
  return c.find(p => existsSync(p)) || null;
}
async function getPage() {
  const tried = [];
  try {
    const { default: p } = await import('puppeteer');
    const b = await p.launch({ headless: 'new', args: ['--no-sandbox', '--font-render-hinting=none'] });
    const pg = await b.newPage(); await pg.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
    return { page: pg, close: () => b.close(), engine: 'puppeteer' };
  } catch (e) { tried.push('puppeteer: ' + String(e.message || e).slice(0, 70)); }
  try {
    const { default: p } = await import('puppeteer-core');
    const exe = findChrome(); if (!exe) throw new Error('системный Chrome не найден');
    const b = await p.launch({ headless: 'new', executablePath: exe, args: ['--no-sandbox', '--font-render-hinting=none'] });
    const pg = await b.newPage(); await pg.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
    return { page: pg, close: () => b.close(), engine: 'puppeteer-core' };
  } catch (e) { tried.push('puppeteer-core: ' + String(e.message || e).slice(0, 70)); }
  try {
    const { chromium } = await import('playwright');
    const b = await chromium.launch();
    const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
    return { page: pg, close: () => b.close(), engine: 'playwright' };
  } catch (e) { tried.push('playwright: ' + String(e.message || e).slice(0, 70)); }
  return { page: null, tried };
}

// ── режим --selftest ────────────────────────────────────────────────────────────
if (SELFTEST) {
  const ctx = await getPage();
  if (ctx.page) { await ctx.close(); console.log('audit: браузер доступен (' + ctx.engine + ') — геометрия проверяется.'); process.exit(0); }
  console.log('audit: браузера НЕТ — геометрия НЕ проверяется (только статика).\n  поставить: npm i -D puppeteer  ИЛИ  npm i -D playwright && npx playwright install chromium');
  process.exit(3);
}

// ── валидация файла ──────────────────────────────────────────────────────────────
if (!file) { console.error('Использование: node audit.mjs <deck.html> [--plan <plan.md>] [--json] | --selftest'); process.exit(2); }
const abs = resolve(file);
if (!existsSync(abs)) { console.error(`Файл не найден: ${abs}`); process.exit(2); }
const url = pathToFileURL(abs).href;
const html = readFileSync(abs, 'utf8');
const planNums = planPath && existsSync(resolve(planPath)) ? numTokens(readFileSync(resolve(planPath), 'utf8')) : null;

// ── повтор форм подряд (по списку layout-классов) ───────────────────────────────
function repeatWarn(layouts) {
  const w = [];
  let run = 1;
  for (let i = 1; i < layouts.length; i++) {
    if (layouts[i] && layouts[i] === layouts[i - 1]) { run++; if (run >= 3) w.push(`${run} подряд одинаковых формы «${layouts[i]}» (слайды ~${i - run + 2}–${i + 1})`); }
    else run = 1;
  }
  const distinct = new Set(layouts.filter(Boolean)).size;
  if (layouts.length >= 4 && distinct <= 2) w.push(`мало разнообразия форм: всего ${distinct} разных на ${layouts.length} слайдов`);
  return [...new Set(w)];
}

// ── ЗАМЕР В БРАУЗЕРЕ ─────────────────────────────────────────────────────────────
const MEASURE = async () => {
  const stage = document.querySelector('deck-stage');
  if (!stage) return { error: 'no <deck-stage>' };
  const total = stage.totalSlides || stage.querySelectorAll('section').length;
  const DECOR = '.glow, .glow-2, .hero-glow, .chrome, [data-decorative], .stretch, [data-allow-overflow]';
  const PH = /(lorem|ipsum|\bxxxx\b|\bTODO\b|\bTBD\b|placeholder|заглушка|\bOption [ABC]\b|тут будет|вставь|МЕСТО ПОД|подпись к метрике|Категория [АБВГ]|одной фразой|Заголовок-?вывод|Заголовок раздела|deck_stage)/i;
  const isDecor = (el) => {
    if (el.matches && (el.matches(DECOR) || el.closest(DECOR))) return true;
    const cs = getComputedStyle(el);
    if (cs.pointerEvents === 'none' && !(el.textContent || '').trim() && parseFloat(cs.opacity) < 1) return true;
    return false;
  };
  const hasCyr = (t) => /[Ѐ-ӿ]/.test(t);
  const out = [];
  for (let i = 0; i < total; i++) {
    if (stage.goToSlide) stage.goToSlide(i);
    await new Promise(r => setTimeout(r, 70));
    const s = stage.querySelectorAll('section')[i];
    const sRect = s.getBoundingClientRect();
    const scale = sRect.height ? 1080 / sRect.height : 1;
    const layout = (String(s.className).match(/layout-[\w-]+/) || ['?'])[0];
    const airy = /layout-(statement|quote|cover)/.test(s.className);
    const hasFr = !!s.querySelector('.fr');
    const hasPg = !!s.querySelector('.pg');

    let maxBottom = 0, maxRight = 0, culprit = null;
    const leaves = [];
    const placeholders = new Set();
    const nums = new Set();
    for (const el of s.querySelectorAll('*')) {
      if (isDecor(el)) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const bottom = (r.bottom - sRect.top) * scale, right = (r.right - sRect.left) * scale;
      if (bottom > maxBottom) { maxBottom = bottom; culprit = (el.className && el.className.toString().slice(0, 36)) || el.tagName; }
      if (right > maxRight) maxRight = right;
      const txt = (el.textContent || '').trim();
      if (txt && el.children.length === 0) {
        leaves.push({ top: (r.top - sRect.top) * scale, bottom, left: (r.left - sRect.left) * scale, right, id: (el.className && el.className.toString().slice(0, 24)) || el.tagName });
        if (PH.test(txt)) placeholders.add(txt.slice(0, 40));
        // числа из контента, НЕ из рамки/индексов
        if (!el.closest('.fr, .idx, .n, .pg')) (txt.match(/\d[\d.,]*\d|\d+/g) || []).forEach(x => nums.add(x));
      }
    }
    const overlaps = [];
    for (let a = 0; a < leaves.length; a++) for (let b = a + 1; b < leaves.length; b++) {
      const A = leaves[a], B = leaves[b];
      const ix = Math.min(A.right, B.right) - Math.max(A.left, B.left);
      const iy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
      if (ix > 4 && iy > 4) overlaps.push(`${A.id} ↔ ${B.id} (${Math.round(ix)}×${Math.round(iy)}px)`);
    }
    const contentBottom = Math.round(maxBottom), contentRight = Math.round(maxRight);
    const vOverflow = contentBottom - 1080, hOverflow = contentRight - 1920, headroom = 1080 - contentBottom;
    const warnAt = hasCyr(s.textContent || '') ? 60 : 40;

    let status = 'OK';
    const reasons = [];
    if (vOverflow > 0) { status = 'FAIL'; reasons.push(`переполнение по высоте +${vOverflow}px (${culprit})`); }
    if (hOverflow > 2) { status = 'FAIL'; reasons.push(`переполнение по ширине +${hOverflow}px`); }
    if (overlaps.length) { status = 'FAIL'; reasons.push(`наезжание: ${overlaps.slice(0, 3).join('; ')}`); }
    if (placeholders.size) { status = 'FAIL'; reasons.push(`плейсхолдеры: ${[...placeholders].slice(0, 3).join(' | ')}`); }
    // структура и недозаполнение — WARN
    if (!hasFr) { if (status === 'OK') status = 'WARN'; reasons.push('нет фирменной рамки .fr'); }
    if (!hasPg) { if (status === 'OK') status = 'WARN'; reasons.push('нет .pg (номер слайда не проставится)'); }
    if (status === 'OK' && !airy && contentBottom < 620) { status = 'WARN'; reasons.push(`пустовато: контент кончается на ${contentBottom}px (низ слайда пустой)`); }
    if (status === 'OK' && headroom < warnAt) { status = 'WARN'; reasons.push(`мало запаса снизу: ${headroom}px (нужно ≥${warnAt})`); }

    out.push({ slide: i + 1, status, layout, contentBottom, headroom, vOverflow, hOverflow, reasons, nums: [...nums] });
  }
  if (stage.goToSlide) stage.goToSlide(0);
  const stray = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walk.nextNode())) {
    const t = (node.textContent || '').trim(); if (!t) continue;
    const p = node.parentElement; if (!p || p.closest('deck-stage')) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(p.tagName)) continue;
    stray.push(t.slice(0, 60));
  }
  return { total, slides: out, stray };
};

// ── СТАТИЧЕСКИЙ ФОЛБЭК (без браузера) ────────────────────────────────────────────
function staticAudit(src) {
  const slides = [];
  const re = /<section\b([^>]*)>([\s\S]*?)<\/section>/gi;
  let m, idx = 0;
  while ((m = re.exec(src))) {
    idx++;
    const attrs = m[1], inner = m[2];
    const layout = (attrs.match(/layout-[\w-]+/) || ['?'])[0];
    const hasFr = /class="[^"]*\bfr\b[^"]*"/.test(inner);
    const hasPg = /class="[^"]*\bpg\b[^"]*"/.test(inner);
    const text = inner.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
    const reasons = [];
    let status = 'OK';
    if (PLACEHOLDER_RE.test(text)) { status = 'FAIL'; reasons.push('плейсхолдер в тексте'); }
    if (!hasFr) { if (status === 'OK') status = 'WARN'; reasons.push('нет рамки .fr'); }
    if (!hasPg) { if (status === 'OK') status = 'WARN'; reasons.push('нет .pg'); }
    slides.push({ slide: idx, status, layout, reasons });
  }
  return { total: idx, slides };
}

// ── ЗАПУСК ────────────────────────────────────────────────────────────────────────
const ctx = await getPage();
let report, geometryChecked = true, engine = ctx.engine;

if (ctx.page) {
  try {
    await ctx.page.goto(url, { waitUntil: 'load' });
    await ctx.page.evaluate(async () => {
      try { await customElements.whenDefined('deck-stage'); } catch {}
      if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch {} }
      await new Promise(r => setTimeout(r, 150));
    });
    report = await ctx.page.evaluate(MEASURE);
  } catch (e) { console.error('Ошибка замера: ' + (e.message || e)); report = { fatal: true }; }
  await ctx.close();
  if (report.error) { console.error('Не найден <deck-stage> — это дека из шаблона?'); process.exit(2); }
  if (report.fatal) { geometryChecked = false; report = staticAudit(html); engine = 'статика (ошибка браузера)'; }
} else {
  geometryChecked = false;
  report = staticAudit(html);
  engine = 'статика — БРАУЗЕРА НЕТ';
}

// сверка чисел с реестром (только если есть план и геометрия — там точные числа без индексов)
let numWarn = null;
if (planNums && geometryChecked && report.slides) {
  const deckNums = new Set();
  report.slides.forEach(s => (s.nums || []).forEach(n => deckNums.add(n)));
  const orphan = [...deckNums].filter(n => !planNums.has(n) && n.replace(/[.,]/g, '').length >= 2); // игнор однозначных (3 зоны и т.п.)
  if (orphan.length) numWarn = orphan.slice(0, 12);
}

// повтор форм
const layouts = (report.slides || []).map(s => s.layout);
const repeats = repeatWarn(layouts);

// ── ВЫВОД ──────────────────────────────────────────────────────────────────────
if (JSON_OUT) console.log(JSON.stringify({ ...report, geometryChecked, engine, numWarn, repeats }, null, 2));

const fails = (report.slides || []).filter(s => s.status === 'FAIL');
const warns = (report.slides || []).filter(s => s.status === 'WARN');
const strayFail = report.stray && report.stray.length > 0;

if (!JSON_OUT) {
  console.log(`\n  АУДИТ ДЕКИ · ${engine} · слайдов: ${report.total}\n`);
  if (!geometryChecked) console.log('  ⚠️  ГЕОМЕТРИЯ НЕ ПРОВЕРЕНА (нет браузера). Проверены только структура/плейсхолдеры/повторы.\n      Обязательно сверь высоту слайдов вручную (бюджет ~590px, self-check.md).\n');
  for (const s of (report.slides || [])) {
    const mark = s.status === 'FAIL' ? '✗ FAIL' : s.status === 'WARN' ? '! WARN' : '✓ OK  ';
    const tail = s.reasons && s.reasons.length ? '  — ' + s.reasons.join('; ') : (s.contentBottom != null ? `  (низ ${s.contentBottom}px)` : '');
    console.log(`  ${mark}  слайд ${String(s.slide).padStart(2)} [${s.layout}]${tail}`);
  }
  if (repeats.length) console.log('\n  ! WARN  однотипность форм: ' + repeats.join('; '));
  if (numWarn) console.log('\n  ! WARN  числа в деке, которых НЕТ в реестре плана (проверь — не выдумано ли): ' + numWarn.join(', '));
  if (strayFail) { console.log('\n  ✗ FAIL  протёкший текст ВНЕ слайдов:'); report.stray.slice(0, 5).forEach(t => console.log(`          «${t}»`)); }
  console.log('');
  if (fails.length || strayFail) console.log(`  ИТОГ: ${fails.length}${strayFail ? '+stray' : ''} FAIL — чинить и перезапускать. ${warns.length} WARN${repeats.length || numWarn ? ' + замечания выше' : ''}.`);
  else if (warns.length || repeats.length || numWarn) console.log(`  ИТОГ: без FAIL, но есть WARN/замечания — желательно поправить.${geometryChecked ? '' : ' (геометрия не проверена!)'}`);
  else console.log(`  ИТОГ: чисто.${geometryChecked ? ' Можно сдавать.' : ' Но ГЕОМЕТРИЯ НЕ ПРОВЕРЕНА — сверь высоту вручную.'}`);
  console.log('');
}

process.exit(fails.length || strayFail ? 1 : 0);
