# Reset database script
cd "D:\work\projects\workinghour\src\backend"

# Kill all Python processes
Write-Host "Stopping all Python processes..."
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    foreach ($proc in $pythonProcesses) {
        Write-Host "  Killing Python process $($proc.Id)"
        Stop-Process -Id $proc.Id -Force
    }
    Start-Sleep -Seconds 2
}

# Backup database if exists
if (Test-Path 'instance\workinghour.db') {
    $timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    Write-Host "Backing up database to backups\workinghour_backup_$timestamp.db"
    if (-not (Test-Path 'backups')) {
        New-Item -ItemType Directory -Path 'backups' -Force
    }
    Copy-Item 'instance\workinghour.db' "backups\workinghour_backup_$timestamp.db"

    Write-Host "Deleting old database..."
    Remove-Item 'instance\workinghour.db' -Force
    Write-Host "Database deleted successfully"
} else {
    Write-Host "Database file not found"
}
