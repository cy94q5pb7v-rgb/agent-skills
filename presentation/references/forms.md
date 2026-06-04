# Галерея форм слайдов

**Как пользоваться (важно):** у каждого слайда в плане есть поле **«что показать по сути»**. Найди здесь раздел под это «что показать», выбери **ЛУЧШУЮ** форму из 1–4 вариантов, **скопируй её `<section>` ЦЕЛИКОМ** (вместе с рамкой `.fr`), замени плейсхолдеры на реальный контент. Не листай всю галерею — иди сразу в нужный раздел по типу контента.

Правила для всех: соседние слайды — **разные** формы; числа — **только из «Реестра данных»** плана; крупный текст помечай `data-fit`; `.pg` оставляй пустым (движок проставит номер); `.sec` и левую подпись в `.fr` меняй по смыслу. Все формы непротекаемые (поля 132/118, ~590px под контент). Стиль — Сбер (`:root` не трогай).

> Рамка `.fr` во всех сниппетах одинаковая — меняется только текст `.sec` и левая подпись. На тёмных слайдах добавляй класс `invert` к `<section>`.

---

## Обложка / титул — слайд 1 (и финал)

Всегда первым слайдом. Тёмно-зелёная, с фирменным кругом-мотивом.

```html
<section class="layout-cover invert">
  <div class="ring" data-decorative style="width:680px;height:680px;right:-170px;top:-190px;"></div>
  <div class="disc" data-decorative style="width:430px;height:430px;right:-40px;top:-60px;"></div>
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Раздел</span></div><div class="fr-bot"><span>Подзаголовок</span><span class="pg"></span></div></div>
  <p class="kicker">Кикер</p>
  <h1 data-fit data-fit-min="64">Главная мысль одной фразой</h1>
  <p class="sub">Короткое пояснение: для кого и о чём.</p>
</section>
```
Финал — то же, но мотив в другом углу (`left:-200px;bottom:-220px`) и `.kicker` «Что дальше», заголовок-вывод + действие.

## Одна мысль (тезис)

Когда слайд = одна сильная фраза. Воздух уместен (не штрафуется).

```html
<section class="layout-statement">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Главное</span></div><div class="fr-bot"><span>Тезис</span><span class="pg"></span></div></div>
  <div class="bar"></div>
  <p class="lead" data-fit data-fit-min="52">Одна сильная мысль крупно — её видно за 3 секунды.</p>
</section>
```

## Перечень аспектов (2–4 пункта)

**Вариант А — редакционные колонки** (предпочтительно для 3 аспектов):
```html
<section class="layout-cols">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Подход</span></div><div class="fr-bot"><span>Аспекты</span><span class="pg"></span></div></div>
  <div><p class="kicker">Подход</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2></div>
  <div class="cols"><!-- .cols.two для двух -->
    <div class="col"><div class="idx">01</div><div class="ct"><h3>Аспект</h3><p>Коротко, по делу.</p></div></div>
    <div class="col"><div class="idx">02</div><div class="ct"><h3>Аспект</h3><p>Коротко, по делу.</p></div></div>
    <div class="col"><div class="idx">03</div><div class="ct"><h3>Аспект</h3><p>Коротко, по делу.</p></div></div>
  </div>
</section>
```

**Вариант Б — карточки:**
```html
<section class="layout-cards">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Состав</span></div><div class="fr-bot"><span>Состав</span><span class="pg"></span></div></div>
  <div><p class="kicker">Состав</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2></div>
  <div class="cards"><!-- .cards.two для двух -->
    <div class="card"><h3>Первое</h3><p>Что это и зачем.</p></div>
    <div class="card"><h3>Второе</h3><p>Что это и зачем.</p></div>
    <div class="card"><h3>Третье</h3><p>Что это и зачем.</p></div>
  </div>
</section>
```

## Числа

**Вариант А — ряд крупных чисел** (2–3 метрики):
```html
<section class="layout-stats">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">В цифрах</span></div><div class="fr-bot"><span>Результат</span><span class="pg"></span></div></div>
  <div><p class="kicker">Результат</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2></div>
  <div class="stats">
    <div class="stat"><div class="num" data-fit data-fit-min="56">2×</div><div class="lab">подпись</div></div>
    <div class="stat"><div class="num" data-fit data-fit-min="56">−40%</div><div class="lab">подпись</div></div>
    <div class="stat"><div class="num" data-fit data-fit-min="56">12 млн</div><div class="lab">подпись</div></div>
  </div>
</section>
```

**Вариант Б — одно гигантское число (герой)** (когда ОДНА цифра и есть вся суть):
```html
<section class="layout-hero">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Главная метрика</span></div><div class="fr-bot"><span>Итог</span><span class="pg"></span></div></div>
  <p class="kicker">Кикер</p>
  <div class="huge" data-fit data-fit-min="120">87%</div>
  <p class="cap">Что это за число и почему важно — одной строкой.</p>
</section>
```

