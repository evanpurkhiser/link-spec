param(
    [string]$Rekordbox = 'C:\Program Files\rekordbox\rekordbox 7.2.19\rekordbox.exe',
    [string]$ReadyMarker = 'C:\Users\Research\link-export-conformance\link-ready.json',
    [int]$WindowTimeoutSeconds = 90,
    [int]$SettleSeconds = 35
)

$ErrorActionPreference = 'Stop'

trap {
    [ordered]@{
        success = $false
        error = $_.Exception.Message
        failed_at = [DateTimeOffset]::Now.ToUnixTimeSeconds()
    } | ConvertTo-Json | Set-Content -Encoding UTF8 $ReadyMarker
    exit 1
}

Remove-Item -Force -ErrorAction SilentlyContinue $ReadyMarker
$process = Start-Process -FilePath $Rekordbox -PassThru
$deadline = (Get-Date).AddSeconds($WindowTimeoutSeconds)

do {
    Start-Sleep -Milliseconds 500
    $process.Refresh()
} while ($process.MainWindowHandle -eq 0 -and (Get-Date) -lt $deadline)

if ($process.MainWindowHandle -eq 0) {
    throw 'rekordbox did not create an interactive window before the deadline.'
}

Start-Sleep -Seconds $SettleSeconds

[ordered]@{
    success = $true
    process_id = $process.Id
    main_window_handle = $process.MainWindowHandle.ToInt64()
    ready_at = [DateTimeOffset]::Now.ToUnixTimeSeconds()
} | ConvertTo-Json | Set-Content -Encoding UTF8 $ReadyMarker
