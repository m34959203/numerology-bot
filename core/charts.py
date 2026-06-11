"""Визуальные графики отчёта (reportlab.graphics → Drawing для PDF).

Воспроизводят встроенные графики книги «МАТРИЦА» (лист РАСЧЕТ / 19), которые
заказчица просила показывать в боте:
- «График жизненных сил по годам» — энергокривая по возрасту (Matr!BE59:BE158);
- «График жизненной энергии» — 6 цифр кода жизни (лист 19, F21:K21).

Без внешних зависимостей: только reportlab (уже в стеке). Палитра и шрифты
синхронизированы с core.pdf. Числовые ряды берутся из core.numerology.matrix
(сверено с книгой 1:1), здесь — только отрисовка.
"""

from __future__ import annotations

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors

# палитра — та же, что в core.pdf (дублируем, чтобы не плодить циклический импорт)
_INK = colors.HexColor("#1E2340")
_ACCENT = colors.HexColor("#A8761F")
_MUTED = colors.HexColor("#6B6E84")
_RULE = colors.HexColor("#E2DACB")


def life_force_curve(curve: list[float], font: str, *, width: float = 462, height: float = 150):
    """«График жизненных сил по годам» — линия энергии по возрасту (0..N).

    curve — энергокривая (matrix.energy_curve). Подписи оси X — каждые 10 лет.
    """
    d = Drawing(width, height)
    lp = LinePlot()
    lp.x, lp.y = 28, 24
    lp.width, lp.height = width - 44, height - 44
    lp.data = [[(age, val) for age, val in enumerate(curve)]]
    lp.lines[0].strokeColor = _ACCENT
    lp.lines[0].strokeWidth = 1.6
    lp.joinedLines = 1
    lp.xValueAxis.valueMin = 0
    lp.xValueAxis.valueMax = len(curve) - 1
    lp.xValueAxis.valueStep = 10
    lp.xValueAxis.labels.fontName = font
    lp.xValueAxis.labels.fontSize = 7
    lp.xValueAxis.labels.fillColor = _MUTED
    lp.xValueAxis.strokeColor = _RULE
    lp.yValueAxis.valueMin = 0
    lp.yValueAxis.valueMax = 9
    lp.yValueAxis.valueStep = 3
    lp.yValueAxis.labels.fontName = font
    lp.yValueAxis.labels.fontSize = 7
    lp.yValueAxis.labels.fillColor = _MUTED
    lp.yValueAxis.strokeColor = _RULE
    lp.yValueAxis.gridStrokeColor = _RULE
    lp.yValueAxis.visibleGrid = 1
    d.add(lp)
    d.add(String(0, height - 10, "возраст →", fontName=font, fontSize=7, fillColor=_MUTED))
    return d


def life_code_energy(digits: list[int], font: str, *, width: float = 462, height: float = 150):
    """«График жизненной энергии» — столбцы 6 цифр кода жизни (лист 19)."""
    d = Drawing(width, height)
    bc = VerticalBarChart()
    bc.x, bc.y = 28, 22
    bc.width, bc.height = width - 44, height - 40
    bc.data = [list(digits)]
    bc.categoryAxis.categoryNames = [str(i + 1) for i in range(len(digits))]
    bc.categoryAxis.labels.fontName = font
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.fillColor = _MUTED
    bc.categoryAxis.strokeColor = _RULE
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 9
    bc.valueAxis.valueStep = 3
    bc.valueAxis.labels.fontName = font
    bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.labels.fillColor = _MUTED
    bc.valueAxis.strokeColor = _RULE
    bc.bars[0].fillColor = _ACCENT
    bc.bars[0].strokeColor = colors.white
    bc.barLabels.fontName = font
    bc.barLabels.fontSize = 9
    bc.barLabels.fillColor = _INK
    bc.barLabelFormat = "%d"
    bc.barLabels.dy = 6
    d.add(bc)
    d.add(String(0, height - 10, "позиция кода →", fontName=font, fontSize=7, fillColor=_MUTED))
    return d
