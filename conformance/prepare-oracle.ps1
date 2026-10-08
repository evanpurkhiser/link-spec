param([switch]$Remove)

$ErrorActionPreference = 'Stop'
$groove = Join-Path $env:USERPROFILE 'Music\rekordbox\Sampler\GROOVE CIRCUIT'
$preset = Join-Path $groove 'PRESET'
$original = Join-Path $groove 'PRESET.link-export-original'
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$rights = [System.Security.AccessControl.FileSystemRights]::Write -bor
    [System.Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles
$inheritance = [System.Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
    [System.Security.AccessControl.InheritanceFlags]::ObjectInherit

function Stop-Rekordbox {
    $processes = @(Get-Process rekordbox, rekordboxAgent -ErrorAction SilentlyContinue)
    foreach ($process in $processes) {
        $null = $process.CloseMainWindow()
    }

    if ($processes.Count -eq 0) {
        return
    }

    Start-Sleep -Seconds 7
    Get-Process rekordbox, rekordboxAgent -ErrorAction SilentlyContinue |
        Stop-Process -Force
    Start-Sleep -Seconds 2
}

function Remove-LabDenyRule {
    if (-not (Test-Path $groove)) {
        return
    }

    $acl = Get-Acl $groove
    $rules = @($acl.Access | Where-Object {
        $_.IdentityReference.Value -eq $identity -and
        $_.AccessControlType -eq [System.Security.AccessControl.AccessControlType]::Deny -and
        ($_.FileSystemRights -band $rights) -ne 0
    })
    foreach ($rule in $rules) {
        $acl.RemoveAccessRuleSpecific($rule)
    }
    Set-Acl -Path $groove -AclObject $acl
}

Stop-Rekordbox
Remove-LabDenyRule

if ($Remove) {
    if (-not (Test-Path $original)) {
        throw "Factory preset backup is absent: $original"
    }
    if (Test-Path $preset) {
        $entries = @(Get-ChildItem -LiteralPath $preset -Force)
        if ($entries.Count -ne 0) {
            throw "Refusing to replace non-empty guarded preset: $preset"
        }
        Remove-Item -LiteralPath $preset
    }
    Move-Item -LiteralPath $original -Destination $preset
    Write-Output 'Restored the factory Groove Circuit preset and removed the lab deny rule.'
    exit 0
}

New-Item -ItemType Directory -Force -Path $groove | Out-Null
if (-not (Test-Path $original)) {
    if (-not (Test-Path $preset)) {
        throw "Factory preset is absent; expected it at $preset"
    }
    Move-Item -LiteralPath $preset -Destination $original
}
if (-not (Test-Path $preset)) {
    New-Item -ItemType Directory -Path $preset | Out-Null
}
$entries = @(Get-ChildItem -LiteralPath $preset -Force)
if ($entries.Count -ne 0) {
    throw "Guarded preset must be empty before applying the deny rule: $preset"
}

$acl = Get-Acl $groove
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $identity,
    $rights,
    $inheritance,
    [System.Security.AccessControl.PropagationFlags]::None,
    [System.Security.AccessControl.AccessControlType]::Deny
)
$acl.AddAccessRule($rule) | Out-Null
Set-Acl -Path $groove -AclObject $acl
Write-Output 'Blocked Groove Circuit preset provisioning for deterministic fixtures.'
