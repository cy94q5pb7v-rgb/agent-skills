#!/usr/bin/env node
/**
 * audit.mjs — самопроверка HTML-презентации, собранной скиллом `presentation`.
 *
 * ЧТО ДЕЛАЕТ: загружает деку в headless-браузер, проходит по КАЖДОМУ слайду и мерит
 * реальную геометрию. Ловит три класса дефектов, которые на глаз в терминале не видно:
 *   1. ПЕРЕПОЛНЕНИЕ — контент вылез за пределы слайда 1920×1080 (обрезается молча,
 *      т.к. у секции overflow:hidden). По вертикали И по горизонтали.
 *   2. НАЕЗЖАНИЕ — два текстовых блока перекрывают друг друга (то самое «наезжает»).
 *   3. ПЛЕЙСХОЛДЕРЫ — в текст слайда протёк мусор-заглушка (lorem, placeholder,
 *      «Option A», TODO, имя шаблона и т.п.).
 *
 * ЗАПУСК:
 *   node audit.mjs <путь-к-деке.html>
 *   node audit.mjs ./deck.html --json     # машинный вывод (JSON в stdout)
 *
 * КОДЫ ВЫХОДА (по ним агент понимает, что делать):
 *   0  — всё чисто (OK/WARN), можно сдавать.
 *   1  — есть FAIL (переполнение / наезжание / плейсхолдер). НЕ сдавать, чинить и перезапускать.
 *   2  — ошибка вызова (не передан/не найден файл).
 *   3  — браузер недоступен. Аудит не выполнен — опирайся на бюджет высоты и ручной чеклист
 *        (references/self-check.md). Поставить браузер: `npm i -D puppeteer` ИЛИ `npm i -D playwright && npx playwright install chromium`.
 *
 * ЗАВИСИМОСТИ: Node 18+ и один из движков — puppeteer | puppeteer-core (+системный Chrome) | playwright.
 */

import { pathToFileURL } from 'node:url';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const args = process.argv.slice(2);
const JSON_OUT = args.includes('--json');
const file = args.find(a => !a.startsWith('--'));

if (!file) { console.error('Использование: node audit.mjs <deck.html> [--json]'); process.exit(2); }
const abs = resolve(file);
if (!existsSync(abs)) { console.error(`Файл не найден: ${abs}`); process.exit(2); }
const url = pathToFileURL(abs).href; // всегда читаем СВЕЖУЮ версию с диска

// ── Поиск системного Chrome (для puppeteer-core) ───────────────────────────────
function findChrome() {
  if (process.env.PUPPETEER_EXECUTABLE_PATH) return process.env.PUPPETEER_EXECUTABLE_PATH;
  const candidates = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ];
  return candidates.find(p => existsSync(p)) || null;
}

