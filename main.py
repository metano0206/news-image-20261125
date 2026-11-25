#!/usr/bin/env python3
"""The World on Wednesday 25 November 2026, in one picture.

Entry for make.fun's "Sum up 25 November's world news in one image"
bounty.  Running this program writes one PNG infographic to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png when the variable
is unset).  Python 3.13 standard library only; no network, no clock,
no randomness: two runs write byte-identical files.

The picture is drawn from scratch: a hand-authored vector stroke font
(each glyph a set of polylines, stroked with round joins and
distance-based anti-aliasing), scanline shapes and simple scenes,
rendered at twice the final size and averaged down, then encoded as a
PNG with zlib.

DRAFT STATE: the NEWS DATA block below still holds yesterday's
(24 November's) stories as a placeholder, so the draft can be built,
checked and submitted through the whole pipeline.  The final version
replaces that whole block -- date line and stories -- with
25 November's news once the day is complete.  Everything outside the
block is the press that prints them, and never changes.
"""

import math
import os
import struct
import zlib

# =====================================================================
# NEWS DATA -- the whole day lives in this block, and nowhere else.
# Swap these values in one edit to update the picture; the layout code
# below never changes.  Text is upper case, like a newspaper poster.
#
# PLACEHOLDER: the values below are yesterday's (Tuesday 24 November)
# stories standing in for the draft.  The final version replaces this
# whole block -- DAY_NAME, DATE_LINE and every story -- with
# Wednesday 25 November's news.
# =====================================================================

DAY_NAME = "TUESDAY"
DATE_LINE = "24 NOVEMBER 2026"
KICKER = "THE WORLD IN ONE PICTURE"
SOURCE_LINE = "AS REPORTED BY REUTERS, AP, AFP AND SCMP"

LEAD = {
    "tag": "EUROPE - WAR IN UKRAINE",
    "color": (31, 58, 95),
    "headline": "RUSSIAN STRIKES KILL AT LEAST 14 NEAR KYIV",
    "summary": (
        "A FIVE-STOREY HOME COLLAPSED IN DYMER. RESCUERS KEPT "
        "DIGGING AS THE TOLL ROSE."
    ),
    "scene": "kyiv",
}

STORIES = [
    {
        "tag": "BUSINESS - TECH",
        "color": (13, 110, 78),
        "headline": "NVIDIA REINSTATES HUANG AS CEO",
        "summary": (
            "HUANG RETURNS UNDER TRUMP PRESSURE. SHARES LEAPT 31%."
        ),
        "scene": "chip",
    },
    {
        "tag": "CLIMATE",
        "color": (13, 115, 119),
        "headline": "COP31 TALKS COLLAPSE, NO DEAL",
        "summary": (
            "NO DEAL IN ANTALYA: THE EU REJECTED A FINAL TEXT THAT "
            "DROPPED FOSSIL FUELS."
        ),
        "scene": "globe",
    },
    {
        "tag": "AMERICA",
        "color": (91, 60, 130),
        "headline": "DEMOCRATS WIN 258 HOUSE SEATS",
        "summary": (
            "258 SEATS, THE BIGGEST MAJORITY SINCE 1992. CONTROL "
            "BEGINS IN JANUARY."
        ),
        "scene": "capitol",
    },
    {
        "tag": "ASIA - INDONESIA",
        "color": (178, 84, 22),
        "headline": "FACTORY FIRE KILLS AT LEAST 26",
        "summary": (
            "THE TOLL ROSE IN THE BANTEN CANDY FACTORY. EIGHT "
            "STILL MISSING."
        ),
        "scene": "factory",
    },
]

TICKER = (
    "ALSO TODAY: OREGON AND VIRGINIA SUE SPACEX OVER GROK AI IMAGES"
)

# =====================================================================
# THE FONT -- a vector stroke face, authored for this program.
# Each glyph is (width, [stroke, ...]) in font units: x grows right,
# y grows down, cap height is 10 units (y=0 is the cap line, y=10 the
# baseline).  A stroke is a polyline; curves are ellipse arcs expanded
# by arc().  Strokes are drawn with round caps and joins, so a lone
# point renders as a round dot.
# =====================================================================


