#!/usr/bin/env python3
"""ONE PAGE WORLD - the day's world news on a single page.

A self-contained drawing press: every letter and picture below is drawn
by this program alone (Python standard library only, no network, no
files read).  Running it writes entry.png into MAKEFUN_OUTPUT_DIR.

Design notes (this program's own):
  * Letters are hand-defined stroke paths on a 12-unit cap grid and are
    painted by measuring, for each pixel near a path, the distance to
    the nearest stroke segment; coverage fades across one pixel so the
    letterforms come out smooth instead of dotted.
  * Filled shapes (rectangles, discs, polygons) are painted with their
    own analytic or supersampled coverage, on the same canvas.
  * The page is a broadsheet: masthead with a boxed date, one lead
    story with a panorama scene, four boxed stories, and a dark
    "also today" ticker along the foot.
"""

import math
import os
import struct
import zlib

# ----------------------------------------------------------------------
# NEWS DATA - the verified world news of 25 November 2026.
#
# Each story below was checked against at least two independent
# reports (Reuters, AP, WSJ, Al Jazeera, Ukrainska Pravda and others)
# before it was put on the page.
# ----------------------------------------------------------------------
PAPER_NAME = "ONE PAGE WORLD"
DATE_WEEKDAY = "WEDNESDAY"
DATE_LINE = "25 NOVEMBER 2026"
SOURCE_LINE = "THE DAY'S WORLD NEWS ON ONE PAGE - AS REPORTED BY REUTERS, AP, AFP AND SCMP"

LEAD = {
    "chip": "MIDDLE EAST - STRAIT OF HORMUZ",
    "headline": "IRAN SAYS TWO TANKERS HIT MINES IN HORMUZ",
    "summary": "TEHRAN SAID BOTH SHIPS EXPLODED AND CAUGHT FIRE ON AN "
               "UNAUTHORISED ROUTE. OIL PRICES ROSE.",
    "scene": "war",
}

PANELS = [
    {
        "chip": "TECH - US COURT",
        "headline": "HUAWEI GUILTY OF STEALING SECRETS",
        "summary": "GUILTY OF BANK FRAUD TOO. CLEARED OF RACKETEERING.",
        "scene": "chip",
    },
    {
        "chip": "MARKETS - ASIA",
        "headline": "ASIAN STOCKS PLUNGE ON AI DOUBTS",
        "summary": "SEOUL'S KOSPI TUMBLED 6.2%. TOKYO'S NIKKEI FELL 2.8%.",
        "scene": "globe",
    },
    {
        "chip": "AMERICA - TRADE",
        "headline": "US PROPOSES TARIFFS ON 14 PARTNERS",
        "summary": "HEADLINE RATES OF 20 TO 40%. CHINA FACES THE HIGHEST.",
        "scene": "capitol",
    },
    {
        "chip": "EUROPE - WAR IN UKRAINE",
        "headline": "TWO RUSSIAN REFINERIES SET ABLAZE",
        "summary": "ROSNEFT'S SYZRAN AND KUIBYSHEV PLANTS BURNED. ONE KILLED.",
        "scene": "factory",
    },
]

TICKER = "ALSO TODAY: SHENZHOU-24 DOCKS WITH TIANGONG, CARRYING PAKISTAN'S FIRST ASTRONAUT INTO ORBIT"

# ----------------------------------------------------------------------
# Page geometry and palette (all sizes in pixels, canvas 1024 x 1024)
# ----------------------------------------------------------------------
PAGE_W = 1024
PAGE_H = 1024
MARGIN = 36
INK = (26, 26, 30)
PAPER = (247, 243, 231)
FAINT = (108, 102, 90)
ACCENT = (178, 30, 43)
NAVY = (24, 55, 96)
WHITE = (255, 255, 255)

