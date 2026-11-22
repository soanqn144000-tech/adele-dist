#!/bin/bash
# 아델 시작 (맥) — 「클로드 코드 열기」가 이것을 받아 돌린다.
#
# 사명자가 하는 일은 단추 한 번. 나머지는 여기서 한다:
#   1. 클로드 코드를 찾는다 — PATH 에 없어도 흔한 자리를 다 훑는다
#   2. 없으면 공식 설치기로 깐다. 다음부터 터미널에서도 켜지게 길(PATH)도 올린다
#   3. 아델 본체를 ~/Adele 에 받아 풀고, 받은 표시(격리표)를 뗀다
#   4. 설치 안내(CLAUDE.md)를 놓고 그 자리에서 클로드를 켠다 — 첫마디까지 넣어서
#
# 로직을 저장소에 두는 까닭: 여기를 고치면 사명자는 다시 받을 필요가 없다.
# (2026-09-21 동료 한 분이 클로드 코드를 깔고도 터미널에서 못 켰다 — 그 자리를 막는다)
set -u
REPO="soanqn144000-tech/adele-dist"
RAW="${ADELE_START_RAW:-https://raw.githubusercontent.com/$REPO/main/start}"   # 시험할 때만 바꾼다
DIR="$HOME/Adele"
USERDIR="$HOME/Library/Application Support/Adele"

# ── 화면 ─────────────────────────────────────────────────────────
# 색은 아델 색(초록·금)만 쓴다. 흰 바탕·검은 바탕 어디서도 읽히는 값으로 골랐다.
# 오른쪽 테두리는 안 그린다 — 한글은 폭이 글꼴마다 달라 상자가 어긋난다.
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  G=$'\033[38;5;35m'; Y=$'\033[38;5;136m'; D=$'\033[38;5;245m'; R=$'\033[38;5;167m'; B=$'\033[1m'; N=$'\033[0m'
else
  G=; Y=; D=; R=; B=; N=
fi
LINE="────────────────────────────────────────────"

banner() {
  [ -t 1 ] && clear
  printf '\n\n   %s✦%s  %s아 델%s\n' "$Y" "$N" "$B$G" "$N"
  printf '      %s텔레그램으로 말을 거는 내 비서%s\n' "$D" "$N"
  printf '   %s%s%s\n\n' "$D" "$LINE" "$N"
}
doing() { printf '   %s◦%s %s\n' "$Y" "$N" "$*"; }                       # 지금 하는 일
ok()    { printf '   %s✓%s %s  %s%s%s\n' "$G" "$N" "$1" "$D" "$2" "$N"; }  # 끝난 일 · 덧붙임
say()   { printf '     %s·%s %s\n' "$D" "$N" "$*"; }
head2() { printf '\n   %s%s%s\n   %s%s%s\n\n' "$D" "$LINE" "$N" "$B" "$*" "$N"; }
fail() {
  printf '\n   %s⚠ %s%s\n\n' "$R" "$*" "$N"
  say "이 창을 사진 찍어 아델을 알려 주신 분께 보내 주십시오."
  [ -z "${ADELE_START_PREPARE:-}" ] && { printf '\n'; read -r -p "     (엔터를 누르면 닫힙니다) " _ </dev/tty; }; exit 1
}

# 11/18 동료 맥(Ghostty)에서 클로드가 "EINVAL kqueue" 로 바로 죽었다 — 맥은 /dev/tty 를 kqueue 로 못 지켜본다.
# 진짜 단말 이름(/dev/ttys000 같은)을 찾아 그걸로 키보드를 붙인다.
real_tty() {
  local t; t="$(tty 0<&1 2>/dev/null)"
  case "$t" in /dev/tty?*) ;; *) t="/dev/$(ps -o tty= -p $$ 2>/dev/null | tr -d ' ')";; esac
  { [ -c "$t" ] && [ "$t" != /dev/ ]; } && echo "$t" || echo /dev/tty
}

