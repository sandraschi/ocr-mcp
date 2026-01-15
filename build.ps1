# Zed Extension Build Script for OCRDocumentProcessing
# Run this script to build the Rust extension for Zed IDE

rustup target add wasm32-wasip1

Write-Host "Building OCRDocumentProcessing Extension..." -ForegroundColor Green
cargo build --release --target wasm32-wasip1

if ($LASTEXITCODE -eq 0) {
    Write-Host "---------------------------------------" -ForegroundColor Green
    Write-Host "✅ Build Successful!" -ForegroundColor Green
    Write-Host "Next: In Zed, run 'Extensions: Install Dev Extension'" -ForegroundColor Cyan
    Write-Host "and select: $PWD" -ForegroundColor Cyan
    Write-Host "---------------------------------------" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed. Check the Rust errors above." -ForegroundColor Red
}