def arc(cx, cy, rx, ry, a0, a1, steps=12):
    """Points along an ellipse, angles in degrees, y axis pointing
    down (so increasing angles sweep clockwise on the page)."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


GLYPHS = {
    "A": (7.4, [[(0.3, 10), (3.7, 0), (7.1, 10)],
                [(1.5, 6.4), (5.9, 6.4)]]),
    "B": (7.2, [[(0, 0), (0, 10)],
                [(0, 0), (3.6, 0)] + arc(3.6, 2.5, 2.3, 2.5, -90, 90, 8)
                + [(0, 5)],
                [(0, 5), (4.2, 5)] + arc(4.2, 7.5, 2.7, 2.5, -90, 90, 8)
                + [(0, 10)]]),
    "C": (7.6, [arc(3.9, 5, 3.6, 5, -52, -308, 18)]),
    "D": (7.4, [[(0, 0), (0, 10)],
                [(0, 0), (3.3, 0)] + arc(3.3, 5, 3.5, 5, -90, 90, 12)
                + [(0, 10)]]),
    "E": (6.4, [[(6.4, 0), (0, 0), (0, 10), (6.4, 10)],
                [(0, 5), (5.2, 5)]]),
    "F": (6.2, [[(6.2, 0), (0, 0), (0, 10)],
                [(0, 5), (5.0, 5)]]),
    "G": (7.8, [arc(3.9, 5, 3.6, 5, -52, -325, 18)
                + [(6.85, 5.4), (4.3, 5.4)]]),
    "H": (7.4, [[(0, 0), (0, 10)], [(7.4, 0), (7.4, 10)],
                [(0, 5), (7.4, 5)]]),
    "I": (3.4, [[(0, 0), (3.4, 0)], [(1.7, 0), (1.7, 10)],
                [(0, 10), (3.4, 10)]]),
    "J": (6.4, [[(6.2, 0), (6.2, 6.6)]
                + arc(4.2, 6.6, 2.0, 3.4, 0, 90, 8) + [(0.9, 10)]]),
    "K": (7.2, [[(0, 0), (0, 10)], [(6.9, 0), (0.7, 5.4)],
                [(1.9, 4.3), (7.1, 10)]]),
    "L": (6.2, [[(0, 0), (0, 10), (6.2, 10)]]),
    "M": (8.8, [[(0, 10), (0, 0), (4.4, 6.4), (8.8, 0), (8.8, 10)]]),
    "N": (7.6, [[(0, 10), (0, 0), (7.6, 10), (7.6, 0)]]),
    "O": (7.8, [arc(3.9, 5, 3.6, 5, -90, 270, 24)]),
    "P": (6.8, [[(0, 10), (0, 0), (3.7, 0)]
                + arc(3.7, 2.6, 2.7, 2.6, -90, 90, 10) + [(0, 5.2)]]),
    "Q": (7.8, [arc(3.9, 5, 3.6, 5, -90, 270, 24),
                [(4.5, 7.3), (7.7, 10.3)]]),
    "R": (6.8, [[(0, 10), (0, 0), (3.7, 0)]
                + arc(3.7, 2.6, 2.7, 2.6, -90, 90, 10) + [(0, 5.2)],
                [(3.3, 5.2), (7.0, 10)]]),
    "S": (6.8, [[(6.2, 1.9), (5.0, 0.5), (3.3, 0), (1.6, 0.6),
                 (0.7, 1.9), (0.9, 3.3), (2.1, 4.3), (4.5, 5.6),
                 (5.8, 6.7), (6.1, 8.1), (5.1, 9.4), (3.3, 10),
                 (1.6, 9.5), (0.6, 8.3)]]),
    "T": (7.0, [[(0, 0), (7, 0)], [(3.5, 0), (3.5, 10)]]),
    "U": (7.4, [[(0, 0), (0, 6.6)]
                + arc(3.7, 6.6, 3.7, 3.4, 180, 0, 12) + [(7.4, 0)]]),
    "V": (7.4, [[(0, 0), (3.7, 10), (7.4, 0)]]),
    "W": (10.2, [[(0, 0), (1.9, 10), (5.1, 3.6), (8.3, 10),
                  (10.2, 0)]]),
    "X": (7.2, [[(0, 0), (7.2, 10)], [(7.2, 0), (0, 10)]]),
    "Y": (7.2, [[(0, 0), (3.6, 4.8), (7.2, 0)],
                [(3.6, 4.8), (3.6, 10)]]),
    "Z": (6.8, [[(0, 0), (6.8, 0), (0, 10), (6.8, 10)]]),
    "0": (7.2, [arc(3.6, 5, 3.2, 5, -90, 270, 24)]),
    "1": (5.4, [[(0.9, 2.0), (3.0, 0.1), (3.0, 10)],
                [(0.8, 10), (5.2, 10)]]),
    "2": (6.8, [[(0.9, 1.8), (1.8, 0.5), (3.6, 0), (5.4, 0.7),
                 (6.1, 2.2), (5.4, 4.0), (3.4, 5.9), (0.8, 9.6),
                 (0.8, 10), (6.6, 10)]]),
    "3": (6.8, [[(0.8, 1.3), (2.2, 0.2), (4.0, 0), (5.6, 0.9),
                 (5.9, 2.4), (5.1, 3.9), (3.8, 4.6), (5.2, 5.4),
                 (6.1, 6.9), (5.9, 8.6), (4.6, 9.8), (2.6, 10),
                 (1.0, 9.3), (0.6, 8.1)]]),
    "4": (7.2, [[(4.8, 10), (4.8, 0), (0.6, 7.2), (7.2, 7.2)]]),
    "5": (6.6, [[(6.2, 0), (1.0, 0), (0.8, 4.0), (2.4, 3.5),
                 (4.4, 3.7), (5.8, 4.9), (6.0, 6.7), (5.1, 8.8),
                 (3.3, 10), (1.4, 9.6), (0.5, 8.3)]]),
    "6": (6.8, [[(5.8, 1.3), (4.2, 0.3), (2.4, 0.9), (1.2, 2.8),
                 (0.7, 5.2), (0.8, 7.4), (1.8, 9.3), (3.4, 10),
                 (5.0, 9.4), (6.1, 7.8), (6.0, 6.0), (4.9, 4.7),
                 (3.2, 4.5), (1.7, 5.2)]]),
    "7": (6.6, [[(0.4, 0), (6.6, 0), (3.2, 10)]]),
    "8": (6.8, [arc(3.4, 2.5, 2.3, 2.5, -90, 270, 18),
                arc(3.4, 7.3, 2.9, 2.7, -90, 270, 20)]),
    "9": (6.8, [arc(3.4, 3.1, 2.9, 3.1, -90, 270, 20),
                [(6.3, 3.1), (6.1, 6.2), (4.9, 8.9), (3.0, 10),
                 (1.2, 9.3)]]),
    " ": (3.6, []),
    ".": (2.6, [[(1.3, 9.1), (1.3, 9.1)]]),
    ",": (2.6, [[(1.4, 8.3), (1.4, 8.3)], [(1.5, 8.6), (0.9, 10.7)]]),
    "'": (2.4, [[(1.3, 0), (1.0, 2.3)]]),
    ":": (2.6, [[(1.3, 3.0), (1.3, 3.0)], [(1.3, 8.9), (1.3, 8.9)]]),
    ";": (2.6, [[(1.3, 3.0), (1.3, 3.0)], [(1.4, 8.3), (1.4, 8.3)],
                [(1.5, 8.6), (0.9, 10.7)]]),
    "!": (2.6, [[(1.3, 0), (1.3, 6.7)], [(1.3, 9.1), (1.3, 9.1)]]),
    "?": (6.4, [[(1.0, 1.7), (1.9, 0.4), (3.5, 0), (5.0, 0.7),
                 (5.5, 2.2), (4.7, 3.9), (3.4, 5.0), (3.4, 6.7)],
                [(3.4, 9.1), (3.4, 9.1)]]),
    "-": (4.8, [[(0.6, 5), (4.2, 5)]]),
    "(": (4.0, [arc(2.8, 5, 2.6, 5.2, -70, -290, 14)]),
    ")": (4.0, [arc(1.2, 5, 2.6, 5.2, -110, 110, 14)]),
    "/": (5.6, [[(0.6, 10), (5.0, 0)]]),
    "%": (7.4, [arc(1.9, 1.9, 1.6, 1.6, -90, 270, 12),
                arc(5.5, 8.1, 1.6, 1.6, -90, 270, 12),
                [(6.8, 0), (0.6, 10)]]),
    "$": (6.8, [[(5.9, 1.7), (4.7, 0.4), (3.1, 0), (1.5, 0.6),
                 (0.8, 1.8), (1.6, 3.1), (4.3, 4.6), (5.5, 5.9),
                 (5.3, 7.9), (4.0, 9.6), (2.2, 10), (0.9, 8.9)],
                [(3.3, -0.7), (3.3, 10.7)]]),
    "&": (7.4, [[(5.9, 0.9), (4.6, 0.1), (3.0, 0.5), (2.2, 1.9),
                 (2.6, 3.3), (3.8, 4.6), (6.3, 8.0), (7.0, 9.3)],
                [(6.3, 8.0), (4.4, 9.7), (2.4, 10), (1.0, 8.9),
                 (0.9, 7.0), (1.9, 5.4), (3.8, 4.6)]]),
    "+": (6.0, [[(3.0, 2.2), (3.0, 7.8)], [(0.6, 5), (5.4, 5)]]),
    "*": (6.0, [[(3.0, 1.4), (3.0, 6.2)], [(1.1, 2.4), (4.9, 5.2)],
                [(4.9, 2.4), (1.1, 5.2)]]),
}

TRACK = 1.7        # font units of space after each glyph
STROKE_FRAC = 0.13  # stroke width as a fraction of the cap height

# =====================================================================
# THE PRESS -- a small software printing press.
# It draws into a frame buffer at SS times the final size, then
# averages each SS x SS block down to one pixel (anti-aliasing).
# All coordinates below are in final-image pixels; the press scales.
# =====================================================================

FINAL_W = 1024
FINAL_H = 1024
SS = 2
W = FINAL_W * SS
H = FINAL_H * SS

PAPER = (247, 243, 234)
INK = (26, 26, 40)
WHITE = (255, 255, 255)
RED = (178, 34, 52)
GREY = (96, 96, 110)
LIGHT_LINE = (203, 196, 180)

buf = bytearray(W * H * 3)


def _put(x, y, color):
    i = (y * W + x) * 3
    buf[i] = color[0]
    buf[i + 1] = color[1]
    buf[i + 2] = color[2]


def fill_rect(x, y, w, h, color):
    """Filled rectangle, in final-image coordinates."""
    x0, y0 = int(x * SS), int(y * SS)
    x1, y1 = int((x + w) * SS), int((y + h) * SS)
    row = bytes(color) * max(0, x1 - x0)
    for yy in range(max(0, y0), min(H, y1)):
        start = (yy * W + max(0, x0)) * 3
        buf[start:start + len(row)] = row


def fill_circle(cx, cy, r, color):
    """Filled circle by scanline spans, in final-image coordinates."""
    cx, cy, r = cx * SS, cy * SS, r * SS
    y0 = max(0, int(cy - r))
    y1 = min(H - 1, int(cy + r))
    for yy in range(y0, y1 + 1):
        dy = yy - cy
        span = int(max(0.0, r * r - dy * dy) ** 0.5)
        x0 = max(0, int(cx - span))
        x1 = min(W - 1, int(cx + span))
        row = bytes(color) * (x1 - x0 + 1)
        start = (yy * W + x0) * 3
        buf[start:start + len(row)] = row


def fill_poly(points, color):
    """Filled polygon by scanline, points in final-image coordinates."""
    pts = [(px * SS, py * SS) for px, py in points]
    ys = [p[1] for p in pts]
    y0 = max(0, int(min(ys)))
    y1 = min(H - 1, int(max(ys)))
    n = len(pts)
    for yy in range(y0, y1 + 1):
        scan = yy + 0.5
        xs = []
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if (ay <= scan < by) or (by <= scan < ay):
                xs.append(ax + (scan - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            x0 = max(0, int(xs[i]))
            x1 = min(W - 1, int(xs[i + 1]))
            if x1 >= x0:
                row = bytes(color) * (x1 - x0 + 1)
                start = (yy * W + x0) * 3
                buf[start:start + len(row)] = row


def stroke_circle(cx, cy, r, color, width=2.0):
    """Ring drawn as many small dots along the circumference."""
    steps = max(24, int(2 * math.pi * r * SS / 2))
    for i in range(steps):
        a = 2 * math.pi * i / steps
        fill_circle(cx + r * math.cos(a), cy + r * math.sin(a), width, color)


# ---------------------------------------------------------------------
# TEXT -- stroke glyphs are rasterised once per (character, size,
# weight) into a coverage mask: for every buffer pixel near the
# strokes, how much of it the ink covers, from the pixel centre's
# distance to the nearest segment.  Drawing text then blends those
# masks into the buffer, which keeps the letterforms smooth at any
# size.
# ---------------------------------------------------------------------

_MASKS = {}


def _unit(scale):
    """Final-image pixels per font unit.  The cap height is 10 units
    and equals 7 * scale pixels, matching the layout's line boxes."""
    return 0.7 * scale


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _glyph_mask(ch, scale, weight):
    """Coverage mask for one glyph: a tuple of (dx, dy, coverage) in
    buffer pixels, relative to the glyph's origin (pen position at
    the cap line)."""
    key = (ch, scale, weight)
    hit = _MASKS.get(key)
    if hit is not None:
        return hit
    _, strokes = GLYPHS.get(ch, GLYPHS[" "])
    u = _unit(scale) * SS
    half = max(0.6, 0.5 * STROKE_FRAC * 7 * scale * SS * weight)
    segs = []
    for stroke in strokes:
        pts = [(px * u, py * u) for px, py in stroke]
        if len(pts) == 1:
            segs.append((pts[0], pts[0]))
        for a, b in zip(pts, pts[1:]):
            segs.append((a, b))
    if not segs:
        _MASKS[key] = ()
        return ()
    xs = [p[0] for s in segs for p in s]
    ys = [p[1] for s in segs for p in s]
    x0 = int(math.floor(min(xs) - half - 1))
    x1 = int(math.ceil(max(xs) + half + 1))
    y0 = int(math.floor(min(ys) - half - 1))
    y1 = int(math.ceil(max(ys) + half + 1))
    items = []
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            cx, cy = xx + 0.5, yy + 0.5
            d = min(_seg_dist(cx, cy, a[0], a[1], b[0], b[1])
                    for a, b in segs)
            cov = half + 0.5 - d
            if cov > 0:
                items.append((xx, yy, 1.0 if cov >= 1.0 else cov))
    mask = tuple(items)
    _MASKS[key] = mask
    return mask


