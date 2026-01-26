# srv.ps1 - Service Management Script for Working Hour System
# Supports start, stop, restart and status operations

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'status', 'help')]
    [string]$Action = 'start'
)

# Configuration
$BACKEND_PORT = 8000
$FRONTEND_PORT = 3000
$BACKEND_DIR = "src/backend"
$FRONTEND_DIR = "src/frontend"
# Get project root from skill directory location (up 3 levels)
$PROJECT_ROOT = if ($PSScriptRoot) {
    $PSScriptRoot | Split-Path | Split-Path | Split-Path
} else {
    # Fallback when script is not being executed directly
    Get-Location
}

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

# Get process by port using netstat (more compatible)
function Get-ProcessByPort {
    param([int]$Port)
    try {
        $output = cmd /c "netstat -ano 2>nul" 2>$null
        foreach ($line in $output) {
            if ($line -match "TCP.*:$Port.*LISTENING") {
                $parts = $line.Trim() -split '\s+'
                $procId = $parts[-1]
                if ($procId -match '^\d+$') {
                    $process = Get-Process -Id $procId -ErrorAction SilentlyContinue
                    return $process
                }
            }
        }
    } catch {
        return $null
    }
    return $null
}

# Find Python backend process
function Get-BackendProcess {
    $portProcess = Get-ProcessByPort -Port $BACKEND_PORT
    if ($portProcess) {
        return $portProcess
    }

    # Fallback: find by process name
    $pythonProcesses = Get-Process -Name "python*" -ErrorAction SilentlyContinue
    foreach ($proc in $pythonProcesses) {
        try {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
            if ($cmdLine -and $cmdLine -match "run.py") {
                return $proc
            }
        } catch { }
    }
    return $null
}

# Find Node.js frontend process
function Get-FrontendProcess {
    $portProcess = Get-ProcessByPort -Port $FRONTEND_PORT
    if ($portProcess) {
        return $portProcess
    }

    # Fallback: find by process name
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue
    foreach ($proc in $nodeProcesses) {
        try {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
            if ($cmdLine -and ($cmdLine -match "vite" -or $cmdLine -match "dev")) {
                return $proc
            }
        } catch { }
    }
    return $null
}

# Check service status
function Get-ServiceStatus {
    $backend = Get-BackendProcess
    $frontend = Get-FrontendProcess

    return @{
        Backend = @{
            Running = ($null -ne $backend)
            PID = if ($backend) { $backend.Id } else { "N/A" }
            Port = $BACKEND_PORT
        }
        Frontend = @{
            Running = ($null -ne $frontend)
            PID = if ($frontend) { $frontend.Id } else { "N/A" }
            Port = $FRONTEND_PORT
        }
    }
}

# Display service status
function Show-ServiceStatus {
    $status = Get-ServiceStatus

    Write-Info ""
    Write-Info "=========================================="
    Write-Info "   Service Status - Working Hour System"
    Write-Info "=========================================="
    Write-Host ""

    Write-Host "+-----------+--------+------+---------+"
    Write-Host "| Service   | Status | Port | PID     |"
    Write-Host "+-----------+--------+------+---------+"

    # Backend status
    $backendRunning = $status.Backend.Running
    $backendStatusText = if ($backendRunning) { "Running" } else { "Stopped" }
    $backendPid = $status.Backend.PID
    $backendPort = $status.Backend.Port
    Write-Host ("| Backend   | {0,-6} | {1,-4} | {2,-7} |" -f $backendStatusText, $backendPort, $backendPid)

    # Frontend status
    $frontendRunning = $status.Frontend.Running
    $frontendStatusText = if ($frontendRunning) { "Running" } else { "Stopped" }
    $frontendPid = $status.Frontend.PID
    $frontendPort = $status.Frontend.Port
    Write-Host ("| Frontend  | {0,-6} | {1,-4} | {2,-7} |" -f $frontendStatusText, $frontendPort, $frontendPid)

    Write-Host "+-----------+--------+------+---------+"
    Write-Host ""

    # Display access URLs
    if ($status.Backend.Running -or $status.Frontend.Running) {
        Write-Info "Access URLs:"
        if ($status.Frontend.Running) {
            Write-Success "  * Frontend: http://localhost:$FRONTEND_PORT"
        }
        if ($status.Backend.Running) {
            Write-Success "  * Backend:  http://127.0.0.1:$BACKEND_PORT"
            Write-Success "  * API Docs: http://127.0.0.1:$BACKEND_PORT/docs"
        }
        Write-Host ""
    }
}

