# PowerShell script to start the TradeEdge backend server
# Usage: .\start_server.ps1

Write-Host "Starting TradeEdge API Server..." -ForegroundColor Green
Write-Host ""

# Check if .env file exists
if (Test-Path .env) {
    Write-Host "✓ Found .env file" -ForegroundColor Green
} else {
    Write-Host "⚠ Warning: .env file not found. Make sure FRED_API_KEY is set." -ForegroundColor Yellow
}

# Start the server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