find_claude() {
  local c
  for c in "$(command -v claude 2>/dev/null)" "$HOME/.local/bin/claude" "$HOME/.claude/local/claude" \
           /opt/homebrew/bin/claude /usr/local/bin/claude "$HOME/.npm-global/bin/claude" \
           "$HOME"/.nvm/versions/node/*/bin/claude; do
    [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

banner
printf '   %s준비하는 동안 창을 닫지 마십시오.%s\n\n' "$D" "$N"

# ── 1·2. 클로드 코드 ─────────────────────────────────────────────
CLAUDE="$(find_claude)" || {
  doing "클로드 코드를 깝니다 (1~3분)"
  curl -fsSL https://claude.ai/install.sh | bash || fail "클로드 코드 설치가 실패했습니다."
  CLAUDE="$(find_claude)" || fail "깔았는데 클로드 코드를 못 찾습니다."
}
ok "클로드 코드  " "$("$CLAUDE" --version 2>/dev/null | head -1)"

# 다음부터 터미널에서 그냥 'claude' 만 쳐도 켜지게 — 동료분이 막힌 자리
BIN="$(dirname "$CLAUDE")"
for rc in "$HOME/.zshrc" "$HOME/.bash_profile"; do
  [ "$rc" = "$HOME/.bash_profile" ] && [ ! -e "$rc" ] && continue
  grep -qs "$BIN" "$rc" || printf '\n# 아델: 클로드 코드 길\nexport PATH="%s:$PATH"\n' "$BIN" >> "$rc"
done

# ── 설치가 이미 끝난 사람: 내 폴더에서 바로 켠다 ─────────────────
# 칸 이름만 보면 안 된다 — 깔다 만 사람은 칸은 있고 값이 비었다(2026-11-22)
if grep -qsE '"telegram_bot_token"[[:space:]]*:[[:space:]]*"[^"]+' "$USERDIR/config.json" \
   && grep -qsE '"tg_api_id"[[:space:]]*:[[:space:]]*("[^"]+|[0-9])' "$USERDIR/config.json"; then
  ok "아델        " "설치돼 있습니다"
  [ -n "${ADELE_START_PREPARE:-}" ] && { echo "READY: $USERDIR"; exit 0; }   # 클로드가 부른 것 — 켜지 않는다
  head2 "클로드 코드를 켭니다"
  [ -n "${ADELE_START_DRY:-}" ] && { echo "DRY: $USERDIR"; exit 0; }
  cd "$USERDIR" && exec "$CLAUDE" <"$(real_tty)"   # 파이프로 받아 돌려도 키보드를 쓰게
fi

# ── 3. 아델 본체 ─────────────────────────────────────────────────
if [ ! -x "$DIR/프로그램/Adele" ]; then
  doing "아델 본체를 받습니다 (30MB 남짓)"
  URL="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/tags/latest" \
        | grep -o '"browser_download_url": *"[^"]*Adele-mac-[^"]*\.zip"' | head -1 | sed 's/.*"\(http[^"]*\)"/\1/')"
  [ -n "$URL" ] || fail "받을 주소를 못 찾았습니다 (인터넷 연결을 봐 주십시오)."
  TMP="$(mktemp -d)"
  curl -fL --retry 3 --retry-delay 3 --retry-all-errors --connect-timeout 30 --progress-bar "$URL" -o "$TMP/a.zip" \
    || fail "아델을 받지 못했습니다 (인터넷이 잠깐 끊겼을 수 있습니다 — 한 번 더 붙여넣어 보십시오)."   # 11/18 깃허브가 한 번 멎었다
  ditto -x -k "$TMP/a.zip" "$TMP/x" || fail "압축을 풀지 못했습니다."
  SRC="$TMP/x/Adele"; [ -d "$SRC" ] || SRC="$TMP/x"
  mkdir -p "$DIR" && ditto "$SRC" "$DIR" || fail "아델 폴더를 만들지 못했습니다."
  rm -rf "$TMP"
fi
xattr -dr com.apple.quarantine "$DIR" 2>/dev/null   # 받은 표시를 뗀다 — 뒤에서 켜도 안 막히게
ok "아델 본체    " "~${DIR#"$HOME"}"

# ── 4. 설치 안내를 놓고 클로드를 켠다 ────────────────────────────
curl -fsSL "$RAW/CLAUDE.md" -o "$DIR/CLAUDE.md.new" && mv "$DIR/CLAUDE.md.new" "$DIR/CLAUDE.md"
curl -fsSL "$RAW/setup.py" -o "$DIR/setup.py.new" && mv "$DIR/setup.py.new" "$DIR/setup.py"   # 설치 도구는 늘 최신으로
[ -s "$DIR/CLAUDE.md" ] || fail "설치 안내를 받지 못했습니다."
ok "설치 안내    " "받았습니다"

# 바탕화면에 「클로드 코드 열기」 — 다음부터 두 번 누르면 된다.
# 여기서 curl 로 만든 파일은 '받은 표시'가 안 붙어 맥이 막지 않는다(2026-11-17)
DESK="$HOME/Desktop/클로드 코드 열기.command"
if [ ! -e "$DESK" ] && curl -fsSL "$RAW/%ED%81%B4%EB%A1%9C%EB%93%9C%20%EC%BD%94%EB%93%9C%20%EC%97%B4%EA%B8%B0.command" -o "$DESK.new"; then
  mv "$DESK.new" "$DESK" && chmod +x "$DESK" && ok "바탕화면     " "「클로드 코드 열기」 를 놓았습니다"
fi
rm -f "$DESK.new"
# 업무 레이더(자동감지) 화면도 바탕화면에서 바로 — 사명자는 이것만 본다(2026-11-17)
RAD="$HOME/Desktop/업무 레이더 열기.command"
if [ ! -e "$RAD" ] && curl -fsSL "$RAW/%EC%97%85%EB%AC%B4%20%EB%A0%88%EC%9D%B4%EB%8D%94%20%EC%97%B4%EA%B8%B0.command" -o "$RAD.new"; then
  mv "$RAD.new" "$RAD" && chmod +x "$RAD" && ok "바탕화면     " "「업무 레이더 열기」 를 놓았습니다"
fi
rm -f "$RAD.new"

# 이미 켜져 있는 클로드가 부른 것이면 여기서 끝 — 그 클로드가 이어서 한다(2026-11-17)
[ -n "${ADELE_START_PREPARE:-}" ] && { echo "READY: $DIR"; exit 0; }

head2 "이제 클로드 코드를 켭니다"
say "처음이면 로그인 창이 뜹니다 — 클로드 계정으로 들어가 주십시오"
say "「이 폴더를 믿겠냐」고 물으면 엔터를 누르십시오"
printf '\n'
[ -n "${ADELE_START_DRY:-}" ] && { echo "DRY: $DIR"; exit 0; }
sleep 2
cd "$DIR" && exec "$CLAUDE" "아델 깔아줘" <"$(real_tty)"   # 파이프로 받아 돌려도 키보드를 쓰게
