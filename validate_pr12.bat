@echo off
setlocal EnableExtensions

rem PR #12 validation helper for Windows.
rem Runs the focused longitudinal-profile tests first, then delegates the
rem repository-wide checks to validate_repo.bat.
rem
rem Usage:
rem   validate_pr12.bat
rem   validate_pr12.bat --quick
rem
rem --quick runs the focused PR #12 tests, then skips the full pytest suite in
rem validate_repo.bat while still running all static, documentation, and
rem whitespace checks.

cd /d "%~dp0"

call :header "Focused PR #12 tests"
python -m pytest -q tests/test_longitudinal_profile.py
if errorlevel 1 goto :failed

if /I "%~1"=="--quick" (
    call "%~dp0validate_repo.bat" --quick
) else (
    call "%~dp0validate_repo.bat"
)
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
