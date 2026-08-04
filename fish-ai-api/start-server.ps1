$ErrorActionPreference = 'Stop'
$serverRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $serverRoot '.venv\Scripts\python.exe') -m uvicorn server:app --host 127.0.0.1 --port 8000
