# -*- coding: utf-8 -*-
"""설치를 클로드가 마저 해준다 — 화면 대신 말로.

**왜 만들었나.**
설치 화면(웹)은 고장났을 때 자기가 고장났다고 말을 못 한다. 2026-09-04~05 에
사명자들이 막힌 자리 일곱 중 다섯이 '조용히 죽는' 고장이었다 — 단추 14개가
안 눌려도 화면은 멀쩡해 보였고, 말 걸기가 죽어도 아무 표시가 없었다.
클로드가 대신 하면 **왜 안 되는지 말로 설명한다.** 그게 결정적인 차이다.

**어떻게 도나.**
어려운 일(텔레그램·봇·지식 풀기)은 이미 실행파일 안에 다 들어 있다. 그것들은
설치 화면이 띄운 작은 서버(127.0.0.1:8471)가 이미 밖으로 내주고 있다.
그래서 여기서는 **그 서버에 말을 걸기만 한다** — 파이썬 기본 기능만 쓰므로
사명자 컴퓨터에 아무것도 더 깔 필요가 없다.

    클로드 ──▶ setup.py ──▶ 127.0.0.1:8471 ──▶ 아델 실행파일(텔레그램·봇·크롬)

**화면은 안 띄워도 된다** (2026-09-06).
전에는 사람이 「아델 켜기」를 눌러 **브라우저 창을 띄워 둬야만** 이것이 돌았다.
부장님 데스크탑 아델은 뒤에서 도는데 사명자만 창을 붙들고 있어야 했다.
이제 서버가 안 떠 있으면 **아델을 조용히 뒤에서 깨운다**(`Adele --serve`).
사람이 눌러야 할 것은 클로드 코드를 까는 것까지다.

**쓰는 법** (클로드가 이렇게 부른다)

    python3 setup.py 상태
    python3 setup.py 이름 다니엘
    python3 setup.py 부서 내무부          ← 업무 레이더가 우리 부서 일을 골라낼 낱말을 정한다
    python3 setup.py 열쇠 010-1234-5678      ← my.telegram.org 확인 코드를 보낸다
    python3 setup.py 열쇠코드 <코드>          ← 열쇠를 대신 받고 곧바로 로그인 번호를 보낸다
    python3 setup.py 텔레그램 <api_id> <api_hash> <전화번호>   ← (열쇠를 손으로 받았을 때)
    python3 setup.py 인증번호 12345 [2단계암호]
    python3 setup.py 봇만들기 [이름]
    python3 setup.py 암호 <교회 암호>
    python3 setup.py 방목록
    python3 setup.py 방고르기 core=1,3 mixed=5
    python3 setup.py 파이어베이스
    python3 setup.py 일정 icloud|google [아이디 앱암호 [달력이름]]
    python3 setup.py 24시간켜기
    python3 setup.py 점검
    python3 setup.py 주인다시            ← 주인을 되찾을 때(비상구)
    python3 setup.py 터미널 [부를이름]    ← Ghostty 를 열면 비서가 켜지고 상태줄이 뜬다

못 하는 것은 못 한다고 말한다. 조용히 실패하지 않는다.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PORTS = (8471, 8472, 8473)                                   # 설치 화면이 앉는 자리
TIMEOUT_SLOW = 900                                           # 파이어베이스처럼 오래 걸리는 것


class NotRunning(Exception):
    """설치 화면이 안 떠 있다."""


def _home() -> Path:
    """사용자 폴더. brain 을 못 불러오므로(딸린 것이 많다) 여기서 직접 센다."""
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Adele"
    return Path.home() / "Library" / "Application Support" / "Adele"


def _find_port() -> str:
    """아델이 앉아 있는 자리. 없으면 빈 값."""
    for p in PORTS:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{p}/api/hello", timeout=2) as r:
                if json.loads(r.read() or b"{}").get("adele"):
                    return f"http://127.0.0.1:{p}"
        except (OSError, ValueError):
            continue
    return ""


def _app() -> str:
    """아델 실행파일 자리. 켤 때 `link.remember_app()` 이 적어 둔다."""
    try:
        c = json.loads((_home() / "config.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        c = {}
    got = (c.get("app_path") or "").strip()
    if got and Path(got).exists():
        return got

    # 아직 안 적혀 있는 사람 — 흔한 자리를 훑는다(한 번 켜지면 그다음부터는 위에서 잡힌다)
    name = "Adele.exe" if os.name == "nt" else "Adele"
    h = Path.home()
    fixed = [h / "Adele", h / "Desktop" / "Adele", h / "Downloads" / "Adele",
             h / "Documents" / "Adele", h / "Applications" / "Adele",
             Path("/Applications/Adele")]

    # 압축을 풀면 폴더 이름이 제각각이다 — `Adele-mac-v1.0.14` 처럼 버전이 붙거나,
    # 브라우저가 같은 이름을 피해 `Adele (1)` 로 만든다. 받는 자리만 한 겹 더 훑는다.
    # (2026-09-18 부장님 지적 — "클로드 깔고 걔한테 시켜서 다 설치하게 해야지")
    for box in (h / "Downloads", h / "Desktop", h):
        try:
            fixed += sorted((d for d in box.glob("Adele*") if d.is_dir()), reverse=True)
        except OSError:
            continue

    for d in fixed:
        for cand in (d / "프로그램" / name, d / name):
            try:
                # 폴더도 exists() 는 참이다 — **파일이고 실행되는 것**만 잡는다.
                # 안 그러면 엉뚱한 폴더를 켜려 들다 90초를 버린다(2026-09-06 겪음).
                if cand.is_file() and os.access(cand, os.X_OK):
                    return str(cand)
            except OSError:
                continue
    return ""


def _unblock(exe: str) -> None:
    """받은 표시를 뗀다 — 이게 붙어 있으면 뒤에서 켜도 운영체제가 죽인다.

    전에는 맥의 「아델 켜기」가 이 일을 했다. 그런데 그걸 누르려면 사람이
    Gatekeeper 를 먼저 뚫어야 한다 — 사명자가 가장 많이 막힌 자리다.
    클로드가 먼저 깔려 있으면 여기서 떼면 그만이라, 그 벽이 통째로 사라진다.
    실패해도 그냥 간다 — 원래 안 붙어 있는 경우가 대부분이다.
    """
    folder = Path(exe).parent
    top = folder.parent if folder.name == "프로그램" else folder
    try:
        if os.name == "nt":
            # 윈도우는 '어디서 받았는지' 표가 파일에 딸려 붙는다. 그것만 지운다.
            for p in (Path(exe), *top.rglob("*.exe")):
                try:
                    os.remove(f"{p}:Zone.Identifier")
                except OSError:
                    pass
        else:
            subprocess.run(["xattr", "-dr", "com.apple.quarantine", str(top)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=60, check=False)
    except (OSError, subprocess.SubprocessError):
        pass


def _wake(wait: int = 90) -> str:
    """아델을 **화면 없이** 뒤에서 깨운다. 자리를 잡으면 그 주소를 돌려준다.

    옛 실행파일은 `--serve` 를 모른다 — 그때는 설치 화면이 뜬다(창은 닫아도
    서버는 살아 있으므로 그래도 일은 된다). 새로 구운 것부터 조용해진다.
    """
    exe = _app()
    if not exe:
        return ""
    print("아델을 뒤에서 켜는 중입니다…")
    _unblock(exe)                                          # 받은 표시부터 뗀다
    try:
        kw = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        if os.name == "nt":
            kw["creationflags"] = 0x08000000 | 0x00000008     # 검은 창 없이 · 따로 떨어져
        else:
            kw["start_new_session"] = True                     # 이 명령이 끝나도 계속 산다
        subprocess.Popen([exe, "--serve"], **kw)
    except OSError as e:
        print(f"  켜지 못했습니다 — {type(e).__name__}: {e}")
        return ""
    for i in range(wait):
        time.sleep(1)
        got = _find_port()
        if got:
            return got
        if i and i % 30 == 0:
            print(f"  아직 켜지는 중입니다… ({i}초)")
    print("  켜 봤지만 자리를 잡지 못했습니다.")
    return ""


def _base() -> str:
    """아델의 작은 서버 자리. 안 떠 있으면 **직접 깨워서** 쓴다."""
    return _find_port() or _wake() or _no()


def _no() -> str:
    raise NotRunning(
        "아델 실행파일을 찾지 못했습니다. 받아서 압축을 푼 폴더가 안 보입니다.\n"
        "  훑어본 자리 : 홈 · 바탕화면 · 다운로드 · 문서 (이름이 Adele 로 시작하는 폴더)\n"
        "\n"
        "  [클로드에게] 압축이 아직 안 풀렸으면 풀고, 푼 자리를 알려 주면 그대로 켭니다.\n"
        "               폴더를 옮기셨다면 그 안의 Adele 을 한 번만 켜 주십시오.\n"
        "               맥에서 막히면 그 폴더에 xattr -dr com.apple.quarantine 을 걸면 됩니다.")


def call(path: str, data: dict | None = None, timeout: int = 120) -> dict:
    """설치 화면에 말을 건다. 실패는 감추지 않고 그대로 올린다."""
    url = _base() + path
    body = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"{e.code} {e.read()[:200].decode('utf-8', 'replace')}"}
    except OSError as e:
        return {"ok": False, "error": f"말을 걸지 못했습니다 — {type(e).__name__}: {e}"}


def cfg() -> dict:
    with urllib.request.urlopen(_base() + "/api/config", timeout=10) as r:
        return json.loads(r.read() or b"{}")


# ── 하나씩 ────────────────────────────────────────────────────────────
def 상태() -> int:
    """지금 어디까지 됐나. 남은 것만 짚어준다."""
    c = cfg()
    b = call("/api/brain")
    locked = call("/api/locked").get("locked", True)
    rooms = c.get("rooms") or {}
    n = len(rooms.get("core", {})) + len(rooms.get("mixed", {}))
    rows = [
        ("클로드 코드", b.get("ok"), b.get("version") or "없음"),
        ("텔레그램 로그인", bool(c.get("tg_api_id") and c.get("tg_api_hash")), ""),
        ("봇 토큰", bool(c.get("telegram_bot_token")), ""),
        ("주인(chat id)", bool(c.get("admin_telegram_id")),
         "24시간 켜두면 로그인한 본인 계정으로 저절로 정해집니다"),
        ("교회 지식", not locked, "잠겨 있으면 암호가 필요합니다"),
        ("소속 부서", bool(c.get("my_dept")), c.get("my_dept") or "업무 레이더가 우리 부서 일을 골라내는 데 씁니다"),
        ("훑을 방", n > 0, f"{n}개"),
        ("일정(선택)", bool(c.get("cal_kind") or c.get("icloud_id")), "아이폰·갤럭시 달력 — 없어도 됩니다"),
        ("업무 레이더 화면", bool(c.get("fb_project")), "없어도 나머지는 다 됩니다"),
        ("24시간 켜두기", call("/api/guard").get("ok"), "이걸 켜야 말을 걸 수 있습니다"),
    ]
    for name, ok, note in rows:
        print(f"  {'○' if ok else '✗'} {name:16} {note}")
    남은 = [r[0] for r in rows if not r[1]]
    print()
    print("다 됐습니다." if not 남은 else "아직 남은 것 : " + " · ".join(남은))
    return 0


def _로그인됐나() -> bool:
    """텔레그램 로그인이 끝났나. 안 돼 있는데 봇·방을 시키면 실행파일 속
    파이썬 오류가 그대로 새어나온다(2026-09-06 실제로 봤다) — 그 전에 막는다."""
    c = cfg()
    if not (c.get("tg_api_id") and c.get("tg_api_hash")):
        return False
    return bool(call("/api/tg/status", {}, timeout=120).get("authorized"))


# 봇 이름·설명은 텔레그램 검색에 그대로 뜬다. 어디 소속인지 드러나는 말은 못 쓰게 한다
# (정보통신부 보안 가이드 2-②, 봇 점검표 4번).
# 목록을 글자 그대로 두면 공개 저장소에서 그 낱말로 검색된다 — 한 번 감싸 둔다.
import base64 as _b64
_NO_WORDS = tuple(_b64.b64decode("7Iug7LKc7KeAfOq1kO2ajHzsp4DqtZDtmox87KeA7YyMfOy0ne2ajHzshLHrj4R87KCE64+EfOuzteydjHzrp5DslIB87JiI67CwfOyEoOq1kHzsi6DtlZl866qp7IKsfOyghOuPhOyCrHzqtazsl61867aA64WA7ZqMfOyyreuFhO2ajHzsnqXrhYTtmox87IKs66qF7J6QfOyXtOunpHzsno7sgqzqt4B87LaU7IiYfOyLnOyYqHzsnbTrp4ztnax8MTQ0fOyLreyCrOunjHzshLzthLB8Y2h1cmNofHNoaW5jaGVvbmppfHNjanx6aW9ufGdvc3BlbHxtaXNzaW9u").decode("utf-8").split("|"))


def _금칙어(name: str) -> str:
    low = name.lower().replace(" ", "")
    return next((w for w in _NO_WORDS if w in low), "")


def 이름(*words: str) -> int:
    """비서 이름을 짓는다 — 말을 걸었을 때 이 이름으로 답한다.

    전에는 설치 화면에서만 됐다. 화면을 안 띄우기로 했으니 여기서도 돼야 한다.
    """
    name = " ".join(words).strip()
    if not name:
        print("이름을 같이 적어 주십시오 — 보기 : 이름 다니엘")
        return 1
    if len(name) > 20:
        print("이름이 너무 깁니다(20자까지).")
        return 1
    bad = _금칙어(name)
    if bad:
        print(f"「{bad}」 이(가) 들어간 이름은 못 씁니다 — 봇 이름은 텔레그램 검색에 그대로 뜹니다.")
        print("  소속을 알 수 없는 평범한 이름으로 지어 주십시오. 보기 : 다니엘 · 하루비서 · 메모도우미")
        return 1
    r = call("/api/save", {"bot_name": name}, timeout=300)
    print(f"「{name}」 (으)로 지었습니다." if r.get("ok") else f"저장 실패 — {r.get('error')}")
    return 0 if r.get("ok") else 1


def 텔레그램(api_id: str = "", api_hash: str = "", phone: str = "") -> int:
    """텔레그램에 로그인한다 — 첫 단계(인증번호 보내기).

    api_id · api_hash 는 「열쇠」·「열쇠코드」 가 대신 받아 온다(2026-11-17).
    사람이 손으로 받아 왔을 때만 여기에 직접 넣는다. 한 번 받아두면 설정에
    적히므로 다음부턴 전화번호만 있으면 된다.
    """
    c = cfg()
    api_id = api_id or str(c.get("tg_api_id") or "")
    api_hash = api_hash or str(c.get("tg_api_hash") or "")
    phone = phone or str(c.get("tg_phone") or "")
    if not (api_id and api_hash):
        print("api_id 와 api_hash 가 필요합니다.\n"
              "  「열쇠 <전화번호>」 로 대신 받아 오십시오.\n"
              "  보기 : 텔레그램 12345678 abcdef0123456789 +821012345678")
        return 1
    if not phone:
        print("전화번호가 필요합니다 — 보기 : +821012345678")
        return 1

    call("/api/save", {"tg_api_id": api_id, "tg_api_hash": api_hash, "tg_phone": phone},
         timeout=300)                                          # 다음 단계가 쓸 수 있게 적어 둔다
    if call("/api/tg/status", {}, timeout=120).get("authorized"):
        print("이미 로그인돼 있습니다 — 다음으로 넘어가십시오.")
        return 0
    r = call("/api/tg/code", {"phone": phone}, timeout=180)
    if r.get("error"):
        print("인증번호를 못 보냈습니다 —", r["error"])
        return 1
    print("인증번호를 텔레그램으로 보냈습니다.")
    print("받으신 번호를 알려 주시면 이어서 하겠습니다 :")
    print("  python3 setup.py 인증번호 12345")
    print("  (2단계 암호를 걸어두셨으면) 인증번호 12345 <2단계암호>")
    return 0


def 인증번호(code: str = "", password: str = "") -> int:
    """받은 인증번호로 로그인을 끝낸다."""
    if not code:
        print("받으신 번호를 같이 적어 주십시오 — 보기 : 인증번호 12345")
        return 1
    c = cfg()
    phone = str(c.get("tg_phone") or "")
    if not phone:
        print("먼저 「텔레그램」 부터 하셔야 합니다 — 전화번호를 모릅니다.")
        return 1
    r = call("/api/tg/signin", {"phone": phone, "code": code, "password": password}, timeout=180)
    if r.get("authorized") or r.get("ok"):
        who = r.get("name") or r.get("user") or ""
        print(f"로그인됐습니다{' — ' + who if who else ''}.")
        if r.get("name"):
            call("/api/save", {"my_name": r["name"]}, timeout=300)
        return 0
    err = r.get("error") or ""
    if "password" in err.lower() or "2단계" in err:
        print("2단계 암호가 걸려 있습니다 — 인증번호 <번호> <2단계암호> 로 다시 시켜 주십시오.")
    else:
        print("로그인 실패 —", err or r)
    return 1


def 봇만들기(*words: str) -> int:
    """@BotFather 에게 대신 말을 걸어 봇을 만들고, 토큰까지 적어 둔다."""
    if not _로그인됐나():
        print("먼저 텔레그램 로그인부터 하셔야 합니다.")
        print("  python3 setup.py 텔레그램 <api_id> <api_hash> <전화번호>")
        return 1
    title = " ".join(words).strip() or str(cfg().get("bot_name") or "")
    bad = _금칙어(title)
    if bad:
        print(f"봇 이름에 「{bad}」 이(가) 들어 있어 만들지 않았습니다 — 텔레그램 검색에 그대로 뜹니다.")
        print("  이름부터 바꿔 주십시오 :  python3 setup.py 이름 <새 이름>")
        return 1
    print("봇을 만드는 중입니다 — 1분쯤 걸립니다.")
    r = call("/api/bot/make", {"title": title}, timeout=TIMEOUT_SLOW)
    if not r.get("ok"):
        print("못 만들었습니다 —", r.get("error"))
        print("  텔레그램 로그인이 끝나 있어야 합니다.")
        return 1
    call("/api/save", {"telegram_bot_token": r["token"]}, timeout=300)
    print(f"만들었습니다 — @{r.get('username')}")
    print("주인은 지금 로그인한 텔레그램 본인 계정으로 정해집니다.")
    print("그 계정 말고는 누가 말을 걸어도 봇이 대꾸하지 않고, 단체방에 넣으면 스스로 나옵니다.")
    return 0


def 암호(pw: str) -> int:
    """교회 용어·조직·보고 규칙을 푼다."""
    r = call("/api/unlock", {"password": pw})
    print(r.get("message") or r.get("error") or r)
    return 0 if r.get("ok") else 1


def 방목록() -> int:
    """텔레그램 방을 번호를 붙여 보여준다 — 그 번호로 고른다."""
    if not _로그인됐나():
        print("먼저 텔레그램 로그인부터 하셔야 합니다 — 「텔레그램」 명령을 쓰십시오.")
        return 1
    r = call("/api/rooms", {}, timeout=180)
    rooms = r.get("rooms")
    if rooms is None:
        print("방 목록을 못 받았습니다 —", r.get("error") or "텔레그램 로그인을 먼저 끝내십시오.")
        return 1
    for i, room in enumerate(rooms, 1):
        name = room.get("title") or room.get("name") or "(이름 없음)"
        print(f"  {i:3}. {name}   [{room.get('id')}]")
    print()
    print("고르실 때 : python3 setup.py 방고르기 core=1,3 mixed=5")
    print("  core  = 우리 부서 전용 방 (통째로 읽습니다)")
    print("  mixed = 다른 부서가 섞인 방 (내 것과 우리 일만 골라 읽습니다)")
    return 0


def 부서(*words: str) -> int:
    """소속 부서를 적는다 — 업무 레이더가 섞인 방에서 우리 부서 일을 골라내는 낱말이 이걸로 정해진다.

    「내무부」면 부장님 뇌와 똑같은 내무부 낱말(출결·결석·사고처리·입교…)을 쓴다.
    """
    name = " ".join(words).strip()
    if not name:
        print("부서를 같이 적어 주십시오 — 보기 : 부서 내무부")
        return 1
    r = call("/api/save", {"my_dept": name}, timeout=300)
    if not r.get("ok"):
        print(f"저장 실패 — {r.get('error')}")
        return 1
    print(f"「{name}」 (으)로 적었습니다.")
    if "내무" in name:
        print("  업무 레이더가 내무부 낱말(출결·결석·사고처리·입교 등)로 섞인 방을 골라 읽습니다.")
    return 0


def 방고르기(*args: str) -> int:
    """번호로 고른 방을 설정에 적는다."""
    want = {"core": [], "mixed": []}
    for a in args:
        if "=" not in a:
            continue
        k, v = a.split("=", 1)
        if k in want:
            want[k] = [int(x) for x in v.split(",") if x.strip().isdigit()]
    if not (want["core"] or want["mixed"]):
        print("고르신 방이 없습니다. 보기 : 방고르기 core=1,3 mixed=5")
        return 1

    rooms = call("/api/rooms", {}, timeout=180).get("rooms") or []
    if not rooms:
        print("방 목록을 못 받았습니다 — 텔레그램 로그인을 먼저 끝내십시오.")
        return 1

    picked = {"core": {}, "mixed": {}}
    for kind, nums in want.items():
        for i in nums:
            if 1 <= i <= len(rooms):
                r = rooms[i - 1]
                picked[kind][r.get("title") or r.get("name") or str(r.get("id"))] = r.get("id")
            else:
                print(f"  {i}번은 목록에 없습니다 — 건너뜁니다")

    c = cfg()
    c["rooms"] = picked
    out = call("/api/save", c, timeout=300)
    for kind in ("core", "mixed"):
        for name in picked[kind]:
            print(f"  {kind:5} {name}")
    print("저장했습니다." if out.get("ok") else f"저장 실패 — {out.get('error')}")
    return 0 if out.get("ok") else 1


def 파이어베이스() -> int:
    """업무 레이더 화면이 쓸 곳을 크롬을 몰아서 대신 만든다. 몇 분 걸린다."""
    ready = call("/api/remote/check", {}, timeout=400)
    if not ready.get("ok"):
        print("아직 안 됩니다 —", ready.get("error"))
        if ready.get("detail"):
            print("  (자세히) ", ready["detail"][:200])
        print("  크롬을 켜 두고, 그 크롬에 구글 로그인이 되어 있어야 합니다.")
        return 1
    print("크롬을 잡았습니다. 이제 만듭니다 — 몇 분 걸립니다. 창을 건드리지 마십시오.")
    r = call("/api/remote/firebase", {"name": cfg().get("my_name", "")}, timeout=TIMEOUT_SLOW)
    if r.get("ok"):
        print(f"만들었습니다 — {r.get('project')}")
        if r.get("link"):
            print(f"업무 레이더 화면 : {r['link']}")
        return 0
    print("끝까지 못 갔습니다 —", r.get("error"))
    if r.get("detail"):
        print("  막힌 자리 :", r["detail"][:300])
    return 1


def 시간켜기() -> int:
    """말 걸기를 24시간 살려둔다. 이걸 켜야 텔레그램으로 말을 걸 수 있다."""
    r = call("/api/alwayson", {}, timeout=180)
    print(r.get("message") or r.get("error") or r)
    return 0 if r.get("ok") else 1


def 점검() -> int:
    """진짜 되는지 하나씩 돌려본다 — 말만 하지 않는다."""
    ok = True
    b = call("/api/brain")
    print(f"  {'○' if b.get('ok') else '✗'} 클로드 코드 — {b.get('version') or b.get('error')}")
    ok = ok and bool(b.get("ok"))

    g = call("/api/guard")
    print(f"  {'○' if g.get('ok') else '✗'} 말 걸기 — {g.get('message')}")
    ok = ok and bool(g.get("ok"))

    c = cfg()
    if c.get("telegram_bot_token"):
        h = call("/api/bot/check", {"token": c["telegram_bot_token"]}, timeout=60)
        print(f"  {'○' if h.get('ok') else '✗'} 봇 — {h.get('username') or h.get('error')}")
        ok = ok and bool(h.get("ok"))
    else:
        print("  ✗ 봇 — 토큰이 없습니다")
        ok = False

    print()
    print("다 됩니다. 이제 봇에게 말을 걸어 보십시오." if ok
          else "위에 ✗ 표시된 것을 먼저 고쳐야 합니다.")
    return 0 if ok else 1


def 주인다시() -> int:
    """주인을 처음부터 다시 정한다 — 비상구. 이 PC 앞에 앉은 사람만 할 수 있다.

    말 걸기가 다시 켜질 때 로그인한 본인 계정으로 주인을 새로 정한다.
    본인 계정을 못 읽는 경우에 쓰라고 비밀 입장 링크도 새로 만든다(옛 링크는 죽는다).
    """
    import secrets
    key = secrets.token_urlsafe(32)[:43]
    r = call("/api/save", {"admin_telegram_id": "", "owner_locked": False, "start_key": key},
             timeout=300)
    if not r.get("ok"):
        print("저장 실패 —", r.get("error"))
        return 1
    try:                                                     # 말 걸기는 제 파일이 바뀌면 1분 안에 스스로 다시 켠다
        os.utime(_home() / "features" / "listen.py", None)
    except OSError:
        pass
    print("주인을 비웠습니다. 1분 안에 로그인한 본인 계정으로 다시 정해집니다.")
    tok = str(cfg().get("telegram_bot_token") or "")
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=20) as g:
            uname = json.loads(g.read()).get("result", {}).get("username", "")
    except (OSError, ValueError):
        uname = ""
    if uname:
        print("본인 계정으로 안 잡히면 이 링크를 **본인 텔레그램에서만** 누르십시오 (남에게 보내지 마십시오):")
        print(f"  https://t.me/{uname}?start={key}")
    return 0


# ── 텔레그램 열쇠를 대신 받아 온다 (2026-11-17) ───────────────────────
# 전에는 사람이 my.telegram.org 에 직접 들어가 api_id·api_hash 를 베껴 와야 했다.
# 사명자가 가장 많이 막힌 자리라, 그 사이트에 사람 대신 말을 건다.
# 사람이 하는 일은 전화번호와 텔레그램 앱으로 온 확인 코드를 불러 주는 것뿐이다.
# 받은 값은 화면에 찍지 않고 바로 설정에 넣는다.
import http.cookiejar as _cj
import random as _rnd
import re as _re
import string as _st
import urllib.parse as _up

_MYTG = "https://my.telegram.org"
_UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
                     "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
       "X-Requested-With": "XMLHttpRequest", "Origin": _MYTG, "Referer": _MYTG + "/auth"}


def _phone(p: str) -> str:
    """010-1234-5678 · 01012345678 · +82 10… 무엇으로 불러도 +8210… 으로."""
    d = _re.sub(r"[^\d+]", "", p or "")
    if d.startswith("+"):
        return d
    if d.startswith("82"):
        return "+" + d
    if d.startswith("0"):
        return "+82" + d[1:]
    return "+" + d if d else ""


def _mytg_state() -> Path:
    return _home() / "_mytg.json"


def _post(op, path: str, data: dict) -> str:
    req = urllib.request.Request(_MYTG + path, data=_up.urlencode(data).encode(),
                                 headers=_UA, method="POST")
    try:
        with op.open(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:                       # 400 에도 이유가 본문에 온다("too many tries")
        return e.read().decode("utf-8", "replace")


def 열쇠(phone: str = "") -> int:
    """my.telegram.org 에 확인 코드를 보내 달라고 한다 (1/2)."""
    phone = _phone(phone or str(cfg().get("tg_phone") or ""))
    if not phone:
        print("전화번호가 필요합니다 — 보기 : 열쇠 010-1234-5678")
        return 1
    op = urllib.request.build_opener()
    try:
        out = _post(op, "/auth/send_password", {"phone": phone})
    except OSError as e:
        print(f"텔레그램 사이트에 닿지 못했습니다 — {type(e).__name__}. 인터넷·VPN 을 봐 주십시오.")
        return 1
    try:
        rh = json.loads(out).get("random_hash", "")
    except ValueError:
        rh = ""
    if not rh:
        if "too many" in out.lower():
            print("너무 여러 번 시도해서 텔레그램이 잠시 막았습니다 — 몇 시간 뒤에 다시 하십시오.")
        else:
            print("확인 코드를 못 보냈습니다 — 전화번호를 다시 봐 주십시오.", out[:120])
        return 1
    _home().mkdir(parents=True, exist_ok=True)
    _mytg_state().write_text(json.dumps({"phone": phone, "random_hash": rh}), encoding="utf-8")
    print("확인 코드를 보냈습니다.")
    print("  텔레그램 앱 → 「Telegram」(파란 체크 공식 계정) 대화방에 영문·숫자가 섞인 코드가 와 있습니다.")
    print("  (문자메시지로 오지 않습니다.) 그 코드를 알려 주시면 이어서 합니다 :")
    print("  python3 setup.py 열쇠코드 <코드>")
    return 0


def _read_app(html: str) -> tuple[str, str]:
    """앱이 있으면 화면에서 api_id(숫자)·api_hash(32자) 를 읽는다.
    11/18 실제 화면: 새 모양은 data-copy="숫자" · id="api_hash_value" data-value="32자".
    옛 모양(uneditable-input 칸)도 같이 본다. 한 계정에 앱은 하나뿐이라 있으면 만들지 않는다."""
    vals = [_re.sub(r"<[^>]+>", "", v).strip() for v in
            _re.findall(r'<span[^>]*uneditable-input[^>]*>(.*?)</span>', html, _re.S)]
    vals += [v.strip() for v in _re.findall(r'data-(?:copy|value)=["\']([^"\']+)["\']', html)]
    vals += [_re.sub(r"<[^>]+>", "", v).strip() for v in
             _re.findall(r'<span[^>]*class=["\']vv["\'][^>]*>(.*?)</span>', html, _re.S)]
    aid = next((v for v in vals if v.isdigit() and 4 <= len(v) <= 12), "")
    ah = next((v for v in vals if _re.fullmatch(r"[0-9a-f]{32}", v)), "")
    return aid, ah


def _has_app(html: str) -> bool:
    return any(k in html for k in ("uneditable-input", "api_hash_value", "App api_id", "app_edit_form"))


def 열쇠코드(code: str = "") -> int:
    """받은 확인 코드로 들어가 api_id·api_hash 를 받아 설정에 넣는다 (2/2).
    앱이 아직 없으면 하나 만든다. 끝나면 곧바로 텔레그램 로그인 번호를 보낸다."""
    code = (code or "").strip()
    try:
        st = json.loads(_mytg_state().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("먼저 「열쇠 <전화번호>」 부터 하셔야 합니다.")
        return 1
    if not code:
        print("받으신 코드를 같이 적어 주십시오 — 보기 : 열쇠코드 Ab3dEfGh1Jk")
        return 1
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cj.CookieJar()))
    try:
        out = _post(op, "/auth/login", {"phone": st["phone"], "random_hash": st["random_hash"],
                                        "password": code})
        if out.strip() != "true":
            print("코드가 맞지 않습니다 — 다시 불러 주시거나, 「열쇠」 부터 새로 하십시오.", out[:80])
            return 1
        # 화면 읽기에는 X-Requested-With 를 붙이면 401 이 난다(2026-11-17 겪음) — 브라우저 머리글만
        get = lambda: op.open(urllib.request.Request(_MYTG + "/apps", headers={
            "User-Agent": _UA["User-Agent"], "Referer": _MYTG + "/"}), timeout=30) \
            .read().decode("utf-8", "replace")
        html = get()
        if os.environ.get("ADELE_MYTG_DUMP"):                 # 시험용 — 숫자·열쇠는 가리고 화면 모양만 남긴다
            Path(os.environ["ADELE_MYTG_DUMP"]).write_text(
                _re.sub(r"[0-9a-f]{32}", "<HASH32>", _re.sub(r"\d{5,}", "<NUM>", html)), encoding="utf-8")
        aid, ah = _read_app(html)
        if os.environ.get("ADELE_MYTG_DUMP") and not (aid and ah):
            print("(시험) 화면만 남기고 멈춥니다."); return 1
        if not (aid and ah) and _has_app(html):   # 앱은 있는데 못 읽었다 — 또 만들지 않는다
            print("앱은 있는데 열쇠 칸을 못 읽었습니다.")
            print("  [클로드에게] 사람에게 my.telegram.org → API development tools 화면의 api_id·api_hash 를 불러 달라고 하십시오.")
            return 1
        if not (aid and ah):                                  # 아직 앱이 없다 — 하나 만든다
            tag = _re.search(r'<input[^>]*name=["\']?hash\b[^>]*>', html)
            m = tag and _re.search(r'value=["\']?([^"\'\s>]+)', tag.group(0))
            if not m:
                print("텔레그램 사이트 모양이 바뀌어 열쇠를 못 찾았습니다.")
                print("  (화면의 칸 :", ", ".join(_re.findall(r'name=["\']?([\w-]+)', html))[:200] + ")")
                print("  [클로드에게] 사람에게 my.telegram.org → API development tools 에서 직접 받아 달라고 하십시오.")
                return 1
            for _ in range(3):                                # 짧은 이름이 겹치면 ERROR 가 난다 — 바꿔서 다시
                sn = "memo" + "".join(_rnd.choices(_st.ascii_lowercase + _st.digits, k=8))
                said = _post(op, "/apps/create", {"hash": m.group(1), "app_title": sn, "app_shortname": sn,
                                          "app_url": "", "app_platform": "desktop", "app_desc": ""})
                aid, ah = _read_app(get())
                if aid and ah:
                    break
                print(f"  (텔레그램 답 : {said.strip()[:60] or '빈 답'} — 이름을 바꿔 다시 합니다)")
                time.sleep(3)
        if not (aid and ah):
            print("앱을 만들지 못했습니다(텔레그램이 ERROR 를 냈습니다).")
            print("  VPN·광고차단을 끄고 「열쇠」 부터 한 번 더 해 보십시오.")
            return 1
    except OSError as e:
        print(f"텔레그램 사이트에 닿지 못했습니다 — {type(e).__name__}")
        return 1
    try:
        _mytg_state().unlink()
    except OSError:
        pass
    print("텔레그램 열쇠를 받아 설정에 넣었습니다.")
    return 텔레그램(aid, ah, st["phone"])


# ── 일정 (아이폰=아이클라우드 · 갤럭시=구글) ────────────────────────────
_CAL_HOW = {
    "icloud": ("https://account.apple.com/account/manage",
               "로그인 → 「로그인 및 보안」 → 「앱 암호」 → + → 이름에 아무거나(예: 비서) → 나온 xxxx-xxxx-xxxx-xxxx"),
    "google": ("https://myaccount.google.com/apppasswords",
               "로그인 → 앱 이름에 아무거나(예: 비서) → 만들기 → 나온 16자리. "
               "「2단계 인증」 이 꺼져 있으면 이 화면이 안 열립니다 — 먼저 켜야 합니다"),
}


def 일정(kind: str = "", uid: str = "", pw: str = "", *name: str) -> int:
    """캘린더를 붙인다. 앱 암호가 없으면 받는 곳을 열어 준다."""
    kind = {"아이폰": "icloud", "애플": "icloud", "아이클라우드": "icloud",
            "갤럭시": "google", "구글": "google"}.get(kind, kind).lower()
    if kind not in _CAL_HOW:
        print("어느 쪽인지 적어 주십시오 — 일정 icloud(아이폰) 또는 일정 google(갤럭시)")
        return 1
    url, how = _CAL_HOW[kind]
    if not (uid and pw):
        print("앱 전용 암호가 필요합니다. 계정 비밀번호로는 안 됩니다.")
        print(f"  받는 곳을 엽니다 : {url}")
        print(f"  {how}")
        try:
            if os.name == "nt":
                os.startfile(url)                             # noqa: S606
            else:
                subprocess.run(["open", url], check=False, timeout=10)
        except (OSError, subprocess.SubprocessError):
            pass
        print(f"  받으시면 : python3 setup.py 일정 {kind} <{'애플 ID' if kind == 'icloud' else '지메일'}> <앱암호>")
        return 0
    pw = pw.replace(" ", "")
    r = call("/api/cal/check", {"kind": kind, "id": uid, "pw": pw, "name": " ".join(name)}, timeout=120)
    if not r.get("ok"):
        print("연결이 안 됩니다 —", r.get("error"))
        return 1
    cals = r.get("calendars") or []
    print("일정을 붙였습니다." + (f" 쓸 달력 : {' '.join(name)}" if name else ""))
    if cals and not name:
        print("  달력이 여러 개면 하나를 고르게 하십시오 (안 고르면 맨 앞 것) :")
        for c in cals:
            print("   ·", c)
        print(f"  고를 때 : python3 setup.py 일정 {kind} <아이디> <앱암호> <달력이름>")
    return 0


# ── 터미널을 부장님 것처럼 (2026-11-18) ────────────────────────────────
# Ghostty 를 열면 비서(클로드)가 아델 폴더에서 저절로 켜지고, 맨 아래에 상태줄이 뜬다.
_TERM_RAW = "https://raw.githubusercontent.com/soanqn144000-tech/adele-dist/main/start/term/"


def _ghostty_set(path: Path, kv: list) -> None:
    """Ghostty 설정에서 우리가 쓰는 줄만 갈아 끼운다. 사람이 쓴 다른 줄은 그대로."""
    keys = {k for k, _ in kv}
    old = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    if old and not path.with_suffix(".아델전").exists():
        path.with_suffix(".아델전").write_text("\n".join(old) + "\n", encoding="utf-8")
    keep = [ln for ln in old if ln.split("=", 1)[0].strip() not in keys and "# 아델:" not in ln]
    keep += ["# 아델: Ghostty 를 열면 비서가 켜진다 (setup.py 터미널)"]
    keep += [f"{k} = {v}" for k, v in kv]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(keep) + "\n", encoding="utf-8")


def _cmdpath(p) -> str:
    """훅·상태줄 명령에 넣을 경로. 윈도우 클로드 코드는 깃배시가 없으면 파워셸로 훅을 돌리는데,
    파워셸은 \"경로\" \"경로\" 를 문법 오류로 본다(2026-11-22 방태준 컴). 그래서 윈도우에서는
    따옴표 없이 / 로 쓴다(배시·파워셸 둘 다 읽힌다). 띄어쓰기가 있으면 짧은 이름(8.3)으로 바꾼다."""
    p = str(p)
    if os.name != "nt":
        return f'"{p}"'
    if " " in p:
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(1024)
            if ctypes.windll.kernel32.GetShortPathNameW(p, buf, 1024):
                p = buf.value
        except Exception:                                    # noqa: BLE001
            pass
    return p.replace("\\", "/") if " " not in p else f'"{p}"'


def _strip_jsonc(t: str) -> str:
    """윈도우 터미널 설정은 // 주석·끝 쉼표가 섞인 JSON 이다 — 문자열은 건드리지 않고 걷어낸다."""
    out, i, n, q = [], 0, len(t), False
    while i < n:
        ch = t[i]
        if q:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(t[i + 1]); i += 2; continue
            if ch == '"':
                q = False
        elif ch == '"':
            q = True; out.append(ch)
        elif t.startswith("//", i):
            while i < n and t[i] != "\n":
                i += 1
            continue
        elif t.startswith("/*", i):
            j = t.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        else:
            out.append(ch)
        i += 1
    import re
    return re.sub(r",(\s*[}\]])", r"\1", "".join(out))


