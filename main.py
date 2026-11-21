#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Pure-stdlib Python 3.13 program. Draws one invented passport spread
(1024x1024 PNG) and writes it to /output/entry.png. Deterministic:
no randomness, no time, no network, no third-party libraries.

The country is Veskara, a mountain republic whose lanterns never go
out. Data page (left): portrait, holder details, MRZ strip.
Visa page (right): Kaldor entry visa, three consistent stamps,
a lantern-tax fee stamp, and a condition of stay that reveals
what kind of place Veskara is. Every date is consistent:
issued 14 MAR 2024, expires 14 MAR 2034, all stamps after issue.
"""
import hashlib
import math
import os
import struct
import zlib

W, H = 1024, 1024
OUT = "/output/entry.png"

# ---------------------------------------------------------------- palette
DESK = (35, 39, 46)
DESK_LINE = (176, 141, 60)
PAPER = (242, 236, 217)
PAPER_DARK = (228, 220, 196)
GUILLOCHE = (214, 204, 172)
INK = (28, 32, 40)
INK_SOFT = (74, 78, 88)
GOLD = (176, 141, 60)
GOLD_DARK = (140, 110, 44)
TEAL = (31, 92, 92)
TEAL_DARK = (22, 68, 68)
CREAM = (244, 238, 220)
SKIN = (217, 169, 134)
SKIN_DARK = (198, 148, 112)
HAIR = (58, 44, 34)
JACKET = (47, 79, 79)
SHIRT = (245, 244, 238)
SKY_TOP = (176, 196, 212)
SKY_BOT = (222, 231, 238)
STAMP_BLUE = (38, 68, 138)
STAMP_RED = (150, 58, 48)
STAMP_GREEN = (38, 106, 66)
VISA_BG = (31, 92, 92)

# ------------------------------------------------------------------- font
# 5x7 bitmap font, uppercase + digits + punctuation.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
}

# ------------------------------------------------------------------ canvas
buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def fill_rect(x0, y0, x1, y1, c):
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * W + x0) * 3
        buf[i:i + len(row)] = row


def hline(x0, x1, y, c):
    fill_rect(x0, y, x1, y + 1, c)


def vline(x, y0, y1, c):
    fill_rect(x, y0, x + 1, y1, c)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def rect_outline(x0, y0, x1, y1, c, t=1):
    for k in range(t):
        hline(x0 + k, x1 - k, y0 + k, c)
        hline(x0 + k, x1 - k, y1 - 1 - k, c)
        vline(x0 + k, y0 + k, y1 - k, c)
        vline(x1 - 1 - k, y0 + k, y1 - k, c)


def circle(cx, cy, r, c, t=1):
    for k in range(t):
        rr = r - k
        x = 0
        y = rr
        d = 3 - 2 * rr
        while y >= x:
            for sx, sy in ((x, y), (y, x), (-x, y), (-y, x),
                           (x, -y), (y, -x), (-x, -y), (-y, -x)):
                px(cx + sx, cy + sy, c)
            x += 1
            if d > 0:
                y -= 1
                d = d + 4 * (x - y) + 10
            else:
                d = d + 4 * x + 6


def ellipse_fill(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy / ry) ** 2
        dx = int(rx * math.sqrt(max(0.0, t)))
        hline(cx - dx, cx + dx + 1, cy + dy, c)


def poly_fill(points, c):
    # Scanline fill for a simple polygon (even-odd).
    ys = [p[1] for p in points]
    for y in range(min(ys), max(ys) + 1):
        xs = []
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                t = (y - y0) / (y1 - y0)
                xs.append(x0 + t * (x1 - x0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            hline(int(xs[k]), int(xs[k + 1]) + 1, y, c)


def rotated_rect(cx, cy, w, h, ang_deg, c, t=2):
    a = math.radians(ang_deg)
    ca, sa = math.cos(a), math.sin(a)
    corners = []
    for dx, dy in ((-w // 2, -h // 2), (w // 2, -h // 2),
                   (w // 2, h // 2), (-w // 2, h // 2)):
        corners.append((cx + int(dx * ca - dy * sa),
                        cy + int(dx * sa + dy * ca)))
    for i in range(4):
        x0, y0 = corners[i]
        x1, y1 = corners[(i + 1) % 4]
        for k in range(t):
            line(x0, y0 + k, x1, y1 + k, c)


# -------------------------------------------------------------------- text
def text_w(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, c, scale=2, xscale=None):
    s = s.upper()
    xs = scale if xscale is None else xscale
    cx = x
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(cx + col * xs, y + row * scale,
                              cx + (col + 1) * xs, y + (row + 1) * scale, c)
        cx += 6 * xs
    return cx


def draw_text_center(cx, y, s, c, scale=2):
    draw_text(cx - text_w(s, scale) // 2, y, s, c, scale)


def wrap_lines(s, max_chars):
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        nxt = (cur + " " + w).strip()
        if len(nxt) <= max_chars:
            cur = nxt
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------------- decorations
def guilloche(x0, x1, y0, y1, c):
    y = y0
    while y < y1:
        for x in range(x0, x1):
            yy = y + int(2.5 * math.sin(x / 42.0 + y / 30.0))
            px(x, yy, c)
        y += 13


def coat_of_arms(cx, cy, s):
    # Shield with a lantern inside, star above. s = overall size.
    w, h = int(30 * s), int(36 * s)
    shield = [(cx - w // 2, cy - h // 2), (cx + w // 2, cy - h // 2),
              (cx + w // 2, cy + h // 4), (cx, cy + h // 2),
              (cx - w // 2, cy + h // 4)]
    poly_fill(shield, GOLD)
    inner = [(cx - w // 2 + 3, cy - h // 2 + 3),
             (cx + w // 2 - 3, cy - h // 2 + 3),
             (cx + w // 2 - 3, cy + h // 4 - 1),
             (cx, cy + h // 2 - 4),
             (cx - w // 2 + 3, cy + h // 4 - 1)]
    poly_fill(inner, TEAL_DARK)
    # lantern: roof triangle + body + glow
    lw = int(10 * s)
    ly = cy - int(6 * s)
    poly_fill([(cx - lw, ly), (cx + lw, ly), (cx, ly - int(8 * s))], GOLD)
    fill_rect(cx - lw, ly, cx + lw, ly + int(16 * s), CREAM)
    fill_rect(cx - lw - 2, ly + int(16 * s), cx + lw + 2,
              ly + int(18 * s), GOLD)
    # star above the shield
    sy = cy - h // 2 - int(10 * s)
    for dx, dy in ((0, -4), (1, -1), (4, -1), (2, 1), (3, 4), (0, 2),
                   (-3, 4), (-2, 1), (-4, -1), (-1, -1)):
        px(cx + int(dx * s), sy + int(dy * s), GOLD)


def portrait(x0, y0, x1, y1):
    # Framed passport portrait: dignified flat-style head and shoulders.
    rect_outline(x0, y0, x1, y1, INK, 2)
    # sky bands
    bands = 12
    for i in range(bands):
        t = i / max(1, bands - 1)
        c = tuple(int(SKY_TOP[k] + (SKY_BOT[k] - SKY_TOP[k]) * t)
                  for k in range(3))
        fill_rect(x0 + 2, y0 + 2 + i * (y1 - y0 - 4) // bands,
                  x1 - 2, y0 + 2 + (i + 1) * (y1 - y0 - 4) // bands, c)
    cx = (x0 + x1) // 2
    # shoulders / jacket
    poly_fill([(cx - 52, y1 - 2), (cx - 46, y1 - 52), (cx - 18, y1 - 66),
               (cx + 18, y1 - 66), (cx + 46, y1 - 52), (cx + 52, y1 - 2)],
              JACKET)
    # shirt V + collar
    poly_fill([(cx - 14, y1 - 66), (cx + 14, y1 - 66), (cx, y1 - 40)], SHIRT)
    # neck
    fill_rect(cx - 10, y1 - 84, cx + 10, y1 - 62, SKIN_DARK)
    # head
    ellipse_fill(cx, y1 - 118, 30, 38, SKIN)
    # hair: cap over the top of the head only, clear of the eyes
    ellipse_fill(cx - 2, y1 - 146, 30, 18, HAIR)
    poly_fill([(cx - 32, y1 - 140), (cx + 28, y1 - 140),
               (cx + 30, y1 - 126), (cx - 30, y1 - 126)], HAIR)
    ellipse_fill(cx + 12, y1 - 152, 16, 9, HAIR)
    # face: eyes, brows, nose, mouth — minimal, flat
    fill_rect(cx - 16, y1 - 120, cx - 10, y1 - 116, INK)
    fill_rect(cx + 10, y1 - 120, cx + 16, y1 - 116, INK)
    line(cx - 17, y1 - 126, cx - 9, y1 - 126, HAIR)
    line(cx + 9, y1 - 126, cx + 17, y1 - 126, HAIR)
    line(cx, y1 - 114, cx - 2, y1 - 104, SKIN_DARK)
    line(cx - 7, y1 - 96, cx + 7, y1 - 96, (146, 90, 72))
    # gold lantern pin on the lapel
    circle(cx - 34, y1 - 34, 4, GOLD, 1)
    fill_rect(cx - 36, y1 - 36, cx - 32, y1 - 32, GOLD)


def stamp_circle(cx, cy, r, color, lines):
    circle(cx, cy, r, color, 2)
    circle(cx, cy, r - 6, color, 1)
    y = cy - (len(lines) * 16) // 2
    for s, scale in lines:
        draw_text_center(cx, y, s, color, scale)
        y += 16 if scale == 1 else 20


def stamp_rect(cx, cy, w, h, ang, color, lines):
    rotated_rect(cx, cy, w, h, ang, color, 2)
    rotated_rect(cx, cy, w - 10, h - 10, ang, color, 1)
    y = cy - (len(lines) * 16) // 2
    for s, scale in lines:
        draw_text_center(cx, y, s, color, scale)
        y += 16 if scale == 1 else 20


# -------------------------------------------------------------- composition
def draw():
    fill_rect(0, 0, W, H, DESK)
    rect_outline(8, 8, W - 8, H - 8, DESK_LINE, 2)

    # the open spread
    sx0, sy0, sx1, sy1 = 24, 165, 1000, 858
    fill_rect(sx0, sy0, sx1, sy1, PAPER)
    guilloche(sx0 + 10, sx1 - 10, sy0 + 10, sy1 - 10, GUILLOCHE)
    rect_outline(sx0, sy0, sx1, sy1, GOLD_DARK, 2)
    rect_outline(sx0 + 5, sy0 + 5, sx1 - 5, sy1 - 5, GOLD, 1)
    # gutter shadow
    fill_rect(509, sy0, 512, sy1, (200, 190, 160))
    fill_rect(512, sy0, 515, sy1, (214, 204, 176))

    # ---------------------------------------------------------- left page
    # coat of arms + country
    coat_of_arms(268, 208, 1.0)
    draw_text_center(268, 238, "REPUBLIC OF VESKARRA", INK, 2)
    draw_text_center(268, 266, "PASSPORT", INK, 4)
    hline(64, 472, 300, GOLD_DARK)
    draw_text_center(268, 306, "PASSEPORT", INK_SOFT, 1)

    # portrait
    portrait(64, 330, 204, 500)

    # data fields, right of the portrait
    fields = [
        ("SURNAME", "VOSS"),
        ("GIVEN NAMES", "MARA ILLYEN"),
        ("NATIONALITY", "VESKARRAN"),
        ("DATE OF BIRTH", "07 APR 1988"),
        ("PLACE OF BIRTH", "VELMORA"),
        ("SEX", "F"),
        ("DATE OF ISSUE", "14 MAR 2024"),
        ("DATE OF EXPIRY", "14 MAR 2034"),
        ("AUTHORITY", "VELMORA"),
        ("PASSPORT NO.", "VK-2044-1187"),
    ]
    fy = 330
    for label, value in fields:
        draw_text(224, fy, label, INK_SOFT, 1)
        draw_text(224, fy + 12, value, INK, 2)
        fy += 38

    # holder signature
    sy = 726
    for x in range(224, 470):
        yy = sy + int(3 * math.sin((x - 224) / 9.0))
        px(x, yy, INK)
    line(224, sy + 12, 330, sy + 2, INK)
    line(330, sy + 2, 400, sy + 10, INK)
    draw_text(224, sy + 18, "SIGNATURE OF HOLDER", INK_SOFT, 1)

    # machine-readable zone
    mrz1 = ("P<VSKVOSS<<MARA<ILLYEN" + "<" * 44)[:44]
    mrz2 = ("VK20441187<7VSK8804071F3403141" + "<" * 44)[:44]
    fill_rect(48, 782, 488, 844, PAPER_DARK)
    rect_outline(48, 782, 488, 844, INK_SOFT, 1)
    draw_text(60, 792, mrz1, INK, 2, xscale=1)
    draw_text(60, 816, mrz2, INK, 2, xscale=1)

    # ---------------------------------------------------------- right page
    draw_text_center(756, 196, "VISAS", INK, 3)
    hline(556, 956, 232, GOLD_DARK)

    # Kaldor entry visa sticker
    fill_rect(556, 244, 956, 364, VISA_BG)
    rect_outline(556, 244, 956, 364, GOLD, 2)
    rect_outline(562, 250, 950, 358, GOLD, 1)
    draw_text_center(756, 258, "ENTRY VISA", CREAM, 3)
    draw_text_center(756, 286, "KINGDOM OF KALDOR", CREAM, 2)
    draw_text_center(756, 312, "VALID 02 JUN 2024 - 19 JUN 2024", CREAM, 2)
    draw_text_center(756, 336, "SINGLE ENTRY - 17 DAYS - FEE 12 LUMENS",
                     CREAM, 1)
    draw_text(556, 372, "VISA NO. K-77120", INK_SOFT, 1)

    # stamps: consistent travel history, all after issue 14 MAR 2024
    stamp_circle(640, 452, 52, STAMP_BLUE, [
        ("ARRIVAL", 1), ("KALDOR", 2), ("02 JUN 2024", 1)])
    stamp_rect(852, 452, 196, 96, -8, STAMP_RED, [
        ("DEPARTURE", 2), ("OSTREVA", 2), ("28 SEP 2025", 1)])
    stamp_circle(700, 622, 48, STAMP_GREEN, [
        ("ARRIVAL", 1), ("MERIDIA", 2), ("03 FEB 2026", 1)])

    # lantern-tax fee stamp
    stamp_rect(862, 626, 176, 72, 6, STAMP_RED, [
        ("LANTERN TAX PAID", 1), ("2026 - 4 LUMENS", 1)])

    # condition of stay — the telling paperwork detail
    fill_rect(556, 706, 956, 826, PAPER_DARK)
    rect_outline(556, 706, 956, 826, INK, 2)
    draw_text_center(756, 718, "CONDITION OF STAY", INK, 2)
    hline(576, 936, 744, GOLD_DARK)
    cond = ("HOLDER MUST KEEP A LANTERN LIT AFTER SUNSET. "
            "NO TRAVEL BEYOND THE THIRD RIDGE WITHOUT A GUIDE.")
    lines = wrap_lines(cond, 30)
    cy = 752
    for ln in lines:
        draw_text_center(756, cy, ln, INK, 2)
        cy += 18


# --------------------------------------------------------------------- png
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


def write_png():
    raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3])
                   for y in range(H))
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "wb") as f:
        f.write(png)
    return png


def main():
    draw()
    png = write_png()
    print("wrote", OUT, len(png), "bytes",
          hashlib.sha256(png).hexdigest())


if __name__ == "__main__":
    main()
