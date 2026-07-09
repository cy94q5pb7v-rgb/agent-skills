# PPTX-зеркало — два режима сборки

Используется в Фазе 8 — после QA-pass на HTML.

## Когда какой режим

| Режим | Когда выбирать | Что в PPTX | Что упрощается |
|-------|---------------|-----------|----------------|
| **structural** (дефолт) | Пользователь будет редактировать pptx в PowerPoint | Текст редактируется, цвета/шрифты совпадают, layout близок | CSS-градиенты → solid fill, scroll-анимации → статика, кастомные SVG → упрощённые shapes |
| **pixel-perfect** | Пользователь не планирует редактировать pptx | Каждый слайд — полноэкранный PNG из HTML, визуально идентично | Текст не редактируется, размер файла больше |

Режим определён в `brief.md` (поле «формат вывода»). Если не указан — спроси перед запуском.

---

## Режим `structural` — Python-скрипт

Требования:
- Python 3.10+
- `pip install python-pptx`

Если пакет не установлен — установи через Bash перед запуском скрипта.

Скрипт-шаблон (адаптируй под конкретную деку, читая `final-spec.md`):

```python
"""
Зеркало HTML-презентации в PPTX (structural).

Источник истины: .p-demo/final-spec.md — структура и палитра
                 .p-demo/slides-content.md — финальные тексты
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pathlib import Path
import json
import re


# ==========================================================================
# ПАЛИТРА И ТИПОГРАФИКА — заполни из final-spec.md
# ==========================================================================

PALETTE = {
    "bg": RGBColor(0x0A, 0x0A, 0x0A),       # фон
    "fg": RGBColor(0xFA, 0xFA, 0xFA),       # текст
    "accent": RGBColor(0xFF, 0x6B, 0x35),   # акцент
    "muted": RGBColor(0x6B, 0x6B, 0x6B),    # вторичный
}

# Шрифты — system-fallback, потому что pptx не умеет CDN
FONTS = {
    "primary": "Inter",       # если не установлен — PowerPoint покажет fallback
    "fallback": "Calibri",
}

# Размеры слайда (16:9 по дефолту)
SLIDE_WIDTH_IN = 13.333
SLIDE_HEIGHT_IN = 7.5


# ==========================================================================
# СТРУКТУРА СЛАЙДОВ — заполни из final-spec.md / slides-content.md
# ==========================================================================
#
# Каждый слайд — словарь со схемой:
#   "type":  тип ("hero" | "big_number" | "two_col" | "quote" | "list" | "cta")
#   "h1":    главный заголовок
#   "body":  тело (опционально)
#   "extra": дополнительный контент (число, цитата, имя, и т.д.)

SLIDES = [
    # Заполняется автоматически или вручную из final-spec.md.
    # Пример:
    # {"type": "hero", "h1": "Y решает X быстрее на 10×", "body": None, "extra": None},
    # {"type": "big_number", "h1": "$5M ARR", "body": "за 18 месяцев", "extra": None},
    # {"type": "quote", "h1": "Без Y мы тратили 4 часа в день на ручную работу.", "extra": "— CTO Acme"},
    # {"type": "cta", "h1": "Запишитесь на демо за 15 минут", "extra": "demo.acme.com"},
]


# ==========================================================================
# РЕНДЕРЕРЫ ПОД ТИПЫ СЛАЙДОВ
# ==========================================================================

def add_blank_slide(prs):
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide, PALETTE["bg"])
    return slide


def set_slide_bg(slide, color: RGBColor):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(slide, left, top, width, height, text, *,
                font_size=Pt(32), bold=False, color=None, align=PP_ALIGN.LEFT,
                font_name=None):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    f = run.font
    f.size = font_size
    f.bold = bold
    f.name = font_name or FONTS["primary"]
    if color:
        f.color.rgb = color
    return tb


def render_hero(prs, slide_data):
    slide = add_blank_slide(prs)
    add_textbox(
        slide,
        Inches(1), Inches(2.5),
        Inches(SLIDE_WIDTH_IN - 2), Inches(3),
        slide_data["h1"],
        font_size=Pt(64), bold=True,
        color=PALETTE["fg"], align=PP_ALIGN.LEFT,
    )
    if slide_data.get("body"):
        add_textbox(
            slide,
            Inches(1), Inches(5.2),
            Inches(SLIDE_WIDTH_IN - 2), Inches(1),
            slide_data["body"],
            font_size=Pt(24),
            color=PALETTE["muted"], align=PP_ALIGN.LEFT,
        )


def render_big_number(prs, slide_data):
    slide = add_blank_slide(prs)
    add_textbox(
        slide,
        Inches(0), Inches(2),
        Inches(SLIDE_WIDTH_IN), Inches(3),
        slide_data["h1"],
        font_size=Pt(180), bold=True,
        color=PALETTE["accent"], align=PP_ALIGN.CENTER,
    )
    if slide_data.get("body"):
        add_textbox(
            slide,
            Inches(0), Inches(5.5),
            Inches(SLIDE_WIDTH_IN), Inches(1),
            slide_data["body"],
            font_size=Pt(28),
            color=PALETTE["fg"], align=PP_ALIGN.CENTER,
        )


def render_two_col(prs, slide_data):
    slide = add_blank_slide(prs)
    add_textbox(slide, Inches(1), Inches(0.8), Inches(SLIDE_WIDTH_IN - 2), Inches(1),
                slide_data["h1"], font_size=Pt(40), bold=True, color=PALETTE["fg"])
    left, right = slide_data.get("body", ["", ""])
    add_textbox(slide, Inches(1), Inches(2.5), Inches(5.5), Inches(4),
                left, font_size=Pt(22), color=PALETTE["fg"])
    add_textbox(slide, Inches(7), Inches(2.5), Inches(5.5), Inches(4),
                right, font_size=Pt(22), color=PALETTE["fg"])


def render_quote(prs, slide_data):
    slide = add_blank_slide(prs)
    add_textbox(
        slide, Inches(1.5), Inches(2),
        Inches(SLIDE_WIDTH_IN - 3), Inches(3.5),
        f'«{slide_data["h1"]}»',
        font_size=Pt(40), color=PALETTE["fg"], align=PP_ALIGN.LEFT,
    )
    if slide_data.get("extra"):
        add_textbox(
            slide, Inches(1.5), Inches(5.5),
            Inches(SLIDE_WIDTH_IN - 3), Inches(0.8),
            slide_data["extra"],
            font_size=Pt(20), color=PALETTE["muted"], align=PP_ALIGN.LEFT,
        )


def render_list(prs, slide_data):
    slide = add_blank_slide(prs)
    add_textbox(slide, Inches(1), Inches(0.8), Inches(SLIDE_WIDTH_IN - 2), Inches(1),
                slide_data["h1"], font_size=Pt(40), bold=True, color=PALETTE["fg"])
    items = slide_data.get("body", [])
    tb = slide.shapes.add_textbox(Inches(1), Inches(2.2),
                                   Inches(SLIDE_WIDTH_IN - 2), Inches(4.5))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"— {item}"
        p.runs[0].font.size = Pt(24)
        p.runs[0].font.color.rgb = PALETTE["fg"]
        p.runs[0].font.name = FONTS["primary"]
        p.space_after = Pt(12)


def render_cta(prs, slide_data):
    slide = add_blank_slide(prs)
    add_textbox(
        slide, Inches(1), Inches(2.5),
        Inches(SLIDE_WIDTH_IN - 2), Inches(2),
        slide_data["h1"],
        font_size=Pt(56), bold=True, color=PALETTE["fg"], align=PP_ALIGN.LEFT,
    )
    if slide_data.get("extra"):
        add_textbox(
            slide, Inches(1), Inches(5),
            Inches(SLIDE_WIDTH_IN - 2), Inches(1),
            slide_data["extra"],
            font_size=Pt(28), color=PALETTE["accent"], align=PP_ALIGN.LEFT,
        )


RENDERERS = {
    "hero": render_hero,
    "big_number": render_big_number,
    "two_col": render_two_col,
    "quote": render_quote,
    "list": render_list,
    "cta": render_cta,
}


# ==========================================================================
# СБОРКА
# ==========================================================================

def build(output_path: str = "presentation.pptx"):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_HEIGHT_IN)

    for slide_data in SLIDES:
        renderer = RENDERERS.get(slide_data["type"])
        if not renderer:
            print(f"[!] Неизвестный тип слайда: {slide_data['type']}")
            continue
        renderer(prs, slide_data)

    prs.save(output_path)
    print(f"[+] PPTX сохранён: {output_path} ({len(SLIDES)} слайдов)")


if __name__ == "__main__":
    build()
```