def _blit(ox, oy, mask, color):
    """Blend a coverage mask into the buffer at final-image (ox, oy)."""
    bx = int(round(ox * SS))
    by = int(round(oy * SS))
    r, g, b = color
    for dx, dy, cov in mask:
        xx, yy = bx + dx, by + dy
        if 0 <= xx < W and 0 <= yy < H:
            i = (yy * W + xx) * 3
            inv = 1.0 - cov
            buf[i] = int(r * cov + buf[i] * inv + 0.5)
            buf[i + 1] = int(g * cov + buf[i + 1] * inv + 0.5)
            buf[i + 2] = int(b * cov + buf[i + 2] * inv + 0.5)


def text_width(text, scale):
    text = text.upper()
    if not text:
        return 0.0
    units = sum(GLYPHS.get(ch, GLYPHS[" "])[0] for ch in text)
    units += TRACK * (len(text) - 1)
    return units * _unit(scale)


def draw_text(x, y, text, scale, color, align="left", weight=1.0):
    """Draw one line of capitals; (x, y) is the top-left of the line
    (the cap line), or its centre when align='center'.  Returns the
    line's width.  weight multiplies the stroke width."""
    text = text.upper()
    w = text_width(text, scale)
    if align == "center":
        x = x - w / 2
    pen = x
    u = _unit(scale)
    for ch in text:
        gw = GLYPHS.get(ch, GLYPHS[" "])[0]
        if ch != " ":
            _blit(pen, y, _glyph_mask(ch, scale, weight), color)
        pen += (gw + TRACK) * u
    return w