# ----------------------------------------------------------------------
# Glyph table.  Each entry: (advance width, [stroke, ...]) where a
# stroke is a list of (x, y) points on a grid whose baseline is y=0 and
# whose cap height is y=12.  A stroke of two identical points is a dot.
# ----------------------------------------------------------------------
GLYPHS = {
    "A": (8.0, [[(0, 0), (4, 12), (8, 0)], [(1.8, 4.4), (6.2, 4.4)]]),
    "B": (8.0, [[(1.2, 0), (1.2, 12)],
                [(1.2, 12), (4.6, 12), (6.4, 10.6), (6.4, 8.6), (4.8, 7), (1.2, 7)],
                [(1.2, 7), (5, 7), (6.8, 5.2), (6.8, 2), (5, 0), (1.2, 0)]]),
    "C": (8.0, [[(7.6, 9.6), (5.4, 11.6), (3, 12), (1, 10.4), (0.4, 6),
                 (1, 1.8), (3, 0.2), (5.4, 0.4), (7.6, 2.4)]]),
    "D": (8.0, [[(1.2, 0), (1.2, 12)],
                [(1.2, 12), (4.4, 12), (6.8, 9.6), (6.8, 2.4), (4.4, 0), (1.2, 0)]]),
    "E": (7.5, [[(7, 12), (1.2, 12), (1.2, 0), (7, 0)], [(1.2, 6.2), (5.6, 6.2)]]),
    "F": (7.0, [[(1.2, 0), (1.2, 12), (7, 12)], [(1.2, 6.2), (5.4, 6.2)]]),
    "G": (8.5, [[(8, 9.8), (5.8, 11.8), (3.2, 12), (1, 10.2), (0.4, 6),
                 (1, 1.8), (3.2, 0.2), (5.8, 0.4), (8, 2.2), (8, 5.6), (5.2, 5.6)]]),
    "H": (8.0, [[(1.2, 0), (1.2, 12)], [(6.8, 0), (6.8, 12)], [(1.2, 6.2), (6.8, 6.2)]]),
    "I": (3.0, [[(1.5, 0), (1.5, 12)]]),
    "J": (6.0, [[(5, 12), (5, 2.6), (3.8, 0.6), (1.8, 0.2), (0.4, 1.6)]]),
    "K": (8.0, [[(1.2, 0), (1.2, 12)], [(6.8, 12), (1.6, 5.6)], [(2.4, 6.6), (7, 0)]]),
    "L": (7.0, [[(1.2, 12), (1.2, 0), (6.8, 0)]]),
    "M": (10.5, [[(0.8, 0), (0.8, 12), (5.2, 4.6), (9.6, 12), (9.6, 0)]]),
    "N": (8.5, [[(1.2, 0), (1.2, 12), (7.2, 0), (7.2, 12)]]),
    "O": (8.5, [[(4.2, 12), (1.2, 10.2), (0.4, 6), (1.2, 1.8), (4.2, 0),
                 (7.2, 1.8), (8, 6), (7.2, 10.2), (4.2, 12)]]),
    "P": (8.0, [[(1.2, 0), (1.2, 12)],
                [(1.2, 12), (4.8, 12), (6.8, 10.4), (6.8, 7.6), (4.8, 6), (1.2, 6)]]),
    "Q": (8.5, [[(4.2, 12), (1.2, 10.2), (0.4, 6), (1.2, 1.8), (4.2, 0),
                 (7.2, 1.8), (8, 6), (7.2, 10.2), (4.2, 12)],
                [(5.4, 3.4), (8.2, -0.6)]]),
    "R": (8.0, [[(1.2, 0), (1.2, 12)],
                [(1.2, 12), (4.8, 12), (6.8, 10.4), (6.8, 7.6), (4.8, 6), (1.2, 6)],
                [(4.6, 6), (7.2, 0)]]),
    "S": (7.5, [[(7, 10), (4.8, 12), (2.2, 11.6), (0.8, 9.4), (1.6, 7),
                 (6, 5), (7.2, 2.8), (5.6, 0.4), (2.8, 0), (0.6, 1.8)]]),
    "T": (8.0, [[(0.4, 12), (7.6, 12)], [(4, 12), (4, 0)]]),
    "U": (8.5, [[(1, 12), (1, 3.4), (2.2, 0.8), (4.2, 0), (6.2, 0.8),
                 (7.4, 3.4), (7.4, 12)]]),
    "V": (8.5, [[(0.4, 12), (4.2, 0), (8, 12)]]),
    "W": (11.5, [[(0.4, 12), (2.4, 0), (5.6, 8.6), (8.8, 0), (11, 12)]]),
    "X": (8.0, [[(0.6, 12), (7.4, 0)], [(0.6, 0), (7.4, 12)]]),
    "Y": (8.0, [[(0.4, 12), (4, 6.4), (7.6, 12)], [(4, 6.4), (4, 0)]]),
    "Z": (7.5, [[(0.6, 12), (7, 12), (0.6, 0), (7, 0)]]),
    "0": (8.0, [[(4, 12), (1.6, 10.4), (0.8, 6), (1.6, 1.6), (4, 0),
                 (6.4, 1.6), (7.2, 6), (6.4, 10.4), (4, 12)]]),
    "1": (5.5, [[(1.2, 9.4), (3.6, 12), (3.6, 0)], [(1.4, 0), (5.2, 0)]]),
    "2": (7.5, [[(0.8, 9.6), (2.4, 11.8), (5, 12), (6.8, 10), (6.4, 7.4),
                 (0.8, 0), (7, 0)]]),
    "3": (7.5, [[(0.8, 10.2), (3, 12), (5.4, 11.4), (6, 8.8), (4.6, 6.8), (3, 6.6)],
                [(3, 6.6), (5, 6.4), (6.6, 4.6), (6.2, 1.8), (4, 0), (1, 0.6)]]),
    "4": (8.0, [[(5.4, 0), (5.4, 12), (0.6, 4.2), (7.4, 4.2)]]),
    "5": (7.5, [[(6.8, 12), (1.4, 12), (1.2, 7), (4.4, 7.4), (6.6, 5.4),
                 (6.4, 2), (4.2, 0), (1.2, 0.6)]]),
    "6": (7.5, [[(6.6, 10.4), (4.4, 12), (1.8, 9.6), (0.8, 6), (1, 2.4),
                 (3, 0.2), (5.2, 0.4), (6.6, 2.4), (6.4, 5), (4.6, 6.6), (1.2, 5.2)]]),
    "7": (7.5, [[(0.6, 12), (7, 12), (3.4, 0)]]),
    "8": (7.5, [[(3.8, 6.4), (1.6, 8), (1.8, 10.6), (3.8, 12), (5.6, 10.6),
                 (5.8, 8), (3.8, 6.4), (1.4, 4.4), (1.6, 1.6), (3.8, 0),
                 (5.8, 1.6), (6, 4.4), (3.8, 6.4)]]),
    "9": (7.5, [[(0.8, 1.6), (3, 0), (5.4, 2.4), (6.4, 6), (6.2, 9.8),
                 (4.2, 11.8), (2, 11.6), (0.8, 10), (1, 7.2), (2.8, 5.6), (6.2, 6.8)]]),
    ".": (2.5, [[(1.2, 0.8), (1.2, 0.8)]]),
    ",": (2.5, [[(1.4, 1.2), (0.8, -1.2)]]),
    ":": (2.5, [[(1.2, 8.6), (1.2, 8.6)], [(1.2, 0.8), (1.2, 0.8)]]),
    ";": (2.5, [[(1.2, 8.6), (1.2, 8.6)], [(1.4, 1.2), (0.8, -1.2)]]),
    "!": (2.5, [[(1.2, 12), (1.2, 3.4)], [(1.2, 0.8), (1.2, 0.8)]]),
    "?": (7.0, [[(0.8, 9.8), (2.4, 11.8), (4.8, 11.8), (6.2, 9.8), (5.8, 7.4),
                 (3.8, 5.8), (3.8, 3.6)], [(3.8, 0.8), (3.8, 0.8)]]),
    "-": (5.0, [[(0.6, 6), (4.4, 6)]]),
    "%": (9.0, [[(2, 12), (7, 0)],
                [(2.2, 10.6), (1, 9.8), (1.2, 8.2), (2.6, 7.6), (3.8, 8.4),
                 (3.6, 10), (2.2, 10.6)],
                [(6.8, 4.4), (5.6, 3.6), (5.8, 2), (7.2, 1.4), (8.4, 2.2),
                 (8.2, 3.8), (6.8, 4.4)]]),
    "/": (5.0, [[(4.4, 12.6), (0.6, -0.6)]]),
    "(": (4.5, [[(4, 12), (1.8, 9), (1.2, 6), (1.8, 3), (4, 0)]]),
    ")": (4.5, [[(0.6, 12), (2.8, 9), (3.4, 6), (2.8, 3), (0.6, 0)]]),
    "+": (7.0, [[(0.8, 6), (6.2, 6)], [(3.5, 9.5), (3.5, 2.5)]]),
    "'": (2.5, [[(1.2, 12), (1.2, 9.6)]]),
    '"': (4.0, [[(1, 12), (1, 9.6)], [(3.2, 12), (3.2, 9.6)]]),
    "$": (7.5, [[(3.8, 13.2), (3.8, -1.2)],
                [(6.8, 10), (4.8, 11.8), (2.2, 11.4), (0.9, 9.3), (1.7, 7),
                 (5.9, 5), (7.1, 2.8), (5.5, 0.4), (2.8, 0), (0.7, 1.8)]]),
}
SPACE_ADVANCE = 4.5