**Алгоритм работы для Claude:**

1. Прочитай `final-spec.md` и `slides-content.md`.
2. Скопируй шаблон выше в `.p-demo/build_pptx.py`.
3. Заполни:
   - `PALETTE` — точными HEX из спеки (через `RGBColor(0xXX, 0xYY, 0xZZ)`).
   - `FONTS` — имя шрифта из спеки (с system-fallback, потому что pptx не умеет CDN — Inter → Calibri/Aptos если у получателя нет Inter).
   - `SLIDE_WIDTH_IN/HEIGHT_IN` — из брифа (16:9 = 13.333×7.5; 4:3 = 10×7.5; A4-портрет = 8.27×11.69).
   - `SLIDES` — массив словарей по каждому слайду из спеки. Для каждого определи `type`, заполни `h1`, `body`, `extra`.
4. Если в спеке есть тип слайда, которого нет в `RENDERERS` (например, диаграмма, timeline, продуктовый скриншот) — допиши свой рендерер, опираясь на `python-pptx`-API:
   - Прямоугольники: `slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, ...)`
   - Линии: `slide.shapes.add_connector(...)`
   - Картинки: `slide.shapes.add_picture(path, ...)` — если в HTML был `<img>` или сложный SVG, можно заранее экспортировать в PNG и вставить.
