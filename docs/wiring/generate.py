#!/usr/bin/env python3
"""生成 docs/wiring 下的两张接线示意图（纯 SVG，零依赖）。

用法：
    python3 docs/wiring/generate.py

输出：
    docs/wiring/wiring-diagram.svg     三层温控接线图
    docs/wiring/pro-mini-pin-map.svg   Arduino Pro Mini 引脚位置图
"""

import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

FONT = "system-ui, -apple-system, 'Segoe UI', 'Microsoft YaHei', 'PingFang SC', sans-serif"

INK = "#16222f"
SUB = "#5b6b7c"
FAINT = "#8b98a6"
SIG = "#1f6feb"
PWR = "#d92b2b"
GND = "#1c1c1c"
NTC = "#a85b1a"

SSR_FILL = "#fff6ea"
SSR_LINE = "#c07000"
LOAD_FILL = "#fdecea"
LOAD_LINE = "#b3261e"
MCU_FILL = "#eef4fb"
MCU_LINE = "#2f5478"
BAND = "#fafbfd"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=14, fill=INK, anchor="start", weight=400, opacity=1):
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" '
            'font-weight="%s" opacity="%s">%s</text>'
            % (x, y, size, fill, anchor, weight, opacity, esc(s)))


def rect(x, y, w, h, fill="none", stroke="none", sw=2, rx=0, dash=""):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" '
            'stroke="%s" stroke-width="%s"%s/>'
            % (x, y, w, h, rx, fill, stroke, sw, d))


def path(d, stroke=SIG, sw=2.6, fill="none", dash=""):
    da = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" '
            'stroke-linecap="round" stroke-linejoin="round"%s/>'
            % (d, fill, stroke, sw, da))


def line(x1, y1, x2, y2, **kw):
    return path("M%s %s L%s %s" % (x1, y1, x2, y2), **kw)


def poly(pts, **kw):
    return path("M" + " L".join("%s %s" % p for p in pts), **kw)


def dot(x, y, r=5, fill=SIG):
    return '<circle cx="%s" cy="%s" r="%s" fill="%s"/>' % (x, y, r, fill)


def gnd_sym(x, y, label=True):
    out = [line(x, y, x, y + 6, stroke=GND, sw=2.6)]
    out.append(line(x - 20, y + 6, x + 20, y + 6, stroke=GND, sw=3.2))
    out.append(line(x - 13, y + 13, x + 13, y + 13, stroke=GND, sw=3.2))
    out.append(line(x - 6, y + 20, x + 6, y + 20, stroke=GND, sw=3.2))
    if label:
        out.append(text(x + 26, y + 18, "GND", 11.5, FAINT, weight=600))
    return "".join(out)


def vcc_sym(x, y):
    out = [line(x, y, x, y + 30, stroke=PWR, sw=2.6)]
    out.append(path("M%s %s L%s %s L%s %s Z" % (x - 7, y + 14, x, y, x + 7, y + 14),
                    stroke=PWR, sw=1.5, fill=PWR))
    out.append(text(x, y - 10, "VCC", 13, PWR, anchor="middle", weight=700))
    return "".join(out)


def resistor(x, y, w=80, h=28, label="10kΩ"):
    out = [rect(x, y - h / 2.0, w, h, fill="#ffffff", stroke=NTC, sw=2.2, rx=3)]
    out.append(text(x + w / 2.0, y - h / 2.0 - 9, label, 13, NTC,
                    anchor="middle", weight=600))
    return "".join(out)


def ntc_sym(x, y_top, h=70, w=28):
    out = [rect(x - w / 2.0, y_top, w, h, fill="#ffffff", stroke=NTC, sw=2.2)]
    out.append(line(x - w / 2.0 - 13, y_top + h + 8, x + w / 2.0 + 11, y_top - 11,
                    stroke=NTC, sw=2.2))
    return "".join(out)


# ---------------------------------------------------------------- 主接线图

ROWS = [
    # 层, y, 数字引脚, 模拟引脚, AVR 端口
    (1, 320, "D2", "A2", "PD2", "PC2"),
    (2, 560, "D3", "A1", "PD3", "PC1"),
    (3, 800, "D4", "A0", "PD4", "PC0"),
]

W, H = 1600, 1240
MX0, MX1, MY0, MY1, MC = 660, 1020, 252, 884, 840
SX0, SX1 = 400, 540
LX0, LX1 = 200, 320
LOOP_X = 150
NODE, RW, VTAP = 1160, 1270, 1330