# ----------------------------------------------------------------------
# Canvas: an RGB bytearray painted with coverage blending.
# ----------------------------------------------------------------------
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def blend(self, x, y, color, alpha):
        if alpha <= 0.0 or x < 0 or y < 0 or x >= self.w or y >= self.h:
            return
        i = (y * self.w + x) * 3
        keep = 1.0 - alpha
        self.px[i] = int(self.px[i] * keep + color[0] * alpha + 0.5)
        self.px[i + 1] = int(self.px[i + 1] * keep + color[1] * alpha + 0.5)
        self.px[i + 2] = int(self.px[i + 2] * keep + color[2] * alpha + 0.5)

    def rect(self, x0, y0, x1, y1, color):
        """Filled rectangle with anti-aliased edges (float coords)."""
        xa = max(0, int(math.floor(x0)))
        xb = min(self.w - 1, int(math.ceil(x1)) - 1)
        ya = max(0, int(math.floor(y0)))
        yb = min(self.h - 1, int(math.ceil(y1)) - 1)
        for y in range(ya, yb + 1):
            covy = min(y1, y + 1.0) - max(y0, float(y))
            if covy <= 0.0:
                continue
            for x in range(xa, xb + 1):
                covx = min(x1, x + 1.0) - max(x0, float(x))
                if covx > 0.0:
                    self.blend(x, y, color, covx * covy)

    def disc(self, cx, cy, rad, color):
        xa = max(0, int(cx - rad - 1))
        xb = min(self.w - 1, int(cx + rad + 1))
        ya = max(0, int(cy - rad - 1))
        yb = min(self.h - 1, int(cy + rad + 1))
        for y in range(ya, yb + 1):
            for x in range(xa, xb + 1):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                self.blend(x, y, color, min(1.0, max(0.0, rad + 0.75 - d)))

    def segment(self, ax, ay, bx, by, half, color):
        """Thick round-capped stroke from (ax, ay) to (bx, by)."""
        pad = half + 1.0
        xa = max(0, int(min(ax, bx) - pad))
        xb = min(self.w - 1, int(max(ax, bx) + pad))
        ya = max(0, int(min(ay, by) - pad))
        yb = min(self.h - 1, int(max(ay, by) + pad))
        dx = bx - ax
        dy = by - ay
        len2 = dx * dx + dy * dy
        for y in range(ya, yb + 1):
            py = y + 0.5
            for x in range(xa, xb + 1):
                px = x + 0.5
                if len2 == 0.0:
                    d = math.hypot(px - ax, py - ay)
                else:
                    t = ((px - ax) * dx + (py - ay) * dy) / len2
                    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
                    d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
                self.blend(x, y, color, min(1.0, max(0.0, half + 0.75 - d)))

    def poly(self, pts, color):
        """Filled polygon, 2x2 supersampled coverage."""
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        xa = max(0, int(min(xs)))
        xb = min(self.w - 1, int(max(xs)))
        ya = max(0, int(min(ys)))
        yb = min(self.h - 1, int(max(ys)))
        n = len(pts)
        for y in range(ya, yb + 1):
            for x in range(xa, xb + 1):
                inside = 0
                for oy in (0.25, 0.75):
                    for ox in (0.25, 0.75):
                        sx = x + ox
                        sy = y + oy
                        hit = False
                        j = n - 1
                        for i in range(n):
                            xi, yi = pts[i]
                            xj, yj = pts[j]
                            if (yi > sy) != (yj > sy):
                                xint = (xj - xi) * (sy - yi) / (yj - yi) + xi
                                if sx < xint:
                                    hit = not hit
                            j = i
                        if hit:
                            inside += 1
                if inside:
                    self.blend(x, y, color, inside / 4.0)


