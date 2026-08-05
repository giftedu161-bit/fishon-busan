$ErrorActionPreference = 'Stop'
$serverRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $serverRoot
$env:GEMINI_API_KEY = [Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')
& (Join-Path $serverRoot '.venv\Scripts\python.exe') -m uvicorn server:app --host 127.0.0.1 --port 8000