# Start services
function Start-Service {
    $status = Get-ServiceStatus

    if ($status.Backend.Running -or $status.Frontend.Running) {
        Write-Warning-Custom "Services are already running:"
        if ($status.Backend.Running) {
            Write-Warning-Custom "  * Backend (PID: $($status.Backend.PID))"
        }
        if ($status.Frontend.Running) {
            Write-Warning-Custom "  * Frontend (PID: $($status.Frontend.PID))"
        }
        Write-Warning-Custom ""
        Write-Warning-Custom "Use '/srv stop' to stop services, or '/srv restart' to restart"
        return
    }

    Write-Info ""
    Write-Info "=========================================="
    Write-Info "   Starting Working Hour System Services"
    Write-Info "=========================================="
    Write-Host ""

    # Change to project root
    Push-Location $PROJECT_ROOT

    # Start backend
    Write-Info "Starting backend service..."
    $backendDir = Join-Path $PROJECT_ROOT $BACKEND_DIR
    if (Test-Path $backendDir) {
        try {
            Start-Process -FilePath "python" -ArgumentList "run.py" -WorkingDirectory $backendDir -WindowStyle Hidden
            Write-Success "[OK] Backend started (port: $BACKEND_PORT)"
            Start-Sleep -Seconds 1
        } catch {
            Write-Error-Custom "[FAIL] Backend start failed: $_"
        }
    } else {
        Write-Error-Custom "[FAIL] Backend directory not found: $backendDir"
    }

    # Start frontend
    Write-Info "Starting frontend service..."
    $frontendDir = Join-Path $PROJECT_ROOT $FRONTEND_DIR
    if (Test-Path $frontendDir) {
        try {
            Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WorkingDirectory $frontendDir -WindowStyle Hidden
            Write-Success "[OK] Frontend started (port: $FRONTEND_PORT)"
            Start-Sleep -Seconds 1
        } catch {
            Write-Error-Custom "[FAIL] Frontend start failed: $_"
        }
    } else {
        Write-Error-Custom "[FAIL] Frontend directory not found: $frontendDir"
    }

    Pop-Location

    # Wait for services to start and show status
    Write-Info ""
    Write-Info "Waiting for services to start..."
    Start-Sleep -Seconds 3
    Show-ServiceStatus
}

# Stop services by port
function Stop-ServiceByPort {
    param([int]$Port, [string]$Name)

    try {
        $output = cmd /c "netstat -ano 2>nul" 2>$null
        foreach ($line in $output) {
            if ($line -match "TCP.*:$Port.*LISTENING") {
                $parts = $line.Trim() -split '\s+'
                $procId = $parts[-1]
                if ($procId -match '^\d+$') {
                    taskkill /F /PID $procId > $null 2>&1
                    return $procId
                }
            }
        }
    } catch {
        return $null
    }
    return $null
}

# Stop services
function Stop-Service {
    Write-Info ""
    Write-Info "=========================================="
    Write-Info "   Stopping Working Hour System Services"
    Write-Info "=========================================="
    Write-Host ""

    $stopped = $false

    # Stop backend by port
    $backendPid = Stop-ServiceByPort -Port $BACKEND_PORT -Name "Backend"
    if ($backendPid) {
        Write-Success "[OK] Backend stopped (PID: $backendPid)"
        $stopped = $true
    } else {
        Write-Warning-Custom "[INFO] Backend not running"
    }

    # Stop frontend by port
    $frontendPid = Stop-ServiceByPort -Port $FRONTEND_PORT -Name "Frontend"
    if ($frontendPid) {
        Write-Success "[OK] Frontend stopped (PID: $frontendPid)"
        $stopped = $true
    } else {
        Write-Warning-Custom "[INFO] Frontend not running"
    }

    if (-not $stopped) {
        Write-Warning-Custom ""
        Write-Warning-Custom "No services are running"
        return
    }

    # Wait for ports to be released
    Write-Info ""
    Write-Info "Waiting for ports to be released..."
    Start-Sleep -Seconds 2

    # Verify port status
    $backendCheck = Get-ProcessByPort -Port $BACKEND_PORT
    $frontendCheck = Get-ProcessByPort -Port $FRONTEND_PORT

    if ($backendCheck -or $frontendCheck) {
        Write-Warning-Custom "[WARN] Some ports may still be in use, trying force stop..."
        # Try one more time
        Stop-ServiceByPort -Port $BACKEND_PORT -Name "Backend" | Out-Null
        Stop-ServiceByPort -Port $FRONTEND_PORT -Name "Frontend" | Out-Null
        Start-Sleep -Seconds 1
    }

    Write-Success ""
    Write-Success "[OK] All services stopped successfully"
    Write-Host ""
}

# Restart services
function Restart-Service {
    Write-Info ""
    Write-Info "=========================================="
    Write-Info "   Restarting Working Hour System Services"
    Write-Info "=========================================="
    Write-Host ""

    Write-Info "Stopping existing services..."
    Stop-Service

    Write-Info "Waiting for ports to be released..."
    Start-Sleep -Seconds 3

    Write-Info ""
    Write-Info "Restarting services..."
    Start-Service
}

# Show help
function Show-Help {
    Write-Info ""
    Write-Info "=========================================="
    Write-Info "   Working Hour System Service Management"
    Write-Info "=========================================="
    Write-Host ""

    Write-Host "Usage: /srv [action]"
    Write-Host ""
    Write-Host "Actions:"
    Write-Host "  (none)  - Start frontend and backend services (default)"
    Write-Host "  start   - Start frontend and backend services"
    Write-Host "  status  - Show service running status"
    Write-Host "  restart - Restart frontend and backend services"
    Write-Host "  stop    - Stop frontend and backend services"
    Write-Host "  help    - Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  /srv           # Start services"
    Write-Host "  /srv status    # Show status"
    Write-Host "  /srv restart   # Restart services"
    Write-Host "  /srv stop      # Stop services"
    Write-Host ""
    Write-Host "Access URLs:"
    Write-Success "  * Frontend:   http://localhost:$FRONTEND_PORT"
    Write-Success "  * Backend:    http://127.0.0.1:$BACKEND_PORT"
    Write-Success "  * API Docs:   http://127.0.0.1:$BACKEND_PORT/docs"
    Write-Host ""
}

# Main logic
switch ($Action) {
    'start' {
        Start-Service
    }
    'stop' {
        Stop-Service
    }
    'restart' {
        Restart-Service
    }
    'status' {
        Show-ServiceStatus
    }
    'help' {
        Show-Help
    }
}
