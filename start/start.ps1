# 아델 시작 (윈도우) — 「클로드 코드 열기.bat」이 이것을 받아 돌린다.
#
# start.sh 와 같은 일을 한다:
#   1. 클로드 코드를 찾는다 — PATH 에 없어도 흔한 자리를 다 훑는다
#   2. 없으면 공식 설치기로 깐다. 다음부터 터미널에서도 켜지게 길(PATH)도 올린다
#   3. 아델 본체를 %USERPROFILE%\Adele 에 받아 풀고, 받은 표시(Zone.Identifier)를 뗀다
#   4. 설치 안내(CLAUDE.md)를 놓고 그 자리에서 클로드를 켠다 — 첫마디까지 넣어서
#
# 이 파일은 bat 가 바이트로 받아 UTF-8 로 풀어 돌린다(한글이 깨지지 않게). BOM 을 넣지 마라.
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Repo    = 'soanqn144000-tech/adele-dist'
$Raw     = "https://raw.githubusercontent.com/$Repo/main/start"
$Dir     = Join-Path $env:USERPROFILE 'Adele'
$UserDir = Join-Path $env:LOCALAPPDATA 'Adele'

# ── 화면 ─────────────────────────────────────────────────────────
# start.sh 와 같은 모양. 기호는 윈도우 한글 글꼴에 다 들어 있는 것(◆ ● ○ ─ ·)만 쓴다.
# 오른쪽 테두리는 안 그린다 — 한글은 폭이 글꼴마다 달라 상자가 어긋난다.
$Line = '─' * 44
function Banner {
  Clear-Host; Write-Host ''; Write-Host ''
  Write-Host '   ◆  ' -ForegroundColor DarkYellow -NoNewline; Write-Host '아 델' -ForegroundColor Green
  Write-Host '      텔레그램으로 말을 거는 내 비서' -ForegroundColor DarkGray
  Write-Host "   $Line" -ForegroundColor DarkGray; Write-Host ''
}
function Doing($m) { Write-Host '   ○ ' -ForegroundColor DarkYellow -NoNewline; Write-Host $m }
function Ok($m, $note) {
  Write-Host '   ● ' -ForegroundColor Green -NoNewline; Write-Host "$m  " -NoNewline
  Write-Host $note -ForegroundColor DarkGray
}
function Say($m)   { Write-Host '     · ' -ForegroundColor DarkGray -NoNewline; Write-Host $m }
function Head2($m) { Write-Host ''; Write-Host "   $Line" -ForegroundColor DarkGray; Write-Host "   $m" -ForegroundColor White; Write-Host '' }
function Fail($m) {
  Write-Host ''; Write-Host "   ! $m" -ForegroundColor Red; Write-Host ''
  Say '이 창을 사진 찍어 아델을 알려 주신 분께 보내 주십시오.'
  if (-not $env:ADELE_START_PREPARE) { Write-Host ''; Read-Host '     (엔터를 누르면 닫힙니다)' | Out-Null }; exit 1
}

function Find-Claude {
  $c = @()
  $cmd = Get-Command claude -ErrorAction SilentlyContinue
  if ($cmd) { $c += $cmd.Source }
  $c += (Join-Path $env:USERPROFILE '.local\bin\claude.exe'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\claude.exe'),
        (Join-Path $env:APPDATA 'npm\claude.cmd')
  foreach ($p in $c) { if ($p -and (Test-Path $p -PathType Leaf)) { return $p } }
  return $null
}

Banner
Write-Host '   준비하는 동안 창을 닫지 마십시오.' -ForegroundColor DarkGray; Write-Host ''

# ── 1·2. 클로드 코드 ─────────────────────────────────────────────
$Claude = Find-Claude
if (-not $Claude) {
  Doing '클로드 코드를 깝니다 (1~3분)'
  try {
    $b = (New-Object Net.WebClient).DownloadData('https://claude.ai/install.ps1')
    Invoke-Expression ([Text.Encoding]::UTF8.GetString($b))
  } catch { Fail "클로드 코드 설치가 실패했습니다. ($($_.Exception.Message))" }
  $Claude = Find-Claude
  if (-not $Claude) { Fail '깔았는데 클로드 코드를 못 찾습니다.' }
}
try { $ver = (& $Claude --version 2>$null | Select-Object -First 1) } catch { $ver = '' }
Ok '클로드 코드  ' $ver

# 다음부터 터미널에서 그냥 'claude' 만 쳐도 켜지게 — 동료분이 막힌 자리
$Bin = Split-Path $Claude
$up  = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (($up -split ';') -contains $Bin)) {
  [Environment]::SetEnvironmentVariable('Path', ((@($up, $Bin) | Where-Object { $_ }) -join ';'), 'User')
}
if (-not (($env:Path -split ';') -contains $Bin)) { $env:Path = "$Bin;$env:Path" }

# ── 설치가 이미 끝난 사람: 내 폴더에서 바로 켠다 ─────────────────
$cfg = Join-Path $UserDir 'config.json'
# 칸 이름만 보면 안 된다 — 깔다 만 사람은 칸은 있고 값이 비었다(2026-11-22 방태준 컴에서 멈춤)
$done = $false
if (Test-Path $cfg) {
  try { $c = Get-Content $cfg -Raw -Encoding UTF8 | ConvertFrom-Json
        $done = [bool]("$($c.telegram_bot_token)".Trim()) -and [bool]("$($c.tg_api_id)".Trim()) } catch { $done = $false }
}
if ($done) {
  Ok '아델        ' '설치돼 있습니다'
  if ($env:ADELE_START_PREPARE) { Write-Host "READY: $UserDir"; exit 0 }   # 클로드가 부른 것 — 켜지 않는다
  Head2 '클로드 코드를 켭니다'
  Set-Location $UserDir; & $Claude; exit
}

