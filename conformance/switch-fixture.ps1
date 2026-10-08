param(
    [string]$Fixture = '',
    [switch]$Restore,
    [switch]$StopOnly,
    [switch]$SkipStop
)

$ErrorActionPreference = 'Stop'
$library = Join-Path $env:APPDATA 'Pioneer\rekordbox'
$database = Join-Path $library 'master.db'
$backup = Join-Path $library 'link-export-conformance-original.db'
$active = Join-Path $library 'link-export-conformance-active.json'
$stagedActive = Join-Path $PSScriptRoot 'active-guest-manifest.json'

function Stop-Rekordbox {
    $processNames = @('rekordbox', 'rekordboxAgent', 'edb_streamd')
    $processes = @(Get-Process $processNames -ErrorAction SilentlyContinue)
    foreach ($process in $processes) {
        $null = $process.CloseMainWindow()
    }

    if ($processes.Count -gt 0) {
        Start-Sleep -Seconds 5
        Get-Process $processNames -ErrorAction SilentlyContinue |
            Stop-Process -Force
        Start-Sleep -Seconds 2
    }
}

function Remove-DatabaseJournals {
    Remove-Item "${database}-wal", "${database}-shm" -Force -ErrorAction SilentlyContinue
}

function Install-DatabaseFile {
    param([string]$Source)

    if (Test-Path $database) {
        $replacementBackup = "$database.replaced"
        Remove-Item $replacementBackup -Force -ErrorAction SilentlyContinue
        $maxAttempts = 15
        for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
            try {
                [System.IO.File]::Replace($Source, $database, $replacementBackup, $true)
                break
            }
            catch [System.IO.IOException] {
                $win32Error = $_.Exception.HResult -band 0xffff
                $isTransientLock = $win32Error -in @(32, 33)
                if (-not $isTransientLock -or $attempt -eq $maxAttempts) {
                    throw
                }

                Write-Warning "Database replacement is locked; retrying ($attempt/$maxAttempts)."
                Start-Sleep -Seconds 2
            }
        }
        Remove-Item $replacementBackup -Force
        return
    }

    [System.IO.File]::Move($Source, $database)
}

if ($StopOnly -and ($Restore -or $Fixture -or $SkipStop)) {
    throw '-StopOnly cannot be combined with -Fixture, -Restore, or -SkipStop.'
}

if ($StopOnly) {
    Stop-Rekordbox
    Write-Output 'Rekordbox is stopped.'
    exit 0
}

if (-not $SkipStop) {
    Stop-Rekordbox
}

if ($Restore) {
    if (-not (Test-Path $backup)) {
        throw "No conformance backup exists at $backup"
    }
    Copy-Item $backup "$database.restore" -Force
    Install-DatabaseFile "$database.restore"
    Remove-DatabaseJournals
    Remove-Item $active -Force -ErrorAction SilentlyContinue
    Remove-Item $stagedActive -Force -ErrorAction SilentlyContinue
    Write-Output "Restored the pre-conformance database."
    exit 0
}

if (-not $Fixture) {
    throw 'Pass -Fixture with a staged fixture directory, or use -Restore.'
}

$fixtureDatabase = Join-Path $Fixture 'master.db'
$fixtureManifest = Join-Path $Fixture 'manifest.json'
if (-not (Test-Path $fixtureDatabase) -or -not (Test-Path $fixtureManifest)) {
    throw "Fixture must contain master.db and manifest.json: $Fixture"
}

$manifest = Get-Content $fixtureManifest -Raw | ConvertFrom-Json
$fixtureHash = (Get-FileHash $fixtureDatabase -Algorithm SHA256).Hash.ToLowerInvariant()
if ($fixtureHash -ne $manifest.database_sha256.ToLowerInvariant()) {
    throw "Fixture hash does not match manifest: $fixtureHash"
}

if (-not (Test-Path $backup)) {
    Copy-Item $database $backup
}

Copy-Item $fixtureDatabase "$database.next" -Force
$installedHash = (Get-FileHash "$database.next" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($installedHash -ne $fixtureHash) {
    Remove-Item "$database.next" -Force -ErrorAction SilentlyContinue
    throw "Copied fixture hash does not match source: $installedHash"
}
Install-DatabaseFile "$database.next"
Remove-DatabaseJournals
Copy-Item $fixtureManifest $active -Force
Copy-Item $fixtureManifest $stagedActive -Force
Get-Content $active
Write-Output 'Fixture installed. Start rekordbox manually after reviewing the manifest above.'
