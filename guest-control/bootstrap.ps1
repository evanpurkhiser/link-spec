[CmdletBinding(DefaultParameterSetName = 'Install')]
param(
    [Parameter(Mandatory = $true, ParameterSetName = 'Install')]
    [ValidatePattern('^ssh-ed25519 [A-Za-z0-9+/=]+(?: .*)?$')]
    [string]$PublicKey,

    [Parameter(ParameterSetName = 'Remove')]
    [switch]$Remove,

    [string]$ListenAddress = '172.31.96.96',
    [string]$AllowedRemoteAddress = '172.31.96.50'
)

$ErrorActionPreference = 'Stop'
$sshFirewallRule = 'rekordbox-link-export-lab-ssh'
$protocolFirewallRule = 'rekordbox-link-export-lab-protocol'
$sshDirectory = Join-Path $env:ProgramData 'ssh'
$configPath = Join-Path $sshDirectory 'sshd_config'
$backupPath = Join-Path $sshDirectory 'sshd_config.pre-rekordbox-lab'
$authorizedKeysPath = Join-Path $sshDirectory 'administrators_authorized_keys'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script from an elevated PowerShell session.'
}

if ($Remove) {
    Stop-Service sshd -ErrorAction SilentlyContinue
    Set-Service sshd -StartupType Disabled -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -Name $sshFirewallRule -ErrorAction SilentlyContinue
    Remove-NetFirewallRule -Name $protocolFirewallRule -ErrorAction SilentlyContinue
    Remove-Item $authorizedKeysPath -Force -ErrorAction SilentlyContinue

    if (Test-Path $backupPath) {
        Move-Item $backupPath $configPath -Force
    }

    Write-Output 'The isolated guest-control endpoint is disabled.'
    exit 0
}

if (-not (Get-NetIPAddress -IPAddress $ListenAddress -ErrorAction SilentlyContinue)) {
    throw "The isolated guest address $ListenAddress is not installed."
}

$capabilityName = 'OpenSSH.Server~~~~0.0.1.0'
$capability = Get-WindowsCapability -Online -Name $capabilityName
if ($capability.State -ne 'Installed') {
    Add-WindowsCapability -Online -Name $capabilityName | Out-Null
}

New-Item -ItemType Directory -Path $sshDirectory -Force | Out-Null
if ((Test-Path $configPath) -and -not (Test-Path $backupPath)) {
    Copy-Item $configPath $backupPath
}

@"
Port 22
ListenAddress $ListenAddress
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitEmptyPasswords no
AllowUsers Research
Subsystem sftp sftp-server.exe
Match Group administrators
       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
"@ | Set-Content -Path $configPath -Encoding ascii

$PublicKey.Trim() | Set-Content -Path $authorizedKeysPath -Encoding ascii
& icacls.exe $authorizedKeysPath /inheritance:r /grant 'SYSTEM:F' /grant 'Administrators:F' | Out-Null

Remove-NetFirewallRule -Name $sshFirewallRule -ErrorAction SilentlyContinue
New-NetFirewallRule `
    -Name $sshFirewallRule `
    -DisplayName 'rekordbox Link Export lab SSH' `
    -Enabled True `
    -Direction Inbound `
    -Action Allow `
    -Protocol TCP `
    -LocalAddress $ListenAddress `
    -LocalPort 22 `
    -RemoteAddress $AllowedRemoteAddress | Out-Null

Remove-NetFirewallRule -Name $protocolFirewallRule -ErrorAction SilentlyContinue
New-NetFirewallRule `
    -Name $protocolFirewallRule `
    -DisplayName 'rekordbox Link Export lab protocol' `
    -Enabled True `
    -Direction Inbound `
    -Action Allow `
    -Protocol Any `
    -LocalAddress $ListenAddress `
    -RemoteAddress $AllowedRemoteAddress | Out-Null

& sc.exe config sshd start= delayed-auto | Out-Null
& sc.exe failure sshd reset= 0 actions= restart/5000/restart/15000/restart/30000 | Out-Null
& sc.exe failureflag sshd 1 | Out-Null
Restart-Service sshd

Get-NetTCPConnection -State Listen -LocalAddress $ListenAddress -LocalPort 22 |
    Select-Object LocalAddress, LocalPort, State
