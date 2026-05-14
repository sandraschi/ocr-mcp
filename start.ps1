Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
# ------------------------------

# Ensure uv prefers CUDA torch when a GPU is available
$env:UV_EXTRA_INDEX_URL = "https://download.pytorch.org/whl/cu126"

# Delegates to web_sota/start.ps1 which starts backend (uvicorn :10859) + frontend (Vite :10858)
& "$PSScriptRoot\web_sota\start.ps1" @PSBoundParameters