def wrap(text, scale, max_width):
    """Greedy word wrap: a list of lines that fit max_width pixels."""
    lines = []
    line = ""
    for word in text.split():
        trial = word if not line else line + " " + word
        if text_width(trial, scale) <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_text_block(x, y, text, scale, color, max_width, leading=None,
                    weight=1.0):
    """Wrapped paragraph; returns the y just below the last line."""
    if leading is None:
        leading = int(7 * scale * 1.45)
    for line in wrap(text, scale, max_width):
        draw_text(x, y, line, scale, color, weight=weight)
        y += leading
    return y


# =====================================================================
# SCENES -- small drawn pictures, one per story.  Each paints inside
# the box (x, y, w, h) it is given, in final-image coordinates.
# =====================================================================

def scene_kyiv(x, y, w, h):
    # Night sky, two bands of deep blue.
    fill_rect(x, y, w, h * 0.62, (24, 30, 64))
    fill_rect(x, y + h * 0.62, w, h * 0.38, (40, 44, 84))
    # Moon and a few stars (fixed positions: no randomness).
    fill_circle(x + w * 0.82, y + h * 0.18, 13, (238, 232, 200))
    for sx, sy in ((0.08, 0.12), (0.22, 0.3), (0.4, 0.1), (0.55, 0.24),
                   (0.66, 0.08), (0.3, 0.44), (0.12, 0.5)):
        fill_circle(x + w * sx, y + h * sy, 1.6, (210, 214, 235))
    # Burst of light over the skyline.
    cx, cy = x + w * 0.46, y + h * 0.52
    star = []
    for i in range(16):
        ang = math.pi * i / 8
        rad = 30 if i % 2 == 0 else 12
        star.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    fill_poly(star, (245, 166, 35))
    fill_circle(cx, cy, 8, (255, 226, 130))
    # Smoke: overlapping grey circles rising from the burst.
    for dx, dy, r in ((-16, -26, 12), (2, -40, 15), (22, -52, 11),
                      (40, -62, 8)):
        fill_circle(cx + dx, cy + dy, r, (120, 122, 140))
    # Skyline of apartment blocks along the bottom.
    ground = y + h
    blocks = ((0.0, 0.30), (0.13, 0.44), (0.27, 0.24), (0.38, 0.52),
              (0.52, 0.34), (0.63, 0.46), (0.76, 0.27), (0.87, 0.38))
    for bx, bh in blocks:
        bw = w * 0.115
        fill_rect(x + w * bx, ground - h * bh, bw, h * bh, (10, 11, 22))
        # A few lit windows, on a fixed grid.
        for wy in range(int(h * bh) - 14, 8, -16):
            for wx in (6, 20):
                if (wx + wy) % 3 == 0:
                    fill_rect(x + w * bx + wx, ground - wy - 6, 5, 7,
                              (250, 205, 110))
    fill_rect(x, ground - 3, w, 3, (6, 6, 14))


