"""Checks power-ups, abilities and the logo stages against the mock badge API.

  .venv/bin/python tools/test_items.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Runner

EXPOSE = ("__T = {G = function() return G end, run = function() return run end, new_run = new_run,"
          " place_bomb = place_bomb, update_bombs = update_bombs, check_hits = check_hits,"
          " update_player = update_player, player_can = player_can, idx = idx,"
          " FLOOR = FLOOR, WALL = WALL, BLOCK = BLOCK}")

fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails += 1


def game(stage=1, seed=1):
    r = Runner(seed, expose=EXPOSE)
    T = r.lua.globals().__T
    T.new_run(stage, 1)
    G = T.G()
    G.intro = 0
    return r, T, G


def clear_row(T, G, r_, c0, c1):
    """Make a clean test strip: floor from c0 to c1 on row r_, nothing on it."""
    for c in range(c0, c1 + 1):
        i = T.idx(c, r_)
        G.grid[i] = T.FLOOR
        G["items"][i] = None
        G.deco[i] = None


def put_player(G, c, r_):
    G.player.x, G.player.y = c * 16, r_ * 16


def kill_foes(G):
    for e in G.foes.values():
        e.alive = False


# 1. power-ups are no longer rare: about one fork in five hides one
counts = []
for stage in range(1, 9):
    for seed in range(1, 4):
        r, T, G = game(stage, seed)
        items = [v for v in G["items"].values() if v != "gate"]
        blocks = sum(1 for v in G.grid.values() if v == T.BLOCK)
        counts.append((stage, len(items), blocks))
avg = sum(c[1] for c in counts) / len(counts)
print("   items per stage (avg):", round(avg, 1), " min:", min(c[1] for c in counts))
check("several power-ups per stage", avg >= 6 and min(c[1] for c in counts) >= 3)

# 2. every stage builds its picture out of breakable blocks
for stage in range(1, 9):
    r, T, G = game(stage, 5)
    pic = sum(1 for k, v in G.deco.items() if v and G.grid[k] == T.BLOCK)
    check(f"stage {stage}: picture of {pic} breakable blocks", pic >= 15)

# 3. pick-ups do what they say
r, T, G = game(1)
run = T.run()
p = G.player
for item, test in [
    ("max", lambda: run.fire == 8),
    ("pierce", lambda: run.pierce),
    ("kick", lambda: run.kick),
    ("remote", lambda: run.remote),
    ("pass", lambda: run["pass"]),
    ("life", lambda: run.lives == 4),
    ("time", lambda: G.time > 200),
]:
    i = T.idx(1, 1)
    G.grid[i] = T.FLOOR
    G["items"][i] = item
    put_player(G, 1, 1)
    T.check_hits()
    check(f"pick-up {item}", bool(test()))
G["items"][T.idx(1, 1)] = "curse"
T.check_hits()
check("pick-up curse sets an outage", p.curse in ("slow", "nobomb", "reverse"))

# 4. REMOTE: bombs wait; SELECT with no bomb left sets off the oldest
r, T, G = game(1)
run = T.run()
kill_foes(G)
run.remote = True
clear_row(T, G, 1, 1, 13)
put_player(G, 1, 1)
T.place_bomb()
for _ in range(100):
    T.update_bombs(0.05)
check("remote bomb waits past its fuse", G.nbombs == 1)
T.place_bomb()          # run.bombs is 1: no bomb left, so this detonates
T.update_bombs(0.01)
check("SELECT detonates the remote bomb", G.nbombs == 0)

# 5. FIREDANCER: the flame goes through forks
r, T, G = game(1)
run = T.run()
kill_foes(G)
clear_row(T, G, 1, 1, 13)
for c in (3, 5):
    G.grid[T.idx(c, 1)] = T.BLOCK
run.pierce = True
run.fire = 6
put_player(G, 1, 1)
T.place_bomb()
T.update_bombs(2.39)
T.update_bombs(0.02)
check("pierce breaks both forks in a row",
      G.breaking[T.idx(3, 1)] is not None and G.breaking[T.idx(5, 1)] is not None)
run.pierce = False
r, T, G = game(1)
run = T.run()
kill_foes(G)
clear_row(T, G, 1, 1, 13)
for c in (3, 5):
    G.grid[T.idx(c, 1)] = T.BLOCK
run.fire = 6
put_player(G, 1, 1)
T.place_bomb()
T.update_bombs(2.39)
T.update_bombs(0.02)
check("without pierce only the first fork breaks",
      G.breaking[T.idx(3, 1)] is not None and G.breaking[T.idx(5, 1)] is None)

# 6. KICK: walking into a bomb sends it sliding to the wall
r, T, G = game(1)
run = T.run()
kill_foes(G)
run.kick = True
clear_row(T, G, 1, 1, 13)
put_player(G, 2, 1)
T.place_bomb()
put_player(G, 1, 1)
G.bombs[T.idx(2, 1)]["pass"] = False
r.m.keys = {"right"}
G.player.want = "right"
for _ in range(40):
    T.update_player(0.03)
    T.update_bombs(0.03)
    if G.nbombs == 0:
        break
cols = [k % 15 for k in G.bombs.keys()]
check("kicked bomb slid away", len(cols) == 1 and cols[0] > 6 or G.nbombs == 0)

# 7. ZK PASS lets the player into forks, never into walls
r, T, G = game(1)
run = T.run()
G.grid[T.idx(1, 2)] = T.BLOCK
check("no pass: fork blocks", not T.player_can(1, 2))
run["pass"] = True
check("pass: fork is open", T.player_can(1, 2))
check("pass: outer wall still blocks", not T.player_can(0, 1))

# 8. OUTAGE "no bombs" stops bombs; "reverse" flips the D-pad
r, T, G = game(1)
G.player.curse, G.player.curse_t = "nobomb", 8
put_player(G, 1, 1)
T.place_bomb()
check("outage: no bombs", G.nbombs == 0)
G.player.curse = "reverse"
r.m.keys = {"right"}
G.player.want = "right"
G.grid[T.idx(1, 2)] = T.FLOOR
put_player(G, 2, 1)
G.grid[T.idx(1, 1)] = T.FLOOR
x0 = G.player.x
for _ in range(10):
    T.update_player(0.03)
check("outage: right moves left", G.player.x < x0)

# 9. REMOTE: holding SELECT sets off waiting bombs, not the one under the player
r, T, G = game(1)
run = T.run()
kill_foes(G)
run.remote = True
run.bombs = 3
clear_row(T, G, 1, 1, 13)
put_player(G, 3, 1)
T.place_bomb()
put_player(G, 6, 1)
T.place_bomb()
r.m.keys = {"select"}
for _ in range(20):
    T.update_player(0.03)
T.update_bombs(0.01)
check("hold SELECT: the far bomb went off, the one underfoot waits",
      G.bombs[T.idx(3, 1)] is None and G.bombs[T.idx(6, 1)] is not None)

print("FAILED" if fails else "all passed", fails)
sys.exit(1 if fails else 0)
