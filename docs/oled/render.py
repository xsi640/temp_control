#!/usr/bin/env python3
"""把 U8g2 仿真的 128x64 位图渲染成 OLED 示意图（SVG）。

流程：
    1. 编译并运行 sim.cpp，得到真实字体的 frame-*.pbm
    2. 本脚本把位图逐像素画进带外壳的 SVG（像素精确）
    3. 需要 PNG 时用 Chrome/Edge 截图，见 docs/oled/README.md

用法：
    python3 docs/oled/render.py            # 只生成 SVG
    python3 docs/oled/render.py --png      # 顺带调用浏览器导出 PNG

依赖：g++、U8g2 库源码（用于仿真）。SVG 本身零依赖。
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
U8G2_SRC = Path(os.environ.get("U8G2_SRC", Path.home() / "Arduino/libraries/U8g2/src"))

GW, GH = 128, 64
PAD = 22
W, H = GW + PAD * 2, GH + PAD * 2
SCALE = 6

BEZEL_TOP = "#232d37"
BEZEL_BOTTOM = "#0a0f14"
GLASS = "#03080c"
PIXEL = "#e8fbff"

STATES = [
    ("screen-run-heat", "frame-run-heat"),
    ("screen-run-idle", "frame-run-idle"),
    ("screen-edit-temp", "frame-edit-temp"),
    ("screen-edit-hyst", "frame-edit-hyst"),
    ("screen-fault", "frame-fault"),
    ("screen-sleep", "frame-sleep"),
]


def build_sim(build_dir):
    sources = sorted(U8G2_SRC.glob("clib/u8g2_*.c")) + sorted(U8G2_SRC.glob("clib/u8x8_*.c"))
    out = build_dir / "sim"
    cmd = [
        "g++", "-std=c++11", "-O2",
        "-I", str(OUT_DIR.parent.parent / "firmware/temp_control"),
        "-I", str(U8G2_SRC),
        str(OUT_DIR / "sim.cpp"),
    ] + [str(s) for s in sources] + ["-o", str(out)]
    subprocess.run(cmd, check=True)
    return out


def read_pbm(path):
    tokens = path.read_text().split()
    assert tokens[0] == "P1", tokens[0]
    w, h = int(tokens[1]), int(tokens[2])
    bits = tokens[3:3 + w * h]
    return [[bits[y * w + x] == "1" for x in range(w)] for y in range(h)]


def svg_from_bitmap(bits, asleep=False):
    b = []
    b.append(
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d">' % (W * SCALE, H * SCALE, W, H)
    )
    b.append("<defs>")
    b.append(
        '<linearGradient id="bezel" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
        "</linearGradient>" % (BEZEL_TOP, BEZEL_BOTTOM)
    )
    b.append(
        '<radialGradient id="glass" cx="46%%" cy="38%%" r="78%%">'
        '<stop offset="0" stop-color="#0a202c"/>'
        '<stop offset="1" stop-color="%s"/></radialGradient>' % GLASS
    )
    b.append(
        '<linearGradient id="sheen" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0.08"/>'
        '<stop offset="0.45" stop-color="#ffffff" stop-opacity="0"/>'
        "</linearGradient>"
    )
    b.append(
        '<filter id="glow" x="-15%" y="-15%" width="130%" height="130%">'
        '<feGaussianBlur stdDeviation="0.22" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>'
        "</filter>"
    )
    b.append("</defs>")

    b.append('<rect x="0" y="0" width="%d" height="%d" rx="13" fill="url(#bezel)"/>' % (W, H))
    b.append('<rect x="0.6" y="0.6" width="%s" height="%s" rx="12.4" fill="none" '
             'stroke="#394652" stroke-width="0.8" opacity="0.9"/>' % (W - 1.2, H - 1.2))
    b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="url(#glass)"/>'
             % (PAD, PAD, GW, GH))

    if not asleep:
        b.append('<g transform="translate(%d %d)" filter="url(#glow)" fill="%s">'
                 % (PAD, PAD, PIXEL))
        for y in range(GH):
            row = bits[y]
            x = 0
            while x < GW:
                if not row[x]:
                    x += 1
                    continue
                start = x
                while x < GW and row[x]:
                    x += 1
                b.append('<rect x="%d" y="%d" width="%d" height="1"/>'
                         % (start, y, x - start))
        b.append("</g>")

    b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="url(#sheen)"/>'
             % (PAD, PAD, GW, GH))
    b.append('<rect x="%d" y="%d" width="%d" height="%d" rx="2" fill="none" '
             'stroke="#0e1a24" stroke-width="0.6"/>' % (PAD, PAD, GW, GH))
    b.append("</svg>")
    return "".join(b)


def find_chrome():
    for name in ("chrome", "google-chrome", "msedge", "chromium"):
        path = shutil.which(name)
        if path:
            return path
    for path in (
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe",
        "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
    ):
        if Path(path).exists():
            return path
    return None


def win_path(path):
    """WSL 路径转 Windows 路径；Chrome 是 Windows 程序，写不进 /mnt/*。"""
    text = str(Path(path).resolve())
    if text.startswith("/mnt/") and len(text) > 6:
        drive = text[5].upper()
        return drive + ":\\" + text[7:].replace("/", "\\")
    return text


def to_png(svg_path, png_path):
    chrome = find_chrome()
    if not chrome:
        print("skip png (no browser found):", png_path.name)
        return

    # Write a temporary file first. If Chrome fails, an old screenshot must
    # not be mistaken for a freshly generated one.
    tmp_png = png_path.with_name(".tmp-" + png_path.name)
    tmp_png.unlink(missing_ok=True)
    subprocess.run([
        chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=2",
        "--window-size=%d,%d" % (W * SCALE, H * SCALE),
        "--screenshot=%s" % win_path(tmp_png),
        "file:///" + win_path(svg_path).replace("\\", "/"),
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if tmp_png.exists() and tmp_png.stat().st_size > 0:
        tmp_png.replace(png_path)
        print("wrote", png_path)
    else:
        tmp_png.unlink(missing_ok=True)
        print("png failed:", png_path.name)


def main():
    want_png = "--png" in sys.argv
    with tempfile.TemporaryDirectory(prefix="temp-control-oled-") as tmp:
        build_dir = Path(tmp)
        sim = build_sim(build_dir)
        subprocess.run([str(sim)], cwd=str(build_dir), check=True)
        for stem, frame in STATES:
            bits = read_pbm(build_dir / (frame + ".pbm"))
            svg = svg_from_bitmap(bits, asleep=(frame == "frame-sleep"))
            svg_path = OUT_DIR / (stem + ".svg")
            svg_path.write_text(svg, encoding="utf-8")
            print("wrote", svg_path)
            if want_png:
                to_png(svg_path, OUT_DIR / (stem + ".png"))


if __name__ == "__main__":
    main()
