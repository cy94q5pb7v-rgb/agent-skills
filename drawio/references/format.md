# Шпаргалка по формату .drawio (mxGraph XML)

Это справочник для генерации валидных файлов draw.io / diagrams.net вручную. Формат — XML на базе библиотеки mxGraph.

## Общая структура

```xml
<mxfile host="app.diagrams.net" agent="Claude" version="22.1.0">
  <diagram id="page1" name="Имя вкладки">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1"
                  tooltips="1" connect="1" arrows="1" fold="1" page="1"
                  pageScale="1" pageWidth="1600" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <!-- здесь узлы и связи -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

- `<mxfile>` — корень. Может содержать несколько `<diagram>` (вкладки/страницы).
- `<mxGraphModel>` — холст. `pageWidth`/`pageHeight` — размер страницы в px.
- `<root>` обязан начинаться с двух служебных ячеек: `id="0"` (корень) и `id="1"` (слой по умолчанию, `parent="0"`). Все видимые элементы — потомки `1` (или контейнера).
- Несколько страниц: повторяй блок `<diagram>` с уникальными `id`.

## Узел (vertex)

```xml
<mxCell id="n1" value="Текст" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        vertex="1" parent="1">
  <mxGeometry x="80" y="80" width="160" height="60" as="geometry"/>
</mxCell>
```

- `id` — уникальный (любая строка). `value` — видимый текст.
- `vertex="1"` — это узел. `parent` — id родителя (`1` или id контейнера).
- `<mxGeometry>` — позиция и размер. `x,y` — левый-верхний угол. **Если parent — контейнер, координаты ОТНОСИТЕЛЬНЫ контейнера.**

## Связь (edge)

```xml
<mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;"
        edge="1" parent="1" source="n1" target="n2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

- `edge="1"`, `source`/`target` — id соединяемых узлов.
- `<mxGeometry relative="1">` обязателен.
- Подпись на стрелке: добавь `value="Да"` в этот же `mxCell`, либо отдельную дочернюю метку.
- Зафиксировать точки входа/выхода: `exitX`,`exitY`,`entryX`,`entryY` (0..1 по краю узла) в style.

## Контейнер (swimlane / группа)

```xml
<mxCell id="grp" value="Слой приложения"
        style="swimlane;rounded=1;html=1;startSize=30;fillColor=#f5f5f5;strokeColor=#666666;swimlaneFillColor=#ffffff;collapsible=0;"
        vertex="1" parent="1">
  <mxGeometry x="40" y="120" width="600" height="300" as="geometry"/>
</mxCell>
<!-- дочерний узел: координаты ОТНОСИТЕЛЬНО контейнера grp -->
<mxCell id="inner" value="Сервис A" style="rounded=1;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        vertex="1" parent="grp">
  <mxGeometry x="20" y="50" width="160" height="60" as="geometry"/>
</mxCell>
```

- `swimlane` = контейнер с заголовком. `startSize` — высота полосы заголовка.
- `collapsible=0` — запретить сворачивание.

## Частые стили (style-строки)

Стиль — это набор `ключ=значение;` через точку с запятой.

| Фигура | style |
|---|---|
| Прямоугольник (скруглённый) | `rounded=1;whiteSpace=wrap;html=1;` |
| Прямоугольник (острый) | `whiteSpace=wrap;html=1;` |
| Ромб (решение) | `rhombus;whiteSpace=wrap;html=1;` |
| Эллипс / круг | `ellipse;whiteSpace=wrap;html=1;` |
| Скруглённый старт/конец | `rounded=1;arcSize=40;whiteSpace=wrap;html=1;` |
| Параллелограмм (ввод/вывод) | `shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;` |
| Цилиндр (БД) | `shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;` |
| Текст без рамки | `text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;` |
| Облако | `ellipse;shape=cloud;whiteSpace=wrap;html=1;` |
| Актёр (человечек) | `shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;` |

Полезные модификаторы стиля:
- `fillColor=#hex;strokeColor=#hex;fontColor=#hex;`
- `fontSize=12;fontStyle=1;` (1=жирный, 2=курсив, 4=подчёркнутый, суммируются)
- `align=center|left|right;verticalAlign=middle|top|bottom;`
- `dashed=1;` — пунктир. `strokeWidth=2;` — толщина.
- `arcSize=10;` — радиус скругления (в % при `rounded=1`).

## Стили связей (edgeStyle)

| Тип | style |
|---|---|
| Ортогональная (углы 90°) | `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;` |
| Прямая | `edgeStyle=none;html=1;` |
| Скруглённая ортогональная | `edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;` |
| Ступенчатая | `edgeStyle=entityRelationEdgeStyle;html=1;` |

Стрелки на концах: `startArrow=`/`endArrow=` со значениями `none`, `classic`, `open`, `block`, `diamond`, `oval`. Для UML/ER: `endArrow=ERmany`, `startArrow=ERone` и т.п.

## ER-диаграмма (таблица)

```xml
<mxCell id="tbl" value="users"
        style="shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;fillColor=#dae8fc;strokeColor=#6c8ebf;"
        vertex="1" parent="1">
  <mxGeometry x="80" y="80" width="200" height="120" as="geometry"/>
</mxCell>
<mxCell id="row1" value="" style="shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;strokeColor=inherit;fillColor=none;collapsible=0;" vertex="1" parent="tbl">
  <mxGeometry y="30" width="200" height="30" as="geometry"/>
</mxCell>
<mxCell id="c1" value="id (PK)" style="shape=partialRectangle;html=1;overflow=hidden;fillColor=none;strokeColor=inherit;align=left;spacingLeft=6;" vertex="1" parent="row1">
  <mxGeometry width="200" height="30" as="geometry"/>
</mxCell>
```

Проще: для лёгких ER рисуй сущности обычными прямоугольниками с полями через `\n`, а кардинальность подписывай на связях.

## Экранирование текста

В `value` спецсимволы XML экранируй:
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` внутри атрибута → `&quot;`

Перенос строки в тексте узла: настоящий символ новой строки внутри значения **или** `&#10;`. При `html=1` можно `<br>`.

## Координатная дисциплина

- `gridSize="10"` — сетка 10px. Делай координаты кратными 20–40.
- Узел: ширина `160–240`, высота `60–80` (обычный); контейнер — по содержимому.
- Колонки: шаг по `x` = ширина узла + `40…80` (т.е. `+200…+280`).
- Ряды: шаг по `y` = высота узла + `60…100` (т.е. `+120…+160`).
- Оставляй поле ~`40px` от края страницы.
- Считай `pageWidth/pageHeight` так, чтобы вся диаграмма помещалась с запасом.

## Несколько страниц

```xml
<mxfile ...>
  <diagram id="p1" name="Обзор"> ... </diagram>
  <diagram id="p2" name="Детали"> ... </diagram>
</mxfile>
```

Каждая `<diagram>` — отдельная вкладка в draw.io со своим `<mxGraphModel>`.

## Библиотечные фигуры (mxgraph.*)

draw.io содержит тысячи готовых иконок (AWS, GCP, Azure, сети, UML, BPMN). Вызов через `shape=mxgraph.<библиотека>.<фигура>`, например:
- `shape=mxgraph.aws4.lambda;`
- `shape=mxgraph.networks.server;`
Используй умеренно — для технических схем они узнаваемы, но не перегружай.
