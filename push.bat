@echo off
chcp 65001 >nul 2>&1
REM ============================================================
REM  One-click push script (push.bat)  -  for Windows Command Prompt (cmd)
REM  Usage: double-click this file, or run "push.bat" in cmd
REM  What it does: push the committed code to
REM      https://github.com/kunshanpyy/1
REM  Remote already has a few web-uploaded files, so we use
REM      --force to overwrite them (your own repo, safe).
REM  Auth: username = GitHub account;
REM        password prompt = PASTE your Personal Access Token
REM        (not your account password; create at
REM         https://github.com/settings/tokens  with "repo" scope)
REM ============================================================

cd /d "%~dp0"

echo ==^> Current directory: %CD%

REM ---- branch ----
for /f "delims=" %%b in ('git branch --show-current 2^>nul') do set "BRANCH=%%b"
if not "%BRANCH%"=="main" (
  echo ==^> Renaming branch to main
  git branch -m main 2>nul
)
for /f "delims=" %%b in ('git branch --show-current 2^>nul') do set "BRANCH=%%b"
echo ==^> Current branch: %BRANCH%

REM ---- remote ----
set "TARGET=https://github.com/kunshanpyy/1.git"
for /f "delims=" %%r in ('git remote get-url origin 2^>nul') do set "REMOTE=%%r"
if "%REMOTE%"=="" (
  echo ==^> No origin found, adding: %TARGET%
  git remote add origin %TARGET%
) else (
  echo ==^> Remote origin: %REMOTE%
)

REM ---- working tree check ----
set "DIRTY="
for /f "delims=" %%s in ('git status --porcelain 2^>nul') do set "DIRTY=1"
if defined DIRTY (
  echo ==^> Uncommitted changes found, auto-committing...
  git add -A
  git commit -m "chore: auto-commit before push" >nul 2>&1
)

REM ---- preview ----
echo ==^> Recent commits:
git log --oneline -5
for /f %%c in ('git ls-files ^| find /c /v ""') do set "FC=%%c"
echo ==^> Files to push: %FC%

REM ---- push ----
echo.
echo ==^> Pushing... (username=GitHub account, password=PASTE Token)
echo.
git push -u origin main
if errorlevel 1 (
  echo ==^> Normal push failed, trying force push...
  git push -u origin main --force
)

echo.
echo Done! Repo: https://github.com/kunshanpyy/1
pause
