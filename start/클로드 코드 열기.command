#!/bin/bash
# 클로드 코드 열기 (맥) — 두 번 누르면 된다.
# 실제 일은 저장소의 start.sh 가 한다. 그래야 고쳐도 사명자가 다시 받을 필요가 없다.
cd "$HOME" || exit 1
S="$(mktemp -t adele-start)"
if curl -fsSL "https://raw.githubusercontent.com/soanqn144000-tech/adele-dist/main/start/start.sh" -o "$S"; then
  exec bash "$S"
fi
echo; echo "  인터넷에 연결되지 않았습니다. 연결을 확인하고 다시 눌러 주십시오."
read -r -p "  (엔터를 누르면 닫힙니다) " _