# ----------------------------------------------------------------------
# Text painting.  `size` is the cap height in pixels; `weight` is the
# stroke width in grid units.  Baseline y grows downward on the page,
# so glyph y is flipped when mapped to the canvas.
# ----------------------------------------------------------------------
def glyph_advance(ch, size):
    scale = size / 12.0
    if ch == " ":
        return SPACE_ADVANCE * scale
    return GLYPHS[ch][0] * scale


def auto_tracking(size, weight):
    """Breathing room per letter, proportional to stroke weight: the
    glyph paths nearly fill their advance, so heavier strokes need
    extra space or neighbouring letters collide."""
    return weight * (size / 12.0) * 0.8


def text_width(text, size, weight=2.0, tracking=None):
    if tracking is None:
        tracking = auto_tracking(size, weight)
    total = 0.0
    for ch in text:
        total += glyph_advance(ch, size) + tracking
    return total - (tracking if text else 0.0)


def draw_text(cv, x, y_base, text, size, weight, color, tracking=None):
    if tracking is None:
        tracking = auto_tracking(size, weight)
    scale = size / 12.0
    half = weight * scale / 2.0
    pen = x
    for ch in text:
        if ch == " ":
            pen += SPACE_ADVANCE * scale + tracking
            continue
        adv, strokes = GLYPHS[ch]
        for stroke in strokes:
            pts = [(pen + gx * scale, y_base - gy * scale) for gx, gy in stroke]
            for i in range(len(pts) - 1):
                cv.segment(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                           half, color)
            if len(pts) == 1:
                cv.segment(pts[0][0], pts[0][1], pts[0][0], pts[0][1], half, color)
        pen += adv * scale + tracking
    return pen - tracking


