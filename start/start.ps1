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

function Say($m)  { Write-Host ''; Write-Host "  $m" }
function Fail($m) {
  Say "⚠ $m"; Say '이 창을 사진 찍어 아델을 알려 주신 분께 보내 주십시오.'
  Read-Host '  (엔터를 누르면 닫힙니다)' | Out-Null; exit 1
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

Clear-Host
Say '아델을 준비합니다. 창을 닫지 마십시오.'

# ── 1·2. 클로드 코드 ─────────────────────────────────────────────
$Claude = Find-Claude
if (-not $Claude) {
  Say '클로드 코드가 없어 깝니다. (1~3분)'
  try {
    $b = (New-Object Net.WebClient).DownloadData('https://claude.ai/install.ps1')
    Invoke-Expression ([Text.Encoding]::UTF8.GetString($b))
  } catch { Fail "클로드 코드 설치가 실패했습니다. ($($_.Exception.Message))" }
  $Claude = Find-Claude
  if (-not $Claude) { Fail '깔았는데 클로드 코드를 못 찾습니다.' }
}
try { $ver = (& $Claude --version 2>$null | Select-Object -First 1) } catch { $ver = '' }
Say "클로드 코드 ✓  ($ver)"

# 다음부터 터미널에서 그냥 'claude' 만 쳐도 켜지게 — 동료분이 막힌 자리
$Bin = Split-Path $Claude
$up  = [Environment]::GetEnvironmentVariable('Path', 'User')
if (-not (($up -split ';') -contains $Bin)) {
  [Environment]::SetEnvironmentVariable('Path', ((@($up, $Bin) | Where-Object { $_ }) -join ';'), 'User')
}
if (-not (($env:Path -split ';') -contains $Bin)) { $env:Path = "$Bin;$env:Path" }

# ── 설치가 이미 끝난 사람: 내 폴더에서 바로 켠다 ─────────────────
$cfg = Join-Path $UserDir 'config.json'
if ((Test-Path $cfg) -and (Select-String -Path $cfg -Pattern '"telegram_bot_token"' -Quiet) `
    -and (Select-String -Path $cfg -Pattern '"tg_api_id"' -Quiet)) {
  Say '설치는 끝나 있습니다. 클로드 코드를 켭니다.'
  Set-Location $UserDir; & $Claude; exit
}

# ── 3. 아델 본체 ─────────────────────────────────────────────────
function Find-Exe { Get-ChildItem $Dir -Recurse -Filter 'Adele.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 }
if (-not (Find-Exe)) {
  Say '아델 본체를 받습니다. (60MB 남짓 — 몇 분 걸릴 수 있습니다)'
  try {
    $rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/tags/latest" -UseBasicParsing
    $url = ($rel.assets | Where-Object { $_.name -like 'Adele-win-*.zip' } | Select-Object -First 1).browser_download_url
  } catch { $url = $null }
  if (-not $url) { Fail '받을 주소를 못 찾았습니다 (인터넷 연결을 봐 주십시오).' }
  $zip = Join-Path $env:TEMP 'adele-start.zip'
  $ProgressPreference = 'SilentlyContinue'            # 진행 막대를 그리면 몇 배 느려진다
  try { Invoke-WebRequest $url -OutFile $zip -UseBasicParsing } catch { Fail '아델을 받지 못했습니다.' }
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
Say "아델 본체 ✓  ($Dir)"

# ── 4. 설치 안내를 놓고 클로드를 켠다 ────────────────────────────
try {
  $md = (New-Object Net.WebClient).DownloadData("$Raw/CLAUDE.md")
  [IO.File]::WriteAllBytes((Join-Path $Dir 'CLAUDE.md'), $md)
} catch { if (-not (Test-Path (Join-Path $Dir 'CLAUDE.md'))) { Fail '설치 안내를 받지 못했습니다.' } }

Say '클로드 코드를 켭니다. 처음이면 로그인 창이 뜹니다 — 클로드 계정으로 들어가 주십시오.'
Say '「이 폴더를 믿겠냐」고 물으면 엔터를 누르십시오.'
Start-Sleep 2
Set-Location $Dir
& $Claude '아델 깔아줘'
