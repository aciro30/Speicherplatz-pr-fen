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
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -RegisterTask -RunOnlyWhenUserLoggedOn

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File .\setup.ps1 -OverwriteConfig -AutoDetect
#>

[CmdletBinding()]
param(
    [int]$Threshold = 80,
    [switch]$OverwriteConfig,
    [switch]$AutoDetect,
    [switch]$RegisterTask,
    [switch]$RunOnlyWhenUserLoggedOn,
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
        [int]$Minutes,
        [switch]$OnlyWhenUserLoggedOn
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
        -RepetitionInterval (New-TimeSpan -Minutes $Minutes)

    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable

    $currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $description = "Prueft regelmaessig den freien Speicherplatz und verschickt optional E-Mail-Warnungen."

    if ($OnlyWhenUserLoggedOn) {
        $principal = New-ScheduledTaskPrincipal `
            -UserId $currentUser `
            -LogonType Interactive `
            -RunLevel Highest

        $task = New-ScheduledTask `
            -Action $action `
            -Trigger $trigger `
            -Settings $settings `
            -Principal $principal `
            -Description $description

        Register-ScheduledTask `
            -TaskName $Name `
            -InputObject $task `
            -Force | Out-Null

        return
    }

    Write-Host "Fuer 'Ausfuehren unabhaengig von der Benutzeranmeldung' werden Windows-Anmeldedaten benoetigt."
    $credential = Get-Credential `
        -UserName $currentUser `
        -Message "Windows-Anmeldedaten fuer den Scheduled Task '$Name'"

    $principal = New-ScheduledTaskPrincipal `
        -UserId $credential.UserName `
        -LogonType Password `
        -RunLevel Highest

    $task = New-ScheduledTask `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description $description

    Register-ScheduledTask `
        -TaskName $Name `
        -InputObject $task `
        -User $credential.UserName `
        -Password $credential.GetNetworkCredential().Password `
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

Write-Step "Environment-Datei pruefen"
$envPath = Join-Path $projectRoot ".env"
$envExamplePath = Join-Path $projectRoot ".env.example"
if (-not (Test-Path $envPath)) {
    if (Test-Path $envExamplePath) {
        Copy-Item $envExamplePath $envPath
        Write-Host ".env wurde aus .env.example erstellt. Bitte SMTP_PASSWORD vor produktiver Nutzung eintragen."
    }
    else {
        Write-Host ".env.example wurde nicht gefunden. Bitte SMTP_PASSWORD als Umgebungsvariable setzen."
    }
}
else {
    Write-Host ".env existiert bereits: $envPath"
}

$envContent = @{}
if (Test-Path $envPath) {
    Get-Content $envPath | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
            return
        }

        $parts = $line.Split("=", 2)
        $envContent[$parts[0].Trim()] = $parts[1].Trim()
    }
}

$requiredEnvNames = @("SMTP_SERVER", "SMTP_PORT", "SMTP_SENDER_EMAIL", "SMTP_PASSWORD")
$missingEnvNames = @($requiredEnvNames | Where-Object {
    -not $envContent.ContainsKey($_) -or [string]::IsNullOrWhiteSpace($envContent[$_])
})

if ($missingEnvNames.Count -gt 0) {
    Write-Warning "In .env fehlen noch folgende Werte: $($missingEnvNames -join ', ')"
    Write-Warning "E-Mail-Versand funktioniert erst, wenn diese Werte gesetzt sind."
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
        -Minutes $IntervalMinutes `
        -OnlyWhenUserLoggedOn:$RunOnlyWhenUserLoggedOn

    Write-Host "Scheduled Task registriert: $TaskName"
    Write-Host "Intervall: alle $IntervalMinutes Minuten"
    if ($RunOnlyWhenUserLoggedOn) {
        Write-Host "Ausfuehrung: nur wenn der Benutzer angemeldet ist"
    }
    else {
        Write-Host "Ausfuehrung: auch wenn der Benutzer nicht angemeldet ist"
    }
}

Write-Host ""
Write-Host "Setup abgeschlossen." -ForegroundColor Green
Write-Host "Konfiguration: $projectRoot\config\config.json"
Write-Host "Manueller Start: $venvPython $projectRoot\src\disk_monitor.py --once"
