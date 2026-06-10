#!/usr/bin/env pwsh
# bump-build.ps1 — Increment CURRENT_PROJECT_VERSION in ArchonHub.xcodeproj
# Usage: pwsh bump-build.ps1
#        pwsh bump-build.ps1 -Set 42      (force a specific build number)

param(
    [int]$Set = 0
)

$pbxproj = Join-Path $PSScriptRoot "ArchonHub.xcodeproj\project.pbxproj"

if (-not (Test-Path $pbxproj)) {
    Write-Error "project.pbxproj not found at: $pbxproj"
    exit 1
}

$content = Get-Content $pbxproj -Raw

# Find current build number (first occurrence)
if ($content -match 'CURRENT_PROJECT_VERSION = (\d+);') {
    $current = [int]$Matches[1]
} else {
    Write-Error "Could not find CURRENT_PROJECT_VERSION in project.pbxproj"
    exit 1
}

$new = if ($Set -gt 0) { $Set } else { $current + 1 }

$updated = $content -replace 'CURRENT_PROJECT_VERSION = \d+;', "CURRENT_PROJECT_VERSION = $new;"
Set-Content $pbxproj $updated -NoNewline

Write-Host "✅ Build number: $current → $new"
