@echo off
REM Adele start (Windows). Double-click: finds/installs Claude Code, gets Adele, opens Claude.
REM ASCII only - cmd.exe mis-parses UTF-8 Korean. The real work is start.ps1 in the repo,
REM downloaded as bytes and decoded as UTF-8 so the Korean messages survive.
title Adele - Claude Code
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { $b=(New-Object Net.WebClient).DownloadData('https://raw.githubusercontent.com/soanqn144000-tech/adele-dist/main/start/start.ps1') } catch { Write-Host ''; Write-Host '  [!] Internet connection failed. Check the network and try again.'; Read-Host '  Press Enter'; exit 1 }; iex ([Text.Encoding]::UTF8.GetString($b))"
if errorlevel 1 pause
