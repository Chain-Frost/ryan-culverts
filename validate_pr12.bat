@echo off
setlocal EnableExtensions

rem PR #12 validation helper for Windows.
rem Run from anywhere; the script changes to the repository root automatically.
rem
rem Usage:
rem   validate_pr12.bat
rem   validate_pr12.bat --quick
rem
rem --quick skips the full pytest suite after the focused PR #12 tests.

cd /d "%~dp0"

set "QUICK=0"
if /I "%~1"=="--quick" set "QUICK=1"

call :header "Python version"
python --version
if errorlevel 1 goto :failed

call :header "Focused PR #12 tests"
python -m pytest -q tests/test_longitudinal_profile.py
if errorlevel 1 goto :failed

if "%QUICK%"=="1" (
    echo.
    echo [SKIP] Full pytest suite ^(--quick supplied^)
) else (
    call :header "Full pytest suite"
    python -m pytest -q
    if errorlevel 1 goto :failed
)

call :header "Ruff lint"
python -m ruff check .
if errorlevel 1 goto :failed

call :header "Ruff format check"
python -m ruff format --check .
if errorlevel 1 goto :failed

call :header "Pyright"
python -m pyright
if errorlevel 1 goto :failed

call :header "Markdown lint"
python -m pymarkdown -d MD013 scan -r README.md docs AGENTS.md
if errorlevel 1 goto :failed

call :header "MkDocs strict build"
python -m mkdocs build --strict
if errorlevel 1 goto :failed

call :header "Git whitespace check"
git diff --check
if errorlevel 1 goto :failed

echo.
echo ============================================================
echo PR #12 validation PASSED
echo ============================================================
exit /b 0

:header
echo.
echo ============================================================
echo %~1
echo ============================================================
exit /b 0

:failed
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo ============================================================
echo PR #12 validation FAILED
if not "%EXIT_CODE%"=="0" echo Exit code: %EXIT_CODE%
echo ============================================================
exit /b %EXIT_CODE%