def _wt_autostart(home: Path) -> bool:
    """(윈도우) 터미널에서 파워셸을 열면 아델 폴더에서 클로드 코드가 바로 켜지게.
    프로필 스크립트는 실행 정책에 막히는 PC 가 많아 윈도우 터미널 설정을 고친다(2026-11-22)."""
    la = os.environ.get("LOCALAPPDATA", "")
    cands = [Path(la) / "Packages" / "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json",
             Path(la) / "Packages" / "Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe" / "LocalState" / "settings.json",
             Path(la) / "Microsoft" / "Windows Terminal" / "settings.json"]
    cmd = f'powershell.exe -NoLogo -NoExit -Command "Set-Location -LiteralPath \'{home}\'; claude"'
    done = False
    for f in cands:
        if not f.exists():
            continue
        try:
            raw = f.read_text(encoding="utf-8-sig")
            cfg = json.loads(_strip_jsonc(raw))
        except (OSError, ValueError) as e:
            print(f"터미널 설정을 못 읽었습니다 ({f.name}) — {type(e).__name__}")
            continue
        profs = cfg.get("profiles")
        lst = profs.get("list", []) if isinstance(profs, dict) else (profs or [])
        hit = [p for p in lst if isinstance(p, dict) and (
            "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}" == str(p.get("guid", "")).lower()
            or str(p.get("commandline", "")).lower().startswith(("powershell", "%systemroot%\\system32\\windowspowershell"))
            or str(p.get("name", "")) == "Windows PowerShell")]
        if not hit:
            continue
        bak = f.with_suffix(".json.아델전")
        if not bak.exists():
            bak.write_text(raw, encoding="utf-8")
        for p in hit:
            p["commandline"] = cmd
            p["startingDirectory"] = str(home)
        f.write_text(json.dumps(cfg, ensure_ascii=False, indent=4), encoding="utf-8")
        done = True
    return done