**Вариант В — горизонтальный график** (доли/сравнение величин; `width` бара = доля от максимума):
```html
<section class="layout-chart">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Структура</span></div><div class="fr-bot"><span>В долях</span><span class="pg"></span></div></div>
  <div><p class="kicker">Структура</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод по данным</h2></div>
  <div class="chart"><!-- 3–5 строк -->
    <div class="bar-row"><div class="blab">Категория</div><div class="bar-track"><div class="bar-fill" style="width:82%"></div></div><div class="bval">82%</div></div>
    <div class="bar-row"><div class="blab">Категория</div><div class="bar-track"><div class="bar-fill" style="width:64%"></div></div><div class="bval">64%</div></div>
    <div class="bar-row"><div class="blab">Категория</div><div class="bar-track"><div class="bar-fill" style="width:41%"></div></div><div class="bval">41%</div></div>
  </div>
</section>
```

## Сравнение / было → стало

```html
<section class="layout-compare">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Сравнение</span></div><div class="fr-bot"><span>Было → стало</span><span class="pg"></span></div></div>
  <div><p class="kicker">Сравнение</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2></div>
  <div class="compare">
    <div class="col2"><h3>Было</h3><ul><li>пункт</li><li>пункт</li></ul></div>
    <div class="col2 win"><h3>Стало</h3><ul><li>пункт</li><li>пункт</li></ul></div>
  </div>
</section>
```

## Процесс / этапы

**Вариант А — нумерованные шаги (вертикально):**
```html
<section class="layout-list">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Как это работает</span></div><div class="fr-bot"><span>Шаги</span><span class="pg"></span></div></div>
  <div><p class="kicker">Процесс</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2></div>
  <ul class="list">
    <li><span class="n">01</span><span class="t">Шаг и его результат.</span></li>
    <li><span class="n">02</span><span class="t">Шаг и его результат.</span></li>
    <li><span class="n">03</span><span class="t">Шаг и его результат.</span></li>
  </ul>
</section>
```

**Вариант Б — таймлайн (горизонтально, хронология/этапы):**
```html
<section class="layout-timeline">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Хронология</span></div><div class="fr-bot"><span>Этапы</span><span class="pg"></span></div></div>
  <div><p class="kicker">Дорожная карта</p><h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2></div>
  <div class="timeline"><!-- число шагов = число .tstep -->
    <div class="tstep"><div class="dot"></div><h3>Этап 1</h3><p>Что происходит.</p></div>
    <div class="tstep"><div class="dot"></div><h3>Этап 2</h3><p>Что происходит.</p></div>
    <div class="tstep"><div class="dot"></div><h3>Этап 3</h3><p>Что происходит.</p></div>
    <div class="tstep"><div class="dot"></div><h3>Этап 4</h3><p>Что происходит.</p></div>
  </div>
</section>
```

## Текст + визуал

Слева текст, справа место под реальный скриншот/схему (НЕ AI-картинку — `.ph` плейсхолдер).
```html
<section class="layout-split">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Контекст</span></div><div class="fr-bot"><span>Подпись слева</span><span class="pg"></span></div></div>
  <div>
    <p class="kicker">Кикер</p>
    <h2 class="title" data-fit data-fit-min="40">Заголовок-вывод</h2>
    <p class="body">2–3 строки конкретики: цифры, факты по делу.</p>
  </div>
  <div class="ph">МЕСТО ПОД ВИЗУАЛ<br>(реальный скриншот/схему — спроси у пользователя)</div>
</section>
```

## Цитата / ключевой вывод

Тёмный акцентный слайд для ритма. Воздух уместен.
```html
<section class="layout-quote invert">
  <div class="fr" data-decorative><div class="fr-top"><span class="wm"><span class="dot"></span>Сбер</span><span class="sec">Цитата</span></div><div class="fr-bot"><span>Вывод</span><span class="pg"></span></div></div>
  <blockquote data-fit data-fit-min="36">«Сильная цитата или ключевой вывод».</blockquote>
  <div class="by">— Источник</div>
</section>
```

---

## Шпаргалка: «что показать» → форма

| Что показать по сути | Бери форму |
|---|---|
| главная мысль деки (слайд 1) | Обложка |
| одна сильная фраза | Тезис |
| 2–4 аспекта/составляющих | Колонки / Карточки |
| метрики (2–3 числа) | Ряд чисел |
| одно ключевое число | Герой-число |
| доли / сравнение величин | График |
| было → стало, мы vs они | Сравнение |
| шаги процесса | Список шагов / Таймлайн |
| текст + скриншот/схема | Текст + визуал |
| цитата / вывод | Цитата |

Не подходит ни одна точно — возьми ближайшую и **адаптируй/комбинируй** (формы можно собирать на тех же принципах: рамка `.fr`, поля, `data-fit`, заполнение кадра).
