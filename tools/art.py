"""FORK BOMB art source.

Every sprite is a list of 16 rows of palette characters ('.' = see-through).
Run:  python3 tools/art.py   -> writes art.lua (loaded by the game) and
                                 tools/out/sheet.png (a preview of everything).
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Fixed colours shared by every world.
PAL = {
    "k": 0x15111F,  # outline
    "K": 0x2A2440,  # dark navy
    "w": 0xF5F3FF,  # white
    "s": 0xB9B4D0,  # light grey
    "d": 0x6E6889,  # mid grey
    "x": 0x47425E,  # dark grey
    "p": 0x9945FF,  # solana purple
    "P": 0x5E2BB0,  # dark purple
    "v": 0xC8A8FF,  # light purple
    "g": 0x14F195,  # solana green
    "G": 0x0B9E62,  # dark green
    "a": 0x3FD8E8,  # aqua
    "A": 0x1E7FA8,  # deep aqua
    "y": 0xFFD84A,  # yellow
    "o": 0xFF8A3D,  # orange
    "r": 0xE5334B,  # red
    "R": 0x8C1C2E,  # dark red
    "m": 0xFF6FB5,  # pink
    "n": 0xF6C39A,  # bread / skin
    "N": 0xC98552,  # crust
    "l": 0x8BE04E,  # lettuce
}

# Per-world colours: F floor, E floor lines, B block, L block light, D block dark.
WORLDS = [
    {"name": "DEVNET",     "F": 0x0C1714, "E": 0x16302A, "B": 0x1F9E6A, "L": 0x6FF2B8, "D": 0x0D553A},
    {"name": "TESTNET",    "F": 0x0B1420, "E": 0x16304C, "B": 0x2A86C9, "L": 0x8AD8FF, "D": 0x143F66},
    {"name": "MAINNET",    "F": 0x120D21, "E": 0x261A44, "B": 0x7A3FE0, "L": 0xC7A6FF, "D": 0x3A1C7A},
    {"name": "BREAKPOINT", "F": 0x190D17, "E": 0x381933, "B": 0xD9467F, "L": 0xFFA3CB, "D": 0x6E1A40},
]
WORLD_KEYS = "FEBLD"

N = 16


class Grid:
    def __init__(self, w=N, h=N, fill="."):
        self.w, self.h = w, h
        self.c = [[fill] * w for _ in range(h)]

    def px(self, x, y, ch):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.c[y][x] = ch

    def rect(self, x, y, w, h, ch):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.px(i, j, ch)

    def hline(self, x0, x1, y, ch):
        for i in range(x0, x1 + 1):
            self.px(i, y, ch)

    def vline(self, x, y0, y1, ch):
        for j in range(y0, y1 + 1):
            self.px(x, j, ch)

    def disc(self, cx, cy, r, ch):
        for j in range(self.h):
            for i in range(self.w):
                if (i + 0.5 - cx) ** 2 + (j + 0.5 - cy) ** 2 <= r * r:
                    self.c[j][i] = ch

    def stamp(self, rows, x=0, y=0):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != ".":
                    self.px(x + i, y + j, ch)

    def rows(self):
        return ["".join(r) for r in self.c]


def check(name, rows, w=N, h=N):
    assert len(rows) == h, f"{name}: {len(rows)} rows"
    for i, r in enumerate(rows):
        assert len(r) == w, f"{name} row {i}: {len(r)} wide: {r!r}"
        for ch in r:
            assert ch == "." or ch in PAL or ch in WORLD_KEYS, f"{name}: bad char {ch!r}"
    return rows


def mirror(rows):
    return [r[::-1] for r in rows]


def recolor(rows, mapping):
    return ["".join(mapping.get(c, c) for c in r) for r in rows]


def silhouette(rows, ch="w"):
    return ["".join(ch if c != "." else "." for c in r) for r in rows]


def glitch(rows):
    """Death frame: rows slide sideways like a desynced slot."""
    out = []
    for j, r in enumerate(rows):
        s = (2 if j % 4 == 1 else -2 if j % 4 == 3 else 0)
        if s > 0:
            r = "." * s + r[:-s]
        elif s < 0:
            r = r[-s:] + "." * (-s)
        out.append(r)
    return out


def dust(rows, keep):
    out = []
    for j, r in enumerate(rows):
        out.append("".join(c if c != "." and (i * 7 + j * 13) % keep == 0 else "." for i, c in enumerate(r)))
    return out


S = {}  # name -> rows

# ---------------------------------------------------------------- tiles
g = Grid(fill="F")
g.hline(0, 15, 0, "E")
g.vline(0, 0, 15, "E")
g.hline(4, 9, 11, "E")
g.px(10, 10, "E"); g.px(11, 9, "E"); g.px(11, 8, "E")
g.px(4, 10, "E"); g.px(4, 12, "E"); g.px(3, 11, "E")
g.px(12, 4, "E")
S["floor"] = g.rows()

# validator rack: indestructible
g = Grid(fill="k")
g.rect(1, 1, 14, 14, "d")
g.hline(1, 14, 1, "s"); g.vline(1, 1, 14, "s")
g.hline(1, 14, 14, "K"); g.vline(14, 1, 14, "K")
g.px(1, 1, "w")
for y in (3, 6, 9):
    g.hline(3, 12, y, "K")
    g.hline(3, 12, y + 1, "x")
    g.px(3, y + 1, "K")
g.px(3, 12, "g"); g.px(5, 12, "a"); g.px(7, 12, "x"); g.px(9, 12, "x")
g.hline(11, 12, 12, "K")
S["wall"] = g.rows()

# fork block: destructible
g = Grid(fill="k")
g.rect(1, 1, 14, 14, "B")
g.hline(1, 13, 1, "L"); g.vline(1, 1, 13, "L")
g.hline(2, 14, 14, "D"); g.vline(14, 2, 14, "D")
g.hline(2, 13, 13, "D"); g.vline(13, 2, 13, "D")
g.px(2, 2, "w")
# fork glyph: a chain that splits in two
for y in range(8, 12):
    g.px(7, y, "D"); g.px(8, y, "D")
for i in range(4):
    g.px(7 - i, 7 - i, "D"); g.px(8 + i, 7 - i, "D")
g.px(4, 4, "L"); g.px(11, 4, "L")
g.rect(3, 3, 2, 2, "D"); g.rect(11, 3, 2, 2, "D")
g.rect(7, 11, 2, 2, "D")
S["block"] = g.rows()

# block breaking: 3 frames
b0 = [list(r) for r in S["block"]]
crack = [(7, 2), (6, 3), (6, 4), (7, 5), (8, 6), (8, 7), (7, 8), (6, 9), (5, 10), (10, 3), (11, 7), (12, 8), (3, 7), (2, 8)]
for x, y in crack:
    b0[y][x] = "k"
S["break1"] = ["".join(r) for r in b0]
g = Grid()
for (x, y, w, h) in [(0, 0, 6, 6), (9, 1, 6, 5), (1, 9, 5, 6), (9, 9, 6, 6)]:
    g.rect(x, y, w, h, "k")
    g.rect(x + 1, y + 1, w - 2, h - 2, "B")
    g.hline(x + 1, x + w - 2, y + 1, "L")
S["break2"] = g.rows()
g = Grid()
for (x, y) in [(0, 0), (12, 1), (1, 12), (13, 13), (6, 3), (3, 7), (11, 6), (7, 12)]:
    g.rect(x, y, 3, 3, "D"); g.px(x, y, "L")
S["break3"] = g.rows()

# Solana bars (logo walls). t = top/bottom bars lean "/", m = middle leans "\".
BAR_COLS = {"1": ("g", "G", "w"), "2": ("a", "A", "w"), "3": ("p", "P", "v")}


def bar(kind, part, colors):
    face, dark, hi = colors
    g = Grid()
    top, bot = 3, 12
    for y in range(top, bot + 1):
        k = y - top  # 0..9
        lean = (bot - y) // 2 if kind == "t" else k // 2  # 0..4
        x0, x1 = 0, 15
        if part == "l":
            x0 = 4 + lean - 2
        if part == "r":
            x1 = 15 - (6 - lean) + 2
        for x in range(x0, x1 + 1):
            ch = face
            if y == top:
                ch = hi
            elif y == bot or y == bot - 1:
                ch = dark
            g.px(x, y, ch)
        if part == "l":
            g.px(x0, y, "k")
        if part == "r":
            g.px(x1, y, "k")
    g.hline(0, 15, top - 1, ".")
    return g.rows()


for n, cols in BAR_COLS.items():
    kind = "m" if n == "2" else "t"
    for part in "lcr":
        S[f"bar{n}{part}"] = bar(kind, part, cols)

# bomb: 3 pulse frames
def bomb(r, spark):
    g = Grid()
    g.disc(7.5, 9.5, r + 1, "k")
    g.disc(7.5, 9.5, r, "K")
    g.disc(6.0, 8.0, r * 0.45, "P")
    g.px(5, 7, "v"); g.px(5, 6, "w")
    g.rect(9, 2, 3, 3, "k")
    g.rect(10, 3, 1, 1, "x")
    g.px(11, 1, "s"); g.px(12, 0, "s")
    for (x, y, ch) in spark:
        g.px(x, y, ch)
    return g.rows()


S["bomb1"] = bomb(5.5, [(13, 0, "y"), (14, 0, "o"), (13, 1, "o")])
S["bomb2"] = bomb(6.2, [(13, 0, "w"), (12, 1, "y"), (14, 1, "y"), (13, 2, "y")])
S["bomb3"] = bomb(5.0, [(13, 0, "o")])

# flames: Solana gradient fire with ragged edges (purple outside, aqua, white core).
JAG = [0, 1, 0, -1, 1, 0, -1, 0, 1, -1, 0, 1, 0, -1, 1, 0]


def flame_h(kind, strength, phase):
    """A horizontal piece: kind h (through), el (tip on the left), er (tip on the right)."""
    base = {3: 6.0, 2: 5.0, 1: 3.0}[strength]
    g = Grid()
    for x in range(16):
        t = 1.0
        if kind == "el":
            t = max(0.0, min(1.0, (x - 1) / 9.0))
        if kind == "er":
            t = max(0.0, min(1.0, (14 - x) / 9.0))
        hw = base * t + (JAG[(x + phase) % 16] * 0.8 if t > 0.3 else 0)
        for y in range(16):
            d = abs(y + 0.5 - 8)
            if d <= hw:
                ch = "p"
                if d <= hw * 0.62:
                    ch = "a"
                if d <= hw * 0.28 or (d < 1 and hw > 1.5):
                    ch = "w"
                g.px(x, y, ch)
    if strength >= 2:
        g.px((3 + phase * 5) % 14 + 1, 8 - int(base * 0.5), "g")
    return g.rows()


def transpose(rows):
    return ["".join(rows[y][x] for y in range(16)) for x in range(16)]


def flame(kind, strength):
    phase = strength * 3
    if kind == "h":
        return flame_h("h", strength, phase)
    if kind == "el":
        return flame_h("el", strength, phase)
    if kind == "er":
        return flame_h("er", strength, phase)
    if kind == "v":
        return transpose(flame_h("h", strength, phase + 2))
    if kind == "eu":
        return transpose(flame_h("el", strength, phase + 2))
    if kind == "ed":
        return transpose(flame_h("er", strength, phase + 2))
    # centre: both arms plus a hot blob
    h = flame_h("h", strength, phase)
    v = transpose(flame_h("h", strength, phase + 2))
    rank = {".": 0, "g": 1, "p": 2, "a": 3, "w": 4}
    g = Grid()
    for y in range(16):
        for x in range(16):
            c = max(h[y][x], v[y][x], key=lambda ch: rank[ch])
            g.px(x, y, c)
    r = {3: 6.5, 2: 5.5, 1: 3.5}[strength]
    g.disc(8, 8, r, "p")
    g.disc(8, 8, r * 0.65, "a")
    g.disc(8, 8, r * 0.35, "w")
    if strength >= 2:
        for (x, y) in [(2, 3), (13, 2), (3, 13), (12, 12)]:
            g.px(x, y, "g")
    return g.rows()


for kind in ("c", "h", "v", "el", "er", "eu", "ed"):
    for st in (1, 2, 3):
        S[f"fire_{kind}{st}"] = flame(kind, st)

# power-ups: framed icon on a dark plate
def plate(border, icon_rows, ox=3, oy=3):
    g = Grid(fill=".")
    g.rect(1, 1, 14, 14, "k")
    g.rect(2, 2, 12, 12, "K")
    g.hline(2, 13, 1, border); g.hline(2, 13, 14, border)
    g.vline(1, 2, 13, border); g.vline(14, 2, 13, border)
    g.stamp(icon_rows, ox, oy)
    return g.rows()


ICON_BOMB = [
    "......yo..",
    ".....s....",
    "...kks....",
    "..kKKKk...",
    ".kKPKKKk..",
    ".kKvKKKk..",
    ".kKKKKKk..",
    "..kKKKk...",
    "...kkk....",
    "..........",
]
ICON_PLUS = [".g.", "ggg", ".g."]
ICON_FIRE = [
    "....p.....",
    "...pp.....",
    "...pap....",
    "..papp.p..",
    "..paap.pp.",
    ".paawapap.",
    ".pawwwaap.",
    ".pawwwwap.",
    "..paawap..",
    "...pppp...",
]
ICON_BOLT = [
    ".....yyy..",
    "....yyy...",
    "...yyy....",
    "..yyy.....",
    ".yyyyyyy..",
    ".....yy...",
    "....yy....",
    "...yy.....",
    "..yy......",
    ".y........",
]
ICON_SHIELD = [
    ".kkkkkkkk.",
    "kggggggggk",
    "kgwwggGGgk",
    "kgwgggGGgk",
    "kgggggGGgk",
    ".kgggGGgk.",
    ".kggGGGgk.",
    "..kgGGgk..",
    "...kGGk...",
    "....kk....",
]

def with_plus(icon):
    g = Grid(10, 10)
    g.stamp(icon)
    g.stamp(ICON_PLUS, 7, 7)
    return g.rows()

for name, border, icon in [
    ("pu_bomb", "p", with_plus(ICON_BOMB)),
    ("pu_fire", "o", with_plus(ICON_FIRE)),
    ("pu_speed", "y", ICON_BOLT),
    ("pu_shield", "g", ICON_SHIELD),
]:
    S[name + "1"] = plate(border, icon)
    S[name + "2"] = plate("w", icon)

# finality gate (exit)
def gate(open_, phase):
    g = Grid()
    g.rect(1, 1, 14, 14, "k")
    g.rect(2, 2, 12, 12, "x")
    g.hline(2, 13, 2, "s"); g.vline(2, 2, 13, "s")
    g.rect(4, 4, 8, 8, "k")
    if open_:
        rings = ["p", "a", "g", "w"]
        for i in range(4):
            ch = rings[(i + phase) % 4]
            g.rect(4 + i, 4 + i, 8 - 2 * i, 8 - 2 * i, ch)
    else:
        g.rect(5, 5, 6, 6, "K")
        g.hline(5, 10, 7, "x"); g.hline(5, 10, 8, "x")
        g.px(7, 9, "r"); g.px(8, 9, "r")
    # corner bolts
    for (x, y) in [(3, 3), (12, 3), (3, 12), (12, 12)]:
        g.px(x, y, "d")
    return g.rows()

S["gate0"] = gate(False, 0)
S["gate1"] = gate(True, 0)
S["gate2"] = gate(True, 1)
S["gate3"] = gate(True, 2)

# ---------------------------------------------------------------- hero "Val"
HERO_D = [
    "................",
    "....kkkkkkkk....",
    "...kppppppppk...",
    "..akpKKKKKKpka..",
    ".aakpKgKKgKpkaa.",
    ".aakpKgKKgKpkaa.",
    ".aakpKKKKKKpkaa.",
    "..akpKKggKKpka..",
    "...kppppppppk...",
    "....kkkkkkkk....",
    "...kkppppppkk...",
    "..kskppppppksk..",
    "..kskggggggksk..",
    "...kkppppppkk...",
    "....kPPkkPPk....",
    "...kkkk..kkkk...",
]
HERO_U = [
    "................",
    "....kkkkkkkk....",
    "...kppppppppk...",
    "..akppppppppka..",
    ".aakppvvvvppkaa.",
    ".aakpppppppPkaa.",
    ".aakpppppppPkaa.",
    "..akpPPPPPPPka..",
    "...kppppppppk...",
    "....kkkkkkkk....",
    "...kkppppppkk...",
    "..kskppggppksk..",
    "..kskggggggksk..",
    "...kkppppppkk...",
    "....kPPkkPPk....",
    "...kkkk..kkkk...",
]
HERO_L = [
    "................",
    "....kkkkkkkk....",
    "...kppppppppk...",
    "..kKKKKKppppk...",
    "..kKgKKKpaaak...",
    "..kKgKKKpaaak...",
    "..kKKKKKppapk...",
    "..kKggKKppppk...",
    "...kppppppppk...",
    "....kkkkkkkk....",
    "....kppppppk....",
    "....kpppsspk....",
    "....kgggsggk....",
    "....kppppppk....",
    "....kPPkPPk.....",
    "...kkkk.kkk.....",
]


def legs(rows, a, b):
    return rows[:14] + [a, b]


S["hero_d0"] = check("hero_d0", HERO_D)
S["hero_d1"] = legs(HERO_D, "....kPPk.kPk....", "...kkkk...kkk...")
S["hero_d2"] = legs(HERO_D, "....kPk.kPPk....", "...kkk...kkkk...")
S["hero_u0"] = check("hero_u0", HERO_U)
S["hero_u1"] = legs(HERO_U, "....kPPk.kPk....", "...kkkk...kkk...")
S["hero_u2"] = legs(HERO_U, "....kPk.kPPk....", "...kkk...kkkk...")
S["hero_l0"] = check("hero_l0", HERO_L)
S["hero_l1"] = legs(HERO_L, "...kPPk.kPPk....", "..kkkk..kkkk....")
S["hero_l2"] = legs(HERO_L, ".....kPPPPk.....", "....kkkkkk......")
for i in range(3):
    S[f"hero_r{i}"] = mirror(S[f"hero_l{i}"])
S["hero_x1"] = silhouette(HERO_D, "w")
S["hero_x2"] = glitch(HERO_D)
S["hero_x3"] = dust(HERO_D, 3)
S["hero_x4"] = dust(HERO_D, 9)

# ---------------------------------------------------------------- enemies
RUG1 = [
    "................",
    "................",
    "................",
    "..kkkkkkkkkkkk..",
    ".ykrrrrrrrrrrky.",
    "..krwwkrrwwkrk..",
    ".ykrwkkrrwkkrky.",
    "..krrrrrrrrrrk..",
    ".ykRoyyoRoyyoky.",
    "..krrrryyrrrrk..",
    ".ykrrrrrrrrrrky.",
    "..kkkkkkkkkkkk..",
    "...y.y.y.y.y.y..",
    "................",
    "................",
    "................",
]
RUG2 = ["................"] + [r.replace(".ykr", "y.kr").replace("rky.", "rk.y") for r in RUG1[:11]] + ["..y.y.y.y.y.y...", "................", "................", "................"]
S["rug1"] = check("rug1", RUG1)
S["rug2"] = check("rug2", RUG2)

JEET1 = [
    "................",
    ".nn..........nn.",
    ".nn..kkkkkk..nn.",
    "..k.kwwwwwwk.ka.",
    "..k.kwkwwkwk.k..",
    "...kkwkwwkwkk...",
    "....kwwwwwwk....",
    "....kwwkkwwk....",
    "....kwwwwwwk....",
    "....kssssssk....",
    "....kwwwwwwk....",
    "....ksssswwk....",
    "....kwwwwwwk....",
    "....ksswwwwk....",
    "....kwwwwkk.....",
    "....kkkkkk......",
]
JEET2 = ["................", "................", ".nn..kkkkkk..nn.", ".nk.kwwwwwwk.kn."] + JEET1[4:]
S["jeet1"] = check("jeet1", JEET1)
S["jeet2"] = check("jeet2", JEET2)

SAND1 = [
    "................",
    "................",
    "....kkkkkkkk....",
    "..kknnnnnnnnkk..",
    ".knnwknnnnwknnk.",
    ".knkknnnnnnkknk.",
    ".kNNNNNNNNNNNNk.",
    ".kllllllllllllk.",
    "kllrrlllllrrllk.",
    ".kNNNNNNNNNNNNk.",
    ".kwkwkwkwkwkwkk.",
    ".kkkkkkkkkkkkkk.",
    ".knnnnnnnnnnnnk.",
    "..kknnnnnnnnkk..",
    "....kkkkkkkk....",
    "................",
]
SAND2 = SAND1[1:11] + [".kKKKKKKKKKKKKk."] + SAND1[11:15] + ["................"]
S["sand1"] = check("sand1", SAND1)
S["sand2"] = check("sand2", SAND2)

FUD1 = [
    "................",
    ".....kkkkkk.....",
    "...kksssssskk...",
    "..ksssssssssssk.",
    ".ksddwwddwwdddk.",
    ".kddwkkddwkkddk.",
    ".kddddddddddddk.",
    ".kdddkkkkkddddk.",
    ".kddkdkdkdkdddk.",
    ".kddddddddddddk.",
    ".kxdddddddddddk.",
    ".kxxddddddddxdk.",
    ".kxxdxxdxxdxxdk.",
    ".kk..kk..kk..kk.",
    "................",
    "................",
]
FUD1[3] = "..kssssssssssk.."
FUD2 = FUD1[:12] + [".kxdxxdxxdxxdxk.", "..kk..kk..kk..k.", "................", "................"]
FUD2 = [FUD2[-1]] + FUD2[:-1]  # bob down a pixel
S["fud1"] = check("fud1", FUD1)
S["fud2"] = check("fud2", FUD2)

for e in ("rug", "jeet", "sand", "fud"):
    S[f"{e}_x1"] = silhouette(S[f"{e}1"], "w")
    S[f"{e}_x2"] = dust(S[f"{e}1"], 3)

PUFF = Grid()
for (x, y, r) in [(5, 9, 3.2), (10, 8, 3.6), (8, 5, 3.0)]:
    PUFF.disc(x, y, r, "s")
for (x, y, r) in [(5, 9, 1.6), (10, 8, 2.0), (8, 5, 1.4)]:
    PUFF.disc(x, y, r, "w")
S["puff"] = PUFF.rows()

# ---------------------------------------------------------------- HUD icons (8x8)
HUD = {
    "i_life": [
        "..kkkk..",
        ".kppppk.",
        "akKKKKka",
        "akgKKgka",
        "akKggKka",
        ".kppppk.",
        "..kkkk..",
        "........",
    ],
    "i_bomb": [
        ".....y..",
        "....s...",
        "..kks...",
        ".kKKKk..",
        "kKvKKKk.",
        "kKKKKKk.",
        ".kKKKk..",
        "..kkk...",
    ],
    "i_fire": [
        "...p....",
        "..pp.p..",
        "..pap.p.",
        ".paapap.",
        "papwaap.",
        "pawwwap.",
        ".pawwp..",
        "..ppp...",
    ],
    "i_speed": [
        "....yyy.",
        "...yyy..",
        "..yyy...",
        ".yyyyyy.",
        "....yy..",
        "...yy...",
        "..yy....",
        ".y......",
    ],
    "i_clock": [
        "..kkkk..",
        ".kwwwwk.",
        "kwwkwwwk",
        "kwwkwwwk",
        "kwwkkkwk",
        "kwwwwwwk",
        ".kwwwwk.",
        "..kkkk..",
    ],
    "i_shield": [
        "kkkkkkk.",
        "kgwgggk.",
        "kgwgGGk.",
        "kgggGGk.",
        ".kgGGk..",
        "..kGk...",
        "...k....",
        "........",
    ],
}
for k, v in HUD.items():
    check(k, v, 8, 8)

# ---------------------------------------------------------------- 5x7 pixel font for the title
FONT = {
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def title(text):
    """Chunky 2-tone title: letters 5x7 with a drop shadow, Solana gradient left to right."""
    grad = "pvaAgG"  # unused darks fall back below
    cols = ["p", "p", "v", "a", "a", "g", "g"]
    w = len(text) * 6
    g = Grid(w + 1, 9)
    for i, ch in enumerate(text):
        glyph = FONT[ch]
        for y, row in enumerate(glyph):
            for x, c in enumerate(row):
                if c == "#":
                    gx = i * 6 + x
                    g.px(gx + 1, y + 2, "k")
    for i, ch in enumerate(text):
        glyph = FONT[ch]
        for y, row in enumerate(glyph):
            for x, c in enumerate(row):
                if c == "#":
                    gx = i * 6 + x
                    t = gx / max(1, w - 1)
                    col = cols[min(len(cols) - 1, int(t * len(cols)))]
                    g.px(gx, y + 1, "w" if y == 0 else col)
    return g.rows()


S_EXTRA = {"title": title("FORK BOMB")}

# ---------------------------------------------------------------- validate + export
for k, v in S.items():
    check(k, v)


def lua_str(s):
    return '"' + s + '"'


def export():
    out = ["-- FORK BOMB art. Generated by tools/art.py: edit that file, not this one.", "local A = {}"]
    out.append("A.pal = {" + ", ".join(f"{k}=0x{v:06X}" for k, v in PAL.items()) + "}")
    out.append("A.worlds = {")
    for w in WORLDS:
        out.append("  {name=" + lua_str(w["name"]) + ", " + ", ".join(f"{k}=0x{w[k]:06X}" for k in WORLD_KEYS) + "},")
    out.append("}")
    out.append("A.s = {")
    for k, v in list(S.items()) + list(HUD.items()) + list(S_EXTRA.items()):
        out.append(f"  {k} = {{" + ",".join(lua_str(r) for r in v) + "},")
    out.append("}")
    out.append("return A")
    path = os.path.join(ROOT, "art.lua")
    with open(path, "w") as f:
        f.write("\n".join(out) + "\n")
    return path


def colour(ch, world):
    if ch in PAL:
        return PAL[ch]
    return world[ch]


def sheet(path, scale=4):
    from PIL import Image, ImageDraw
    items = list(S.items()) + list(HUD.items())
    cols = 12
    cell = 18
    rows_n = (len(items) + cols - 1) // cols
    world = WORLDS[2]
    img = Image.new("RGB", (cols * cell * scale, rows_n * (cell + 6) * scale + 40 * scale), (40, 40, 48))
    for idx, (name, rows) in enumerate(items):
        cx = (idx % cols) * cell * scale
        cy = (idx // cols) * (cell + 6) * scale
        base = Image.new("RGB", (len(rows[0]) * scale, len(rows) * scale), PAL_RGB(world["F"]))
        for y, r in enumerate(rows):
            for x, ch in enumerate(r):
                if ch != ".":
                    c = colour(ch, world)
                    for j in range(scale):
                        for i in range(scale):
                            base.putpixel((x * scale + i, y * scale + j), PAL_RGB(c))
        img.paste(base, (cx + scale, cy + scale))
        ImageDraw.Draw(img).text((cx + scale, cy + (cell - 1) * scale), name, fill=(200, 200, 210))
    ty = rows_n * (cell + 6) * scale
    x = scale
    for name, rows in S_EXTRA.items():
        for y, r in enumerate(rows):
            for xx, ch in enumerate(r):
                if ch != ".":
                    for j in range(scale):
                        for i in range(scale):
                            img.putpixel((x + xx * scale + i, ty + y * scale + j), PAL_RGB(PAL[ch]))
        x += (len(rows[0]) + 4) * scale
    img.save(path)


def PAL_RGB(v):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)


if __name__ == "__main__":
    p = export()
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    sheet(os.path.join(HERE, "out", "sheet.png"))
    print("wrote", p, "and tools/out/sheet.png;", len(S) + len(HUD) + len(S_EXTRA), "sprites")