def draw_text_centered(cv, cx, y_base, text, size, weight, color, tracking=None):
    w = text_width(text, size, weight, tracking)
    return draw_text(cv, cx - w / 2.0, y_base, text, size, weight, color, tracking)


def draw_text_right(cv, xr, y_base, text, size, weight, color, tracking=None):
    w = text_width(text, size, weight, tracking)
    return draw_text(cv, xr - w, y_base, text, size, weight, color, tracking)


def wrap(text, size, max_w, weight=2.0):
    words = text.split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, size, weight) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ----------------------------------------------------------------------
# Scene: the lead panorama (panel scenes arrive in the next round)
# ----------------------------------------------------------------------
def scene_war(cv, x, y, w, h):
    sky_top = (16, 22, 48)
    sky_bot = (44, 54, 92)
    bands = 12
    for i in range(bands):
        t = i / bands
        col = tuple(int(sky_top[c] + (sky_bot[c] - sky_top[c]) * t) for c in range(3))
        cv.rect(x, y + h * i / bands, x + w, y + h * (i + 1) / bands + 1, col)
    cv.disc(x + w * 0.80, y + h * 0.30, h * 0.13, (238, 232, 200))
    for sx, sy in ((0.08, 0.22), (0.22, 0.12), (0.55, 0.16), (0.66, 0.30), (0.38, 0.28)):
        cv.disc(x + w * sx, y + h * sy, 1.6, (230, 230, 220))
    ground = y + h
    blocks = [(0.00, 0.52, 0.13), (0.14, 0.36, 0.11), (0.26, 0.60, 0.14),
              (0.41, 0.44, 0.10), (0.52, 0.66, 0.13), (0.66, 0.40, 0.11),
              (0.78, 0.56, 0.12), (0.91, 0.46, 0.09)]
    sil = (10, 12, 22)
    win = (250, 205, 110)
    for fx, fh, fw in blocks:
        bx = x + w * fx
        bw = w * fw
        by = ground - h * fh
        cv.rect(bx, by, bx + bw, ground, sil)
        rows = int(fh * h / 16)
        cols = max(1, int(bw / 15))
        for r in range(rows):
            for c in range(cols):
                if (r * 7 + c * 13 + int(fx * 100)) % 5 in (0, 2):
                    cv.rect(bx + 4 + c * 15, by + 6 + r * 16,
                            bx + 9 + c * 15, by + 11 + r * 16, win)
    ex = x + w * 0.335
    ey = ground - h * 0.62
    star = []
    for i in range(16):
        ang = i * math.pi / 8
        rad = h * (0.19 if i % 2 == 0 else 0.08)
        star.append((ex + rad * math.cos(ang), ey + rad * math.sin(ang)))
    cv.poly(star, (255, 176, 48))
    cv.disc(ex, ey, h * 0.055, (255, 226, 150))
    for gx, gy, gr in ((0.375, 0.26, 0.045), (0.415, 0.185, 0.06), (0.465, 0.12, 0.08)):
        cv.disc(x + w * gx, y + h * gy, h * gr, (146, 148, 158))


