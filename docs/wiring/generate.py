#!/usr/bin/env python3
"""生成 docs/wiring 下的接线示意图（纯 SVG，零依赖）。

用法：
    python3 docs/wiring/generate.py

输出：
    docs/wiring/wiring-diagram.svg     五路温控接线图（含编码器 / OLED）
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
CAP = "#0f766e"

SSR_FILL = "#fff6ea"
SSR_LINE = "#c07000"
LOAD_FILL = "#fdecea"
LOAD_LINE = "#b3261e"
MCU_FILL = "#eef4fb"
MCU_LINE = "#2f5478"
UI_FILL = "#f1f7f1"
UI_LINE = "#2e7d4f"
BAND = "#fafbfd"
CAP_FILL = "#e6f4f1"


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


def vtext(x, y, s, size=11, fill=INK, weight=600):
    return ('<g transform="translate(%s %s) rotate(-90)">%s</g>'
            % (x, y, text(0, 0, s, size, fill, anchor="middle", weight=weight)))


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


def resistor(x, y, w=80, h=26, label="10kΩ"):
    out = [rect(x, y - h / 2.0, w, h, fill="#ffffff", stroke=NTC, sw=2.2, rx=3)]
    out.append(text(x + w / 2.0, y - h / 2.0 - 8, label, 13, NTC,
                    anchor="middle", weight=600))
    return "".join(out)


def ntc_sym(x, y_top, h=64, w=26):
    out = [rect(x - w / 2.0, y_top, w, h, fill="#ffffff", stroke=NTC, sw=2.2)]
    out.append(line(x - w / 2.0 - 12, y_top + h + 6, x + w / 2.0 + 10, y_top - 9,
                    stroke=NTC, sw=2.2))
    return "".join(out)


def cap_sym(x, y_top, w=24):
    """Vertical ceramic capacitor: two plates, 18px total height."""
    out = [line(x, y_top, x, y_top + 4, stroke=CAP, sw=2.2)]
    out.append(line(x - w / 2.0, y_top + 4, x + w / 2.0, y_top + 4, stroke=CAP, sw=3.0))
    out.append(line(x - w / 2.0, y_top + 12, x + w / 2.0, y_top + 12, stroke=CAP, sw=3.0))
    out.append(line(x, y_top + 12, x, y_top + 18, stroke=CAP, sw=2.2))
    return "".join(out)


# ---------------------------------------------------------------- 主接线图

ROWS = [
    # 通道, y, 数字引脚, 模拟引脚, AVR 数字端口, AVR 模拟端口
    (1, 300, "D5", "A0", "PD5", "PC0"),
    (2, 460, "D6", "A1", "PD6", "PC1"),
    (3, 620, "D7", "A2", "PD7", "PC2"),
    (4, 780, "D8", "A3", "PB0", "PC3"),
    (5, 940, "D9", "A6", "PB1", "ADC6"),
]

W, H = 1640, 1650
MX0, MX1, MY0, MY1, MC = 660, 1020, 245, 1020, 840
SX0, SX1 = 400, 540
LX0, LX1 = 200, 320
LOOP_X = 150
NODE, RW, VTAP = 1180, 1290, 1352

# 控制面板元件位置
ENC_X, ENC_Y, ENC_W, ENC_H = 742, 1170, 180, 100
OL_X, OL_Y, OL_W, OL_H = 980, 1170, 190, 100


def wiring_diagram():
    b = []

    # 标题
    b.append(text(60, 64, "五路温控系统 · 接线图", 30, INK, weight=700))
    b.append(text(60, 98,
                  "Arduino Pro Mini (ATmega328P, 5V/16MHz) · NTC 10kΩ B3950 上拉接法 · "
                  "100nF 去耦 · SSR 开关加热 · EC11 编码器 · SSD1306 OLED",
                  15, SUB))
    b.append(text(60, 120,
                  "5 路独立控温 · 爬柜、孵化箱、恒温箱等场景通用",
                  13, SUB))
    b.append(line(60, 140, 1580, 140, stroke="#dbe3ec", sw=1.6))

    b.append(text(150, 214, "⚠ 220V 强电区：接线前必须断电", 13, LOAD_LINE, weight=700))

    # 行背景
    for _, y, _, _, _, _ in ROWS:
        b.append(rect(60, y - 72, 1520, 144, fill=BAND, rx=12))

    # MCU 本体
    b.append(rect(MX0, MY0, MX1 - MX0, MY1 - MY0, fill=MCU_FILL,
                  stroke=MCU_LINE, sw=2.4, rx=12))
    b.append(text(MC, 600, "Arduino Pro Mini", 22, INK, anchor="middle", weight=700))
    b.append(text(MC, 626, "ATmega328P · 5V 16MHz", 12.5, SUB, anchor="middle"))
    b.append(text(MC, 648, "10 位 ADC", 12.5, SUB, anchor="middle"))

    # MCU 电源脚
    b.append(line(690, MY0, 690, MY0 - 30, stroke=PWR, sw=2.6))
    b.append(vcc_sym(690, MY0 - 60))
    b.append(line(690, MY1, 690, MY1 + 16, stroke=GND, sw=2.6))
    b.append(gnd_sym(690, MY1 + 16, label=False))
    b.append(text(716, MY1 + 34, "GND", 11, FAINT, weight=600))

    for layer, y, dpin, apin, dport, aport in ROWS:
        # ---- 加热器闭环
        b.append(poly([(360, y - 18), (LX1, y - 18)], stroke=LOAD_LINE, sw=2.6))
        b.append(poly([(LX0, y - 18), (LOOP_X, y - 18), (LOOP_X, y + 18),
                       (360, y + 18)], stroke=LOAD_LINE, sw=2.6))
        b.append(rect(LX0, y - 50, LX1 - LX0, 60, fill=LOAD_FILL,
                      stroke=LOAD_LINE, sw=2.2, rx=6))
        b.append(text((LX0 + LX1) / 2.0, y - 26, "加热器", 14.5, LOAD_LINE,
                      anchor="middle", weight=700))
        b.append(text((LX0 + LX1) / 2.0, y - 8, "通道%d · 220V~" % layer, 11.5,
                      LOAD_LINE, anchor="middle"))

        # ---- SSR
        b.append(rect(SX0, y - 55, SX1 - SX0, 100, fill=SSR_FILL,
                      stroke=SSR_LINE, sw=2.2, rx=8))
        b.append(text((SX0 + SX1) / 2.0, y - 33, "SSR 通道%d" % layer, 15, SSR_LINE,
                      anchor="middle", weight=700))
        b.append(text((SX0 + SX1) / 2.0, y - 19, "固态继电器", 10, SUB,
                      anchor="middle"))
        b.append(text((SX0 + SX1) / 2.0, y + 40, "光耦隔离", 9.5, "#b0762a",
                      anchor="middle"))
        # 输出脚（左）
        b.append(line(SX0, y - 18, 360, y - 18, stroke=LOAD_LINE, sw=2.6))
        b.append(line(SX0, y + 18, 360, y + 18, stroke=LOAD_LINE, sw=2.6))
        b.append(text(SX0 + 10, y - 11, "AC", 9.5, LOAD_LINE, weight=600))
        b.append(text(SX0 + 10, y + 31, "AC", 9.5, LOAD_LINE, weight=600))
        # 输入脚（右）
        b.append(line(SX1, y - 18, 580, y - 18, stroke=SIG, sw=2.6))
        b.append(line(SX1, y + 18, 580, y + 18, stroke=GND, sw=2.6))
        b.append(text(SX1 - 10, y - 11, "+", 12, SIG, anchor="end", weight=700))
        b.append(text(SX1 - 10, y + 31, "−", 12, GND, anchor="end", weight=700))
        b.append(line(580, y + 18, 580, y + 36, stroke=GND, sw=2.6))
        b.append(gnd_sym(580, y + 36, label=False))

        # ---- 信号线 D 脚
        b.append(poly([(580, y - 18), (612, y - 18), (612, y), (MX0, y)],
                      stroke=SIG, sw=2.6))
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
        b.append(line(NODE, y, 1210, y, stroke=SIG, sw=2.6))
        b.append(resistor(1210, y))
        b.append(poly([(RW, y), (VTAP, y), (VTAP, y - 40)], stroke=PWR, sw=2.6))
        b.append(vcc_sym(VTAP, y - 70))
        b.append(poly([(NODE, y), (NODE, y + 26)], stroke=SIG, sw=2.6))
        b.append(ntc_sym(NODE, y + 26))
        b.append(poly([(NODE, y + 90), (NODE, y + 104)], stroke=SIG, sw=2.6))
        b.append(gnd_sym(NODE, y + 104, label=False))
        b.append(text(1215, y + 68, "NTC 10kΩ", 12, NTC, weight=600))
        # 通道 5 的 GND 标注改到左侧，给右下角的 ADC 细节框让位
        if layer == ROWS[-1][0]:
            b.append(text(NODE - 28, y + 118, "GND", 11, FAINT,
                          anchor="end", weight=600))
        else:
            b.append(text(NODE + 28, y + 118, "GND", 11, FAINT, weight=600))
        b.append(text(NODE, y - 10, "通道%d 测温" % layer, 11.5, FAINT, anchor="middle"))

    # ---------------- 控制面板：编码器 + OLED ----------------
    b.append(text(60, 1136, "控制与显示（弱电）", 15, UI_LINE, weight=700))
    notes_ui = [
        "旋转：顺时针增大 / 逆时针减小",
        "短按：设定温度 → 回差 → 运行",
        "长按：立即返回运行界面",
        "30 秒无操作息屏，操作即唤醒",
        "编辑中 10 秒无操作自动退出",
    ]
    for i, s in enumerate(notes_ui):
        b.append(text(60, 1164 + i * 24, "· " + s, 12, SUB))

    # 编码器
    b.append(rect(ENC_X, ENC_Y, ENC_W, ENC_H, fill=UI_FILL, stroke=UI_LINE,
                  sw=2.2, rx=8))
    b.append(text(ENC_X + ENC_W / 2.0, ENC_Y + 32, "旋转编码器", 15, UI_LINE,
                  anchor="middle", weight=700))
    b.append(text(ENC_X + ENC_W / 2.0, ENC_Y + 52, "EC11 · 带按键", 10.5, SUB,
                  anchor="middle"))
    b.append(text(ENC_X + ENC_W / 2.0, ENC_Y + 74, "A / B / SW + COM", 10, FAINT,
                  anchor="middle"))

    # OLED
    b.append(rect(OL_X, OL_Y, OL_W, OL_H, fill=UI_FILL, stroke=UI_LINE,
                  sw=2.2, rx=8))
    b.append(text(OL_X + OL_W / 2.0, OL_Y + 32, "OLED 0.96\"", 15, UI_LINE,
                  anchor="middle", weight=700))
    b.append(text(OL_X + OL_W / 2.0, OL_Y + 52, "SSD1306 · I2C", 10.5, SUB,
                  anchor="middle"))
    b.append(text(OL_X + OL_W / 2.0, OL_Y + 74, "地址 0x3C", 10, FAINT,
                  anchor="middle"))

    # 竖直引线 + 竖排针脚标注
    stubs = [
        (ENC_X + 26, "A", "D2", UI_LINE),
        (ENC_X + 64, "B", "D3", UI_LINE),
        (ENC_X + 102, "SW", "D4", UI_LINE),
        (OL_X + 40, "SDA", "A4", UI_LINE),
        (OL_X + 92, "SCL", "A5", UI_LINE),
    ]
    for sx, comp_pin, mcu_pin, col in stubs:
        b.append(line(sx, ENC_Y, sx, MY1, stroke=SIG, sw=2.4))
        b.append(dot(sx, MY1, 4, SIG))
        b.append(vtext(sx - 3, (MY1 + ENC_Y) / 2.0 + 10, comp_pin, 10.5, col, 700))
        b.append(vtext(sx + 14, (MY1 + ENC_Y) / 2.0 + 10, mcu_pin, 10.5, FAINT, 600))

    # 编码器 COM → GND
    b.append(line(ENC_X, ENC_Y + 86, ENC_X - 34, ENC_Y + 86, stroke=GND, sw=2.4))
    b.append(line(ENC_X - 34, ENC_Y + 86, ENC_X - 34, ENC_Y + 116, stroke=GND, sw=2.4))
    b.append(gnd_sym(ENC_X - 34, ENC_Y + 116, label=False))
    b.append(text(ENC_X - 6, ENC_Y + 80, "COM", 10, GND, anchor="end", weight=600))

    # OLED VCC / GND
    vcc_x = OL_X + 150
    b.append(line(vcc_x, OL_Y, vcc_x, OL_Y - 6, stroke=PWR, sw=2.4))
    b.append(path("M%s %s L%s %s L%s %s Z"
                  % (vcc_x - 7, OL_Y - 18, vcc_x, OL_Y - 32,
                     vcc_x + 7, OL_Y - 18), stroke=PWR, sw=1.5, fill=PWR))
    b.append(text(vcc_x, OL_Y - 38, "VCC", 10.5, PWR,
                  anchor="middle", weight=700))

    gnd_x = OL_X + 80
    b.append(line(gnd_x, OL_Y + OL_H, gnd_x, OL_Y + OL_H + 18,
                  stroke=GND, sw=2.4))
    b.append(gnd_sym(gnd_x, OL_Y + OL_H + 18, label=False))
    b.append(text(gnd_x + 14, OL_Y + OL_H + 40, "GND", 10, GND, weight=600))

    # ---------------- 单路 ADC 输入细节（含去耦电容） ----------------
    DX, DY, DW, DH = 1210, 1064, 360, 234
    b.append(rect(DX, DY, DW, DH, fill=CAP_FILL, stroke=CAP, sw=1.6, rx=10))
    b.append(text(DX + 16, DY + 26, "单路 ADC 输入（每路一份）", 13.5, CAP,
                  weight=700))
    b.append(text(DX + 16, DY + 46, "上拉分压 + 100nF 低通，靠近板端", 10.5, SUB))

    # VCC → 10kΩ → 节点
    b.append(vcc_sym(DX + 40, DY + 72))
    b.append(line(DX + 40, DY + 102, DX + 60, DY + 102, stroke=PWR, sw=2.4))
    b.append(resistor(DX + 60, DY + 102))
    b.append(line(DX + 140, DY + 102, DX + 190, DY + 102, stroke=SIG, sw=2.4))
    b.append(dot(DX + 190, DY + 102, 4.5, SIG))
    b.append(text(DX + 198, DY + 88, "→ ADC", 10.5, SIG, weight=700))

    # NTC → GND
    b.append(line(DX + 190, DY + 102, DX + 190, DY + 114, stroke=SIG, sw=2.4))
    b.append(ntc_sym(DX + 190, DY + 114, h=40, w=20))
    b.append(line(DX + 190, DY + 154, DX + 190, DY + 164, stroke=SIG, sw=2.4))
    b.append(gnd_sym(DX + 190, DY + 164, label=False))
    b.append(text(DX + 96, DY + 146, "NTC", 10.5, NTC, weight=600))
    b.append(text(DX + 96, DY + 160, "10kΩ", 10.5, NTC, weight=600))

    # 100nF → GND
    b.append(line(DX + 190, DY + 102, DX + 270, DY + 102, stroke=SIG, sw=2.4))
    b.append(line(DX + 270, DY + 102, DX + 270, DY + 112, stroke=CAP, sw=2.2))
    b.append(cap_sym(DX + 270, DY + 112))
    b.append(line(DX + 270, DY + 130, DX + 270, DY + 150, stroke=CAP, sw=2.2))
    b.append(gnd_sym(DX + 270, DY + 150, label=False))
    b.append(text(DX + 284, DY + 124, "100nF", 10.5, CAP, weight=700))

    b.append(line(DX + 16, DY + 186, DX + DW - 16, DY + 186,
                  stroke="#b7ded6", sw=1.2))
    b.append(text(DX + 16, DY + 206, "长线再加：板端 1kΩ 串联", 10.5, SUB))
    b.append(text(DX + 16, DY + 222, "+ 100nF 到 GND，探头端再并 100nF", 10.5, SUB))

    # 图例
    b.append(line(60, 1330, 1580, 1330, stroke="#dbe3ec", sw=1.6))
    items = [(SIG, "信号（数字/模拟/I2C）"), (PWR, "VCC / 5V"),
             (GND, "GND"), (NTC, "NTC / 电阻"), (CAP, "电容")]
    x = 70
    for color, label in items:
        b.append(line(x, 1362, x + 34, 1362, stroke=color, sw=4))
        b.append(text(x + 44, 1367, label, 13, SUB))
        x += 240

    b.append(text(60, 1412, "接线要点", 14.5, INK, weight=700))
    notes_a = [
        "NTC 与 10kΩ 上拉电阻串联分压，中点接 A0 / A1 / A2 / A3 / A6",
        "通道5 用 A6（ADC6，仅模拟输入）；A4 / A5 留给 OLED I2C",
        "通道1→D5 … 通道5→D9 接 SSR 输入正极，SSR 输入负极接 GND",
        "编码器 A/B/SW→D2/D3/D4；OLED SDA/SCL→A4/A5",
        "每路 ADC 节点加 100nF 到 GND；5V 入口加 470–1000µF + 100nF",
        "Pro Mini VCC / OLED VCC 各加 100nF 去耦，AREF 加 100nF",
    ]
    for i, s in enumerate(notes_a):
        b.append(text(60, 1442 + i * 27, "· " + s, 12.5, SUB))

    b.append(text(820, 1412, "安全提示", 14.5, LOAD_LINE, weight=700))
    notes_b = [
        "改线前必须断电；220V 与弱电分区走线，禁止并行缠绕",
        "单 I/O 最大 20mA，5 路 SSR 输入电流需分别核算，超限加三极管",
        "D5–D9 建议各加 10k 下拉，防止复位/烧录时 SSR 误导通",
        "Pro Mini 无 USB，需 FTDI/ISP 烧录；供电用 RAW 7–12V 或稳压 5V 接 VCC",
        "5 路同时加热时电流较大，5V 电源与地线需留足余量",
    ]
    for i, s in enumerate(notes_b):
        b.append(text(820, 1442 + i * 27, "· " + s, 12.5, SUB))

    b.append(text(60, 1608,
                  "依据 Arduino Pro Mini 官方引脚定义绘制（A000005 系列）；实物丝印可能不同，接线前请核对。",
                  11.5, FAINT))
    return "".join(b)


# ------------------------------------------------------------ 引脚位置图

PW, PH = 1280, 1040
BX0, BX1, BY0, BY1 = 380, 880, 150, 700
PIN_TOP, PIN_PITCH = 222, 40

LEFT_PINS = ["D1", "D0", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
RIGHT_PINS = ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0", "D13", "D11", "D12", "D10"]

LEFT_ANN = {
    "GND": ("公共地", "gnd"),
    "D2": ("编码器 A", "sig"),
    "D3": ("编码器 B", "sig"),
    "D4": ("编码器按键", "sig"),
    "D5": ("通道1 SSR", "sig"),
    "D6": ("通道2 SSR", "sig"),
    "D7": ("通道3 SSR", "sig"),
    "D8": ("通道4 SSR", "sig"),
    "D9": ("通道5 SSR", "sig"),
}
RIGHT_ANN = {
    "RAW": ("7–12V 输入（可选）", "pwr"),
    "GND": ("公共地", "gnd"),
    "VCC": ("NTC 上拉 / OLED", "pwr"),
    "A3": ("通道4 NTC", "sig"),
    "A2": ("通道3 NTC", "sig"),
    "A1": ("通道2 NTC", "sig"),
    "A0": ("通道1 NTC", "sig"),
}

PILL = {
    "sig": ("#e8f0fe", "#1f6feb", "#12467f"),
    "pwr": ("#fdeaea", "#d92b2b", "#a01d1d"),
    "gnd": ("#ececec", "#1c1c1c", "#1c1c1c"),
}

HEADER = [("A5", "SCL → OLED", "sig"), ("A4", "SDA → OLED", "sig"),
          ("A7", "未使用", "none"), ("A6", "通道5 NTC", "sig")]


def pin_map():
    b = []
    b.append(text(60, 62, "Arduino Pro Mini 引脚位置图", 28, INK, weight=700))
    b.append(text(60, 94,
                  "ATmega328P · 俯视（元件面朝上）· 本项目使用 A0–A3、A6、D2–D9、A4/A5(I2C)、VCC、GND、RAW",
                  14, SUB))
    b.append(line(60, 118, 1220, 118, stroke="#dbe3ec", sw=1.6))

    b.append(rect(BX0, BY0, BX1 - BX0, BY1 - BY0, fill="#e6f1f4",
                  stroke=MCU_LINE, sw=2.4, rx=10))

    for i in range(6):
        b.append(rect(470 + i * 40, 160, 26, 26, fill="#ffffff",
                      stroke=MCU_LINE, sw=1.8, rx=3))
    b.append(text(630, 208, "FTDI 6P 排针（烧录 / 串口）", 11.5, SUB, anchor="middle"))

    b.append(text(630, 400, "ARDUINO", 20, MCU_LINE, anchor="middle", weight=700))
    b.append(text(630, 426, "PRO MINI", 20, MCU_LINE, anchor="middle", weight=700))
    b.append(text(630, 452, "ATmega328P", 13, SUB, anchor="middle"))

    b.append(rect(700, 620, 68, 26, fill="#ffffff", stroke=MCU_LINE, sw=1.6, rx=4))
    b.append(text(734, 638, "RESET", 10.5, SUB, anchor="middle", weight=600))

    for i in range(12):
        y = PIN_TOP + i * PIN_PITCH

        name = LEFT_PINS[i]
        b.append(line(322, y, BX0, y, stroke="#7d8b9b", sw=2.4))
        b.append('<rect x="322" y="%s" width="16" height="10" fill="#c3ccd6"/>' % (y - 5))
        ann = LEFT_ANN.get(name)
        if ann:
            fill, stroke, fg = PILL[ann[1]]
            b.append(rect(236, y - 17, 78, 24, fill=fill, stroke=stroke, sw=1.6, rx=12))
            b.append(text(275, y - 1, name, 14, fg, anchor="middle", weight=700))
            b.append(text(196, y + 4, ann[0] + " ←", 12, SUB, anchor="end"))
        else:
            b.append(text(306, y + 4, name, 13, "#6b7a8a", anchor="end", weight=600))

        name = RIGHT_PINS[i]
        b.append(line(BX1, y, 938, y, stroke="#7d8b9b", sw=2.4))
        b.append('<rect x="882" y="%s" width="16" height="10" fill="#c3ccd6"/>' % (y - 5))
        ann = RIGHT_ANN.get(name)
        if ann:
            fill, stroke, fg = PILL[ann[1]]
            b.append(rect(944, y - 17, 78, 24, fill=fill, stroke=stroke, sw=1.6, rx=12))
            b.append(text(983, y - 1, name, 14, fg, anchor="middle", weight=700))
            b.append(text(1034, y + 4, "→ " + ann[0], 12, SUB))
        else:
            b.append(text(954, y + 4, name, 13, "#6b7a8a", weight=600))

    # 板上 4 脚排针 A5 / A4 / A7 / A6
    b.append(text(60, 736, "板上 4 脚排针（位号 1–4：A5 / A4 / A7 / A6）", 13, INK,
                  weight=700))
    for i, (name, desc, kind) in enumerate(HEADER):
        x = 116 + i * 205
        b.append(line(x + 30, 760, x + 30, 790, stroke="#7d8b9b", sw=2.2))
        b.append(rect(x, 790, 60, 26, fill="#ffffff", stroke=MCU_LINE, sw=1.8, rx=3))
        b.append(text(x + 30, 808, name, 13, MCU_LINE, anchor="middle", weight=700))
        fill, stroke, fg = PILL.get(kind, ("#ffffff", "#c3ccd6", SUB))
        if kind != "none":
            b.append(rect(x + 70, 790, 96, 26, fill=fill, stroke=stroke, sw=1.4, rx=12))
            b.append(text(x + 118, 808, desc, 11, fg, anchor="middle", weight=600))
        else:
            b.append(text(x + 74, 808, desc, 11, FAINT))

    # 图例
    xx = 60
    b.append(text(60, 882, "图例", 13.5, INK, weight=700))
    for key, label in (("sig", "信号引脚"), ("pwr", "电源引脚"), ("gnd", "接地引脚")):
        fill, stroke, fg = PILL[key]
        b.append(rect(xx, 896, 26, 18, fill=fill, stroke=stroke, sw=1.4, rx=9))
        b.append(text(xx + 34, 910, label, 12.5, SUB))
        xx += 130
    b.append(rect(xx, 896, 26, 18, fill="#ffffff", stroke="#c3ccd6", sw=1.4, rx=3))
    b.append(text(xx + 34, 910, "未使用", 12.5, SUB))

    b.append(text(60, 962,
                  "A6 / A7 只有模拟输入功能（ADC6 / ADC7），不能当数字口使用；实测接线请以实物丝印为准。",
                  12, FAINT))
    b.append(text(60, 990,
                  "5 路 NTC 占满 A0–A3 + A6，A4 / A5 留给 OLED 的 I2C，二者不冲突。",
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
    write("wiring-diagram.svg", W, H, wiring_diagram(), "五路温控系统接线图")
    write("pro-mini-pin-map.svg", PW, PH, pin_map(), "Arduino Pro Mini 引脚位置图")