def wiring_diagram():
    b = []

    # 标题
    b.append(text(60, 66, "三层爬柜温控系统 · 接线图", 30, INK, weight=700))
    b.append(text(60, 100,
                  "Arduino Pro Mini (ATmega328P) · NTC 10kΩ B3950 上拉接法 · SSR 开关加热",
                  16, SUB))
    b.append(line(60, 126, 1540, 126, stroke="#dbe3ec", sw=1.6))

    # 行背景
    for _, y, _, _, _, _ in ROWS:
        b.append(rect(60, y - 105, 1480, 230, fill=BAND, rx=14))

    # 强电区提示
    b.append(text(150, 232, "⚠ 220V 强电区：接线前必须断电", 13, LOAD_LINE, weight=700))

    # MCU 本体
    b.append(rect(MX0, MY0, MX1 - MX0, MY1 - MY0, fill=MCU_FILL,
                  stroke=MCU_LINE, sw=2.4, rx=12))
    b.append(text(MC, 430, "Arduino Pro Mini", 22, INK, anchor="middle", weight=700))
    b.append(text(MC, 456, "ATmega328P · 5V 16MHz · 10 位 ADC", 12.5, SUB,
                  anchor="middle"))

    # MCU 电源脚
    b.append(line(MC, MY0, MC, MY0 - 42, stroke=PWR, sw=2.6))
    b.append(vcc_sym(MC, MY0 - 72))
    b.append(line(MC, MY1, MC, MY1 + 46, stroke=GND, sw=2.6))
    b.append(gnd_sym(MC, MY1 + 46))

    for layer, y, dpin, apin, dport, aport in ROWS:
        # ---- 加热器闭环
        b.append(poly([(360, y - 25), (LX1, y - 25)], stroke=LOAD_LINE, sw=2.6))
        b.append(poly([(LX0, y - 25), (LOOP_X, y - 25), (LOOP_X, y + 25),
                       (360, y + 25)], stroke=LOAD_LINE, sw=2.6))
        b.append(rect(LX0, y - 62, LX1 - LX0, 74, fill=LOAD_FILL,
                      stroke=LOAD_LINE, sw=2.2, rx=6))
        b.append(text((LX0 + LX1) / 2.0, y - 32, "加热器", 15, LOAD_LINE,
                      anchor="middle", weight=700))
        b.append(text((LX0 + LX1) / 2.0, y - 12, "层%d · 220V~" % layer, 11.5,
                      LOAD_LINE, anchor="middle"))
        b.append(text(150, y + 66, "220V 交流回路", 10.5, FAINT))

        # ---- SSR
        b.append(rect(SX0, y - 85, SX1 - SX0, 140, fill=SSR_FILL,
                      stroke=SSR_LINE, sw=2.2, rx=8))
        b.append(text((SX0 + SX1) / 2.0, y - 48, "SSR", 16, SSR_LINE,
                      anchor="middle", weight=700))
        b.append(text((SX0 + SX1) / 2.0, y - 30, "固态继电器 · 层%d" % layer, 10.5,
                      SUB, anchor="middle"))
        b.append(text((SX0 + SX1) / 2.0, y + 5, "光耦隔离", 9.5, "#b0762a",
                      anchor="middle"))
        # 输出脚（左）
        b.append(line(SX0, y - 25, 360, y - 25, stroke=LOAD_LINE, sw=2.6))
        b.append(line(SX0, y + 25, 360, y + 25, stroke=LOAD_LINE, sw=2.6))
        b.append(text(SX0 + 12, y - 18, "AC", 9.5, LOAD_LINE, weight=600))
        b.append(text(SX0 + 12, y + 38, "AC", 9.5, LOAD_LINE, weight=600))
        # 输入脚（右）
        b.append(line(SX1, y - 25, 580, y - 25, stroke=SIG, sw=2.6))
        b.append(line(SX1, y + 25, 580, y + 25, stroke=GND, sw=2.6))
        b.append(text(SX1 - 12, y - 18, "+", 12, SIG, anchor="end", weight=700))
        b.append(text(SX1 - 12, y + 38, "−", 12, GND, anchor="end", weight=700))
        b.append(poly([(580, y + 25), (580, y + 45)], stroke=GND, sw=2.6))
        b.append(gnd_sym(580, y + 45, label=False))

        # ---- 信号线 D 脚
        b.append(poly([(580, y - 25), (612, y - 25), (612, y), (MX0, y)],
                      stroke=SIG, sw=2.6))
        b.append(line(MX0 - 40, y, MX0, y, stroke=SIG, sw=2.6))
        b.append(dot(612, y, 4, SIG))

        # ---- MCU 引脚标注
        b.append(text(MX0 + 16, y + 6, dpin, 17, INK, weight=700))
        b.append(text(MX0 + 16, y + 24, dport, 10.5, FAINT))
        b.append(text(MX1 - 16, y + 6, apin, 17, INK, anchor="end", weight=700))
        b.append(text(MX1 - 16, y + 24, aport, 10.5, FAINT, anchor="end"))
        b.append(line(MX1, y, MX1 + 40, y, stroke=SIG, sw=2.6))

        # ---- NTC 分压
        b.append(line(MX1 + 40, y, NODE, y, stroke=SIG, sw=2.6))
        b.append(dot(NODE, y, 5, SIG))
        b.append(line(NODE, y, 1190, y, stroke=SIG, sw=2.6))
        b.append(resistor(1190, y))
        b.append(poly([(RW, y), (VTAP, y), (VTAP, y - 40)], stroke=PWR, sw=2.6))
        b.append(vcc_sym(VTAP, y - 70))
        b.append(poly([(NODE, y), (NODE, y + 30)], stroke=SIG, sw=2.6))
        b.append(ntc_sym(NODE, y + 30))
        b.append(poly([(NODE, y + 100), (NODE, y + 118)], stroke=SIG, sw=2.6))
        b.append(gnd_sym(NODE, y + 118, label=False))
        b.append(text(1195, y + 72, "NTC 10kΩ B3950", 12.5, NTC, weight=600))
        b.append(text(NODE + 30, y + 132, "GND", 11.5, FAINT, weight=600))
        b.append(text(NODE, y - 12, "层%d 测温" % layer, 12, FAINT, anchor="middle"))

    # 图例
    b.append(line(60, 962, 1540, 962, stroke="#dbe3ec", sw=1.6))
    items = [(SIG, "信号（数字/模拟）"), (PWR, "VCC / 5V"),
             (GND, "GND"), (NTC, "NTC / 电阻")]
    x = 70
    for color, label in items:
        b.append(line(x, 996, x + 34, 996, stroke=color, sw=4))
        b.append(text(x + 44, 1001, label, 13, SUB))
        x += 210

    # 说明文字
    b.append(text(60, 1042, "接线要点", 14.5, INK, weight=700))
    notes_a = [
        "NTC 与 10kΩ 上拉电阻串联分压，中点接 A0 / A1 / A2",
        "层1 → A2、层2 → A1、层3 → A0（与代码数组一致）",
        "层1 → D2、层2 → D3、层3 → D4 驱动 SSR 输入正极",
        "所有 VCC ↑ / GND ⏚ 为同一网络，接到 Pro Mini 对应引脚",
    ]
    for i, s in enumerate(notes_a):
        b.append(text(60, 1072 + i * 28, "· " + s, 13, SUB))

    b.append(text(760, 1042, "安全提示", 14.5, LOAD_LINE, weight=700))
    notes_b = [
        "改线前必须断电；220V 与弱电分区走线，禁止并行缠绕",
        "单 I/O 最大 20mA，SSR 输入电流需 ≤20mA，否则加三极管",
        "Pro Mini 无 USB，需 FTDI/ISP 烧录；供电接 RAW (7–12V)",
        "NTC 引线远离交流线，长线建议双绞屏蔽",
    ]
    for i, s in enumerate(notes_b):
        b.append(text(760, 1072 + i * 28, "· " + s, 13, SUB))

    b.append(text(60, 1204,
                  "依据 Arduino Pro Mini 官方引脚定义绘制（A000005 系列）；实物丝印可能不同，接线前请核对。",
                  11.5, FAINT))
    return "".join(b)