# ----------------------------------------------------------------------
# Panel icons: one small emblem per story, drawn in a square box.
# ----------------------------------------------------------------------
def icon_chip(cv, x, y, s):
    green = (10, 105, 70)
    gold = (216, 178, 60)
    cv.rect(x + s * 0.16, y + s * 0.16, x + s * 0.84, y + s * 0.84, green)
    for i in range(4):
        t = s * (0.26 + i * 0.16)
        cv.rect(x + t, y + s * 0.04, x + t + s * 0.07, y + s * 0.16, gold)
        cv.rect(x + t, y + s * 0.84, x + t + s * 0.07, y + s * 0.96, gold)
        cv.rect(x + s * 0.04, y + t, x + s * 0.16, y + t + s * 0.07, gold)
        cv.rect(x + s * 0.84, y + t, x + s * 0.96, y + t + s * 0.07, gold)
    cv.rect(x + s * 0.33, y + s * 0.33, x + s * 0.67, y + s * 0.67, (16, 140, 96))
    cv.segment(x + s * 0.38, y + s * 0.62, x + s * 0.52, y + s * 0.47,
               s * 0.035, WHITE)
    cv.segment(x + s * 0.52, y + s * 0.47, x + s * 0.63, y + s * 0.58,
               s * 0.035, WHITE)
    cv.segment(x + s * 0.52, y + s * 0.38, x + s * 0.64, y + s * 0.37,
               s * 0.035, WHITE)
    cv.segment(x + s * 0.64, y + s * 0.37, x + s * 0.63, y + s * 0.49,
               s * 0.035, WHITE)