5. Запусти скрипт: `python .p-demo/build_pptx.py`.
6. Открой результат в PowerPoint (или LibreOffice Impress) и сравни с HTML слайд-за-слайдом.
7. Зафиксируй компромиссы в `qa-report.md`: что упростилось, почему.

---

## Режим `pixel-perfect` — Playwright-скрипт

Требования:
- Python 3.10+
- `pip install playwright python-pptx`
- `playwright install chromium`

Шаблон скрипта (`.p-demo/build_pptx_pixel.py`):

```python
"""
Зеркало HTML-презентации в PPTX (pixel-perfect).

Рендерит каждый <section> из HTML в PNG через headless Chromium
и вставляет PNG-картинки полноэкранно в PPTX-слайды.
"""

from playwright.sync_api import sync_playwright
from pptx import Presentation
from pptx.util import Inches
from pathlib import Path
import os


HTML_FILE = "presentation.html"
PPTX_FILE = "presentation.pptx"
SCREENSHOTS_DIR = Path(".p-demo/screenshots")
VIEWPORT = {"width": 1920, "height": 1080}
SLIDE_WIDTH_IN = 13.333  # 16:9
SLIDE_HEIGHT_IN = 7.5


def capture_slides() -> list[Path]:
    """Открывает HTML, скроллит по секциям, делает скриншоты."""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    screenshots = []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport=VIEWPORT, device_scale_factor=2)
        page = context.new_page()

        html_path = Path(HTML_FILE).resolve().as_uri()
        page.goto(html_path)
        page.wait_for_load_state("networkidle")

        sections = page.locator("section, main > section, .slide").all()
        if not sections:
            sections = page.locator("section").all()

        for i, section in enumerate(sections, start=1):
            section.scroll_into_view_if_needed()
            page.wait_for_timeout(300)  # дать анимациям/шрифтам отрисоваться
            shot_path = SCREENSHOTS_DIR / f"slide_{i:02d}.png"
            page.screenshot(path=str(shot_path), clip={
                "x": 0, "y": 0,
                "width": VIEWPORT["width"],
                "height": VIEWPORT["height"],
            })
            screenshots.append(shot_path)
            print(f"[+] Slide {i}: {shot_path}")

        browser.close()

    return screenshots


def build_pptx(screenshots: list[Path]):
    prs = Presentation()
    prs.slide_width = Inches(SLIDE_WIDTH_IN)
    prs.slide_height = Inches(SLIDE_HEIGHT_IN)

    blank_layout = prs.slide_layouts[6]

    for shot in screenshots:
        slide = prs.slides.add_slide(blank_layout)
        slide.shapes.add_picture(
            str(shot),
            Inches(0), Inches(0),
            width=Inches(SLIDE_WIDTH_IN),
            height=Inches(SLIDE_HEIGHT_IN),
        )

    prs.save(PPTX_FILE)
    print(f"[+] PPTX (pixel-perfect): {PPTX_FILE} ({len(screenshots)} слайдов)")


if __name__ == "__main__":
    shots = capture_slides()
    build_pptx(shots)
```

**Алгоритм работы для Claude:**

1. Убедись, что `presentation.html` существует и прошёл QA.
2. Установи зависимости: `pip install playwright python-pptx && playwright install chromium`.
3. Скопируй шаблон в `.p-demo/build_pptx_pixel.py`.
4. При необходимости адаптируй селектор секций (по дефолту `section`).
5. Запусти: `python .p-demo/build_pptx_pixel.py`.
6. Открой PPTX, проверь, что все слайды — PNG-шотами в полный экран, без полей.
7. В `qa-report.md` отметь: текст в pptx нередактируется, но визуал идентичен HTML.

---

## Сравнение: что делать если PPTX выглядит хуже HTML

В режиме structural — это нормально и ожидаемо. CSS-градиенты, scroll-анимации, нестандартная типографическая компоновка через CSS Grid не имеют точных аналогов в PPTX. Допустимые компромиссы:

- Градиенты → solid fill (выбрать средний оттенок) или применить `gradient_stops` через python-pptx (поддерживается частично).
- Кастомные SVG → SimplifiedShape или экспортировать SVG в PNG и вставить.
- Scroll-анимации → статика (это нарратив, а не визуал).
- Custom-шрифты не у получателя → fallback на Calibri/Aptos.

Если расхождение слишком большое и заказчику важен визуал — переключайся на `pixel-perfect`.

Если расхождение слишком большое и заказчик хочет редактировать — гибрид: основные слайды в structural, пиковые слайды — как PNG-вставка через `add_picture`.
