#!/usr/bin/env python3
"""生成 docs/bom/bom-list.svg（纯 SVG，零依赖）。

用法：
    python3 docs/bom/generate.py

截图：
    用 Chrome/Edge 打开 bom-list.svg 后截图，或参见 docs/bom/README.md
    中的 headless 命令生成 bom-list.png。
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).with_name("bom-list.svg")

W, H = 1400, 1440
INK = "#16222f"
SUB = "#5b6b7c"
FAINT = "#8b98a6"
LINE = "#dbe3ec"
BLUE = "#1f6feb"
GREEN = "#2e7d4f"
ORANGE = "#a85b1a"
RED = "#b3261e"
PURPLE = "#6b4fa3"

FONT = ("system-ui, -apple-system, 'Segoe UI', 'Microsoft YaHei', "
        "'PingFang SC', sans-serif")


def text(x, y, s, size=14, fill=INK, anchor="start", weight=400,
         opacity=1, spacing=None):
    extra = ' letter-spacing="%s"' % spacing if spacing is not None else ""
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" '
            'font-weight="%s" opacity="%s"%s>%s</text>'
            % (x, y, size, fill, anchor, weight, opacity, extra, escape(str(s))))


def rect(x, y, w, h, fill="none", stroke="none", sw=2, rx=0):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" '
            'stroke="%s" stroke-width="%s"/>'
            % (x, y, w, h, rx, fill, stroke, sw))


def line(x1, y1, x2, y2, stroke=LINE, sw=1):
    return ('<path d="M%s %s L%s %s" fill="none" stroke="%s" '
            'stroke-width="%s" stroke-linecap="round"/>'
            % (x1, y1, x2, y2, stroke, sw))


def pill(x, y, label, color, fill, w=62, h=24):
    return (rect(x, y, w, h, fill=fill, stroke=color, sw=1.2, rx=12)
            + text(x + w / 2, y + 16, label, 11.5, color, "middle", 700))


ROWS = [
    ("主控", "Arduino Pro Mini（ATmega328P）", "1",
     ["5V / 16MHz；FQBN 使用 cpu=16MHzatmega328"], BLUE, "#e8f0fe"),
    ("显示", "OLED 0.96\" SSD1306 128×64 I2C", "1",
     ["地址 0x3C；若为 SH1106 或 0x3D 需调整驱动"], GREEN, "#eaf5ee"),
    ("输入", "EC11 旋转编码器（带按键）", "1",
     ["A / B / SW + COM；公共脚接 GND"], GREEN, "#eaf5ee"),
    ("传感", "NTC 10kΩ B3950 防水探头", "5",
     ["25℃ 标称 10kΩ；B 值 3950；线长按柜体选"], ORANGE, "#fdf1e5"),
    ("传感", "金属膜电阻 10kΩ 1% 1/4W", "5",
     ["每路一只上拉；VCC → ADC → NTC → GND"], ORANGE, "#fdf1e5"),
    ("执行", "固态继电器 SSR（DC 控 AC）", "5",
     ["输入 3–32V DC；输出 24–380V AC", "按加热器电流 ≥2 倍选型，并配散热片"], RED, "#fdecea"),
    ("电源", "5V/1A 稳压电源适配器", "1",
     ["独立 5V 直供 VCC；或 7–12V 接 RAW"], PURPLE, "#f0edf8"),
    ("烧录", "USB-TTL（CH340 / CP2102 / FT232）", "1",
     ["5V 电平；需 DTR 自动复位或手动按 RST"], BLUE, "#e8f0fe"),
    ("保护", "220V 保险丝 / 断路器", "1",
     ["按总负载电流选择；强电侧安装"], RED, "#fdecea"),
    ("接线", "5.08mm 接线端子 2P / 3P", "若干",
     ["SSR、电源、加热器接线"], SUB, "#f1f4f7"),
    ("线材", "弱电线 22–24AWG / 强电线 18–20AWG", "若干",
     ["强弱电分开走线，避免并行缠绕"], SUB, "#f1f4f7"),
    ("辅料", "热缩管、杜邦线、扎带", "若干",
     ["绝缘、跳线与线束整理"], SUB, "#f1f4f7"),
    ("可选", "SSR 散热片 / 外壳 / 通风扇", "可选",
     ["按柜体结构与散热需求配置"], SUB, "#f1f4f7"),
]

CARD = [
    ("5", "路独立测温", BLUE),
    ("5", "路 SSR 加热", RED),
    ("5V", "主控 / 逻辑电平", PURPLE),
    ("0x3C", "OLED I2C 地址", GREEN),
]


def build():
    b = []
    b.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" font-family="%s">'
             % (W, H, W, H, FONT))
    b.append("<title>五路温控系统物料清单</title>")
    b.append('<defs><linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
             '<stop offset="0" stop-color="#1f6feb"/>'
             '<stop offset="0.55" stop-color="#2e7d4f"/>'
             '<stop offset="1" stop-color="#d97706"/></linearGradient></defs>')
    b.append(rect(0, 0, W, H, fill="#ffffff"))
    b.append(rect(0, 0, W, 9, fill="url(#bar)"))

    # 页眉
    b.append(text(64, 62, "BILL OF MATERIALS · TEMP_CONTROL", 12, FAINT, weight=700, spacing=1.6))
    b.append(text(64, 116, "五路温控系统 · 物料清单", 38, INK, weight=700))
    b.append(text(64, 151,
                  "Arduino Pro Mini 5V/16MHz · 5 路 NTC 测温 · 5 路 SSR 加热 · OLED + 旋转编码器",
                  15, SUB))
    b.append(text(64, 176, "可用于爬柜、孵化箱、恒温箱等需要多点独立控温的场景", 13, SUB))

    # 页眉标签
    tags = [("BOM v1.0", 940, 54), ("2026-11", 1060, 42), ("firmware/temp_control", 1140, 190)]
    for label, x, w in tags:
        b.append(rect(x, 186, w, 28, fill="#f6f8fb", stroke=LINE, sw=1, rx=14))
        b.append(text(x + w / 2, 205, label, 11.5, SUB, "middle", 600))

    # 概览卡片
    for i, (big, label, color) in enumerate(CARD):
        x = 64 + i * 324
        b.append(rect(x, 238, 300, 86, fill="#f8fafc", stroke=LINE, sw=1.2, rx=12))
        b.append(rect(x, 238, 5, 86, fill=color, rx=2))
        b.append(text(x + 22, 288, big, 30, color, weight=700))
        b.append(text(x + 122, 284, label, 12.6, SUB, weight=600))

    # 表头
    b.append(text(64, 372, "核心物料清单", 19, INK, weight=700))
    b.append(text(228, 371, f"共 {len(ROWS)} 项 · 数量按 5 路配置", 12, FAINT))

    table_x, table_w = 64, 1272
    header_y, header_h = 392, 44
    b.append(rect(table_x, header_y, table_w, header_h, fill=INK, rx=8))
    heads = [
        (86, "#", "middle"),
        (154, "类别", "middle"),
        (212, "物料 / 规格", "start"),
        (656, "数量", "middle"),
        (704, "选型与备注", "start"),
    ]
    for x, label, anchor in heads:
        b.append(text(x, header_y + 28, label, 12.5, "#ffffff", anchor, 700))

    # 表格行
    y = header_y + header_h
    for idx, (cat, item, qty, notes, color, fill) in enumerate(ROWS, 1):
        row_h = 58 if len(notes) == 1 else 72
        if idx % 2 == 0:
            b.append(rect(table_x, y, table_w, row_h, fill="#f8fafc"))
        b.append(line(table_x, y + row_h, table_x + table_w, y + row_h, LINE, 1))
        b.append(text(86, y + 35, str(idx), 12.5, FAINT, "middle", 600))
        b.append(pill(123, y + 17, cat, color, fill))
        b.append(text(212, y + 35, item, 14.2, INK, weight=600))
        b.append(text(656, y + 35, qty, 14, INK, "middle", 700))
        if len(notes) == 1:
            b.append(text(704, y + 35, notes[0], 12.4, SUB))
        else:
            b.append(text(704, y + 27, notes[0], 12.2, SUB))
            b.append(text(704, y + 46, notes[1], 12.2, SUB))
        y += row_h

    b.append(rect(table_x, header_y, table_w, y - header_y, fill="none", stroke=LINE, sw=1.2, rx=8))

    # 底部说明
    notes_y = y + 42
    b.append(text(64, notes_y, "选型提示", 14.5, INK, weight=700))
    tips = [
        "SSR 输入电流按实物规格核算，常见 10–15mA/路；5V 电源建议 ≥1A 并留余量。",
        "NTC 与 10kΩ 上拉电阻直接决定测温精度，建议 1% 电阻、同批次 B3950 探头。",
        "阻性加热负载可选过零型 SSR；感性负载需选随机型并按需加 RC 吸收。",
        "清单为功能最小集；外壳、散热片、端子数量按柜体结构增减。",
    ]
    for i, tip in enumerate(tips):
        b.append(text(64, notes_y + 26 + i * 23, "· " + tip, 12, SUB))

    # 安全提示框
    box_x, box_y, box_w, box_h = 760, notes_y - 18, 576, 132
    b.append(rect(box_x, box_y, box_w, box_h, fill="#fdecea", stroke=RED, sw=1.2, rx=10))
    b.append(text(box_x + 20, box_y + 28, "安全提示", 14, RED, weight=700))
    safe = [
        "220V 强电必须断电接线，加保险丝并可靠绝缘。",
        "强弱电分区走线，禁止并行缠绕；金属外壳接地。",
        "烧录和调试时先断开 220V，只保留 5V 弱电。",
    ]
    for i, s in enumerate(safe):
        b.append(text(box_x + 20, box_y + 55 + i * 24, "· " + s, 11.8, "#7f1d1d"))

    # 页脚
    b.append(line(64, 1390, 1336, 1390, LINE, 1.2))
    b.append(text(64, 1422, "temp_control · 五路温控系统", 12, FAINT, weight=600))
    b.append(text(1336, 1422, "BOM v1.0 · 2026-11", 12, FAINT, "end"))
    b.append("</svg>")

    OUT.write_text("\n".join(b), encoding="utf-8")
    print("wrote", OUT)


if __name__ == "__main__":
    build()
