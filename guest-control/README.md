# Isolated Windows guest control

The conformance lab uses a dedicated SSH key to control the Windows rekordbox
guest. This channel is independent of Evan's SSH agent: the private key is
generated locally under `state/`, is accepted only by this disposable Windows
guest, and is never forwarded.

## Network boundary

The SSH server listens only on the guest's host-only Link Export address,
`172.31.96.96`. Windows Firewall accepts TCP port 22 only from the host-side
macvlan shim, `172.31.96.50`. The shim is parented by the private
`rekordbox-lab` bridge and has a single `/32` route to the guest. The bridge has
one end of a closed carrier-only veth pair as its sole member. The peer has no
master or IP address, has forwarding disabled, and is not attached elsewhere.
The host installs bidirectional drops in the standard `FORWARD` chain before
starting the VM.

A second inbound rule accepts Link Export traffic of any protocol only when its
local address is `172.31.96.96` and its remote address is `172.31.96.50`. The
protocol uses a fixed port-query listener and dynamically assigned service
ports, so a fixed destination-port list cannot represent the real server. The
address pair and host isolation gate provide the restriction instead.

This management channel is reachable from the host itself. It does not create a
route from the guest to the host's LAN or the physical RX3.

## One-time bootstrap

The Windows capability and key-only guest configuration are installed. The
remaining host prerequisite is the corrected isolated-network helper update
documented in `../../rekordbox-windows/README.md`. Do not start a live guest
shell until that helper is installed and the isolation check passes.

Generate the lab key without loading it into an agent:

```sh
./guest-control/guestctl keygen
```

`run-bootstrap.ps1` is a console-friendly wrapper which reads
`id_ed25519.pub` from the same staging directory and keeps the elevated window
open so installation errors remain visible.

Start the isolated VM and pass the public key to an elevated Windows
PowerShell. `bootstrap.ps1` is deliberately self-contained so it can be staged
through the console or copied into the guest while the installation network is
active:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 `
  -PublicKey 'ssh-ed25519 AAAA... rekordbox-link-export-lab'
```

The script installs the built-in `OpenSSH.Server` Windows capability, writes a
minimal key-only server configuration, restricts its listener and firewall
scope, and starts `sshd`. Installing the optional Windows capability can require
Windows Update access. Perform that installation before the guest is moved to
the host-only segment if the capability payload is not already cached.

The service uses delayed automatic start and bounded restart recovery. The
rootless installation network cannot make `172.31.96.96` a valid local bind
address, so the listener is expected to remain stopped there. It becomes valid
only when QEMU is attached to `rekordbox-lab`; verify it after the host
isolation gate passes.

After the isolated network gate passes:

```sh
./guest-control/guestctl wait
./guest-control/guestctl powershell 'Get-Process rekordbox -ErrorAction SilentlyContinue'
./guest-control/guestctl shell
```

`guestctl` always invokes `/usr/bin/ssh` with `-F /dev/null`,
`IdentityAgent=none`, `IdentitiesOnly=yes`, and the dedicated private key. It
never loads host SSH configuration or consults `SSH_AUTH_SOCK`.

PowerShell commands are written to a random host temporary `.ps1`, copied to
the guest's local temporary directory, executed with `-File`, and deleted from
both sides. This avoids Windows command-line length limits and preserves
nonzero status for syntax and runtime errors. Fixture databases use the same
dedicated SCP channel; the isolated VM does not depend on Dockur's `host.lan`
SMB helper.

## Teardown

Disable the guest endpoint from an elevated Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\bootstrap.ps1 -Remove
```

This stops and disables `sshd`, removes both lab firewall rules and the
authorized key, and restores the pre-lab `sshd_config` when a backup exists. It
retains the Windows OpenSSH capability so another run does not need Windows
Update. Delete `guest-control/state/` to destroy the host-side lab key and
learned host key.