def scene_chip(x, y, w, h):
    cx, cy = x + w / 2, y + h / 2
    green = (13, 110, 78)
    # Pins on all four sides of the package.
    for i in range(4):
        px = cx - 24 + i * 16
        fill_rect(px, cy - 36, 6, 10, green)
        fill_rect(px, cy + 26, 6, 10, green)
        py = cy - 24 + i * 16
        fill_rect(cx - 36, py, 10, 6, green)
        fill_rect(cx + 26, py, 10, 6, green)
    # Body and core.
    fill_rect(cx - 28, cy - 28, 56, 56, green)
    fill_rect(cx - 15, cy - 15, 30, 30, (9, 74, 52))
    draw_text(cx, cy - 7, "AI", 2, WHITE, align="center", weight=1.2)


def scene_globe(x, y, w, h):
    cx, cy = x + w / 2, y + h / 2 + 4
    teal = (13, 115, 119)
    fill_circle(cx, cy, 24, (64, 156, 190))
    # Land masses: rough blobs on the disc.
    for dx, dy, r in ((-9, -7, 8), (6, -12, 6), (11, 5, 8),
                      (-4, 11, 7), (-15, 6, 5)):
        fill_circle(cx + dx, cy + dy, r, (52, 150, 96))
    stroke_circle(cx, cy, 24, teal, 1.4)
    # Heat waves rising off the top.
    for dx in (-14, 0, 14):
        fill_poly([(cx + dx - 3, cy - 28), (cx + dx + 3, cy - 28),
                   (cx + dx + 5, cy - 36), (cx + dx + 1, cy - 41),
                   (cx + dx - 4, cy - 36)], (214, 90, 40))


