<#
.SYNOPSIS
  Richtet den Speicherplatz-Monitor unter Windows ein.

.DESCRIPTION
  Das Skript erstellt eine virtuelle Python-Umgebung, installiert die
  Abhaengigkeiten, erzeugt config\config.json und kann optional einen
  Windows Scheduled Task fuer regelmaessige Pruefungen registrieren.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\setup.ps1

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -OverwriteConfig -AutoDetect
#>

[CmdletBinding()]
param(
    [int]$Threshold = 80,
    [switch]$OverwriteConfig,
    [switch]$AutoDetect,
    [switch]$RegisterTask,
    [int]$IntervalMinutes = 720,
    [string]$TaskName = "Speicherplatz-Monitor"
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{
            Command = "py"
            Args = @("-3")
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{
            Command = "python"
            Args = @()
        }
    }

    throw "Python wurde nicht gefunden. Bitte Python 3 installieren und zum PATH hinzufuegen."
}

function Invoke-Python {
    param(
        [hashtable]$Python,
        [string[]]$Arguments
    )

    & $Python.Command @($Python.Args + $Arguments)
    if ($LASTEXITCODE -ne 0) {
        $argumentText = ($Python.Args + $Arguments) -join " "
        throw "Python-Befehl fehlgeschlagen: $($Python.Command) $argumentText"
    }
}

function Register-MonitorTask {
    param(
        [string]$Name,
        [string]$PythonExe,
        [string]$ProjectRoot,
        [int]$Minutes
    )

    if ($Minutes -lt 1) {
        throw "IntervalMinutes muss mindestens 1 sein."
    }

    $scriptPath = Join-Path $ProjectRoot "src\disk_monitor.py"
    $arguments = "`"$scriptPath`" --once"

    $action = New-ScheduledTaskAction `
        -Execute $PythonExe `
        -Argument $arguments `
        -WorkingDirectory $ProjectRoot

    $startAt = (Get-Date).AddMinutes(1)
    $trigger = New-ScheduledTaskTrigger `
        -Once `
        -At $startAt `
        -RepetitionInterval (New-TimeSpan -Minutes $Minutes) `
        -RepetitionDuration (New-TimeSpan -Days 3650)

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable

    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $principal = New-ScheduledTaskPrincipal `
        -UserId $currentUser `
        -LogonType InteractiveToken `
        -RunLevel Highest

    Register-ScheduledTask `
        -TaskName $Name `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Prueft regelmaessig den freien Speicherplatz und verschickt optional E-Mail-Warnungen." `
        -Force | Out-Null
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

Write-Step "Projektverzeichnis pruefen"
if (-not (Test-Path "src\disk_monitor.py")) {
    throw "src\disk_monitor.py wurde nicht gefunden. Bitte setup.ps1 aus dem Projektordner starten."
}

if (-not (Test-Path "requirements.txt")) {
    throw "requirements.txt wurde nicht gefunden."
}

$python = Get-PythonCommand

Write-Step "Python-Version pruefen"
Invoke-Python -Python $python -Arguments @("--version")

Write-Step "Virtuelle Umgebung erstellen"
$venvPath = Join-Path $projectRoot "venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Invoke-Python -Python $python -Arguments @("-m", "venv", $venvPath)
}
else {
    Write-Host "Virtuelle Umgebung existiert bereits: $venvPath"
}

Write-Step "Abhaengigkeiten installieren"
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "pip upgrade fehlgeschlagen."
}

& $venvPython -m pip install -r (Join-Path $projectRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "Installation der Abhaengigkeiten fehlgeschlagen."
}

Write-Step "Konfiguration erstellen"
$setupArgs = @("src\setup_config.py", "--threshold", "$Threshold")
if ($OverwriteConfig) {
    $setupArgs += "--overwrite"
}
if ($AutoDetect) {
    $setupArgs += "--auto-detect"
}

& $venvPython @setupArgs
if ($LASTEXITCODE -ne 0) {
    throw "Konfiguration konnte nicht erstellt werden."
}

Write-Step "Testlauf ausfuehren"
& $venvPython "src\disk_monitor.py" "--once"
if ($LASTEXITCODE -ne 0) {
    throw "Testlauf fehlgeschlagen."
}

if ($RegisterTask) {
    Write-Step "Scheduled Task registrieren"
    Register-MonitorTask `
        -Name $TaskName `
        -PythonExe $venvPython `
        -ProjectRoot $projectRoot `
        -Minutes $IntervalMinutes

    Write-Host "Scheduled Task registriert: $TaskName"
    Write-Host "Intervall: alle $IntervalMinutes Minuten"
}

Write-Host ""
Write-Host "Setup abgeschlossen." -ForegroundColor Green
Write-Host "Konfiguration: $projectRoot\config\config.json"
Write-Host "Manueller Start: $venvPython $projectRoot\src\disk_monitor.py --once"