def icon_globe(cv, x, y, s):
    cx = x + s * 0.5
    cy = y + s * 0.54
    r = s * 0.38
    cv.disc(cx, cy, r, (38, 110, 168))
    land = (52, 160, 92)
    cv.disc(cx - r * 0.34, cy - r * 0.30, r * 0.30, land)
    cv.disc(cx + r * 0.30, cy - r * 0.44, r * 0.22, land)
    cv.disc(cx + r * 0.10, cy + r * 0.36, r * 0.28, land)
    cv.disc(cx - r * 0.44, cy + r * 0.30, r * 0.18, land)
    ink = (20, 24, 30)
    pts = [(cx - r * 0.1, cy - r), (cx + r * 0.08, cy - r * 0.55),
           (cx - r * 0.14, cy - r * 0.1), (cx + r * 0.12, cy + r * 0.4),
           (cx - r * 0.02, cy + r * 0.95)]
    for i in range(len(pts) - 1):
        cv.segment(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                   s * 0.022, ink)
    flame = (232, 110, 30)
    for fx in (0.36, 0.5, 0.64):
        bx = x + s * fx
        cv.poly([(bx - s * 0.045, y + s * 0.14), (bx, y + s * 0.015),
                 (bx + s * 0.045, y + s * 0.14), (bx, y + s * 0.10)], flame)


def icon_capitol(cv, x, y, s):
    purple = (96, 62, 158)
    cx = x + s * 0.5
    base = y + s * 0.92
    cv.rect(x + s * 0.10, base - s * 0.07, x + s * 0.90, base, purple)
    cv.rect(x + s * 0.16, base - s * 0.14, x + s * 0.84, base - s * 0.07, purple)
    for i in range(5):
        lx = x + s * (0.24 + i * 0.13)
        cv.rect(lx, base - s * 0.44, lx + s * 0.055, base - s * 0.14, purple)
    cv.rect(x + s * 0.16, base - s * 0.52, x + s * 0.84, base - s * 0.44, purple)
    dome = []
    for i in range(13):
        ang = math.pi * i / 12
        dome.append((cx + s * 0.26 * math.cos(ang), base - s * 0.52 - s * 0.24 * math.sin(ang)))
    cv.poly(dome + [(cx + s * 0.26, base - s * 0.52), (cx - s * 0.26, base - s * 0.52)], purple)
    cv.segment(cx, base - s * 0.76, cx, base - s * 0.90, s * 0.018, purple)
    cv.poly([(cx, base - s * 0.90), (cx + s * 0.13, base - s * 0.855),
             (cx, base - s * 0.81)], ACCENT)


def icon_factory(cv, x, y, s):
    dark = (38, 36, 40)
    base = y + s * 0.92
    cv.rect(x + s * 0.08, base - s * 0.34, x + s * 0.92, base, dark)
    cv.rect(x + s * 0.62, base - s * 0.62, x + s * 0.74, base - s * 0.34, dark)
    cv.rect(x + s * 0.14, base - s * 0.48, x + s * 0.30, base - s * 0.34, dark)
    flame_o = (238, 116, 26)
    flame_y = (250, 190, 60)
    for fx, fh in ((0.22, 0.30), (0.40, 0.38), (0.68, 0.34)):
        bx = x + s * fx
        by = base - s * 0.34
        cv.poly([(bx - s * 0.085, by), (bx - s * 0.02, by - s * fh * 0.6),
                 (bx + s * 0.02, by - s * fh), (bx + s * 0.05, by - s * fh * 0.55),
                 (bx + s * 0.085, by)], flame_o)
        cv.poly([(bx - s * 0.04, by), (bx, by - s * fh * 0.5),
                 (bx + s * 0.04, by)], flame_y)
    cv.disc(x + s * 0.68, y + s * 0.16, s * 0.075, (130, 128, 132))
    cv.disc(x + s * 0.76, y + s * 0.10, s * 0.10, (150, 148, 152))


ICONS = {"chip": icon_chip, "globe": icon_globe,
         "capitol": icon_capitol, "factory": icon_factory}

PANEL_TINTS = [(10, 105, 70), (178, 30, 43), (96, 62, 158), (198, 106, 24)]