def _ps_profile_autostart(home: Path) -> str:
    """(윈도우) 파워셸 프로필에 '열면 클로드 켜기' 를 적는다. 시작 메뉴의 Windows PowerShell 은
    터미널 설정을 안 거쳐서 프로필만 먹는다(2026-11-22 방태준 컴에서 확인).
    다만 윈도우 기본 실행 정책(Restricted)이면 프로필이 안 돈다 — 정책은 보안 설정이라 손대지 않고 알린다.
    돌려주는 값: 'ok' | 'policy' | 'fail'"""
    # 클로드 코드 안에서 부르면 Bypass 가 물려 와 '허용'으로 잘못 읽힌다(2026-11-22) — 물려받은 값을 지우고,
    # Process 범위를 뺀 실제 정책(CurrentUser → LocalMachine, 둘 다 없으면 Restricted)을 센다.
    env = {k: v for k, v in os.environ.items() if k.upper() != "PSEXECUTIONPOLICYPREFERENCE"}
    q = ("[Console]::OutputEncoding=[Text.Encoding]::UTF8; $PROFILE; "
         "$p='Restricted'; foreach($s in 'MachinePolicy','UserPolicy','CurrentUser','LocalMachine'){"
         "$v=Get-ExecutionPolicy -Scope $s; if(\"$v\" -ne 'Undefined'){$p=\"$v\"; break}}; $p")
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", q], env=env,
                             capture_output=True, text=True, encoding="utf-8", timeout=60).stdout.strip().splitlines()
        prof, pol = Path(out[0].strip()), (out[-1].strip() if len(out) > 1 else "")
    except Exception:                                        # noqa: BLE001
        return "fail"
    block = ("# >>> 아델 비서 — 파워셸을 열면 클로드 코드를 켠다(setup.py 터미널)\n"
             "if (-not $env:CLAUDECODE -and -not $env:ADELE_NO_AUTO -and [Environment]::UserInteractive"
             " -and -not ([Environment]::GetCommandLineArgs() | Where-Object { $_ -match '^-(c|com|command|f|file|enc)' })) {\n"
             f"  Set-Location -LiteralPath '{home}'; claude\n}}\n"
             "# <<< 아델 비서\n")
    allowed = pol.lower() in ("remotesigned", "unrestricted", "bypass")
    try:
        import re
        old = prof.read_text(encoding="utf-8-sig") if prof.exists() else ""
        rest = re.sub(r"# >>> 아델 비서.*?# <<< 아델 비서\n?", "", old, flags=re.S)
        if not allowed:
            # 막힌 PC 에 프로필을 두면 파워셸을 열 때마다 빨간 오류가 뜬다 — 쓰지 않고, 전에 쓴 것도 걷는다
            if old != rest:
                if rest.strip():
                    prof.write_text(rest, encoding="utf-8-sig")
                else:
                    prof.rename(prof.with_name(prof.name + ".아델끔"))   # 우리 것만 있던 파일 — 지우지 않고 이름만 바꿔 둔다
            return "policy"
        prof.parent.mkdir(parents=True, exist_ok=True)
        prof.write_text(rest.rstrip("\n") + ("\n\n" if rest.strip() else "") + block, encoding="utf-8-sig")
    except OSError:
        return "fail"
    return "ok"