def scene_capitol(x, y, w, h):
    cx = x + w / 2
    base = y + h - 4
    purple = (91, 60, 130)
    # Dome: a spire over stacked arcs.
    fill_rect(cx - 2, base - 58, 4, 8, purple)
    fill_circle(cx, base - 48, 4, purple)
    for i, half in enumerate((10, 16, 21)):
        fill_rect(cx - half, base - 46 + i * 5, half * 2, 5, purple)
    # Entablature, columns and steps.
    fill_rect(cx - 30, base - 30, 60, 5, purple)
    for i in range(5):
        fill_rect(cx - 26 + i * 11, base - 25, 5, 20, purple)
    fill_rect(cx - 33, base - 5, 66, 3, purple)
    fill_rect(cx - 36, base - 2, 72, 2, purple)


def scene_factory(x, y, w, h):
    cx = x + w / 2
    base = y + h - 4
    dark = (52, 40, 34)
    # Chimney and a saw-tooth roof block.
    fill_rect(cx - 30, base - 40, 9, 24, dark)
    roof = [(cx - 38, base - 20), (cx - 20, base - 30), (cx - 2, base - 20),
            (cx + 16, base - 30), (cx + 34, base - 20), (cx + 38, base - 20),
            (cx + 38, base), (cx - 38, base)]
    fill_poly(roof, dark)
    # Flames above the roof: three teardrops.
    for dx, s in ((-16, 0.8), (2, 1.05), (20, 0.7)):
        fx, fy = cx + dx, base - 28
        fill_poly([(fx - 7 * s, fy), (fx, fy - 22 * s), (fx + 7 * s, fy)],
                  (224, 110, 30))
        fill_poly([(fx - 3.5 * s, fy), (fx, fy - 12 * s),
                   (fx + 3.5 * s, fy)], (248, 190, 60))
    # Smoke from the chimney.
    for dx, dy, r in ((-26, -46, 5), (-20, -52, 7), (-12, -57, 6)):
        fill_circle(cx + dx, base + dy, r, (150, 144, 136))


