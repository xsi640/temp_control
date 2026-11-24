#!/usr/bin/env python3
"""按固件实际排版生成 OLED 界面示意图（零依赖，输出 SVG）。

坐标与固件一致：
  U8g2 字体 u8g2_font_6x10_tf，字符步进 6px
  第一行基线 y=9，其后每层 y = 19 + i*10
  面板 128x64

用法：
    python3 docs/oled/render.py
"""

import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

MONO = "'DejaVu Sans Mono', Consolas, 'Courier New', monospace"

GLASS_W, GLASS_H = 128, 64
PAD = 20
W, H = GLASS_W + PAD * 2, GLASS_H + PAD * 2

BEZEL = "#11171d"
GLASS = "#03080c"
PIXEL = "#dff9ff"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(lines):
    """lines: 6 个字符串（第 1 行为表头，其余为 5 层）。None 表示该行不画。"""
    b = []
    b.append('<rect x="0" y="0" width="%s" height="%s" rx="12" fill="%s"/>'
             % (W, H, BEZEL))
    b.append('<rect x="1" y="1" width="%s" height="%s" rx="11" fill="none" '
             'stroke="#2b343d" stroke-width="1"/>' % (W - 2, H - 2))
    b.append('<rect x="%s" y="%s" width="%s" height="%s" rx="2" fill="%s"/>'
             % (PAD, PAD, GLASS_W, GLASS_H, GLASS))

    for idx, line in enumerate(lines):
        if line is None:
            continue
        y = 9 if idx == 0 else 19 + (idx - 1) * 10
        for col, ch in enumerate(line):
            if ch == " ":
                continue
            b.append('<text x="%s" y="%s" font-family="%s" font-size="10" '
                     'fill="%s">%s</text>'
                     % (PAD + col * 6, PAD + y, MONO, PIXEL, esc(ch)))
    return "".join(b)


def write(name, lines):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
           'viewBox="0 0 %s %s">%s</svg>'
           % (W, H, W, H, render(lines)))
    p = os.path.join(OUT_DIR, name)
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("wrote", p)


STATES = [
    # 文件名, 表头, 5 层内容
    ("screen-run-heat.svg", "SET 32.0C  HY 0.8C", [
        "1 31.4C HEAT",
        "2 30.9C HEAT",
        "3 32.4C ----",
        "4 31.8C ----",
        "5 32.1C ----",
    ]),
    ("screen-run-idle.svg", "SET 32.0C  HY 0.8C", [
        "1 32.3C ----",
        "2 32.1C ----",
        "3 32.4C ----",
        "4 31.8C ----",
        "5 32.1C ----",
    ]),
    ("screen-edit-temp.svg", "[SET 32.0C] HY 0.8C", [
        "1 31.4C HEAT",
        "2 30.9C HEAT",
        "3 32.4C ----",
        "4 31.8C ----",
        "5 32.1C ----",
    ]),
    ("screen-edit-hyst.svg", "SET 32.0C [HY 0.8C]", [
        "1 31.4C ----",
        "2 31.6C ----",
        "3 32.0C ----",
        "4 31.8C ----",
        "5 32.1C ----",
    ]),
    ("screen-fault.svg", "SET 32.0C  HY 0.8C", [
        "1 31.4C HEAT",
        "2 30.9C HEAT",
        "3   ERR  OFF",
        "4 31.8C ----",
        "5 32.1C ----",
    ]),
    ("screen-sleep.svg", None, [None] * 5),
]


if __name__ == "__main__":
    for name, head, rows in STATES:
        write(name, [head] + rows)