# ----------------------------------------------------------------------
# Page assembly
# ----------------------------------------------------------------------
def build_page():
    cv = Canvas(PAGE_W, PAGE_H, PAPER)
    right = PAGE_W - MARGIN
    inner_w = right - MARGIN

    # Masthead: paper name left (shrunk to clear the date box), date right.
    box_w = 252
    name_size = 52.0
    while text_width(PAPER_NAME, name_size, 2.15) > inner_w - box_w - 18 and name_size > 30:
        name_size -= 1.0
    draw_text(cv, MARGIN, 76, PAPER_NAME, name_size, 2.15, NAVY)
    cv.rect(right - box_w, 26, right, 88, INK)
    draw_text_centered(cv, right - box_w / 2, 52, DATE_WEEKDAY, 20, 1.6, WHITE)
    draw_text_centered(cv, right - box_w / 2, 79, DATE_LINE, 20, 1.6, WHITE)
    cv.rect(MARGIN, 98, right, 101, INK)
    cv.rect(MARGIN, 105, right, 110, INK)
    draw_text_centered(cv, PAGE_W / 2, 132, SOURCE_LINE, 16, 1.25, FAINT)
    cv.rect(MARGIN, 142, right, 144, INK)

    # Lead story.
    ly = 158
    chip = LEAD["chip"]
    chip_w = text_width(chip, 19, 1.5) + 22
    cv.rect(MARGIN, ly, MARGIN + chip_w, ly + 30, NAVY)
    draw_text(cv, MARGIN + 11, ly + 22, chip, 19, 1.5, WHITE)
    hy = ly + 30 + 58
    for line in wrap(LEAD["headline"], 58, inner_w, 2.1):
        draw_text(cv, MARGIN, hy, line, 58, 2.1, INK)
        hy += 68
    scene_y = hy - 68 + 24
    scene_war(cv, MARGIN, scene_y, inner_w, 100)
    sy = scene_y + 100 + 32
    for line in wrap(LEAD["summary"], 22.5, inner_w, 1.6):
        draw_text(cv, MARGIN, sy, line, 22.5, 1.6, INK)
        sy += 28

    # Four boxed stories in two rows.
    tick_y = PAGE_H - MARGIN - 52
    panel_top = sy + 16
    gap = 14
    panel_h = (tick_y - 14 - panel_top - gap) / 2
    panel_w = (inner_w - gap) / 2
    for idx, panel in enumerate(PANELS):
        px = MARGIN + (idx % 2) * (panel_w + gap)
        py = panel_top + (idx // 2) * (panel_h + gap)
        tint = PANEL_TINTS[idx]
        cv.rect(px, py, px + panel_w, py + 4, tint)
        pchip = panel["chip"]
        pchip_w = text_width(pchip, 16.5, 1.5) + 18
        cv.rect(px + 12, py + 12, px + 12 + pchip_w, py + 38, tint)
        draw_text(cv, px + 21, py + 31, pchip, 16.5, 1.5, WHITE)
        ICONS[panel["scene"]](cv, px + panel_w - 52, py + 4, 40)
        hbase = py + 74
        for line in wrap(panel["headline"], 30, panel_w - 24, 2.0):
            draw_text(cv, px + 12, hbase, line, 30, 2.0, INK)
            hbase += 36
        sbase = hbase + 24
        for line in wrap(panel["summary"], 19.5, panel_w - 24, 1.55):
            draw_text(cv, px + 12, sbase, line, 19.5, 1.55, INK)
            sbase += 24

    # Ticker along the foot, shrunk until it fits the band.
    cv.rect(MARGIN, tick_y, right, tick_y + 52, INK)
    tsize = 24.0
    while text_width(TICKER, tsize, 1.8) > inner_w - 28 and tsize > 12:
        tsize -= 0.5
    draw_text_centered(cv, PAGE_W / 2, tick_y + 36, TICKER, tsize, 1.8, WHITE)
    return cv


def save_png(cv, path):
    raw = bytearray()
    row = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * row:(y + 1) * row]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    save_png(build_page(), os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
