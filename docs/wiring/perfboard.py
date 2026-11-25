#!/usr/bin/env python3
"""生成洞洞板（perfboard）焊接图（纯 SVG，零依赖）。

用法：
    python3 docs/wiring/perfboard.py

输出：
    docs/wiring/perfboard-layout.svg

坐标约定：
  * 洞距 2.54mm；列 0-38（左→右），行 0-58（上→下），元件面俯视；
  * 板面 96.5mm x 147mm，对应常见的 10cm x 15cm 洞洞板；
  * (列, 行) 表示第几列第几个孔。

布局思路：
  * Pro Mini 居中，左侧 D5-D9 对着左边 5 个 SSR 块；
  * 右侧 A0-A3 对着右边 5 个 NTC 块，信号线都很短；
  * 编码器放左上，OLED 放右下，电源入口在左上角。

布线：
  * 焊接面两条母线：GND 用裸铜（列 0、行 58、列 31），+5V 用绝缘线（行 2 与列 28），
    只在抽头孔剥皮上锡；这样元件面的地线可以跨过 +5V 母线而不短路；
  * 元件面用绝缘跳线点对点相连，可以跨越别的焊盘，只在两端上锡。
  * NTC 的 100nF 直接跨焊在 2P 端子背面；编码器 10nF 放在排针下方独立孔位。
"""

from pathlib import Path

OUT = Path(__file__).with_name("perfboard-layout.svg")

COLS, ROWS = 39, 59
P = 22

FONT = ("system-ui, -apple-system, 'Segoe UI', 'Microsoft YaHei', "
        "'PingFang SC', sans-serif")

INK = "#16222f"
SUB = "#5b6b7c"
FAINT = "#8b98a6"
LINE = "#dbe3ec"
BOARD = "#f4f9f2"
BOARD_LINE = "#aec9aa"
HOLE = "#9fb2c4"

MCU_FILL = "#e9f1fb"
MCU_LINE = "#2f5478"
TERM_FILL = "#fdf4e9"
TERM_LINE = "#b3690a"
RES_FILL = "#fffdf6"
RES_LINE = "#a85b1a"
CAP_FILL = "#e9f6f2"
CAP_LINE = "#0f766e"
UI_FILL = "#f0f7f0"
UI_LINE = "#2e7d4f"

P5V = "#d32f2f"
GND = "#2b2b2b"
ENC = "#2e7d4f"
OLED = "#7b1fa2"
CH = ["#c2185b", "#ef6c00", "#2e7d32", "#1565c0", "#6a1b9a"]


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=11, fill=INK, anchor="start", weight=400):
    return ('<text x="%.1f" y="%.1f" font-size="%s" fill="%s" text-anchor="%s" '
            'font-weight="%s">%s</text>'
            % (x, y, size, fill, anchor, weight, esc(s)))


def rect(x, y, w, h, fill="none", stroke="none", sw=1.4, rx=0, dash=None, op=1):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="%s" fill="%s" '
            'fill-opacity="%s" stroke="%s" stroke-width="%s"%s/>'
            % (x, y, w, h, rx, fill, op, stroke, sw, d))


def path(d, stroke, sw=2.0, fill="none", dash=None, op=1):
    da = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" stroke-opacity="%s" '
            'stroke-linecap="round" stroke-linejoin="round"%s/>'
            % (d, fill, stroke, sw, op, da))


def line(x1, y1, x2, y2, stroke=INK, sw=1.4, dash=None):
    return path("M%.1f %.1f L%.1f %.1f" % (x1, y1, x2, y2), stroke, sw, dash=dash)


def circle(cx, cy, r, fill="none", stroke="none", sw=1.2):
    return ('<circle cx="%.1f" cy="%.1f" r="%.1f" fill="%s" stroke="%s" '
            'stroke-width="%s"/>' % (cx, cy, r, fill, stroke, sw))


# ---------------------------------------------------------------- 布局