# ── 3. 아델 본체 ─────────────────────────────────────────────────
function Find-Exe { Get-ChildItem $Dir -Recurse -Filter 'Adele.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 }
if (-not (Find-Exe)) {
  Doing '아델 본체를 받습니다 (60MB 남짓 — 몇 분 걸릴 수 있습니다)'
  try {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/tags/latest" -UseBasicParsing
    # 옛 판이 같이 걸려 있어도 가장 높은 번호를 고른다(2026-11-22 — 맨 앞 것을 집어 옛 1.0.14 를 받을 뻔했다)
    $url = ($rel.assets | Where-Object { $_.name -match '^Adele-win-v[\d.]+\.zip$' } |
            Sort-Object { [version]($_.name -replace '^Adele-win-v' -replace '\.zip$') } -Descending |
            Select-Object -First 1).browser_download_url
  } catch { $url = $null }
  if (-not $url) { Fail '받을 주소를 못 찾았습니다 (인터넷 연결을 봐 주십시오).' }
  $zip = Join-Path $env:TEMP 'adele-start.zip'
  $ProgressPreference = 'SilentlyContinue'            # 진행 막대를 그리면 몇 배 느려진다
  $got = $false   # 11/18 깃허브가 한 번 멎었다 — 세 번까지 다시 받는다
  foreach ($t in 1..3) { try { Invoke-WebRequest $url -OutFile $zip -UseBasicParsing; $got = $true; break } catch { Start-Sleep 3 } }
  if (-not $got) { Fail '아델을 받지 못했습니다 (인터넷이 잠깐 끊겼을 수 있습니다 — 한 번 더 붙여넣어 보십시오).' }
  try { Expand-Archive -Path $zip -DestinationPath $Dir -Force } catch { Fail '압축을 풀지 못했습니다.' }
  Remove-Item $zip -ErrorAction SilentlyContinue
  # 압축 안에 Adele 폴더가 한 겹 더 있으면 끌어올린다 — 아델이 제 자리를 찾게
  $inner = Join-Path $Dir 'Adele'
  if ((Test-Path (Join-Path $inner 'Adele.exe')) -and -not (Test-Path (Join-Path $Dir 'Adele.exe'))) {
    Get-ChildItem $inner -Force | Move-Item -Destination $Dir -Force
    Remove-Item $inner -Recurse -Force -ErrorAction SilentlyContinue
  }
  if (-not (Find-Exe)) { Fail '풀었는데 Adele.exe 가 안 보입니다.' }
}
Get-ChildItem $Dir -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue
Ok '아델 본체    ' $Dir

# ── 4. 설치 안내를 놓고 클로드를 켠다 ────────────────────────────
try {
  $md = (New-Object Net.WebClient).DownloadData("$Raw/CLAUDE.md")
  [IO.File]::WriteAllBytes((Join-Path $Dir 'CLAUDE.md'), $md)
  try { [IO.File]::WriteAllBytes((Join-Path $Dir 'setup.py'), (New-Object Net.WebClient).DownloadData("$Raw/setup.py")) } catch { }   # 설치 도구는 늘 최신으로
} catch { if (-not (Test-Path (Join-Path $Dir 'CLAUDE.md'))) { Fail '설치 안내를 받지 못했습니다.' } }

Ok '설치 안내    ' '받았습니다'

# 바탕화면에 「클로드 코드 열기」 — 다음부터 두 번 누르면 된다.
# 여기서 받은 파일은 '받은 표시'가 안 붙어 윈도우가 막지 않는다(2026-11-17)
try {
  $Desk = Join-Path ([Environment]::GetFolderPath('Desktop')) '클로드 코드 열기.bat'
  if (-not (Test-Path $Desk)) {
    $bat = (New-Object Net.WebClient).DownloadData("$Raw/Adele-Start.bat")
    [IO.File]::WriteAllBytes($Desk, $bat)
    Ok '바탕화면     ' '「클로드 코드 열기」 를 놓았습니다'
  }
  $Rad = Join-Path ([Environment]::GetFolderPath('Desktop')) '업무 레이더 열기.bat'
  if (-not (Test-Path $Rad)) {
    [IO.File]::WriteAllBytes($Rad, (New-Object Net.WebClient).DownloadData("$Raw/Adele-Radar.bat"))
    Ok '바탕화면     ' '「업무 레이더 열기」 를 놓았습니다'
  }
} catch { }

# 이미 켜져 있는 클로드가 부른 것이면 여기서 끝 — 그 클로드가 이어서 한다(2026-11-17)
if ($env:ADELE_START_PREPARE) { Write-Host "READY: $Dir"; exit 0 }

Head2 '이제 클로드 코드를 켭니다'
Say '처음이면 로그인 창이 뜹니다 — 클로드 계정으로 들어가 주십시오'
Say '「이 폴더를 믿겠냐」고 물으면 엔터를 누르십시오'
Write-Host ''
Start-Sleep 2
Set-Location $Dir
& $Claude '아델 깔아줘'
