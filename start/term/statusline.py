#!/usr/bin/env python3
"""비서 상태줄 — 클로드 코드 맨 아래 한 줄. 부장님 터미널과 같은 모양(2026-11-18).

    ◎ BENJAMIN  생각 중 ··   11/18(수) 16:18   5시간 1% →21:00   이번 주 37% →11/20(금) 01:00   ● 비서

· 이름은 아델 설정의 display_name(없으면 bot_name).
· 상태는 ~/.adele_term/state.json (set_state.py 가 클로드 훅에서 적는다).
· 「● 비서」 = 텔레그램 말 걸기가 살아 있나(아델 폴더 data/listen_alive.txt 가 3분 안에 찍혔나).
절대 죽지 않는다 — 무엇이 틀려도 한 줄은 찍는다.
"""
import json
import os
import sys
import time

ESC = "\033["
R = ESC + "0m"
BOLD = ESC + "1m"
WEEK = "월화수목금토일"
INK = (211, 215, 222)
CLOCK = (127, 184, 216)
PAL = {
    "idle":   ([150, 85, 20],  [205, 130, 50]),
    "think":  ([235, 140, 30], [255, 185, 70]),
    "listen": ([230, 170, 40], [255, 210, 90]),
    "speak":  ([255, 160, 90], [255, 200, 150]),
}


def rgb(c):
    return f"{ESC}38;2;{c[0]};{c[1]};{c[2]}m"


def dim(c, b):
    return [int(x * b) for x in c]


def home():
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Adele")
    if os.name == "nt":
        return os.path.join(os.environ.get("LOCALAPPDATA", ""), "Adele")
    return os.path.expanduser("~/.local/share/Adele")


def name():
    try:
        with open(os.path.join(home(), "config.json"), encoding="utf-8") as f:
            c = json.load(f)
        n = (c.get("display_name") or c.get("bot_name") or "").strip()
    except Exception:
        n = ""
    return (n or "비서").upper()


def read_state():
    p = os.path.expanduser("~/.adele_term/state.json")
    try:
        with open(p, encoding="utf-8") as f:
            st = json.load(f).get("state", "idle")
        return st, time.time() - os.path.getmtime(p)
    except Exception:
        return "idle", 0


def orb(state, age, nm):
    t = int(time.time())
    NAME = rgb(PAL["think"][1]) + BOLD + nm + R
    if state == "working":
        body, acc = PAL["think"]
        frames = ["◌", "○", "◎", "◉", "◎", "○"]
        glow = [dim(body, .45), dim(body, .75), body, acc, acc, body][t % 6]
        dots = "·" * (t % 3 + 1)
        return f"{rgb(glow)}{BOLD}{frames[t % 6]}{R} {NAME}  {rgb(acc)}생각 중 {dots:<3}{R}"
    if state == "review":
        body, acc = PAL["listen"]
        return f"{rgb([body, acc][t % 2])}{BOLD}◉{R} {NAME}  {rgb(acc)}듣는 중 · 답을 기다려요{R}"
    if state == "done" and age < 90:
        body, acc = PAL["speak"]
        return f"{rgb(acc)}{BOLD}●{R} {NAME}  {rgb(acc)}완료{R}"
    body, acc = PAL["idle"]
    glow = [dim(body, .55), dim(body, .8), body, dim(body, .8)][(t // 2) % 4]
    return f"{rgb(glow)}●{R} {NAME}  {rgb(dim(acc, .7))}대기{R}"


def reset_at(lim, key):
    r = (lim or {}).get("resets_at")
    if r in (None, ""):
        return ""
    try:
        if isinstance(r, (int, float)) or str(r).replace(".", "", 1).isdigit():
            t = float(r)
            t = t / 1000 if t > 1e12 else t
        else:
            from datetime import datetime
            t = datetime.fromisoformat(str(r).replace("Z", "+00:00")).timestamp()
        lt = time.localtime(t)
    except Exception:
        return ""
    hm = f"{lt.tm_hour:02d}:{lt.tm_min:02d}"
    when = hm if key == "five_hour" else f"{lt.tm_mon}/{lt.tm_mday}({WEEK[lt.tm_wday]}) {hm}"
    return f" {rgb(CLOCK)}→{when}{R}"


def usage(data):
    out = []
    rl = (data or {}).get("rate_limits") or {}
    for key, label in (("five_hour", "5시간"), ("seven_day", "이번 주")):
        v = (rl.get(key) or {}).get("used_percentage")
        if v is None:
            continue
        v = round(float(v))
        c = rgb((255, 90, 70) if v >= 80 else (255, 210, 80) if v >= 50 else (140, 230, 120))
        out.append(f"{rgb(INK)}{BOLD}{label}{R} {c}{BOLD}{v}%{R}{reset_at(rl.get(key), key)}")
    return "   ".join(out)


def helper():
    """텔레그램 비서(말 걸기)가 살아 있나."""
    p = os.path.join(home(), "data", "listen_alive.txt")
    try:
        age = time.time() - os.path.getmtime(p)
    except Exception:
        return f"{rgb((150, 150, 150))}●{R} {rgb(INK)}비서 꺼짐{R}"
    if age < 180:
        return f"{rgb((120, 220, 120))}●{R} {rgb(INK)}비서{R}"
    return f"{rgb((255, 90, 70))}●{R} {rgb(INK)}비서 꺼짐{R}"


def main():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        data = {}
    st, age = read_state()
    lt = time.localtime()
    clock = f"{rgb(CLOCK)}{BOLD}{lt.tm_mon}/{lt.tm_mday}({WEEK[lt.tm_wday]}) {lt.tm_hour:02d}:{lt.tm_min:02d}{R}"
    parts = [orb(st, age, name()), clock]
    u = usage(data)
    if u:
        parts.append(u)
    parts.append(helper())
    print("   ".join(parts))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("● 비서")
