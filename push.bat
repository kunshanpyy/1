@echo off
chcp 65001 >nul 2>&1
REM ============================================================
REM  One-click push script (push.bat)  -  for Windows Command Prompt (cmd)
REM  Usage: double-click this file, or run "push.bat" in cmd
REM  No Git-Bash needed. Auto-locates git.exe even if it is not
REM  on the system PATH (e.g. WorkBuddy PortableGit).
REM  Pushes committed code to https://github.com/kunshanpyy/1
REM  Remote has a few web-uploaded files, so we use --force to
REM  overwrite them (your own repo, safe).
REM  Auth: username = GitHub account; password prompt = PASTE your
REM        Personal Access Token (not account password; create at
REM        https://github.com/settings/tokens  with "repo" scope)
REM ============================================================

cd /d "%~dp0"

REM ---- auto-locate git.exe ----
set "GIT=git"
where git >nul 2>&1
if errorlevel 1 (
  set "GIT="
  for %%P in (
    "D:\LenovoSoftstore\Install\WorkBuddy\resources\vendor\PortableGit\mingw64\bin\git.exe"
    "D:\LenovoSoftstore\Install\WorkBuddy\resources\vendor\PortableGit\cmd\git.exe"
    "%ProgramFiles%\Git\bin\git.exe"
    "%ProgramFiles%\Git\cmd\git.exe"
    "%ProgramFiles(x86)%\Git\cmd\git.exe"
    "%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
  ) do (
    if not defined GIT if exist "%%~P" set "GIT=%%~P"
  )
)
if not defined GIT (
  echo ERROR: git.exe not found on this machine.
  echo        Install Git for Windows: https://git-scm.com/download/win
  echo        Check "Add to PATH" during install, then re-run this script.
  pause
  exit /b 1
)
echo ==^> Using git: %GIT%

REM ---- branch ----
for /f "delims=" %%b in ('"%GIT%" branch --show-current 2^>nul') do set "BRANCH=%%b"
if not "%BRANCH%"=="main" (
  echo ==^> Renaming branch to main
  "%GIT%" branch -m main 2>nul
)
for /f "delims=" %%b in ('"%GIT%" branch --show-current 2^>nul') do set "BRANCH=%%b"
echo ==^> Current branch: %BRANCH%

REM ---- remote ----
set "TARGET=https://github.com/kunshanpyy/1.git"
for /f "delims=" %%r in ('"%GIT%" remote get-url origin 2^>nul') do set "REMOTE=%%r"
if "%REMOTE%"=="" (
  echo ==^> No origin found, adding: %TARGET%
  "%GIT%" remote add origin %TARGET%
) else (
  echo ==^> Remote origin: %REMOTE%
)

REM ---- working tree check ----
set "DIRTY="
for /f "delims=" %%s in ('"%GIT%" status --porcelain 2^>nul') do set "DIRTY=1"
if defined DIRTY (
  echo ==^> Uncommitted changes found, auto-committing...
  "%GIT%" add -A
  "%GIT%" commit -m "chore: auto-commit before push" >nul 2>&1
)

REM ---- preview ----
echo ==^> Recent commits:
"%GIT%" --no-pager log --oneline -5
for /f %%c in ('"%GIT%" ls-files 2^>nul ^| findstr /n "^" ^| find /c ":"') do set "FC=%%c"
echo ==^> Files to push: %FC%

REM ---- push ----
REM  Note: some restricted networks/proxies break Windows Schannel
REM  certificate REVOCATION checking (CRYPT_E_NO_REVOCATION_CHECK).
REM  We retry with revocation check disabled, then as a last resort
REM  also disable cert verification.
echo.
echo ==^> Pushing... (username=GitHub account, password=PASTE Token)
echo.
"%GIT%" push -u origin main
if errorlevel 1 (
  echo ==^> Retry without revocation check...
  "%GIT%" -c http.schannelCheckRevoke=false push -u origin main
)
if errorlevel 1 (
  echo ==^> Force push without revocation check...
  "%GIT%" -c http.schannelCheckRevoke=false push -u origin main --force
)
if errorlevel 1 (
  echo ==^> Last resort: force push without cert verification...
  "%GIT%" -c http.schannelCheckRevoke=false -c http.sslVerify=false push -u origin main --force
)

echo.
if errorlevel 1 (
  echo FAILED: all push attempts failed. See errors above (network / proxy / token).
) else (
  echo Done! Repo: https://github.com/kunshanpyy/1
)
pause
