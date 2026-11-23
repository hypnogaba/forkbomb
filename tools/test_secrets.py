"""Checks the Finality gate reveal and the SECRETS screen, finds and !LAMP payouts.

  .venv/bin/python tools/test_secrets.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Runner

EXPOSE = ("__T = {G = function() return G end, run = function() return run end, new_run = new_run,"
          " play_tick = play_tick, find_secret = find_secret, idx = idx, IMG = IMG,"
          " FLOOR = FLOOR, BLOCK = BLOCK, settings = settings, scene = function() return scene end,"
          " menu = function() return menu end, menu_sel = function() return menu_sel end,"
          " show_over = function() show_over() end}")

fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails += 1


def toasts(r, text):
    return [t for _, t in r.m.toasts if text in t]


def keys(r, seq):
    for k in seq.split():
        r.key(k)


# 1. all foes dead while the gate is still under its fork: the fork cracks and the gate shows
for stage in range(1, 9):
    for seed in (1, 2, 3):
        r = Runner(seed, expose=EXPOSE)
        T = r.lua.globals().__T
        T.new_run(stage, 1)
        G = T.G()
        G.intro = 0
        gate_hidden = G.grid[G.gate] == T.BLOCK
        for e in G.foes.values():
            e.alive = False
            e.gone = True
        for _ in range(40):            # 1.2 s: longer than a block takes to break
            T.play_tick(0.03)
        ok = G.open and G.grid[G.gate] == T.FLOOR and G["items"][G.gate] == "gate"
        if not ok or not gate_hidden:
            check(f"stage {stage} seed {seed}: gate shown after all clear (was hidden: {gate_hidden})", ok)
check("every stage: the hidden gate breaks out once all foes are gone", True)
r = Runner(1, expose=EXPOSE)
T = r.lua.globals().__T
T.new_run(1, 1)
G = T.G()
G.intro = 0
for e in G.foes.values():
    e.alive = False
    e.gone = True
T.play_tick(0.03)
check("toast says the gate broke out", len(toasts(r, "breaks out")) == 1)
for _ in range(40):
    T.play_tick(0.03)
check("toast only once", len(toasts(r, "All clear")) == 1)
# walk onto the gate: the stage is cleared
c, rr = G.gate % 15, G.gate // 15
G.player.x, G.player.y = c * 16, rr * 16
T.play_tick(0.03)
check("walking into the revealed gate clears the stage", G.cleared)

# 2. title codes count as secrets and pay 1 !LAMP each, once
r = Runner(1, expose=EXPOSE)
T = r.lua.globals().__T
keys(r, "up up down down left right left right")
check("IBRL code: SECRET 1/5 toast", len(toasts(r, "SECRET 1/5")) == 1)
check("IBRL code: 1 !LAMP asked", (1, "secret: IBRL MODE") in r.m.awards)
keys(r, "up up down down left right left right")
check("second time: no second award", r.m.awards.count((1, "secret: IBRL MODE")) == 1)
check("stored", r.m.storage.get("secrets") is not None and r.m.storage["secrets"]["ibrl"] is True)

# 3. the SECRETS menu item shows the count and opens the screen
items = [m.id for m in T.menu().values()]
check("SECRETS is in the title menu", "secrets" in items)
label = [m.text for m in T.menu().values() if m.id == "secrets"][0]
check("label shows 1/5", label == "SECRETS 1/5")
for _ in range(items.index("secrets")):
    r.key("down")
r.key("select")
check("SELECT opens the secrets screen", T.scene() == "secrets")
r.key("back")
check("CANCEL goes back to the title", T.scene() == "title")

# 4. all five: 3 more !LAMPs and GOLD VAL, worn at once and in the skin cycle
keys(r, "left right left right up up")
check("skin code still switches skins", T.settings.skin == "toly")
keys(r, "up down up down left right")
T.find_secret("poh")
pre = T.find_secret("wagmi")
check("5th secret: ALL 5 prefix", "ALL 5" in pre)
check("all secrets: 3 !LAMPs", (3, "all secrets found") in r.m.awards)
check("GOLD VAL worn", T.settings.skin == "gold")
check("gold sprites loaded", all(T.IMG["gold_" + f] is not None for f in
      ["d0", "d1", "d2", "u0", "u1", "u2", "l0", "l1", "l2", "r0", "r1", "r2", "x1", "x2", "x3", "x4"]))
seen = []
for _ in range(4):
    keys(r, "left right left right up up")
    seen.append(T.settings.skin)
check("skin cycle includes gold", sorted(seen) == ["gold", "hero", "mert", "toly"])
check("secrets saved", all(r.m.storage["secrets"][k] is True for k in ["ibrl", "skin", "gm", "poh", "wagmi"]))

# 5. a capped day (awarded 0) keeps the secret unpaid; the next launch pays it
answers = {"n": 0}


def capped(n, reason):
    answers["n"] += 1
    return True, {"awarded": 0, "balance": 5}


r = Runner(1, award=capped, expose=EXPOSE)
keys(r, "up down up down left right")
check("capped: asked once", answers["n"] == 1)
r.key("down")
r.key("up")
keys(r, "left right")             # more keys on the title do not ask again this session
check("capped: not asked again this session", answers["n"] == 1)
store = {k: (dict(v.items()) if hasattr(v, "items") else v) for k, v in r.m.storage.items()}
# a fresh launch reads storage at boot: seed the next runner's mock storage first
import sim
orig = sim.Mock.__init__


def mock_init(self, lua, rng):
    orig(self, lua, rng)
    for k, v in store.items():
        self.storage[k] = lua.table_from(v) if isinstance(v, dict) else v


sim.Mock.__init__ = mock_init
r3 = sim.Runner(3, expose=EXPOSE)
sim.Mock.__init__ = orig
check("next launch: the unpaid secret is paid on the title", (1, "secret: GM") in r3.m.awards)
check("after paying: stored as paid", r3.m.storage.get("spaid") is not None and r3.m.storage["spaid"]["gm"] is True)

# 6. offline (not ok) does not mark the secret paid and asks again later
r = Runner(1, award=lambda n, reason: (False, "offline"), expose=EXPOSE)
keys(r, "up down up down left right")
check("offline: not paid", r.m.storage.get("spaid") is None)

# 7. not linked to X: one toast, no more asking
asks = {"n": 0}


def need_x(n, reason):
    asks["n"] += 1
    return True, {"needsX": True}


r = Runner(1, award=need_x, expose=EXPOSE)
keys(r, "up down up down left right")
keys(r, "up up down down left right left right")
check("needsX: asked once", asks["n"] == 1)
check("needsX: says link X", len(toasts(r, "Link X")) == 1)

# 8. share on X from the game-over screen: a QR to an X post that links the picture card
from urllib.parse import unquote_plus
r = Runner(1, expose=EXPOSE)
T = r.lua.globals().__T
T.new_run(2, 1)
T.run().score = 4321
cap = {}
r.lua.globals()["ui"]["qr"] = lambda x, y, size, text: cap.setdefault("t", text) and None
T.show_over()
r.key("up")
check("UP on game over: share screen", T.scene() == "share")
url = cap.get("t", "")
txt = unquote_plus(url.split("text=", 1)[1].split("&url=")[0]) if "text=" in url else ""
check("X post with the score and the stage", url.startswith("https://x.com/intent/post?text=") and "4321" in txt and "stage 1-2" in txt)
check("link to the card page", "%2Fshare%3Fs%3D4321" in url)
check("QR text fits 256 bytes", len(url) <= 256)
r.key("back")
check("CANCEL: back to game over", T.scene() == "over")

print("all passed" if fails == 0 else f"{fails} FAILED", fails)
sys.exit(1 if fails else 0)
