"""Checks how the badge sends scores to the leaderboard (mock http).

  .venv/bin/python tools/test_board.py
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Runner

EXPOSE = ("__T = {new_run = new_run, run = function() return run end, lost_life = lost_life,"
          " next_stage = next_stage, show_title = show_title, settings = settings}")
fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails += 1


def runner(answer):
    r = Runner(1, expose=EXPOSE)
    r.http_answer = answer
    r.T = r.lua.globals().__T
    return r


ok200 = lambda m, u, b: (True, {"status": 200, "body": '{"top":[],"me":null}', "type": "application/json"})
posts = lambda r: [c for c in r.m.http if c[0] == "POST"]

# 1. game over sends the score once, with the stage and the X handle
r = runner(ok200)
r.T.new_run(3, 1)
r.T.run().score = 4321
r.T.run().lives = 1
r.T.lost_life()
p = posts(r)
check("game over posts the score", len(p) == 1 and json.loads(p[0][2]) == {"score": 4321, "stage": 3, "epoch": 1, "name": "@val"})
check("to the leaderboard host", p and p[0][1] == "https://forkbomb-scores.hypnogaba.workers.dev/score")

# 2. a score of 0 is not sent
r = runner(ok200)
r.T.new_run(1, 1)
r.T.run().lives = 1
r.T.lost_life()
check("score 0 is not sent", len(posts(r)) == 0)

# 3. offline: kept and sent from the title screen later
state = {"online": False}
r = runner(lambda m, u, b: ok200(m, u, b) if state["online"] else (False, "offline"))
r.T.new_run(2, 1)
r.T.run().score = 777
r.T.run().lives = 1
r.T.lost_life()
check("offline score kept for later", r.m.storage.get("lb_pending") is not None)
state["online"] = True
r.T.show_title()
check("sent from the menu when back online", len(posts(r)) == 2 and json.loads(posts(r)[-1][2])["score"] == 777)
check("pending cleared after it went through", r.m.storage.get("lb_pending") is None)

# 4. "anon" when the player turns the name off
r = runner(ok200)
r.T.settings.name = False
r.T.new_run(1, 1)
r.T.run().score = 50
r.T.run().lives = 1
r.T.lost_life()
check("name off sends anon", json.loads(posts(r)[0][2])["name"] == "anon")

# 5. finishing 4-2 sends stage 8 of the finished epoch
r = runner(ok200)
r.T.new_run(1, 1)
r.T.run().stage = 8
r.T.run().score = 9000
r.T.next_stage()
check("epoch end posts stage 8, epoch 1", json.loads(posts(r)[0][2])["stage"] == 8 and json.loads(posts(r)[0][2])["epoch"] == 1)

# 6. a refused score (4xx) is final: not kept for retry; a 503 is kept
r = runner(lambda m, u, b: (True, {"status": 400, "body": "{}", "type": "application/json"}))
r.T.new_run(1, 1)
r.T.run().score = 60
r.T.run().lives = 1
r.T.lost_life()
check("400: not retried", r.m.storage.get("lb_pending") is None)
r = runner(lambda m, u, b: (True, {"status": 503, "body": "", "type": "text/plain"}))
r.T.new_run(1, 1)
r.T.run().score = 60
r.T.run().lives = 1
r.T.lost_life()
check("503: kept for later", r.m.storage.get("lb_pending") is not None)

print("FAILED" if fails else "all passed", fails)
sys.exit(1 if fails else 0)