SCENES = {
    "kyiv": scene_kyiv,
    "chip": scene_chip,
    "globe": scene_globe,
    "capitol": scene_capitol,
    "factory": scene_factory,
}


# =====================================================================
# LAYOUT -- masthead, one lead story, four panels, one ticker line.
# =====================================================================

MARGIN = 32
PAGE_W = FINAL_W - 2 * MARGIN


def rule(y, thickness=3, color=INK):
    fill_rect(MARGIN, y, PAGE_W, thickness, color)


def draw_masthead():
    draw_text(FINAL_W // 2, 18, KICKER, 3, RED, align="center",
              weight=1.1)
    draw_text(FINAL_W // 2, 48, DAY_NAME, 4, INK, align="center",
              weight=1.15)
    draw_text(FINAL_W // 2, 90, DATE_LINE, 8, INK, align="center",
              weight=1.4)
    rule(160, 5)
    rule(168, 2)
    draw_text(FINAL_W // 2, 174, SOURCE_LINE, 2, GREY, align="center")


def draw_lead(story):
    y = 196
    h = 252
    fill_rect(MARGIN, y, PAGE_W, h, WHITE)
    fill_rect(MARGIN, y, PAGE_W, 3, INK)
    fill_rect(MARGIN, y + h - 3, PAGE_W, 3, INK)
    # Scene on the left, words on the right.
    SCENES[story["scene"]](MARGIN + 12, y + 12, 300, h - 24)
    tx = MARGIN + 328
    tw = FINAL_W - MARGIN - tx
    # Tag chip.
    chip_w = text_width(story["tag"], 3) + 20
    fill_rect(tx, y + 14, chip_w, 30, story["color"])
    draw_text(tx + 10, y + 18, story["tag"], 3, WHITE, weight=1.15)
    # Headline, then summary.
    hy = draw_text_block(tx, y + 58, story["headline"], 5, INK, tw,
                         leading=46, weight=1.25)
    draw_text_block(tx, hy + 6, story["summary"], 3, (52, 52, 66), tw,
                    leading=29)


def draw_panel(x, y, w, h, story):
    fill_rect(x, y, w, h, WHITE)
    fill_rect(x, y, w, 3, story["color"])
    fill_rect(x, y + h - 3, w, 3, LIGHT_LINE)
    pad = 16
    # Tag chip on the left; the story's scene at the top right.
    chip_w = text_width(story["tag"], 2) + 16
    fill_rect(x + pad, y + 12, chip_w, 24, story["color"])
    draw_text(x + pad + 8, y + 17, story["tag"], 2, WHITE, weight=1.15)
    SCENES[story["scene"]](x + w - pad - 88, y + 8, 88, 64)
    # Headline below the icon row, summary below the headline.
    hy = draw_text_block(x + pad, y + 84, story["headline"], 4, INK,
                         w - 2 * pad, leading=36, weight=1.2)
    draw_text_block(x + pad, hy + 6, story["summary"], 3, (52, 52, 66),
                    w - 2 * pad, leading=27)


def draw_ticker():
    y = 984
    fill_rect(MARGIN, y, PAGE_W, 36, INK)
    draw_text(FINAL_W // 2, y + 11, TICKER, 2, PAPER, align="center",
              weight=1.1)


def render():
    fill_rect(0, 0, FINAL_W, FINAL_H, PAPER)
    draw_masthead()
    draw_lead(LEAD)
    # Four panels in two rows of two.
    col_w = (PAGE_W - 16) // 2
    positions = ((MARGIN, 464), (MARGIN + col_w + 16, 464),
                 (MARGIN, 724), (MARGIN + col_w + 16, 724))
    for (px, py), story in zip(positions, STORIES):
        draw_panel(px, py, col_w, 244, story)
    draw_ticker()


# =====================================================================
# PNG ENCODING -- downsample, then store with zlib.  Fixed settings
# only, so the bytes are identical on every run.
# =====================================================================

def downsample():
    out = bytearray(FINAL_W * FINAL_H * 3)
    for fy in range(FINAL_H):
        top = (2 * fy) * W * 3
        for fx in range(FINAL_W):
            i = top + 2 * fx * 3
            j = (fy * FINAL_W + fx) * 3
            for c in range(3):
                out[j + c] = (buf[i + c] + buf[i + 3 + c] +
                              buf[i + W * 3 + c] + buf[i + W * 3 + 3 + c]) // 4
    return out


def png_bytes(pixels):
    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data +
                struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    raw = bytearray()
    stride = FINAL_W * 3
    for fy in range(FINAL_H):
        raw.append(0)
        raw += pixels[fy * stride:(fy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", FINAL_W, FINAL_H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", zlib.compress(bytes(raw), 9)) +
            chunk(b"IEND", b""))


def main():
    render()
    data = png_bytes(downsample())
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "entry.png"), "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