MCU_C0, MCU_C1 = 11.5, 18.5
MCU_R0, MCU_R1 = 13.0, 26.0
LEFT_PINS = ["D1", "D0", "RST", "GND", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
RIGHT_PINS = ["RAW", "GND", "RST", "VCC", "A3", "A2", "A1", "A0",
              "D13", "D11", "D12", "D10"]
AHDR = ["A5", "A4", "A7", "A6"]
PIN_R0 = 14


def lpin(i):
    return (12, PIN_R0 + i)


def rpin(i):
    return (18, PIN_R0 + i)


LP = {n: lpin(i) for i, n in enumerate(LEFT_PINS)}
RP = {n: rpin(i) for i, n in enumerate(RIGHT_PINS)}
AH = {n: (13 + i, 27) for i, n in enumerate(AHDR)}

BASE = [29, 34, 39, 44, 49]

CHN = [
    dict(n=1, base=BASE[0], adc=RP["A0"], drv=LP["D5"]),
    dict(n=2, base=BASE[1], adc=RP["A1"], drv=LP["D6"]),
    dict(n=3, base=BASE[2], adc=RP["A2"], drv=LP["D7"]),
    dict(n=4, base=BASE[3], adc=RP["A3"], drv=LP["D8"]),
    dict(n=5, base=BASE[4], adc=AH["A6"], drv=LP["D9"]),
]

#
# 每个通道单元的孔位（相对 base 行）
#   SSR 块：端子 (2,b)=GND  (4,b)=信号；下拉 10k (5,b) -> (5,b+3)
#   NTC 块：端子 (32,b)=信号  (32,b+2)=GND；上拉 10k (29,b) -> (32,b)
#           滤波 100nF (31,b) -> (31,b+2)
#

GND_BUS = [
    [(0, 3), (0, 58)],
    [(0, 58), (31, 58)],
    [(31, 58), (31, 4)],
]
P5V_BUS = [
    [(4, 2), (28, 2)],
    [(28, 2), (28, 56)],
]


def cell_terms(ch):
    b = ch["base"]
    return dict(
        ssr_gnd=(2, b), ssr_sig=(4, b), pd_top=(5, b), pd_bot=(5, b + 3),
        ntc_sig=(21, b), ntc_gnd=(21, b + 2), cap_top=(23, b), cap_bot=(23, b + 2),
        pu_hot=(27, b - 1), pu_node=(24, b - 1),
    )


def build_wires():
    """(名称, 颜色, 线宽, 起点, 终点, 方式, 说明)

    方式：'o' 正交（块内短跳线），'c' 曲线（长跳线，架空走线）。
    """
    W = []

    # ---- 电源
    W.append(("5V 输入 GND", GND, 2.6, (2, 3), (0, 3), "o", "→ GND 母线"))
    W.append(("5V 输入 +5V", P5V, 2.6, (4, 3), (4, 2), "o", "→ +5V 母线"))
    W.append(("470µF +", P5V, 2.2, (6, 3), (6, 2), "o", "长脚"))
    W.append(("470µF −", GND, 2.2, (6, 6), (0, 6), "o", "短脚 / 条纹"))
    W.append(("100nF 入口 +", P5V, 2.0, (8, 3), (8, 2), "o", "并联去耦"))
    W.append(("100nF 入口 −", GND, 2.0, (8, 6), (6, 6), "o", "与 470µF 共地"))
    W.append(("Pro Mini VCC", P5V, 2.2, RP["VCC"], (28, 17), "c", "+5V 母线"))
    W.append(("Pro Mini GND", GND, 2.2, LP["GND"], (0, 15), "c", "GND 母线"))

    # ---- 编码器
    W.append(("编码器 A", ENC, 2.0, (2, 9), LP["D2"], "c", "D2"))
    W.append(("编码器 B", ENC, 2.0, (3, 9), LP["D3"], "c", "D3"))
    W.append(("编码器 A→10nF", ENC, 1.6, (2, 9), (2, 11), "o", "10nF 上端"))
    W.append(("编码器 B→10nF", ENC, 1.6, (3, 9), (3, 11), "o", "10nF 上端"))
    W.append(("编码器 SW", ENC, 2.0, (5, 9), LP["D4"], "c", "D4"))
    W.append(("编码器 COM 1", GND, 2.0, (4, 9), (4, 10), "o", "绕开 A/B"))
    W.append(("编码器 SW 地", GND, 1.8, (6, 9), (6, 10), "o", "按键另一端接地"))
    W.append(("编码器 COM 2", GND, 2.0, (4, 10), (6, 10), "o", "与按键地汇合"))
    W.append(("编码器 COM 3", GND, 2.0, (6, 10), (6, 7), "o", "经 5 脚 GND 上行"))
    W.append(("编码器 COM 4", GND, 2.0, (6, 7), (0, 7), "o", "接 GND 母线"))
    W.append(("10nF A 地", GND, 1.8, (2, 13), (0, 13), "o", "10nF 下端"))
    W.append(("10nF B 地", GND, 1.8, (3, 13), (2, 13), "o", "汇入 A 电容地"))

    # ---- OLED
    W.append(("OLED GND", GND, 2.0, (7, 55), (7, 58), "o", "落到底部 GND 母线"))
    W.append(("OLED VCC 1", P5V, 1.8, (8, 55), (8, 57), "o", "下绕一行"))
    W.append(("OLED VCC 2", P5V, 1.8, (8, 57), (28, 57), "o", "沿板底走"))
    W.append(("OLED VCC 3", P5V, 1.8, (28, 57), (28, 56), "o", "+5V 母线末端"))
    W.append(("OLED SCL 1", OLED, 2.0, (9, 55), (9, 27), "o", "9 列上行"))
    W.append(("OLED SCL 2", OLED, 2.0, (9, 27), AH["A5"], "o", "A5"))
    W.append(("OLED SDA 1", OLED, 2.0, (10, 55), (10, 28), "o", "10 列上行"))
    W.append(("OLED SDA 2", OLED, 2.0, (10, 28), (14, 28), "o", "从 A5 下方绕过"))
    W.append(("OLED SDA 3", OLED, 2.0, (14, 28), AH["A4"], "o", "A4"))

    # ---- 通道
    for ch in CHN:
        n, t = ch["n"], cell_terms(ch)
        b = ch["base"]
        W.append(("L%d SSR 信号" % n, CH[n - 1], 2.0, t["ssr_sig"], ch["drv"], "c",
                  "D%d" % (4 + n)))
        W.append(("L%d 下拉到信号" % n, RES_LINE, 1.6, t["pd_top"], t["ssr_sig"], "o", "10k 上端"))
        W.append(("L%d 下拉到地" % n, GND, 1.6, t["pd_bot"], (0, b + 3), "o", "10k 下端"))
        W.append(("L%d SSR 地" % n, GND, 2.0, t["ssr_gnd"], (0, b), "o", ""))
        W.append(("L%d NTC 信号" % n, CH[n - 1], 2.0, t["ntc_sig"], ch["adc"], "c",
                  "A%d" % (n - 1) if n < 5 else "A6"))
        W.append(("L%d 100nF 上端" % n, CAP_LINE, 1.4, t["ntc_sig"], t["cap_top"], "b",
                  "背面短跳，跨过端子"))
        W.append(("L%d 100nF 下端" % n, GND, 1.4, t["ntc_gnd"], t["cap_bot"], "b",
                  "背面短跳，跨过端子"))
        W.append(("L%d 节点到上拉" % n, CAP_LINE, 1.6, t["ntc_sig"], t["pu_node"], "o",
                  "信号节点 → 10k 左端"))
        W.append(("L%d NTC 上拉" % n, P5V, 1.8, t["pu_hot"], (28, b - 1), "o", "10k → +5V"))
        W.append(("L%d NTC 地引出" % n, GND, 1.6, t["ntc_gnd"], (21, b + 3), "o", "绕到端子下方"))
        W.append(("L%d NTC 地" % n, GND, 2.0, (21, b + 3), (31, b + 3), "h", "跨 +5V 绝缘线"))
    return W


WIRES = build_wires()


def net_pairs(name):
    """返回该连接两端的网络，用于检测同一焊盘被两个不同网络占用。"""
    table = {
        "5V 输入 GND": ("GND", "GND"), "5V 输入 +5V": ("P5V", "P5V"),
        "470µF +": ("P5V", "P5V"), "470µF −": ("GND", "GND"),
        "100nF 入口 +": ("P5V", "P5V"), "100nF 入口 −": ("GND", "GND"),
        "Pro Mini VCC": ("P5V", "P5V"), "Pro Mini GND": ("GND", "GND"),
        "编码器 A": ("EA", "EA"), "编码器 B": ("EB", "EB"),
        "编码器 SW": ("ESW", "ESW"),
        "10nF A 地": ("GND", "GND"), "10nF B 地": ("GND", "GND"),
        "OLED GND": ("GND", "GND"), "OLED VCC": ("P5V", "P5V"),
        "OLED VCC→母线": ("P5V", "P5V"),
    }
    if name in table:
        return table[name]
    if name.startswith("编码器 A"):
        return ("EA", "EA")
    if name.startswith("编码器 B"):
        return ("EB", "EB")
    if name.startswith("编码器 COM"):
        return ("GND", "GND")
    if name.startswith("编码器 SW 地"):
        return ("GND", "GND")
    if name.startswith("OLED SCL"):
        return ("SCL", "SCL")
    if name.startswith("OLED SDA"):
        return ("SDA", "SDA")
    if name.startswith("OLED VCC"):
        return ("P5V", "P5V")
    tag = name.split()[0]
    if "SSR 信号" in name:
        return ("%sS" % tag, "%sS" % tag)
    if "下拉到信号" in name:
        return ("%sS" % tag, "%sS" % tag)
    if "下拉到地" in name or "SSR 地" in name:
        return ("GND", "GND")
    if "NTC 信号" in name or "节点到上拉" in name:
        return ("%sN" % tag, "%sN" % tag)
    if "100nF 上端" in name:
        return ("%sN" % tag, "%sN" % tag)
    if "100nF 下端" in name:
        return ("GND", "GND")
    if "NTC 上拉" in name:
        return ("P5V", "P5V")
    if "NTC 地" in name:
        return ("GND", "GND")
    return (name, name)


def conflicts(wires):
    seen, bad = {}, []
    for name, color, sw, a, b, mode, note in wires:
        na, nb = net_pairs(name)
        for pt, net in ((a, na), (b, nb)):
            if pt in seen and seen[pt] != net:
                bad.append((pt, seen[pt], net, name))
            seen[pt] = net
    for bus, net in ((GND_BUS, "GND"), (P5V_BUS, "P5V")):
        for pts in bus:
            for c, r in pts:
                if (c, r) in seen and seen[(c, r)] != net:
                    bad.append(((c, r), net, seen[(c, r)], "母线"))
    return bad


def pad_registry():
    """所有元件焊盘 -> 该焊盘允许的网络集合。"""
    pads = {}

    def add(pt, *nets):
        pads.setdefault(pt, set()).update(nets)

    add((2, 3), "GND"); add((4, 3), "P5V")
    add((6, 3), "P5V"); add((6, 6), "GND")
    add((8, 3), "P5V"); add((8, 6), "GND")
    for c in (2, 3, 4, 5):
        add((c, 9), "EA" if c == 2 else ("EB" if c == 3 else ("GND" if c == 4 else "ESW")))
    add((6, 9), "GND")
    add((2, 11), "EA"); add((2, 13), "GND")
    add((3, 11), "EB"); add((3, 13), "GND")
    for c in (7, 8, 9, 10):
        add((c, 55), {7: "GND", 8: "P5V", 9: "SCL", 10: "SDA"}[c])

    for nm, pt in LP.items():
        add(pt, "*")
    for nm, pt in RP.items():
        add(pt, "*")
    for nm, pt in AH.items():
        add(pt, "*")

    for ch in CHN:
        t = cell_terms(ch)
        n = ch["n"]
        add(t["ssr_gnd"], "GND")
        add(t["ssr_sig"], "L%dS" % n)
        add(t["pd_top"], "L%dS" % n)
        add(t["pd_bot"], "GND")
        add(t["ntc_sig"], "L%dN" % n)
        add(t["ntc_gnd"], "GND")
        add(t["cap_top"], "L%dN" % n)
        add(t["cap_bot"], "GND")
        add(t["pu_node"], "L%dN" % n)
        add(t["pu_hot"], "P5V")
    return pads


def bus_holes():
    """把母线折线展开成它经过的每一个孔。"""
    def expand(pts):
        out = set()
        for (c0, r0), (c1, r1) in zip(pts, pts[1:]):
            if c0 == c1:
                step = 1 if r1 >= r0 else -1
                for r in range(r0, r1 + step, step):
                    out.add((c0, r))
            else:
                step = 1 if c1 >= c0 else -1
                for c in range(c0, c1 + step, step):
                    out.add((c, r0))
        return out

    gnd, v5 = set(), set()
    for pts in GND_BUS:
        gnd |= expand(pts)
    for pts in P5V_BUS:
        v5 |= expand(pts)
    return gnd, v5


def audit(wires):
    """端点必须落在元件焊盘或同网络母线上；否则视为悬空线。"""
    pads = pad_registry()
    gnd, v5 = bus_holes()
    bus = {"GND": gnd, "P5V": v5}
    # 同网络的多条线可以共享一个孔作为节点
    shared = {}
    for name, color, sw, a, b, mode, note in wires:
        na, nb = net_pairs(name)
        for pt, net in ((a, na), (b, nb)):
            shared.setdefault((pt, net), 0)
            shared[(pt, net)] += 1
    problems = []
    for name, color, sw, a, b, mode, note in wires:
        na, nb = net_pairs(name)
        for pt, net in ((a, na), (b, nb)):
            if pt in pads and ("*" in pads[pt] or net in pads[pt]):
                continue
            if net in bus and pt in bus[net]:
                continue
            if shared.get((pt, net), 0) >= 2:
                continue
            where = "焊盘" if pt in pads else "空白孔"
            problems.append((name, pt, net, where))
    return problems


def crossings(wires):
    """正交跳线不得从别的网络的焊盘孔中穿过（同侧焊盘会短路）。"""
    pads = pad_registry()
    gnd, v5 = bus_holes()
    problems = []
    for name, color, sw, a, c, mode, note in wires:
        if mode == "c":
            continue
        na, nc = net_pairs(name)
        (c0, r0), (c1, r1) = a, c
        if mode == "d":
            path = [(c0, r0), (c0, r0 - 1), (c1, r0 - 1), (c1, r1)]
        elif c0 != c1 and r0 != r1:
            path = [(c0, r0), (c0, r1), (c1, r1)]
        else:
            path = [a, c]
        for (ca, ra), (cb, rb) in zip(path, path[1:]):
            if ca == cb:
                step = 1 if rb > ra else -1
                pts = [(ca, r) for r in range(ra + step, rb, step)]
            else:
                step = 1 if cb > ca else -1
                pts = [(c, ra) for c in range(ca + step, cb, step)]
            for pt in pts:
                nets = pads.get(pt)
                if nets is not None and "*" not in nets and na not in nets:
                    problems.append((name, pt, "焊盘", sorted(nets)))
                if pt in gnd and na != "GND":
                    problems.append((name, pt, "GND 母线", []))
                if mode == "b":
                    if pt in v5 and na != "P5V":
                        problems.append((name, pt, "+5V 母线", []))
    return problems


# ---------------------------------------------------------------- 绘制

def draw_holes(b, x0, y0, pid):
    w, h = (COLS - 1) * P, (ROWS - 1) * P
    b.append('<defs><pattern id="%s" width="%d" height="%d" '
             'patternUnits="userSpaceOnUse" x="%d" y="%d">' % (pid, P, P, x0, y0))
    for dx, dy in ((0, 0), (P, 0), (0, P), (P, P)):
        b.append('<circle cx="%d" cy="%d" r="2.1" fill="%s"/>' % (dx, dy, HOLE))
    b.append('</pattern></defs>')
    b.append(rect(x0 - 16, y0 - 16, w + 32, h + 32, fill=BOARD,
                  stroke=BOARD_LINE, sw=1.8, rx=8))
    b.append(rect(x0, y0, w, h, fill="url(#%s)" % pid))


def draw_rulers(b, x0, y0):
    for c in range(0, COLS, 5):
        b.append(text(x0 + c * P, y0 - 24, str(c), 8.6, FAINT, "middle", 600))
    for r in range(0, ROWS, 5):
        b.append(text(x0 - 22, y0 + r * P + 3, str(r), 8.6, FAINT, "end", 600))
    b.append(text(x0 - 22, y0 - 24, "列/行", 8.2, FAINT, "end", 600))


def draw_mcu(b, x0, y0, ghost=False):
    x1, y1 = x0 + MCU_C0 * P, y0 + MCU_R0 * P
    x2, y2 = x0 + MCU_C1 * P, y0 + MCU_R1 * P
    if ghost:
        b.append(rect(x1, y1, x2 - x1, y2 - y1, fill="#c8d4e0", stroke="#8fa3b5",
                      sw=1.0, rx=6, dash="5 4", op=0.28))
        return
    b.append(rect(x1, y1, x2 - x1, y2 - y1, fill=MCU_FILL, stroke=MCU_LINE,
                  sw=1.5, rx=6))
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    b.append(text(cx, cy - 3, "Pro Mini", 8.2, MCU_LINE, "middle", 700))
    b.append(text(cx, cy + 9, "5V 16MHz", 6.8, SUB, "middle"))
    for i, nm in enumerate(LEFT_PINS):
        x, y = x0 + lpin(i)[0] * P, y0 + lpin(i)[1] * P
        b.append(circle(x, y, 3.2, fill=MCU_LINE))
        b.append(text(x + 7, y + 3, nm, 7.0, SUB, "start", 600))
    for i, nm in enumerate(RIGHT_PINS):
        x, y = x0 + rpin(i)[0] * P, y0 + rpin(i)[1] * P
        b.append(circle(x, y, 3.2, fill=MCU_LINE))
        b.append(text(x - 7, y + 3, nm, 7.0, SUB, "end", 600))
    for i, nm in enumerate(AHDR):
        x = x0 + (13.5 + i) * P
        b.append(circle(x, y2, 2.4, fill=MCU_LINE))
        b.append(text(x, y2 - 5, nm, 6.0, SUB, "middle", 600))


def term(b, x0, y0, c0, r0, c1, r1, label, sub, color=TERM_LINE, align="start"):
    xa, ya = x0 + c0 * P, y0 + r0 * P
    xb, yb = x0 + c1 * P, y0 + r1 * P
    b.append(rect(xa, ya, xb - xa, yb - ya, fill="none", stroke=color, sw=1.0,
                  rx=3, dash="4 3", op=0.5))
    if label:
        if align == "start":
            b.append(text(xa + 3, ya - 5, label, 7.8, color, "start", 700))
        else:
            b.append(text(xb - 3, ya - 5, label, 7.8, color, "end", 700))
    if sub:
        b.append(text((xa + xb) / 2, yb + 11, sub, 6.6, FAINT, "middle"))


def res_h(b, x0, y0, c0, c1, r, label):
    y = y0 + r * P
    xa, xb = x0 + c0 * P, x0 + c1 * P
    b.append(line(xa, y, xa + 6, y, stroke=RES_LINE, sw=1.4))
    b.append(line(xb - 6, y, xb, y, stroke=RES_LINE, sw=1.4))
    b.append(rect(xa + 6, y - 5, xb - xa - 12, 10, fill=RES_FILL,
                  stroke=RES_LINE, sw=1.1, rx=2))
    b.append(text((xa + xb) / 2, y - 8, label, 7.0, RES_LINE, "middle", 700))


def res_v(b, x0, y0, c, r0, r1, label):
    x = x0 + c * P
    ya, yb = y0 + r0 * P, y0 + r1 * P
    b.append(line(x, ya, x, ya + 6, stroke=RES_LINE, sw=1.4))
    b.append(line(x, yb - 6, x, yb, stroke=RES_LINE, sw=1.4))
    b.append(rect(x - 5, ya + 6, 10, yb - ya - 12, fill=RES_FILL,
                  stroke=RES_LINE, sw=1.1, rx=2))
    b.append(text(x + 8, (ya + yb) / 2 + 3, label, 6.8, RES_LINE, "start", 700))


def cap_v(b, x0, y0, c, r0, r1, label, big=False):
    x = x0 + c * P
    ya, yb = y0 + r0 * P, y0 + r1 * P
    mid = (ya + yb) / 2
    off = 8 if big else 4
    b.append(line(x, ya, x, mid - off, stroke=CAP_LINE, sw=1.4))
    b.append(line(x, mid + off, x, yb, stroke=CAP_LINE, sw=1.4))
    b.append(line(x - off - 2, mid - off, x + off + 2, mid - off, stroke=CAP_LINE, sw=1.9))
    b.append(line(x - off - 2, mid + off, x + off + 2, mid + off, stroke=CAP_LINE, sw=1.9))
    b.append(text(x + off + 6, mid + 3, label, 6.8, CAP_LINE, "start", 700))


def draw_parts(b, x0, y0):
    draw_mcu(b, x0, y0)

    term(b, x0, y0, 1, 1.9, 5, 4.1, "5V IN", None)
    for c in (2, 4):
        b.append(circle(x0 + c * P, y0 + 3 * P, 3.0, fill=TERM_LINE))
    b.append(text(x0 + 1 * P, y0 + 3.6 * P + 16, "GND　　　 +5V",
                  6.8, FAINT, "start"))

    cap_v(b, x0, y0, 6, 3, 6, "", True)
    cap_v(b, x0, y0, 8, 3, 6, "100nF")
    b.append(text(x0 + 6 * P - 10, y0 + 4.5 * P + 3, "470µF",
                  6.8, CAP_LINE, "end", 700))

    term(b, x0, y0, 1, 8.4, 6.6, 9.6, "EC11 5P", None)
    for c, nm in ((2, "A"), (3, "B"), (4, "COM"), (5, "SW"), (6, "SW2")):
        b.append(circle(x0 + c * P, y0 + 9 * P, 3.0, fill=UI_LINE))
        b.append(text(x0 + c * P, y0 + 9 * P - 6, nm, 5.8, UI_LINE, "middle", 700))
    cap_v(b, x0, y0, 2, 11, 13, "", False)
    cap_v(b, x0, y0, 3, 11, 13, "", False)
    b.append(text(x0 + 4 * P, y0 + 12 * P + 3, "10nF×2",
                  6.8, CAP_LINE, "start", 700))

    term(b, x0, y0, 12.4, 26.4, 16.6, 27.6, None, None)
    for i, nm in enumerate(AHDR):
        x = x0 + (13 + i) * P
        b.append(circle(x, y0 + 27 * P, 3.0, fill=MCU_LINE))
        b.append(text(x, y0 + 27 * P + 11, nm, 5.8, SUB, "middle", 600))
        b.append(line(x0 + (13.5 + i) * P, y0 + 26 * P, x, y0 + 27 * P,
                      stroke=MCU_LINE, sw=0.9, dash="2 2"))
    b.append(text(x0 + 17.0 * P, y0 + 27.4 * P, "A4–A7 短线", 6.0, MCU_LINE,
                  "start", 700))

    term(b, x0, y0, 6.4, 54.4, 10.6, 55.6, "OLED 4P", None)
    for c, nm in ((7, "GND"), (8, "VCC"), (9, "SCL"), (10, "SDA")):
        b.append(circle(x0 + c * P, y0 + 55 * P, 3.0, fill=UI_LINE))
        b.append(text(x0 + c * P, y0 + 55 * P - 6, nm, 6.2, UI_LINE, "middle", 700))

    for i, ch in enumerate(CHN):
        n, b0 = ch["n"], ch["base"]
        col = CH[i]

        term(b, x0, y0, 1, b0 - 1.4, 4.6, b0 + 1.4, "SSR%d" % n, None,
             color=col, align="end")
        for c in (2, 4):
            b.append(circle(x0 + c * P, y0 + b0 * P, 3.0, fill=TERM_LINE))
        b.append(text(x0 + 2 * P - 2, y0 + b0 * P + 13, "2P", 6.4, FAINT, "start"))
        res_v(b, x0, y0, 5, b0, b0 + 3, "10k")

        term(b, x0, y0, 19.2, b0 - 0.7, 22.6, b0 + 2.7, "NTC%d" % n, None,
             color=col, align="start")
        for r in (b0, b0 + 2):
            b.append(circle(x0 + 21 * P, y0 + r * P, 3.0, fill=TERM_LINE))
        res_h(b, x0, y0, 24, 27, b0 - 1, "10k")
        ya, yb = y0 + b0 * P, y0 + (b0 + 2) * P
        xc = x0 + 23 * P
        mid = (ya + yb) / 2
        b.append(line(xc, ya, xc, mid - 3, stroke=CAP_LINE, sw=0.9, dash="2 2"))
        b.append(line(xc, mid + 3, xc, yb, stroke=CAP_LINE, sw=0.9, dash="2 2"))
        b.append(line(xc - 4, mid - 3, xc + 4, mid - 3, stroke=CAP_LINE, sw=1.1, dash="2 2"))
        b.append(line(xc - 4, mid + 3, xc + 4, mid + 3, stroke=CAP_LINE, sw=1.1, dash="2 2"))
        b.append(text(xc + 7, mid + 2.2, "100nF 背", 5.4, CAP_LINE, "start", 700))


def draw_wire(b, x0, y0, a, c, color, sw, mode):
    x1, y1 = x0 + a[0] * P, y0 + a[1] * P
    x2, y2 = x0 + c[0] * P, y0 + c[1] * P
    if mode == "h":
        # 正交走线跨过 +5V 母线：在交叉处画一个半圆"跨线"，表示不连通
        xc = x0 + 28 * P
        bend = a[0] != c[0] and a[1] != c[1]
        hy = y2 if bend else y1
        d = "M%.1f %.1f" % (x1, y1)
        if bend:
            d += " L%.1f %.1f" % (x1, hy)
        if x1 < xc < x2:
            r = 7.0
            d += " L%.1f %.1f A%.1f %.1f 0 0 1 %.1f %.1f" % (
                xc - r, hy, r, r, xc + r, hy)
        d += " L%.1f %.1f" % (x2, y2)
    elif mode == "o":
        if a[0] == c[0] or a[1] == c[1]:
            d = "M%.1f %.1f L%.1f %.1f" % (x1, y1, x2, y2)
        else:
            d = "M%.1f %.1f L%.1f %.1f L%.1f %.1f" % (x1, y1, x1, y2, x2, y2)
    else:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        lift = min(34, max(12, (dx + dy) * 0.14))
        side = 1 if (x2 - x1) * (y2 - y1) >= 0 else -1
        d = "M%.1f %.1f Q%.1f %.1f %.1f %.1f" % (
            x1, y1, mx + side * lift * 0.35, my - lift, x2, y2)
    b.append(path(d, "#ffffff", sw + 3.4))
    b.append(path(d, color, sw))
    b.append(circle(x1, y1, 3.0, fill=color))
    b.append(circle(x2, y2, 3.0, fill=color))


def draw_bus(b, x0, y0, polys, color, sw):
    for pts in polys:
        d = "M" + " L".join("%.1f %.1f" % (x0 + c * P, y0 + r * P) for c, r in pts)
        b.append(path(d, "#ffffff", sw + 3.0))
        b.append(path(d, color, sw))
        for c, r in pts:
            b.append(circle(x0 + c * P, y0 + r * P, 3.4, fill=color))


def draw_bus_guide(b, x0, y0, polys, color, sw):
    """元件面用虚线提示背面母线的位置（不焊）。"""
    for pts in polys:
        d = "M" + " L".join("%.1f %.1f" % (x0 + c * P, y0 + r * P) for c, r in pts)
        b.append(path(d, color, sw, dash="3 5", op=0.45))


def draw_back_link(b, x0, y0, a, c, color, sw=1.5, mode="b"):
    """背面跳线：虚线 + 焊点。"""
    x1, y1 = x0 + a[0] * P, y0 + a[1] * P
    x2, y2 = x0 + c[0] * P, y0 + c[1] * P
    if mode == "d":
        d = "M%.1f %.1f L%.1f %.1f L%.1f %.1f L%.1f %.1f" % (
            x1, y1, x1, y1 - P, x2, y1 - P, x2, y2)
    elif a[1] == c[1] or a[0] == c[0]:
        d = "M%.1f %.1f L%.1f %.1f" % (x1, y1, x2, y2)
    else:
        d = "M%.1f %.1f L%.1f %.1f L%.1f %.1f" % (x1, y1, x1, y2, x2, y2)
    b.append(path(d, "#ffffff", sw + 3.0))
    b.append(path(d, color, sw, dash="5 3"))
    b.append(circle(x1, y1, 2.8, fill=color))
    b.append(circle(x2, y2, 2.8, fill=color))


def draw_back_parts(b, x0, y0):
    """焊接面的背面跨接件：NTC 的 100nF 与信号节点跳线。"""
    for ch in CHN:
        b0 = ch["base"]
        ya, yb = y0 + b0 * P, y0 + (b0 + 2) * P
        mid = (ya + yb) / 2
        xc = x0 + 21 * P
        b.append(line(xc, ya + 4, xc, mid - 4, stroke=CAP_LINE, sw=1.0, dash="3 3"))
        b.append(line(xc, mid + 4, xc, yb - 4, stroke=CAP_LINE, sw=1.0, dash="3 3"))
        b.append(line(xc - 5, mid - 4, xc + 5, mid - 4, stroke=CAP_LINE, sw=1.3))
        b.append(line(xc - 5, mid + 4, xc + 5, mid + 4, stroke=CAP_LINE, sw=1.3))
        b.append(text(xc + 9, mid + 3, "100nF", 5.8, CAP_LINE, "start", 700))


def build():
    bx1, by = 100, 208
    bx2 = 1140
    ph = (ROWS - 1) * P
    W = 2080

    table_y = by + ph + 150
    H = table_y + 70 + (len(WIRES) + 3) * 26 + 320

    b = []
    b.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" font-family="%s">' % (W, H, W, H, FONT))
    b.append("<title>五路温控系统 · 洞洞板焊接图</title>")
    b.append(rect(0, 0, W, H, fill="#ffffff"))
    b.append(text(64, 58, "五路温控系统 · 洞洞板焊接图", 27, INK, "start", 700))
    b.append(text(64, 86,
                  "Arduino Pro Mini（5V/16MHz）· 10cm×15cm 洞洞板（39×59 孔，2.54mm）· "
                  "5 路 NTC + 5 路 SSR · OLED + EC11", 12, SUB))
    b.append(text(64, 108,
                  "孔位写作 (列, 行)：列 0–38 自左向右，行 0–58 自上而下。"
                  "细线是绝缘跳线（架空、可跨越焊盘），粗线是背面裸铜母线。", 10.6, SUB))
    b.append(text(1180, 56, "焊接提示", 10.2, "#b3261e", "start", 700))
    b.append(text(1180, 74, "本图是俯视透视：元件在上，所有焊点在背面；", 9.2, SUB))
    b.append(text(1180, 90, "按 (列,行) 穿孔，翻面后在对应焊盘上锡。", 9.2, SUB))
    b.append(line(64, 124, W - 64, 124, stroke=LINE, sw=1.2))

    b.append(text(bx1, by - 50, "① 元件面（俯视）：模块位置 + 走线规划", 12, INK, "start", 700))
    b.append(text(bx1, by - 34, "先装模块和阻容，再按颜色逐条焊跳线；同色＝同一通道；虚线框只是元件本体范围",
                  9.4, FAINT))
    draw_holes(b, bx1, by, "h1")
    draw_rulers(b, bx1, by)
    for name, color, sw, a, c, mode, note in WIRES:
        if mode in ("b", "d"):
            continue
        draw_wire(b, bx1, by, a, c, color, sw, mode)
    draw_bus_guide(b, bx1, by, GND_BUS, GND, 2.6)
    draw_bus_guide(b, bx1, by, P5V_BUS, P5V, 2.2)
    draw_parts(b, bx1, by)
    b.append(text(bx1 + 28 * P + 7, by + 5 * P, "背面 +5V（绝缘）", 7.0, "#b85555", "start", 600))
    b.append(text(bx1 + 31 * P + 7, by + 8 * P, "背面 GND（裸铜）", 7.0, "#777777", "start", 600))

    b.append(text(bx2, by - 50, "② 焊接面：GND 裸铜母线 + +5V 绝缘线", 12, INK, "start", 700))
    b.append(text(bx2, by - 34, "GND 用 0.6–0.8mm 裸铜逐孔上锡；+5V 用绝缘线沿路径走，只在抽头剥皮上锡",
                  9.4, FAINT))
    draw_holes(b, bx2, by, "h2")
    draw_rulers(b, bx2, by)
    draw_mcu(b, bx2, by, ghost=True)
    draw_bus(b, bx2, by, GND_BUS, GND, 4.4)
    draw_bus(b, bx2, by, P5V_BUS, P5V, 3.2)
    draw_back_parts(b, bx2, by)
    for name, color, sw, a, c, mode, note in WIRES:
        if mode in ("b", "d"):
            draw_back_link(b, bx2, by, a, c, color, sw, mode)
    for c, r, s in ((0, 6, "GND"), (4, 4, "+5V"), (28, 4, "+5V"), (31, 56, "GND")):
        b.append(text(bx2 + c * P + 8, by + r * P - 8, s, 7.4, FAINT, "start", 700))

    ly = by + ph + 54
    b.append(text(64, ly, "图例", 11, INK, "start", 700))
    lx = 118
    for color, sw, label in ((P5V, 3.2, "+5V 母线（绝缘）"), (GND, 4.4, "GND 母线（裸铜）")):
        b.append(line(lx, ly - 4, lx + 26, ly - 4, stroke=color, sw=sw))
        b.append(text(lx + 34, ly, label, 9.6, SUB))
        lx += 230
    for i in range(5):
        b.append(line(lx, ly - 4, lx + 26, ly - 4, stroke=CH[i], sw=2.2))
        b.append(text(lx + 32, ly, "L%d" % (i + 1), 9.6, SUB))
        lx += 70
    for color, label in ((ENC, "编码器"), (OLED, "OLED"), (CAP_LINE, "电容")):
        b.append(line(lx, ly - 4, lx + 26, ly - 4, stroke=color, sw=2.0))
        b.append(text(lx + 32, ly, label, 9.6, SUB))
        lx += 120
    b.append(line(lx, ly - 4, lx + 26, ly - 4, stroke=CAP_LINE, sw=1.5, dash="5 3"))
    b.append(text(lx + 34, ly, "背面短跳", 9.6, SUB))

    tx, ty = 64, table_y
    b.append(text(tx, ty - 12, "接线表：起点 → 终点（两端各焊一次）", 12.5, INK, "start", 700))
    heads = [(tx, "#", "middle"), (tx + 40, "连接", "start"), (tx + 250, "起点 (列,行)", "start"),
             (tx + 400, "终点 (列,行)", "start"), (tx + 550, "说明", "start")]
    b.append(rect(tx, ty, 1950, 26, fill=INK, rx=5))
    for cx, label, anchor in heads:
        b.append(text(cx + 8, ty + 18, label, 9.8, "#ffffff", anchor, 700))
    ry = ty + 26
    for i, (name, color, sw, a, c, mode, note) in enumerate(WIRES):
        h = 26
        if i % 2 == 0:
            b.append(rect(tx, ry, 1950, h, fill="#f7f9fc"))
        b.append(line(tx, ry + h, tx + 1950, ry + h, stroke=LINE, sw=0.8))
        b.append(text(tx + 26, ry + 18, str(i + 1), 8.8, FAINT, "middle", 600))
        b.append(text(tx + 40, ry + 18, name, 9.2, color, "start", 700))
        b.append(text(tx + 250, ry + 18, "(%d,%d)" % a, 9.2, INK))
        b.append(text(tx + 400, ry + 18, "(%d,%d)" % c, 9.2, INK))
        suffix = {"c": "　[曲线]", "b": "　[背面]",
                  "d": "　[背面绕行]", "h": "　[跨线]"}.get(mode, "")
        b.append(text(tx + 550, ry + 18, note + suffix,
                      8.8, SUB))
        ry += h
    extra = [
        ("10nF A", "(2,11)", "(2,13)", CAP_LINE, "A → 地，编码器下方"),
        ("10nF B", "(3,11)", "(3,13)", CAP_LINE, "B → 地，编码器下方"),
    ]
    for name, a, c, color, note in extra:
        h = 26
        b.append(line(tx, ry + h, tx + 1950, ry + h, stroke=LINE, sw=0.8))
        b.append(text(tx + 26, ry + 18, "+", 8.8, FAINT, "middle", 600))
        b.append(text(tx + 40, ry + 18, name, 9.2, color, "start", 700))
        b.append(text(tx + 250, ry + 18, a, 9.2, INK))
        b.append(text(tx + 400, ry + 18, c, 9.2, INK))
        b.append(text(tx + 550, ry + 18, note, 8.8, SUB))
        ry += h
    b.append(rect(tx, ty, 1950, ry - ty, fill="none", stroke=LINE, sw=1.0, rx=5))

    ny = ry + 44
    b.append(text(64, ny, "焊接顺序", 12, INK, "start", 700))
    steps = [
        "1. 插座：Pro Mini 2×12P + 1×4P、EC11 5P、OLED 4P、10 个 2P 端子；对角两点定位后补齐。",
        "2. 背面母线：GND 裸铜（列 0 → 行 58 → 列 31）逐孔上锡；+5V 绝缘线（行 2 → 列 28）只在抽头剥皮。",
        "3. 阻容：10k 上拉 ×5、10k 下拉 ×5、100nF ×6（NTC 的 5 个在端子背面）、10nF ×2、470µF ×1。",
        "4. 跳线：按表逐条焊，同色同通道；先量长度再剪，架空 2–3mm，不压模块。",
        "5. 上电：先不插模块，确认 +5V 对 GND 无短路；再插 Pro Mini 看串口 5 路读数。",
    ]
    for i, s in enumerate(steps):
        b.append(text(64, ny + 24 + i * 20, s, 9.6, SUB))

    b.append(text(1080, ny, "注意事项", 12, "#b3261e", "start", 700))
    notes = [
        "2P 端子 5.08mm：SSR 横放（行内 2 孔），NTC 竖放（列内 2 孔，本体约占 4 列）。",
        "Pro Mini 2×12P 排距 15.24mm（6 孔）：左排列 12、右排列 18，不要按 7 孔画。",
        "图①是俯视走线图：跳线从元件面穿入、背面焊接；图②只画背面母线与背面元件。",
        "电解电容长脚 +5V、短脚（外壳条纹）GND；陶瓷电容无极性。",
        "跳线只在两端上锡；跨越处拱起，不与途经孔位相连。",
        "10nF ×2 放在编码器下方独立孔位：(2,11)-(2,13)、(3,11)-(3,13)，A/B 对地。",
        "编码器用 5P：A/B/C/SW/SW2，SW2 接 GND；4P 模块自带地时悬空第 5 脚。",
        "NTC 的 100nF 焊在背面 23 列 (23,b)–(23,b+2)，再用两根背面短线接到 (21,b)/(21,b+2)。",
        "NTC (21,b) 是最多 4 根引线的节点：端子信号脚、100nF 短线、信号跳线、到 10k 左端的跳线。",
        "NTC 地线先下到 b+3 再向右，跨 +5V 绝缘线处不剥皮、不上锡。",
        "Pro Mini 短边 A4–A7 排与两侧排针错开 1.27mm，不能落在同一 2.54mm 网格：",
        "  用 4 根短线引到板上 1×4P 排针 (13..16,27)，A5/A4/A7/A6 依次对应。",
        "OLED 用 4P 排线外接，模块装面板；板上排针在 (7..10,55)。",
        "强电不上本板：SSR 输出与 220V 全部走板外。",
        "VCC / OLED / AREF 的 100nF 按 BOM 就近焊在模块背面；AREF 不在本板排针上。",
    ]
    for i, s in enumerate(notes):
        b.append(text(1080, ny + 24 + i * 17, "· " + s, 8.8, SUB))

    b.append(text(64, H - 24,
                  "由 docs/wiring/perfboard.py 生成。孔位以实物丝印和卡尺为准。",
                  9.0, FAINT))
    b.append("</svg>")
    OUT.write_text("\n".join(b), encoding="utf-8")
    print("wrote %s (%d bytes)" % (OUT, len("\n".join(b).encode("utf-8"))))


if __name__ == "__main__":
    for pt, n1, n2, name in conflicts(WIRES):
        print("WARN 焊盘冲突 %s: %s vs %s (%s)" % (pt, n1, n2, name))
    for name, pt, net, where in audit(WIRES):
        print("WARN 悬空端点 %s: %s (%s, 网络 %s)" % (name, pt, where, net))
    for name, pt, kind, nets in crossings(WIRES):
        print("WARN 穿越 %s: %s 穿过 %s %s" % (name, pt, kind, nets))
    build()
