# ocr-mcp webapp: backend (10859) + Vite (10858). Run from ocr-mcp repo.
$WebPort = 10858
$BackendPort = 10859
$ProjectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path (Join-Path $ProjectRoot "backend\app.py"))) {
    Write-Host "ERROR: Run from ocr-mcp repo. Backend not found." -ForegroundColor Red
    exit 1
}

# Kill processes on our ports
$pids = Get-NetTCPConnection -LocalPort $WebPort, $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 } | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in @($pids)) {
    Write-Host "Killing PID $p on port $WebPort or $BackendPort..." -ForegroundColor Yellow
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch { }
}

# Sync Python deps (pyyaml, transformers, etc.) so backend has everything
Write-Host "Syncing Python deps (uv sync)..." -ForegroundColor Cyan
Set-Location $ProjectRoot
uv pip uninstall yaml 2>$null
uv sync
$ensureYaml = Join-Path $ProjectRoot "scripts\ensure_pyyaml_init.py"
if (Test-Path $ensureYaml) { uv run python $ensureYaml 2>$null }
$yamlCheck = uv run python -c "import yaml; ok = hasattr(yaml,'dump'); print('OK' if ok else 'MISSING'); print(yaml.__file__)" 2>&1
if ($yamlCheck -notmatch "OK") {
    Write-Host "WARNING: PyYAML not usable in backend env. PaddleOCR-VL will fail. Fix: uv sync then restart backend." -ForegroundColor Yellow
} else {
    Write-Host "PyYAML OK (backend env)" -ForegroundColor Green
}
Set-Location $PSScriptRoot

if (-not (Test-Path "node_modules")) { npm install }

Write-Host "Backend (new window) + Vite here. Backend: http://127.0.0.1:$BackendPort  Frontend: http://localhost:$WebPort" -ForegroundColor Cyan
$cmd = "cd '$ProjectRoot'; `$env:PYTHONPATH='$ProjectRoot'; uv run uvicorn backend.app:app --host 127.0.0.1 --port $BackendPort"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $cmd -WindowStyle Normal

Start-Sleep -Seconds 8
Write-Host "Starting Vite (new window)..." -ForegroundColor Green
$viteCmd = "cd '$PSScriptRoot'; npm run dev -- --port $WebPort --host"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $viteCmd -WindowStyle Normal
Start-Sleep -Seconds 5
Start-Process "http://localhost:$WebPort"
Write-Host "Frontend opened in browser. Backend and Vite run in separate windows." -ForegroundColor Cyan