// ── Получить страницу в любом доступном движке. Возвращает {page, close} или null ──
async function getPage() {
  const tried = [];
  // 1) puppeteer (со своим Chromium)
  try {
    const { default: puppeteer } = await import('puppeteer');
    const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--font-render-hinting=none'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
    return { page, close: () => browser.close(), engine: 'puppeteer' };
  } catch (e) { tried.push('puppeteer: ' + (e.message || e).slice(0, 80)); }
  // 2) puppeteer-core + системный Chrome
  try {
    const { default: puppeteer } = await import('puppeteer-core');
    const execPath = findChrome();
    if (!execPath) throw new Error('системный Chrome не найден');
    const browser = await puppeteer.launch({ headless: 'new', executablePath: execPath, args: ['--no-sandbox', '--font-render-hinting=none'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
    return { page, close: () => browser.close(), engine: 'puppeteer-core' };
  } catch (e) { tried.push('puppeteer-core: ' + (e.message || e).slice(0, 80)); }
  // 3) playwright
  try {
    const { chromium } = await import('playwright');
    const browser = await chromium.launch();
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    return { page, close: () => browser.close(), engine: 'playwright' };
  } catch (e) { tried.push('playwright: ' + (e.message || e).slice(0, 80)); }
  console.error('Браузерный движок недоступен. Попытки:\n  - ' + tried.join('\n  - '));
  return null;
}

// ── Функция замера, исполняется ВНУТРИ страницы ─────────────────────────────────
// Возвращает массив отчётов по слайдам. Логика портирована из make-deck Phase 4 + добавлены
// горизонтальное переполнение, попарный тест наезжаний и grep плейсхолдеров.
const MEASURE = async () => {
  const stage = document.querySelector('deck-stage');
  if (!stage) return { error: 'no <deck-stage>' };
  const total = stage.totalSlides || stage.querySelectorAll('section').length;

  // декоративка, которая по дизайну вылезает за края — её НЕ считаем переполнением
  const DECOR = '.glow, .glow-2, .hero-glow, .chrome, [data-decorative], .stretch, [data-allow-overflow]';
  const isDecor = (el) => {
    if (el.matches && (el.matches(DECOR) || el.closest(DECOR))) return true;
    const cs = getComputedStyle(el);
    if (cs.pointerEvents === 'none' && !(el.textContent || '').trim() && parseFloat(cs.opacity) < 1) return true;
    return false;
  };
  const PLACEHOLDER = /(lorem|ipsum|\bxxxx\b|\bTODO\b|placeholder|заглушка|\bOption [ABC]\b|МЕСТО ПОД|подпись к метрике|одной фразой|Заголовок раздела|deck_stage)/i;
  const hasCyrillic = (t) => /[Ѐ-ӿ]/.test(t);

  const out = [];
  for (let i = 0; i < total; i++) {
    if (stage.goToSlide) stage.goToSlide(i);
    await new Promise(r => setTimeout(r, 70)); // дать применить класс .active и усадку текста
    const s = stage.querySelectorAll('section')[i];
    const sRect = s.getBoundingClientRect();
    const scale = sRect.height ? 1080 / sRect.height : 1; // нормируем в логические 1080

    let maxBottom = 0, maxRight = 0, culprit = null;
    const leaves = []; // текстовые «листья» для теста наезжаний
    const placeholders = new Set();

    for (const el of s.querySelectorAll('*')) {
      if (isDecor(el)) continue;
      const cs = getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) === 0) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;

      const bottom = (r.bottom - sRect.top) * scale;
      const right = (r.right - sRect.left) * scale;
      if (bottom > maxBottom) { maxBottom = bottom; culprit = (el.className && el.className.toString().slice(0, 36)) || el.tagName; }
      if (right > maxRight) maxRight = right;

      const txt = (el.textContent || '').trim();
      if (txt && el.children.length === 0) {
        leaves.push({ top: (r.top - sRect.top) * scale, bottom, left: (r.left - sRect.left) * scale, right, id: (el.className && el.className.toString().slice(0, 24)) || el.tagName });
        if (PLACEHOLDER.test(txt)) placeholders.add(txt.slice(0, 40));
      }
    }

    // попарный тест наезжаний (только заметное пересечение и без data-allow-overlap)
    const overlaps = [];
    for (let a = 0; a < leaves.length; a++) {
      for (let b = a + 1; b < leaves.length; b++) {
        const A = leaves[a], B = leaves[b];
        const ix = Math.min(A.right, B.right) - Math.max(A.left, B.left);
        const iy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
        if (ix > 4 && iy > 4) overlaps.push(`${A.id} ↔ ${B.id} (${Math.round(ix)}×${Math.round(iy)}px)`);
      }
    }

    const contentBottom = Math.round(maxBottom);
    const contentRight = Math.round(maxRight);
    const vOverflow = contentBottom - 1080;
    const hOverflow = contentRight - 1920;
    const headroom = 1080 - contentBottom;
    // кириллица: метрики глифов крупнее латиницы — требуем больше запаса (60 вместо 40)
    const warnAt = hasCyrillic(s.textContent || '') ? 60 : 40;

    let status = 'OK';
    const reasons = [];
    if (vOverflow > 0) { status = 'FAIL'; reasons.push(`переполнение по высоте +${vOverflow}px (${culprit})`); }
    if (hOverflow > 2) { status = 'FAIL'; reasons.push(`переполнение по ширине +${hOverflow}px`); }
    if (overlaps.length) { status = 'FAIL'; reasons.push(`наезжание: ${overlaps.slice(0, 3).join('; ')}`); }
    if (placeholders.size) { status = 'FAIL'; reasons.push(`плейсхолдеры: ${[...placeholders].slice(0, 3).join(' | ')}`); }
    if (status === 'OK' && headroom < warnAt) { status = 'WARN'; reasons.push(`мало запаса снизу: ${headroom}px (нужно ≥${warnAt})`); }

    out.push({ slide: i + 1, status, contentBottom, headroom, vOverflow, hOverflow, reasons });
  }
  if (stage.goToSlide) stage.goToSlide(0);

  // протёкший контент ВНЕ <deck-stage> (сломанный комментарий, мусорная разметка над/под сценой)
  const stray = [];
  const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walk.nextNode())) {
    const t = (node.textContent || '').trim();
    if (!t) continue;
    const p = node.parentElement;
    if (!p || p.closest('deck-stage')) continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(p.tagName)) continue;
    stray.push(t.slice(0, 60));
  }

  return { total, slides: out, stray };
};

