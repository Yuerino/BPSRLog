@echo off
REM Simple launcher for BPSR capture
SETLOCAL ENABLEDELAYEDEXPANSION

IF NOT EXIST .venv (
  echo [run] Creating python virtual environment...
  python -m venv .venv || goto :error
)
CALL .venv\Scripts\activate.bat || goto :error

REM Install deps if scapy missing
python -c "import scapy" 2>NUL 1>NUL
IF %ERRORLEVEL% NEQ 0 (
  echo [run] Installing requirements...
  pip install --upgrade pip
  pip install -r requirements.txt || goto :error
)

echo [run] Starting capture (Ctrl+C to stop)...
python -m bpsr %*
GOTO :eof

:error
echo [run] Failed.
EXIT /B 1
