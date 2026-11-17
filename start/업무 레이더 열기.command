#!/bin/bash
# 업무 레이더 열기 (맥) — 두 번 누르면 자동감지 화면이 사파리로 열린다.
# 아델이 뒤에서 안 돌고 있으면 깨워서 연다. (2026-11-17 — 사명자는 자동감지만 본다)
for p in 8471 8472 8473; do
  curl -fs -m 2 "http://127.0.0.1:$p/api/hello" | grep -q adele && { open "http://127.0.0.1:$p/board"; exit 0; }
done
APP="$HOME/Adele/프로그램/Adele"
[ -x "$APP" ] || { echo "  아델이 안 보입니다 (~/Adele). 「클로드 코드 열기」로 다시 깔아 주십시오."; read -r _; exit 1; }
echo "  업무 레이더를 켜는 중입니다…"
nohup "$APP" --serve >/dev/null 2>&1 &
for i in $(seq 1 60); do
  sleep 1
  for p in 8471 8472 8473; do
    curl -fs -m 2 "http://127.0.0.1:$p/api/hello" | grep -q adele && { open "http://127.0.0.1:$p/board"; exit 0; }
  done
done
echo "  켜지지 않았습니다. 이 창을 사진 찍어 아델을 알려 주신 분께 보내 주십시오."; read -r _