# ------------------------------------------------------------ 引脚位置图

PW, PH = 1280, 900
BX0, BX1, BY0, BY1 = 380, 880, 150, 760

LEFT_PINS = ["D1", "D0", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
RIGHT_PINS = ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0", "D13", "D11", "D12", "D10"]

LEFT_ANN = {
    "GND": ("SSR 输入 −", "gnd"),
    "D2": ("层1 SSR", "sig"),
    "D3": ("层2 SSR", "sig"),
    "D4": ("层3 SSR", "sig"),
}
RIGHT_ANN = {
    "RAW": ("7–12V 输入（可选）", "pwr"),
    "GND": ("公共地", "gnd"),
    "VCC": ("NTC 上拉电阻供电", "pwr"),
    "A2": ("层1 NTC", "sig"),
    "A1": ("层2 NTC", "sig"),
    "A0": ("层3 NTC", "sig"),
}

PILL = {
    "sig": ("#e8f0fe", "#1f6feb", "#12467f"),
    "pwr": ("#fdeaea", "#d92b2b", "#a01d1d"),
    "gnd": ("#ececec", "#1c1c1c", "#1c1c1c"),
}


def pin_map():
    b = []
    b.append(text(60, 62, "Arduino Pro Mini 引脚位置图", 28, INK, weight=700))
    b.append(text(60, 94,
                  "ATmega328P · 左右各 12 脚，俯视（元件面朝上）；本项目使用 A0–A2、D2–D4、VCC、GND、RAW",
                  14, SUB))
    b.append(line(60, 118, 1220, 118, stroke="#dbe3ec", sw=1.6))

    b.append(rect(BX0, BY0, BX1 - BX0, BY1 - BY0, fill="#e6f1f4",
                  stroke=MCU_LINE, sw=2.4, rx=10))

    # FTDI 排针
    for i in range(6):
        b.append(rect(470 + i * 40, 160, 26, 26, fill="#ffffff",
                      stroke=MCU_LINE, sw=1.8, rx=3))
    b.append(text(630, 208, "FTDI 6P 排针（烧录 / 串口，针序以丝印为准）",
                  11.5, SUB, anchor="middle"))

    b.append(text(630, 452, "ARDUINO", 20, MCU_LINE, anchor="middle", weight=700))
    b.append(text(630, 478, "PRO MINI", 20, MCU_LINE, anchor="middle", weight=700))
    b.append(text(630, 504, "ATmega328P", 13, SUB, anchor="middle"))

    b.append(rect(596, 690, 68, 30, fill="#ffffff", stroke=MCU_LINE, sw=1.6, rx=4))
    b.append(text(630, 710, "RESET", 10.5, SUB, anchor="middle", weight=600))

    for i in range(12):
        y = 232 + i * 44

        # 左排
        name = LEFT_PINS[i]
        b.append(line(322, y, BX0, y, stroke="#7d8b9b", sw=2.4))
        b.append('<rect x="322" y="%s" width="16" height="10" fill="#c3ccd6"/>' % (y - 5))
        ann = LEFT_ANN.get(name)
        if ann:
            fill, stroke, fg = PILL[ann[1]]
            b.append(rect(236, y - 19, 78, 26, fill=fill, stroke=stroke, sw=1.6, rx=13))
            b.append(text(275, y - 1, name, 14, fg, anchor="middle", weight=700))
            b.append(text(196, y + 5, ann[0] + " ←", 12, SUB, anchor="end"))
        else:
            b.append(text(306, y + 5, name, 13, "#6b7a8a" if name not in ("GND",) else INK,
                          anchor="end", weight=600))

        # 右排
        name = RIGHT_PINS[i]
        b.append(line(BX1, y, 938, y, stroke="#7d8b9b", sw=2.4))
        b.append('<rect x="882" y="%s" width="16" height="10" fill="#c3ccd6"/>' % (y - 5))
        ann = RIGHT_ANN.get(name)
        if ann:
            fill, stroke, fg = PILL[ann[1]]
            b.append(rect(944, y - 19, 78, 26, fill=fill, stroke=stroke, sw=1.6, rx=13))
            b.append(text(983, y - 1, name, 14, fg, anchor="middle", weight=700))
            b.append(text(1034, y + 5, "→ " + ann[0], 12, SUB))
        else:
            b.append(text(954, y + 5, name, 13, "#6b7a8a", weight=600))

    # 图例
    xx = 60
    b.append(text(60, 810, "图例", 13.5, INK, weight=700))
    for key, label in (("sig", "信号引脚"), ("pwr", "电源引脚"), ("gnd", "接地引脚")):
        fill, stroke, fg = PILL[key]
        b.append(rect(xx, 824, 26, 18, fill=fill, stroke=stroke, sw=1.4, rx=9))
        b.append(text(xx + 34, 838, label, 12.5, SUB))
        xx += 130
    b.append(rect(xx, 824, 26, 18, fill="#ffffff", stroke="#c3ccd6", sw=1.4, rx=3))
    b.append(text(xx + 34, 838, "未使用", 12.5, SUB))

    b.append(text(60, 872,
                  "板上另有 4 脚排针 A4 / A5 / ADC7 / ADC6（本项目未使用）；实测接线请以实物丝印为准。",
                  12, FAINT))
    return "".join(b)


def write(name, w, h, body, title):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
           'viewBox="0 0 %s %s" font-family="%s">'
           '<title>%s</title><rect width="%s" height="%s" fill="#ffffff"/>%s</svg>'
           % (w, h, w, h, FONT, esc(title), w, h, body))
    p = os.path.join(OUT_DIR, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote %s (%d bytes)" % (p, len(svg.encode("utf-8"))))


if __name__ == "__main__":
    write("wiring-diagram.svg", W, H, wiring_diagram(), "三层爬柜温控系统接线图")
    write("pro-mini-pin-map.svg", PW, PH, pin_map(), "Arduino Pro Mini 引脚位置图")
