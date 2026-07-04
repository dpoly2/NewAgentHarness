# Start Open Design daemon (Docker)
# Run this to start the Open Design service before using od:// tools
$deployDir = "D:\projects\open-design\deploy"

if (Test-Path $deployDir) {
    Set-Location $deployDir
    docker compose up -d
    Write-Host "Open Design starting at http://localhost:7456"
} else {
    Write-Host "Open Design not installed. Clone nexu-io/open-design first."
}