def 터미널(name: str = "") -> int:
    """Ghostty(맥)·파워셸(윈도우)을 열면 비서가 켜지게 하고, 클로드 코드 맨 아래에 상태줄을 단다.
    name 을 주면 상태줄·안내에 그 이름(영문이면 대문자)을 쓴다."""
    home = _home()
    if name:
        f = home / "config.json"
        try:
            c = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
            c["display_name"] = name.strip()
            f.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"부를 이름 : {name.strip()}")
            g = home / "CLAUDE.md"                           # 클로드가 스스로를 이 이름으로 부르게
            if g.exists():
                t = g.read_text(encoding="utf-8").split("\n## 당신의 이름")[0].rstrip("\n")
                g.write_text(t + f"\n\n## 당신의 이름\n\n이 사람은 비서를 **{name.strip()}** 이라고 "
                             f"부릅니다. 스스로를 {name.strip()} 이라고 하십시오. "
                             f"'아델' 은 프로그램 이름일 뿐입니다.\n", encoding="utf-8")
        except (OSError, ValueError) as e:
            print(f"이름을 못 적었습니다 — {e}")
    # 1) 상태줄 파일
    d = Path.home() / ".adele_term"
    d.mkdir(exist_ok=True)
    for fn in ("statusline.py", "set_state.py"):
        try:
            src = os.environ.get("ADELE_TERM_SRC")            # 시험용 — 올리기 전 내 폴더에서
            if src:
                (d / fn).write_bytes((Path(src) / fn).read_bytes())
                continue
            with urllib.request.urlopen(_TERM_RAW + fn, timeout=30) as r:
                (d / fn).write_bytes(r.read())
        except Exception as e:                               # noqa: BLE001
            print(f"상태줄 파일을 못 받았습니다 ({fn}) — {type(e).__name__}")
            return 1
    py = sys.executable or "python3"
    # 2) 클로드 코드 설정 — 상태줄과 훅. 다른 설정은 건드리지 않는다
    sp = Path.home() / ".claude" / "settings.json"
    try:
        cs = json.loads(sp.read_text(encoding="utf-8")) if sp.exists() else {}
    except ValueError:
        print("클로드 설정 파일이 깨져 있어 손대지 않았습니다(~/.claude/settings.json).")
        return 1
    if sp.exists() and not sp.with_suffix(".json.아델전").exists():
        sp.with_suffix(".json.아델전").write_text(sp.read_text(encoding="utf-8"), encoding="utf-8")
    cs["statusLine"] = {"type": "command", "command": f'{_cmdpath(py)} {_cmdpath(d / "statusline.py")}',
                        "refreshInterval": 1}
    hooks = cs.setdefault("hooks", {})
    for ev, st in (("UserPromptSubmit", "working"), ("PreToolUse", "working"),
                   ("Stop", "done"), ("Notification", "review")):
        cmd = f'{_cmdpath(py)} {_cmdpath(d / "set_state.py")} {st}'
        lst = [h for h in hooks.get(ev, []) if ".adele_term" not in json.dumps(h)]
        lst.append({"hooks": [{"type": "command", "command": cmd}]})
        hooks[ev] = lst
    sp.parent.mkdir(exist_ok=True)
    sp.write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
    print("상태줄     : 달았습니다 (클로드 코드를 다시 켜면 보입니다)")
    # 3) 윈도우 — 터미널에서 파워셸을 열면 클로드가 바로 켜지게
    if os.name == "nt":
        wt = _wt_autostart(home)
        pp = _ps_profile_autostart(home)
        if pp == "ok":
            print("파워셸     : 열면 비서가 바로 켜집니다 (지금 열린 창은 닫았다 다시 여십시오)")
        elif pp == "policy":
            print("파워셸     : " + ("윈도우 터미널을 열면 비서가 켜집니다. " if wt else "")
                  + "시작 메뉴의 Windows PowerShell 은 윈도우 보안 정책(스크립트 막힘) 때문에 아직 안 켜집니다.")
            print("             본인이 원하면 파워셸에 이 한 줄을 직접 치면 됩니다 — 비서가 대신 바꾸지 않습니다:")
            print("             Set-ExecutionPolicy -Scope CurrentUser RemoteSigned")
        else:
            print("파워셸     : " + ("윈도우 터미널을 열면 비서가 켜집니다." if wt else "자동 켜기를 못 달았습니다."))
    # 4) Ghostty — 맥만
    if sys.platform == "darwin":
        if not (Path("/Applications/Ghostty.app").exists()
                or (Path.home() / "Applications/Ghostty.app").exists()):
            print("Ghostty    : 이 맥에 없습니다 — 깔면 다시 「터미널」 을 돌리십시오.")
        else:
            gh = Path.home() / ".config" / "ghostty" / "config"
            _ghostty_set(gh, [("working-directory", f'"{home}"'),
                              ("window-inherit-working-directory", "false"),
                              ("command", '/bin/zsh -lic "claude; exec zsh -l"')])
            print("Ghostty    : 열면 비서가 바로 켜집니다 (지금 열린 창은 닫았다 다시 여십시오)")
    return 0


CMDS = {"상태": 상태, "이름": 이름, "부서": 부서, "텔레그램": 텔레그램, "인증번호": 인증번호,
        "봇만들기": 봇만들기, "암호": 암호, "방목록": 방목록, "방고르기": 방고르기,
        "파이어베이스": 파이어베이스, "24시간켜기": 시간켜기, "점검": 점검,
        "주인다시": 주인다시, "열쇠": 열쇠, "열쇠코드": 열쇠코드, "일정": 일정,
        "터미널": 터미널, "terminal": 터미널}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in CMDS:
        print(__doc__.split("**쓰는 법**")[1].strip() if "**쓰는 법**" in __doc__ else "")
        return 1
    try:
        return CMDS[argv[0]](*argv[1:])
    except NotRunning as e:
        print(e)
        return 1
    except TypeError:
        print(f"쓰는 법이 다릅니다 — {argv[0]} 에 필요한 것을 확인해 주십시오.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
