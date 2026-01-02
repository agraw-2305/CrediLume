Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Set-Location -Path $PSScriptRoot

$env:PORT = if ($env:PORT) { $env:PORT } else { '5000' }

Write-Host "Starting CrediLume Flask server on http://127.0.0.1:$($env:PORT)" -ForegroundColor Cyan

function Stop-ProcessOnPort([int]$Port) {
  $lines = netstat -ano | Select-String ":$Port\s" -ErrorAction SilentlyContinue
  if (-not $lines) { return }

  $pids = @()
  foreach ($line in $lines) {
    # netstat output ends with PID
    $parts = ($line.Line -split "\s+") | Where-Object { $_ -ne '' }
    if ($parts.Count -ge 5) {
      $pid = $parts[-1]
      if ($pid -match '^[0-9]+$') { $pids += [int]$pid }
    }
  }

  $pids = $pids | Sort-Object -Unique
  foreach ($pid in $pids) {
    if ($pid -and $pid -ne $PID) {
      try {
        Write-Host "Stopping process PID $pid on port $Port..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force -ErrorAction Stop
      } catch {
        Write-Warning "Could not stop PID ${pid}: $($_.Exception.Message)"
      }
    }
  }
}

Stop-ProcessOnPort -Port ([int]$env:PORT)

$venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (Test-Path $venvPython) {
  $env:FLASK_DEBUG = if ($env:FLASK_DEBUG) { $env:FLASK_DEBUG } else { '1' }
  $env:FLASK_RELOADER = if ($env:FLASK_RELOADER) { $env:FLASK_RELOADER } else { '1' }
  & $venvPython app.py
} else {
  Write-Warning '.venv not found. Falling back to system Python.'
  $env:FLASK_DEBUG = if ($env:FLASK_DEBUG) { $env:FLASK_DEBUG } else { '1' }
  $env:FLASK_RELOADER = if ($env:FLASK_RELOADER) { $env:FLASK_RELOADER } else { '1' }
  python app.py
}
