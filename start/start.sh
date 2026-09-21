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

say()  { printf '\n  %s\n' "$*"; }
fail() { say "⚠ $*"; say "이 창을 사진 찍어 아델을 알려 주신 분께 보내 주십시오."; read -r -p "  (엔터를 누르면 닫힙니다) " _ </dev/tty; exit 1; }

find_claude() {
  local c
  for c in "$(command -v claude 2>/dev/null)" "$HOME/.local/bin/claude" "$HOME/.claude/local/claude" \
           /opt/homebrew/bin/claude /usr/local/bin/claude "$HOME/.npm-global/bin/claude" \
           "$HOME"/.nvm/versions/node/*/bin/claude; do
    [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

clear
say "아델을 준비합니다. 창을 닫지 마십시오."

# ── 1·2. 클로드 코드 ─────────────────────────────────────────────
CLAUDE="$(find_claude)" || {
  say "클로드 코드가 없어 깝니다. (1~3분)"
  curl -fsSL https://claude.ai/install.sh | bash || fail "클로드 코드 설치가 실패했습니다."
  CLAUDE="$(find_claude)" || fail "깔았는데 클로드 코드를 못 찾습니다."
}
say "클로드 코드 ✓  ($("$CLAUDE" --version 2>/dev/null | head -1))"

# 다음부터 터미널에서 그냥 'claude' 만 쳐도 켜지게 — 동료분이 막힌 자리
BIN="$(dirname "$CLAUDE")"
for rc in "$HOME/.zshrc" "$HOME/.bash_profile"; do
  [ "$rc" = "$HOME/.bash_profile" ] && [ ! -e "$rc" ] && continue
  grep -qs "$BIN" "$rc" || printf '\n# 아델: 클로드 코드 길\nexport PATH="%s:$PATH"\n' "$BIN" >> "$rc"
done

# ── 설치가 이미 끝난 사람: 내 폴더에서 바로 켠다 ─────────────────
if grep -qs '"telegram_bot_token"' "$USERDIR/config.json" && grep -qs '"tg_api_id"' "$USERDIR/config.json"; then
  say "설치는 끝나 있습니다. 클로드 코드를 켭니다."
  [ -n "${ADELE_START_DRY:-}" ] && { echo "DRY: $USERDIR"; exit 0; }
  cd "$USERDIR" && exec "$CLAUDE" </dev/tty   # 파이프로 받아 돌려도 키보드를 쓰게
fi

# ── 3. 아델 본체 ─────────────────────────────────────────────────
if [ ! -x "$DIR/프로그램/Adele" ]; then
  say "아델 본체를 받습니다. (30MB 남짓)"
  URL="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/tags/latest" \
        | grep -o '"browser_download_url": *"[^"]*Adele-mac-[^"]*\.zip"' | head -1 | sed 's/.*"\(http[^"]*\)"/\1/')"
  [ -n "$URL" ] || fail "받을 주소를 못 찾았습니다 (인터넷 연결을 봐 주십시오)."
  TMP="$(mktemp -d)"
  curl -fL --progress-bar "$URL" -o "$TMP/a.zip" || fail "아델을 받지 못했습니다."
  ditto -x -k "$TMP/a.zip" "$TMP/x" || fail "압축을 풀지 못했습니다."
  SRC="$TMP/x/Adele"; [ -d "$SRC" ] || SRC="$TMP/x"
  mkdir -p "$DIR" && ditto "$SRC" "$DIR" || fail "아델 폴더를 만들지 못했습니다."
  rm -rf "$TMP"
fi
xattr -dr com.apple.quarantine "$DIR" 2>/dev/null   # 받은 표시를 뗀다 — 뒤에서 켜도 안 막히게
say "아델 본체 ✓  ($DIR)"

# ── 4. 설치 안내를 놓고 클로드를 켠다 ────────────────────────────
curl -fsSL "$RAW/CLAUDE.md" -o "$DIR/CLAUDE.md.new" && mv "$DIR/CLAUDE.md.new" "$DIR/CLAUDE.md"
[ -s "$DIR/CLAUDE.md" ] || fail "설치 안내를 받지 못했습니다."

say "클로드 코드를 켭니다. 처음이면 로그인 창이 뜹니다 — 클로드 계정으로 들어가 주십시오."
say "「이 폴더를 믿겠냐」고 물으면 엔터를 누르십시오."
[ -n "${ADELE_START_DRY:-}" ] && { echo "DRY: $DIR"; exit 0; }
sleep 2
cd "$DIR" && exec "$CLAUDE" "아델 깔아줘" </dev/tty   # 파이프로 받아 돌려도 키보드를 쓰게
