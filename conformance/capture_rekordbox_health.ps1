param(
    [Parameter(Mandatory = $true)]
    [string]$Label,

    [Parameter(Mandatory = $true)]
    [DateTime]$SinceUtc
)

$ErrorActionPreference = 'Stop'
$capturedAtUtc = [DateTime]::UtcNow

$processes = @(
    Get-Process -Name rekordbox -ErrorAction SilentlyContinue |
        ForEach-Object {
            [ordered]@{
                id = $_.Id
                start_time_utc = if ($_.StartTime) { $_.StartTime.ToUniversalTime().ToString('o') } else { $null }
                responding = $_.Responding
                working_set_bytes = $_.WorkingSet64
                private_memory_bytes = $_.PrivateMemorySize64
                virtual_memory_bytes = $_.VirtualMemorySize64
                main_window_handle = $_.MainWindowHandle.ToInt64()
            }
        }
)

$helperProcesses = @(
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '(?i)(rekordbox|dbserver|edb_|psv|pioneer)'
        } |
        Sort-Object ProcessId |
        ForEach-Object {
            [ordered]@{
                id = [uint32]$_.ProcessId
                parent_id = [uint32]$_.ParentProcessId
                name = $_.Name
                executable_path = $_.ExecutablePath
                command_line = $_.CommandLine
            }
        }
)

$relatedProcessIds = @(
    $processes | ForEach-Object { [uint32]$_.id }
    $helperProcesses | ForEach-Object { [uint32]$_.id }
)
$tcpListeners = @(
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
        Where-Object { $_.OwningProcess -in $relatedProcessIds } |
        Sort-Object LocalAddress, LocalPort, OwningProcess |
        ForEach-Object {
            [ordered]@{
                local_address = $_.LocalAddress
                local_port = [uint16]$_.LocalPort
                owning_process_id = [uint32]$_.OwningProcess
                state = $_.State.ToString()
            }
        }
)

$events = @(
    Get-WinEvent -FilterHashtable @{LogName = 'Application'; StartTime = $SinceUtc.ToLocalTime()} -ErrorAction SilentlyContinue |
        Where-Object {
            $_.TimeCreated.ToUniversalTime() -le $capturedAtUtc -and
            ($_.ProviderName -in @('Application Error', 'Windows Error Reporting', '.NET Runtime') -or
             $_.Message -match '(?i)rekordbox')
        } |
        Select-Object -First 50 |
        ForEach-Object {
            [ordered]@{
                time_created_utc = $_.TimeCreated.ToUniversalTime().ToString('o')
                provider = $_.ProviderName
                event_id = $_.Id
                level = $_.LevelDisplayName
                record_id = $_.RecordId
                message = $_.Message
            }
        }
)

$os = Get-CimInstance Win32_OperatingSystem

[ordered]@{
    schema_version = 2
    label = $Label
    since_utc = $SinceUtc.ToUniversalTime().ToString('o')
    captured_at_utc = $capturedAtUtc.ToString('o')
    rekordbox_processes = $processes
    rekordbox_process_count = $processes.Count
    helper_processes = $helperProcesses
    helper_process_count = $helperProcesses.Count
    tcp_listeners = $tcpListeners
    os = [ordered]@{
        free_physical_memory_kib = [uint64]$os.FreePhysicalMemory
        free_virtual_memory_kib = [uint64]$os.FreeVirtualMemory
        total_virtual_memory_kib = [uint64]$os.TotalVirtualMemorySize
    }
    application_events = $events
} | ConvertTo-Json -Depth 6
