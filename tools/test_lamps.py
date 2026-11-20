"""Checks the !LAMP reward rules against the mock badge API (tools/sim.py).

  .venv/bin/python tools/test_lamps.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import Runner

EXPOSE = ("__T = {award = award, award_best = award_best, next_stage = next_stage,"
          " new_run = new_run, get_run = function() return run end}")


def runner(answer=None, clock=True):
    box = {"day": 0, "clock": clock}
    now = lambda: (1795000000 + box["day"] * 86400) if box["clock"] else None
    r = Runner(1, award=answer, now=now, expose=EXPOSE)
    r.box = box
    r.T = r.lua.globals().__T
    r.calls = r.m.awards
    return r


fails = 0


def check(name, cond):
    global fails
    print(("ok   " if cond else "FAIL ") + name)
    if not cond:
        fails += 1


def toasts(r, text):
    return sum(1 for _, t in r.m.toasts if text in t)


# 1. same stage twice in a day pays once; a new day pays again
r = runner()
r.T.award("s1", 1, "stage 1 cleared")
r.T.award("s1", 1, "stage 1 cleared")
check("stage pays once a day", len(r.calls) == 1)
r.box["day"] = 1
r.T.award("s1", 1, "stage 1 cleared")
check("new day pays again", len(r.calls) == 2)
check("toast shown", toasts(r, "+1 !LAMP") >= 1)

# 2. offline: nothing marked, next try asks again
state = {"online": False}
r = runner(lambda n, s: (True, {"awarded": n}) if state["online"] else (False, "offline"))
r.T.award("s2", 1, "stage 2 cleared")
state["online"] = True
r.T.award("s2", 1, "stage 2 cleared")
r.T.award("s2", 1, "stage 2 cleared")
check("offline retried, then once", len(r.calls) == 2)

# 3. no X linked: one toast, then no more requests this session
r = runner(lambda n, s: (True, {"awarded": 0, "needsX": True}))
r.T.award("s3", 1, "stage 3 cleared")
r.T.award("s4", 1, "stage 4 cleared")
check("link-X toast once", toasts(r, "Link X") == 1)
check("unlinked: stops asking", len(r.calls) == 1)

# 4. daily cap reached on the server: marked, not asked again
r = runner(lambda n, s: (True, {"awarded": 0, "balance": 5}))
r.T.award("s5", 1, "stage 5 cleared")
r.T.award("s5", 1, "stage 5 cleared")
check("cap used up: asked once", len(r.calls) == 1)

# 5. finishing 4-2 from stage 1 pays the epoch and best bonuses, once a day
r = runner()
r.T.new_run(1, 1)
r.T.get_run().stage = 8
r.T.get_run().score = 5000
r.T.next_stage()
check("epoch + best paid", (5, "epoch finished") in r.calls and (2, "new best score") in r.calls)
n = len(r.calls)
r.T.new_run(1, 1)
r.T.get_run().stage = 8
r.T.get_run().score = 9000
r.T.next_stage()
check("epoch not paid twice a day", len(r.calls) == n)

# 6. CONTINUE at 4-2 does not pay the epoch bonus
r = runner()
r.T.new_run(8, 1)
r.T.next_stage()
check("no epoch bonus on a continue", (5, "epoch finished") not in r.calls)

# 7. no best bonus for a score of 0
r = runner()
r.T.new_run(1, 1)
r.T.award_best()
check("score 0 earns no best bonus", len(r.calls) == 0)

# 8. an answer after midnight does not use up the new day
r = runner()
r.lua.execute("__real = lamps.award; lamps.award = function(n, s, cb) __held = cb end")
r.T.award("s6", 1, "stage 6 cleared")      # asked on day 0, no answer yet
r.box["day"] = 1
r.lua.execute("__held(true, {awarded = 1}); lamps.award = __real")
log = r.m.storage.get("lamps")
check("late answer not stored as today's", log is None or log["got"]["s6"] is None)
r.T.award("s6", 1, "stage 6 cleared")      # day 1 is still open, so it asks again
check("new day asks again after a late answer", len(r.calls) == 1)

# 9. a badge without a clock still earns only once per session
r = runner(clock=False)
r.T.award("s7", 1, "stage 7 cleared")
r.T.award("s7", 1, "stage 7 cleared")
check("no clock: paid once per session", len(r.calls) == 1)

# 10. a badge without the lamps module does nothing and does not crash
r = runner()
r.lua.execute("lamps = nil")
r.T.award("s8", 1, "x")
check("no lamps module: no crash", True)

print("FAILED" if fails else "all passed", fails)
sys.exit(1 if fails else 0)
