$ErrorActionPreference = 'Stop'
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$publicKey = Get-Content (Join-Path $scriptDirectory 'id_ed25519.pub') -Raw

& (Join-Path $scriptDirectory 'bootstrap.ps1') -PublicKey $publicKey.Trim()
Read-Host 'Press Enter to close'