// ── Запуск ──────────────────────────────────────────────────────────────────────
const ctx = await getPage();
if (!ctx) process.exit(3);

let report;
try {
  await ctx.page.goto(url, { waitUntil: 'load' });
  await ctx.page.evaluate(async () => {
    try { await customElements.whenDefined('deck-stage'); } catch {}
    if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch {} }
    await new Promise(r => setTimeout(r, 150));
  });
  report = await ctx.page.evaluate(MEASURE);
} catch (e) {
  console.error('Ошибка при замере: ' + (e.message || e));
  await ctx.close();
  process.exit(3);
}
await ctx.close();

if (report.error) { console.error('Не найден <deck-stage> в файле — это точно дека из шаблона?'); process.exit(2); }

if (JSON_OUT) { console.log(JSON.stringify(report, null, 2)); }

const fails = report.slides.filter(s => s.status === 'FAIL');
const warns = report.slides.filter(s => s.status === 'WARN');
const strayFail = report.stray && report.stray.length > 0;

if (!JSON_OUT) {
  console.log(`\n  АУДИТ ДЕКИ · движок: ${ctx.engine} · слайдов: ${report.total}\n`);
  for (const s of report.slides) {
    const mark = s.status === 'FAIL' ? '✗ FAIL' : s.status === 'WARN' ? '! WARN' : '✓ OK  ';
    const tail = s.reasons.length ? '  — ' + s.reasons.join('; ') : `  (низ ${s.contentBottom}px, запас ${s.headroom}px)`;
    console.log(`  ${mark}  слайд ${String(s.slide).padStart(2)}${tail}`);
  }
  if (strayFail) {
    console.log(`\n  ✗ FAIL  протёкший текст ВНЕ слайдов (сломанный комментарий/разметка):`);
    report.stray.slice(0, 5).forEach(t => console.log(`          «${t}»`));
  }
  console.log('');
  if (fails.length || strayFail) console.log(`  ИТОГ: ${fails.length}${strayFail ? '+1(stray)' : ''} FAIL — чинить и перезапускать. ${warns.length} WARN.`);
  else if (warns.length) console.log(`  ИТОГ: чисто, но ${warns.length} WARN (тесновато — желательно поджать).`);
  else console.log('  ИТОГ: всё чисто. Можно сдавать.');
  console.log('');
}

process.exit(fails.length || strayFail ? 1 : 0);
