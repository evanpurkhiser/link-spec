# Lab cleanup ledger

`data/configuration-behavior-map.json` is a deterministic host-side generated
artifact. It has no guest, network, service, or privilege cleanup. The checksum
ledger is intentionally deferred while the serial real-Rekordbox queue is
writing retained evidence; its finalizer will include this file.

`SQL_LITERAL_INDEX.md` and
`data/static-analysis/sql-literal-index.json` are likewise deterministic
host-side generated artifacts with no external cleanup. Their source-hash set
covers the retained `*.disasm.txt` files and belongs in the same deferred
checksum update.

`CONTROL_AND_MUTATION_REFERENCE.md` and
`data/static-analysis/control-mutation-command-map.json` are deterministic
host-side joins over retained indexes and source references. They add no guest,
network, service, credential, or privilege state and require no cleanup.

This ledger records everything the lab adds outside its two project folders and
which retained artifacts are large or provisional. Cleanup is intentionally a
manual, reviewable operation. Stop the VM before removing network or disk state.

## Routine shutdown

Run as `evan`; these commands use the narrow polkit authorization and do not use
the SSH agent:

```sh
cd /home/evan/workspace/rx3-research/rekordbox-windows
./vmctl stop
./vmctl isolated-stop
./vmctl capture-stop
```

The rootless installation-network path uses a transient user unit rather than
`vmctl`. Stop any active instance with:

```sh
systemctl --user stop 'codex-rekordbox-windows-*.service'
```

The capture stop is needed only while a five-minute capture is active. The VM
also stops after its 12-hour `RuntimeMaxSec`. Windows data remains in
`storage/data.qcow2`.

### Current retained state

At 2026-10-02 21:58 EDT, every transient user recorder and identity unit is
inactive. A global host OOM selected a Chrome/RFB process inside queue
generation `q` at 21:20:46 EDT during the independent repeat of setter-field variant
`out-msec-80000000`; systemd recorded result `oom-kill`, a 520.7 MB peak, and
26 minutes 32 seconds of wall time. The guarded identical-history,
track-compatibility, and malformed-history followers then failed closed because
their required finalization receipts did not exist. They recorded no dependent
oracle data.

Eight setter-field variants have complete repeat receipts, while the partial
summary contains the first seven. The interrupted ninth variant retains
`record-snapshot.json` and the unpromoted candidate
`conformance/goldens/rekordbox-7.2.19/xdj-rx3-status/hot-cue-setter-field-out-msec-80000000.json.next`.
It has no repeat snapshot or receipt and must be resumed or moved under the
experiment's `discovery/` directory; it must not be promoted as canonical
evidence.

The OOM kill prevented the recorder EXIT trap from restoring `play-paths`.
`active-guest-manifest.json` records database SHA-256
`9f0b8c2d4aaa1dfa6549b8f268ce3ee764392682ee1c7524644eed5cd991815e`,
the `hot-cue-bank-mutation-duplicate-slot` fixture, rather than the required
`play-paths` SHA-256
`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`.
Rekordbox remains running in the guest as process 10056. The isolated VM lease
began at 15:15 EDT and remains active; the physical-LAN VM is inactive. Before
any new recorder, stop Rekordbox, resolve the candidate according to the resume
contract, restore `play-paths`, rerun the isolation gate, and use a queue unit
only while the host has adequate available memory. The attempted temporary
`/swapfile` setup did not authenticate and made no host change; this host still
has no swap. Renew the isolated VM lease
before 03:15 EDT on October 3 if capture work continues.

Recovery unit `codex-rekordbox-setter-fields-20261002r.service` began at 22:18
EDT. Its runtime-only `runtime-extension.conf` drop-in sets an eight-hour
ceiling. It resumed the record-side candidate, completed
the independent repeat, and promoted `out-msec-80000000` before advancing.
`conformance/oracle_record.sh` now closes its `rekordbox-windows` browser
session immediately after each noVNC/RFB activation and again on exit. The
browser is not needed while the protocol runner or database snapshot operates;
teardown reduced the live recorder cgroup from roughly 439 MB to 243 MB. Its
focused phase-boundary test requires this cleanup path. Stop unit `r` only to
cancel the mutable-field recovery; its recorder trap attempts to restore
`play-paths`, while a global OOM still requires the explicit post-failure audit
above.

The complete 57-variant extended parser summary, legacy parser matrix,
CDJ-2000nexus matrix, and 15 legacy secondary-column variants remain canonical
and unaffected. Earlier noncanonical attempts remain under their respective
`discovery/` directories as provenance.

The identical-request lifecycle follow-up is declared in
`conformance/data/hot-cue-legacy-identical-request-history.json` and implemented
by `conformance/record_hot_cue_legacy_identical_request_history.sh`. The
recorder performs the full
isolated-VM restart phases, reruns the isolation gate, and restores `play-paths`
through its exit trap. Retain its two-cycle phase/cycle receipts and schema-2
listener/process snapshots under
`data/experiments/hot-cue-bank/legacy-identical-request-history/`. A failed
cycle remains in `cycle-N.next`. The recorder validates every completed phase
and VM-restart receipt before resuming it, quarantines only the incomplete
phase beneath that cycle with an `.interrupted-*` suffix, and rebuilds the
cycle receipt after all declared phases exist. Do not merge unreceipted files
from a prior attempt into a resumed phase.
The generated `dbserver-command-free.disasm.txt` is canonical static evidence
and requires no host cleanup.

The identical-request capture is complete. Generation `x12` recorded cycle 1
and the first five request phases of cycle 2, then encountered a live Windows
database handle while restoring the baseline. The resumable recorder now
validates phase and restart receipts, quarantines only incomplete phase
evidence, and restarts the isolated VM before retrying a baseline restore when
that handle is live. Recovery generation `x13` reused every hash-matched phase,
recaptured only cycle 2's incomplete final canonical phase, and restored
`play-paths`. Its first reduction stopped at an invalid assumption that
Application-event timing belonged to the durable signature. Finalizer `x14`
separates database/restart durability from lifecycle telemetry, validated all
12 observations and four restart receipts, passed 66 tests, wrote
`legacy-identical-request-history/finalization.json`, updated `data/SHA256SUMS`,
and stopped the isolated VM.

Retain both promoted cycle directories, `summary.json`, `finalization.json`,
the reducer, declaration, recorder, and schema-2 health artifacts together.
The top-level `cycle-1.next.interrupted-*` directory and cycle 2's quarantined
`07-after-vm-restart-canonical.interrupted-*` directory are failed-attempt
provenance. They may be removed only after their corresponding promoted cycle
and finalization hashes have been independently archived. There are no guest
assets or active identity units associated with this completed experiment.

Guarded service generation `d` is inactive and produced no lifecycle capture or
finalization receipt. Generations `a`, `b`, and `c` likewise observed failed
queue generations `n`, `o`, and `p` without finalization receipts and exited
without recording. Current generation
`codex-rekordbox-identical-history-20261003x.service` waits behind
generated-payload generation `w`; it has a 72-hour ceiling and records only
after `w` succeeds and the primary queue finalization receipt validates. A
`finalization.json.next` file is an interrupted receipt and may be removed only
after confirming its service is inactive.

Queue generation `m` stopped during the first Hot Cue buffer rejoin arm because
its LINK reactivation used browser-space coordinates and the following port
query timed out. Its trap restored `play-paths` and removed both `.next`
candidates. Queue generation `n`, service
`codex-rekordbox-real-oracle-queue-20261002n.service`, resumed from the
idempotent boundary with direct guest-framebuffer RFB activation and completed
both rejoin observations. The completed summary and any bounded
`*.attempt-*.log` files under
`data/experiments/hot-cue-bank/buffer-disconnect/` are retained provenance.
Generation `n` then completed the authentic CDJ-2000nexus matrix before exiting
with status 126 at the legacy secondary-column stage because its recorder
lacked an executable mode. Generation `a` of the guarded history handoff
consequently failed closed. The recorder mode is fixed, its focused tests pass,
and generation `o` crossed the old failure. Its first live legacy response then
exposed a declaration bug: the 12-field suite still asserted arguments 12 and
15. Generation `o` failed before promoting a candidate, and guarded history
generation `b` failed closed. The generator now drops expectations beyond
argument 11 and tests that invariant for all 15 suites. Queue generation `p`
and guarded history generation `c` are their bounded replacements. Generation
`p` completed and strictly reduced all 15 legacy variants, then promoted the
first setter-field variant. During the second variant's repeat, `cargo run`
noticed concurrent changes in the separate rbxport checkout and attempted a
runtime rebuild that failed before contacting Rekordbox. The valid candidate
golden and record-side logical snapshot are retained for atomic resume.
`oracle_record.sh` now executes the already-built, SHA-256-logged conformance
binary directly, and the field recorder resumes a candidate only when its
matching record snapshot exists. Queue generation `q` and guarded history
generation `d` are the bounded replacements. Stop `q` and `d` during cleanup
if they are active; the collected failed generations require no process
cleanup.

The accepted runner and its Rust test harness are retained inside the lab as
`conformance/pinned/link-export-conformance` and
`conformance/pinned/link-export-conformance-tests`. Their SHA-256 values are
`cefd503a1c44094a113c7ddca47072815b8b57c6f3ee7171d884911678b978b7` and
`35e0dae8d6468e48c71eee78785ccfa73ec070aaaaeb291f4ec208df08694f71`,
respectively. `conformance/pinned/manifest.json` is the machine-readable
acceptance record and notes that the dependency lock is not asserted because
it changed after these artifacts were built. The recorder defaults to the
first artifact and the queue finalizer verifies both files against the
manifest, runs the second directly, then binds all three hashes into its final
receipt. Retain all three files with any oracle generated by this queue;
deleting them removes the executable provenance needed to reproduce final
validation. The downstream 256-pair malformed-history finalizer uses the same
test artifact and binds its executable and manifest hashes into that campaign's
receipt as well.

Every script in the declared real-Rekordbox queue and its guarded handoffs is
checked against runtime `cargo run`, `cargo test`, `cargo build`, and
`target/release` use. The specialized Hot Cue buffer-disconnect recorder also
validates the pinned runner against the manifest before capture.

This timestamped paragraph is an operational snapshot. Obtain authoritative
runtime state before cleanup with:

```sh
systemctl --user show \
  codex-rekordbox-adjacent-malformed-20261003u11.service \
  codex-rekordbox-adjacent-missing-20261003v11.service \
  codex-rekordbox-adjacent-success-20261003w11.service \
  codex-rekordbox-identical-history-20261003x11.service \
  codex-rekordbox-track-compatibility-20261003y11.service \
  codex-rekordbox-location2-malformed-history-20261003z11.service \
  codex-rekordbox-adjacent-success-status-20261003aa11.service \
  codex-rekordbox-adjacent-boundaries-20261003ab11.service \
  codex-rekordbox-adjacent-cues-20261003ac11.service \
  codex-rekordbox-xdj-rr-location9-20261003ad11.service \
  codex-rekordbox-xdj-rr-old-key-20261003ae11.service \
  codex-rekordbox-xdj-xz-corroborating-20261003af12.service \
  codex-rekordbox-adjacent-success-20261003w12.service \
  codex-rekordbox-identical-history-20261003x12.service \
  codex-rekordbox-track-compatibility-20261003y12.service \
  codex-rekordbox-location2-malformed-history-20261003z12.service \
  codex-rekordbox-adjacent-success-status-20261003aa12.service \
  codex-rekordbox-adjacent-boundaries-20261003ab12.service \
  codex-rekordbox-adjacent-cues-20261003ac12.service \
  codex-rekordbox-xdj-rr-location9-20261003ad12.service \
  codex-rekordbox-xdj-rr-old-key-20261003ae12.service \
  codex-rekordbox-xdj-xz-corroborating-20261003af13.service \
  -p ActiveState -p SubState -p Result -p ExecMainStatus
systemctl show rekordbox-windows-isolated.service rekordbox-windows.service \
  -p ActiveState -p SubState -p Result
systemctl --user list-units --type=service --state=running --no-legend | \
  rg 'rekordbox-identity|rekordbox-real-oracle'
find conformance/goldens data/experiments -type f -name '*.next' -print
```

The narrow polkit rule and project-only SSH key cover these VM and guest
operations without sudo prompts or SSH-agent authentication.

Retain `data/experiments/packed-context/play-status-cross/`. Its successful
service journal proves four record/repeat promotions; the launch-permission
failure journal documents the pre-capture executable-bit failure and contains
no Rekordbox result. The suites, four goldens, generator, recorder, summary,
and validator form one provenance set. They require no media files and remain
excluded from backend replay in the current phase.

Retain `data/experiments/packed-context/class2-status-cross/` with its four
suites, four goldens, generator, recorder, validator, and service journal.
They prove the matched-status Delivery/no-builder cross, require no media,
restore `play-paths`, and remain excluded from backend replay.

Retain `data/experiments/packed-context/hot-cue-getter-status-cross/` with its
four suites, four goldens, generator, recorder, validator, and service journal.
They prove direct getter admission and status-50 rejection, require no media,
restore `play-paths`, and remain excluded from backend replay.

Retain `data/experiments/packed-context/hot-cue-catalog-status-cross/` with its
four suites, four goldens, generator, recorder, validator, and service journal.
They prove catalog admission and RX3/CDJ/setup invariance, require no media,
restore `play-paths`, and remain excluded from backend replay.

The `hot-cue-banks`, `hot-cue-bank-cue-fields`, and
`hot-cue-bank-extended-fields` fixtures and their catalog/cue-info goldens are
retained research artifacts, not active guest state. The successful
`hot-cue-bank-mutation-duplicate-slot` fixture, the two single-row negative
fixtures, and `data/experiments/hot-cue-bank/set-extended/` are also retained.
The latter contains the successful live encrypted base/WAL/SHM trio; keep all
three together. The `hot-cue-bank-legacy-mutation` fixture and
`data/experiments/hot-cue-bank/legacy-setter/` are retained for the legacy
ordinal/control evidence; keep that live encrypted base/WAL/SHM trio together
as well. The `hot-cue-bank-legacy-ordinals` fixture, its suite/golden/recorder,
and `data/experiments/hot-cue-bank/legacy-ordinals/` are the complete D/E/F
evidence; keep its live encrypted base/WAL/SHM trio together. The
`hot-cue-bank-legacy-ordinal-boundaries` fixture, suite, golden, recorder, and
`data/experiments/hot-cue-bank/legacy-ordinal-boundaries/` prove the exact
4/5/6 mutation gate and eleven acknowledged no-op controls; retain its live
encrypted base/WAL/SHM trio together. Opening the copied WAL database updates
the SHM file, so the JSON snapshot preserves its pre-open SHM fingerprint.
The `hot-cue-bank-count-boundaries` suite, golden, and recorder reuse the
canonical `hot-cue-banks` fixture and leave no dedicated guest state; retain
them while the positive count behavior is cited. The three
`hot-cue-bank-count-{int32-max,high-bit,uint32-max}` suites and goldens share
that fixture. Retain their before/after process and event-log snapshots under
`data/experiments/hot-cue-bank/count-hazards/`; they prove the signed bit-31
boundary is a healthy empty-menu path rather than a process failure.
The `hot-cue-bank-location-renders` suite, golden, and recorder reuse the same
fixture and restore `play-paths`. Retain the four before/after process and
event-log snapshots under `data/experiments/hot-cue-bank/location-renders/`;
they are the repeat evidence for locations 1/2/3/7, both render widths, and the
two cross-location controls. They leave no dedicated guest database state.
The `hot-cue-bank-location-cross` and `hot-cue-bank-location-state` suites,
goldens, recorders, and health snapshots under the corresponding experiment
directories prove the complete location cross and process-wide stale-buffer
behavior. Retain them together with the deterministic cross generator. Both
recorders restore `play-paths` and leave no dedicated guest database state.
The superseded first-pass copies created while correcting the suite
descriptions are outside the project at
`/tmp/rekordbox-count-boundary-pre-description-fix-1790912649/`. They are not
canonical evidence and may be removed at any time; a reboot also clears them.
Empty `*-wal` files and 32768-byte `*-shm` files beside the
generated and rejected-control database copies are SQLite read-side effects and
may be removed after accepting the JSON snapshots. The superseded combined
extended-field fixture under `/tmp` was removed after its diagnostic JSON was
preserved in `data/experiments/hot-cue-bank/`.

The public status-source audit used shallow working copies under
`/tmp/rekordbox-native-status-audit/`. They are noncanonical scratch data and
may be removed at any time; the pinned revisions, conclusions, retained
firmware-1.43 payload, and validation data all live in this research folder.

Generation `g` retained its pre-health-capture observation under
`/tmp/returned-slots-ffffffff-run-1-label-collision-1790953680/`. It contains
only `observation.json` and its log, has no completion receipt, and is
noncanonical diagnostic evidence. Generation `h` and its canonical lifecycle
summary now record the same transport behavior, so this directory may be
removed at any time.

## Host changes to remove when the lab is retired

The installed files are root-owned copies of sources in `../rekordbox-windows/systemd/`:

```text
/etc/systemd/system/rekordbox-windows.service
/etc/systemd/system/rekordbox-windows-isolated.service
/etc/systemd/system/rekordbox-windows-isolated-network.service
/etc/systemd/system/rekordbox-windows-isolation-check.service
/etc/systemd/system/rekordbox-windows-network.service
/etc/systemd/system/rekordbox-windows-dns.service
/etc/systemd/system/rekordbox-windows-capture.service
/etc/polkit-1/rules.d/49-rekordbox-windows.rules
/usr/local/libexec/rekordbox-windows-prepare-lan
/usr/local/libexec/rekordbox-windows-capture
/usr/local/libexec/rekordbox-windows-prepare-isolated
/usr/local/libexec/rekordbox-windows-check-isolation
```

After stopping the units, removal requires normal administrative approval. Run
`systemctl daemon-reload` after deleting unit files and restart polkit or reboot
after deleting the rule. The Arch packages `polkit` and `duktape` were installed
for this authorization path. Remove them only after checking that no other host
service now depends on them.

## Runtime network state

The preparation unit creates or maintains:

| State | Cleanup action after VM shutdown |
| --- | --- |
| rootful Podman network `rekordbox-lan` | `sudo podman network rm rekordbox-lan` |
| macvlan link `rekordbox-host` | `sudo ip link delete rekordbox-host` |
| route `10.0.0.96/32` through the shim | Removed with the link; verify with `ip route` |
| TCP/UDP DNS rules in `ufw-user-input` | Delete exact rules matching shim/source/port |
| forwarding rule in `ufw-user-forward` | Delete exact rule matching shim/source |
| dnsmasq process | Owned by the DNS unit; disappears on stop |
| loaded `macvtap`/`vhost_net` modules | Leave loaded or unload after confirming no users |

The isolated service additionally creates these disposable objects:

| State | Cleanup action |
| --- | --- |
| bridge `rekordbox-lab` | Removed by `./vmctl isolated-stop` |
| closed carrier pair `rbx-lab-car`/`rbx-lab-peer` | First end is the sole bridge member; peer is unattached and unaddressed; both are removed by the network unit stop path |
| bridge address `172.31.96.1/24` | Removed with the bridge |
| macvlan shim `rbx-lab-host` with `172.31.96.50/32` and MAC `02:00:00:60:00:50` | Removed by the network unit stop path |
| guest-only route `172.31.96.96/32` through `rbx-lab-host` | Removed with the shim |
| rootful Podman network `rekordbox-isolated` | Removed by the network unit stop path |
| two exact `FORWARD` drops matching `-i rekordbox-lab` and `-o rekordbox-lab` | Removed by the network unit stop path |
| Windows address `172.31.96.96/24` | Retain for future runs, or remove with `configure-isolated-network.ps1 -Remove` |
| Windows lab SSH endpoint | Disable with `guest-control/bootstrap.ps1 -Remove` |
| `guest-control/state/` | Delete after disabling the guest endpoint to destroy the dedicated key and learned host key |

The checked-in helper and root-owned installed copy were reconciled on
September 30. A subsequent full service restart recreated the fixed shim MAC,
passed the isolation gate, and restored guest access.

If a failed unit stop leaves state behind, run the checked-in preparation helper
with `down`, then verify exact matching firewall rules before removing them.
Never flush an entire firewall chain.

Use `iptables -S FORWARD`, `iptables -S ufw-user-input`, and
`iptables -S ufw-user-forward` where that UFW chain exists to capture the exact
current rules before deleting them. Delete only exact matching rules; do not
flush an entire chain.

During the 6.18.52 boot, matching signed kernel modules were extracted from
`/var/cache/pacman/pkg/linux-lts-6.18.52-1-x86_64.pkg.tar.zst` into `/tmp` and
loaded. Those temporary extracted files vanish at reboot. The installed 6.18.54
module tree is the normal path after reboot; no persistent module replacement
was made.

## Persistent and large artifacts

Review these before reclaiming space:

| Artifact | Disposition |
| --- | --- |
| `../rekordbox-windows/storage/data.qcow2` | Primary Windows/rekordbox state; retain while experiments continue |
| `../rekordbox-windows/storage/*.iso` | Reinstall media; removable after accepting slower restoration |
| `../rekordbox-windows/windows-container.oci.tar` | Exact pinned container backup; large but makes the folder self-contained |
| `../rekordbox-windows/shared/library/` | Disposable relocated copy; never the source library |
| `data/source-menu-tree.json` and CSVs | Canonical normalized research evidence; retain |
| `data/database/` | Sanitized menu/category/sort/color snapshot; regenerate before deleting |
| `data/static-analysis/` | Generated function evidence for the pinned binary; regenerable text |
| `data/experiments/packed-context/track-types/`, `conformance/suites/context-track-types.json`, its generator/recorder/golden, and validator | Retain together while the exhaustive final-byte result, clean-process repeat, and health claims are cited; the recorder restores `play-paths` and leaves no candidate `.next` database |
| `data/experiments/packed-context/{family-cross,analysis-cross,hot-cue-cross}/`, their three context suites, generators, recorders, goldens, and validators | Retain together while the request-class routing, list-family, Song Info, and Hot Cue Bank cross claims are cited; all recorders restore `play-paths` and leave no `.next` candidate |
| `data/experiments/packed-context/device-setup-cross/`, both context-device-setup suites, their generator/recorder, 16 goldens, and validator | Retain together while ordinary identity/setup invariance is cited; the bounded batch journal is provenance, all goldens are deferred from implementation replay, and the recorder restores `play-paths` |
| `data/experiments/packed-context/display-status-cross/`, the context-display-status suites, generator/recorder, six goldens, and validator | Retain together while requester-keyed AIO ordering is cited; `invalid-recorder.log` documents the excluded status-unaware attempt, the other journals prove status-aware record/repeat runs, all goldens are deferred from implementation replay, and the recorder restores `play-paths` |
| `data/experiments/packed-context/play-status-cross/`, the context-play-status suites, generator/recorder, four goldens, and validator | Retain together while matched RX3/CDJ Play invariance is cited; `launch-permission-failure.log` is a pre-capture failure, `record.log` proves all record/repeat promotions, all goldens are deferred from implementation replay, and the recorder restores `play-paths` |
| `data/experiments/packed-context/class2-status-cross/`, the context-class2-status suites, generator/recorder, four goldens, and validator | Retain together while matched RX3/CDJ Delivery/no-builder invariance is cited; `record.log` proves all 140 record/repeat promotions, all goldens are deferred from implementation replay, and the recorder restores `play-paths` |
| `data/experiments/packed-context/hot-cue-getter-status-cross/`, the context-hot-cue-getter-status suites, generator/recorder, four goldens, and validator | Retain together while the direct status-50 packed-type gate and RX3/CDJ/setup invariance are cited; `record.log` proves all 112 record/repeat promotions, all goldens are deferred from implementation replay, and the recorder restores `play-paths` |
| `data/experiments/packed-context/hot-cue-setter-status-cross/`, the context-hot-cue-setter-status suites, generator/recorder, four goldens, and validator | Retain together while the extended setter type-1 mutation gate, 24 post-rejection database controls, and identity/setup invariance are cited; `record.log` proves all 56 fixture-reset record/repeat promotions, all goldens are deferred, and the recorder restores `play-paths` |
| `data/experiments/packed-context/hot-cue-legacy-setter-status-cross/`, the context-hot-cue-legacy-setter-status suites, generator/recorder, four goldens, and validator | Retain together while the legacy setter type-1 mutation gate, 24 pristine D/E/F controls, and identity/setup invariance are cited; `record.log` proves all 56 fixture-reset record/repeat promotions, all goldens are deferred, and the recorder restores `play-paths` |
| `data/experiments/packed-context/hot-cue-catalog-status-cross/`, the context-hot-cue-catalog-status suites, generator/recorder, four goldens, and validator | Retain together while the catalog type-1 admission gate, root/populated/empty totals, rejected render timeouts, and RX3/CDJ/setup invariance are cited; `record.log` proves all 84 record/repeat promotions, all goldens are deferred, and the recorder restores `play-paths` |
| `data/rekordbox-provisioned-empty-master.db{,-wal,-shm}` | Before/after evidence for factory My Tag provisioning; retain while cited |
| `.venv/` | Local LIEF/Capstone environment; removable and recreatable |
| `conformance/target/` | Cargo build output; remove with `cargo clean` in that directory |
| `conformance/fixtures/generated/` | Disposable encrypted test databases; manifests identify each one |
| `conformance/goldens/` | Oracle results; retain any cited or verified recordings |
| `conformance/fixtures/generated/hot-cue-banks/` and Hot Cue Bank goldens | Retain while `HOT_CUE_BANK_ORACLE.md` cites their exact fingerprints |
| `data/experiments/hot-cue-bank/location-renders/` | Retain with the location-render suite/golden while its process-health and repeat claims are cited |
| `data/experiments/hot-cue-bank/location-{cross,state}/` | Retain with both suites/goldens and the cross generator while location-buffer state is cited |
| `conformance/fixtures/generated/hot-cue-bank-pagination/`, its suite/recorder/golden/validator, and `data/experiments/hot-cue-bank/pagination/` | Retain together while the 70-row page-boundary and normalization rules are cited; `record.log` proves record/repeat promotion, the recorder restores `play-paths`, and backend comparison is deferred |
| `conformance/fixtures/generated/hot-cue-bank-extended-fields/` and `data/experiments/hot-cue-bank/` | Retain while the extended-record layout and inbound-seek crash evidence are cited |
| `conformance/fixtures/generated/hot-cue-bank-mutation*/` | Retain the duplicate-slot fixture as the canonical setter source; retain the two single-row variants while the status-50 controls are cited |
| `data/experiments/hot-cue-bank/set-extended/live-after-master.db{,-wal,-shm}` | Retain together; the base is unchanged and the WAL carries the proven mutation |
| `data/experiments/hot-cue-bank/legacy-setter/live-after-master.db{,-wal,-shm}` | Retain together; the base is unchanged and the WAL carries the proven legacy mutation |
| `data/experiments/hot-cue-bank/legacy-ordinals/live-after-master.db{,-wal,-shm}` | Retain together; the base is unchanged and the WAL carries the D/E/F mutations |
| `conformance/fixtures/generated/hot-cue-bank-deleted-bank-member/`, its suite/golden, and recorder | Retain while the deleted-bank tree/direct predicate split is cited; the recorder restores `play-paths` and leaves no dedicated guest state |
| `data/experiments/song-info-status-location2/` | Repeated RX3-status location-2 state evidence; retain while cited by the Song Info oracle |
| `conformance/results/rbxport/c144f19+tree.80e87ec8aace/` | Canonical current replay, source manifest, actuals, diffs, logs, and summaries; retain while cited |
| `conformance/status-packets/cdj-2000nexus-player-1.hex`, `conformance/runs/cdj-2000nexus-player-1-genuine-status.json`, `conformance/data/cdj-2000nexus-status-matrix.json`, its 13 goldens, and `data/experiments/device-status/cdj-2000nexus/` | Retain together as the exact captured-status provenance and completed 249-case genuine-device matrix; every variant has an independent-repeat receipt and the summary binds all artifacts |
| `conformance/status-packets/cdj-2000nexus-player-3-firmware-1.43.hex`, `PUBLIC_STATUS_SOURCE_AUDIT.md`, and `data/static-analysis/public-status-source-audit.json` | Retain together as the corroborating historical fixture and the audit that records its incomplete capture context; it is not a replay-ready captured-verbatim identity |
| `conformance/results/rbxport/c144f19-dirty/` | Preliminary replay with the wrong Comment secondary-column setting; removable after accepting the canonical Key-configured replay |
| `data/rekordbox-no-player-5min.pcap` | Five-minute negative baseline; retain while the no-player claim matters |
| setup/network screenshots | Keep only screenshots cited by a document |
| `../rekordbox-windows/shared/guest-control/` | Transient bootstrap staging; currently absent |

The rootful Podman tag `localhost/rekordbox-windows-container:6.05` is restored
from the retained OCI archive. Remove the tag with normal administrative
approval only when retiring the VM; the archive remains the authoritative
recovery artifact.

The source database copy under `../rekordbox-windows/shared/library/` and the
rekordbox options file under `/mnt/documents/multimedia/djing/rekordbox/` are
read-only fixture-builder inputs and are never cleanup targets for this lab.
The conformance lab does not read or create track media.

## Documentation cleanup backlog

- Remove screenshots that only document intermediate command entry once their
  claims are recorded in prose and a final-state screenshot exists.
- The `data/windows-guest-*-diagnostic*.png`, `*-direct.png`, and
  `*-current.png` files record the transient SSH/network diagnosis. Retain
  `windows-guest-link-enabled.png` as the final LINK-gate evidence; the other
  Windows diagnostic screenshots are deletion candidates after review.
- Each serial campaign finalizer runs `tools/update_checksums.py` after writing
  its completion receipt. Run it manually after any other retained-artifact
  rename, addition, or deletion. It excludes build output, caches, generated
  fixtures, runtime state, guest credentials, atomic `.next` files, and the
  superseded preliminary replay.
- Record or automate the project-local `.venv` dependency versions before
  deleting it (`lief 0.17.1`, `capstone 5.0.6` at the current snapshot).
- Retain `data/experiments/source-library-count-audit.json` while citing the
  bounded 4,342-database versus 4,356-initial-UI provenance result. The exact
  UI-only source is unrecoverable because the screenshot-time guest WAL was
  not retained.
- Remove the legacy SSH-wrapped manual instructions from the VM README once the
  fixed systemd installation has a scripted installer/uninstaller.

## Conformance fixture cleanup

`conformance/replay_rbxport.py` starts its loopback server as a child process
and terminates it after each fixture, including error paths. A completed run
leaves no service or network interface. If the command is killed forcibly,
check for `rbxport-conformance-server`; terminate only that process. The
`conformance/results/rbxport/<source-fingerprint>/share/` directory is an empty
placeholder because the tested menu requests require no media. It and
`conformance/runtime/rbxport/` are disposable after logs have been reviewed.
The adapter never binds a non-loopback address.

`conformance/activate_fixture.sh` stages guest-local files in
`C:\Users\Research\link-export-conformance`. Remove that guest directory after
restoring the original database. The host activation marker is
`../rekordbox-windows/shared/link-export-conformance/active-guest-manifest.json`;
remove the host staging directory after the run. Canonical generated fixtures
and goldens remain under `conformance/`.

The 17-profile secondary-column oracle batch was closed cleanly on September
30, 2026. The original database was restored through `switch-fixture.ps1`, the
factory Groove Circuit preset and ACL were restored through
`prepare-oracle.ps1 -Remove`, scheduled task `RekordboxOracleLaunch` was
unregistered, and both guest and host `link-export-conformance` staging
directories were removed. No synthetic identity unit remained. `vmctl
isolated-stop` stopped the VM and private network; the VM unit's residual
failed state was reset, and the VM, network, and isolation-check services all
reported `inactive`. Canonical fixtures, 36 goldens, and the 323-case rbxport
replay remain under `conformance/`.

The subsequent category and sort/color sweep restarted the isolated VM and
created 43 more goldens plus an expanded 369-case rbxport replay. That sweep
was also closed cleanly: the original database and factory sampler preset were
restored, the deny rule and scheduled launch task were removed, guest and host
staging directories were removed, and no synthetic identity unit remained.
The isolated VM and network were stopped, the VM unit's residual failed state
was reset, and the VM, network, and isolation-check services all reported
`inactive`. The settings fixtures and goldens are retained research artifacts
rather than cleanup targets.

The boundary, invalid-data, compatibility, History, named-model, and Song Info
batch remains open because the isolated guest will be reused for the remaining
sibling-request and status-backed captures. The deterministic
`play-paths` fixture (`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`)
was restored after the settings-refresh capture, the sampler guard is
installed, scheduled task `RekordboxOracleLaunch` is registered, and the guest
and host staging directories exist. On the latest host audit the isolated VM
service was active, the physical-LAN VM service was inactive, and no synthetic
identity unit existed. Identity emitters are bounded transient services rather
than persistent units.

The same-process settings experiment retains
`data/session-refresh/settings-refresh-master.db{,-wal,-shm}` as synthetic
evidence. The base database is byte-identical to the generated `full` fixture;
the Category and Sort mutations are committed in the paired WAL. The trio,
screenshots, declarations, goldens, lifecycle record, and generated summary are
research artifacts rather than cleanup targets. The disposable guest database
is restored through `activate_fixture.sh` after capture; no settings mutation
needs to remain in the guest.

Before declaring this batch closed:

1. Restore the original database with `guest-control/guestctl powershell` and
   `switch-fixture.ps1 -Restore` through the existing activation helper.
2. Run `prepare-oracle.ps1 -Remove` to restore the sampler preset and ACL.
3. Unregister `RekordboxOracleLaunch` and remove the guest staging directory.
4. Remove `../rekordbox-windows/shared/link-export-conformance/` only after the
   guest restore succeeds.
5. Confirm no `rekordbox-identity-*` user unit remains.
6. Run `../rekordbox-windows/vmctl isolated-stop`, reset only a residual failed
   VM unit if present, and confirm the VM, network, and isolation-check services
   are all `inactive`.

The fixtures, 189 goldens, canonical 2,327-case replay, and documentation are
retained research artifacts and are not cleanup targets.

`record_smart_mytag.sh` restores the `play-paths` fixture from an EXIT trap.
One exploratory invocation exhausted six bounded LINK activation attempts and
produced no partial golden. A subsequent unchanged invocation recorded and
immediately repeated all 49 cases, stopped Rekordbox, and restored
`play-paths`. Failed activation attempts therefore require no manual database
repair; a residual `rekordbox-identity-*` unit remains covered by step 5.

`record_smart_xml.sh` has the same EXIT restoration guarantee. Preserve the
v1 fixture/probe under `data/experiments/smart-xml-matrix/fixture-v1/` and the
v1 JSON recordings: they document why one-condition logic probes were replaced
with mutually exclusive two-condition controls. The v2 exploratory capture,
canonical golden, replay, disassembly, and summary are retained evidence. An
exploratory and a canonical invocation each exhausted bounded LINK activation
retries without writing a partial result; unchanged retries succeeded. The
successful canonical run immediately repeated all 73 cases and restored the
guest to `play-paths` SHA-256
`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`.

`record_smart_serving.sh` retains its 65-case exploratory probe, exact extended
and legacy suites, repeated goldens, replay, and machine summary. The first
exact extended invocation exhausted bounded LINK activation without writing a
partial golden; the unchanged retry and the legacy run succeeded. The EXIT
trap restored the same `play-paths` hash after every invocation. The recorder
accepts an explicit identity path for the retained device-cross follow-up;
each run remains subject to the isolation gate and stops its transient identity.

`record_smart_device_matrix.sh` activates the rule fixture once, starts the UI
once, and records the same two-case suite under all eight ordinary identities.
Its EXIT trap restores `play-paths` even when an identity or LINK activation
fails. Preserve the eight repeated goldens and the machine summary; they are
the evidence that ordinary discovery identity does not alter SmartList rows.

The Play path recorder creates the disposable guest directory
`C:\Users\Research\link-export-conformance\play-paths` with one nonempty
sentinel file, one zero-byte file, and one directory. Removing the broader
guest staging directory in step 3 removes this state; the files contain no
media or library data. The path-specific directory was removed and verified
absent after the canonical repeat; a future recording recreates it.

`conformance/record_display_song_info_batch.sh` stops Rekordbox by reactivating
the fixture before every suite. It records to a `.next` candidate, verifies an
immediate repeat, and promotes only after success. The completed run left no
`.next` files. The first pagination launch and first malformed-suite attempt
failed before golden promotion; their fresh-process retries completed and left
no partial artifact. Later invalid and string-threshold batches encountered
the same LINK/port-query startup race; clean retries likewise left no partial
artifact. The status-model batch recorded to `.next`, verified every four-case
candidate, and promoted all four without leaving partial files.

`conformance/record_song_info_siblings.sh` and
`conformance/record_song_info_sibling_matrix.sh` use the same candidate,
immediate-repeat, and promotion discipline. Their completed runs left no
`.next` or `.actual` files. Ordered malformed-state recordings under
`data/experiments/song-info-sibling-errors/` are retained evidence rather than
cleanup targets. A direct audit must activate its fixture before
`start_oracle_ui.sh`; otherwise an existing headless single-instance process
can cause the scheduled launch to return a null process status. Recording traps
stop every transient identity unit.

The Delivery boundary recorders use a stronger fixture-reset-and-restart repeat
because the first same-process repeat exposed warmed row-order state. The
rejected `.next`/`.actual.json` pair was moved to
`data/experiments/song-info-delivery-boundaries/`; no partial candidate remains
under `conformance/goldens/`. Both encrypted boundary fixtures and their
manifests are retained research artifacts.

`conformance/record_smart_relative_date.sh` stops Windows Time and sets the
guest to `2032-03-31T12:00:00` while measuring operators 6 and 7. Its EXIT trap
restores the current host-local timestamp through the dedicated guest channel,
starts Windows Time, and activates the `play-paths` baseline. An isolated VM
restart does not restore the clock because Windows persists the synthetic time
to its emulated hardware clock. After an interrupted run, execute:

```sh
conformance/guest_clock.sh restore
conformance/activate_fixture.sh conformance/fixtures/generated/play-paths
```

Verify `conformance/guest_clock.sh show` reports `Eastern Standard Time` and a
current timestamp before any non-relative recording. The retained `clock.log`
records the pre-test, controlled, and restored clock states.

Diagnostic screenshots for the LINK/Sync Manager startup race are retained
under `data/experiments/smart-relative-date-matrix/debug/`. The recorder waits
15 seconds for discovery and clicks a point that is blank until the large LINK
control exists. The temporary interactive tasks and copied diagnostic scripts
were removed after capture. If an interrupted diagnostic leaves them behind,
remove them with:

```powershell
Unregister-ScheduledTask -TaskName InspectRekordboxWindows -Confirm:$false
Unregister-ScheduledTask -TaskName CloseRekordboxWindow -Confirm:$false
Remove-Item C:/Users/Research/link-export-conformance/windows.json -Force
Remove-Item C:/Users/Research/link-export-conformance/list-rekordbox-windows.ps1 -Force
Remove-Item C:/Users/Research/link-export-conformance/close-rekordbox-window.ps1 -Force
```

`conformance/record_smart_date_format.sh` activates the date-format fixture and
restores `play-paths` from its EXIT trap. The retained
`data/experiments/ui-debug/link-{before,after}-click.png` pair documents the
LINK startup race: the control is visible in both images, while player number
`1` appears only after successful activation. `link-loop-live.png` preserves
the Mobile Library Sync modal that intercepted the earlier clicks. The
recorder probes the real port-query path after each click and permits six
bounded activation attempts;
only disabled-LINK and port-query-timeout startup failures are retried. It
acknowledges the first-run Mobile Library Sync modal before clicking LINK; the
checkbox and OK coordinates fall on inert track-table cells when the modal is
absent. The diagnostic `rekordbox-ui-debug.service` was stopped. Rekordbox was
closed by
fixture reactivation, and the baseline fixture was restored after the canonical
recording. A future interrupted manual diagnosis should stop that user unit,
reactivate `fixtures/generated/play-paths`, and confirm no `rekordbox-*` user
unit remains.

`conformance/record_smart_text.sh` uses the same bounded LINK activation path,
activates the text fixture, and restores `play-paths` from its EXIT trap. The
canonical 55-case recording and its immediate repeat completed without leaving
a transient user unit or partial golden. Retain the generated fixture, suite,
exploratory probe, canonical golden, replay, disassembly, and machine summary
as research evidence.

`conformance/record_smart_string_property.sh` applies the same cleanup contract
to the 104-case cross-property fixture. Both the exploratory and canonical
runs repeated exactly and restored `play-paths`. Retain the loose probe suite,
probe, exact declaration, repeated golden, replay, and machine summary; they
distinguish observation from promoted expectations.

The thirty-eight Delivery order and lifecycle phase recordings under
`data/experiments/song-info-delivery-order/` are retained evidence. Their
recorders reset and restart Rekordbox before every independent run or
two-phase lifecycle, while each lifecycle deliberately preserves the process
between warm-up and rejoin. They leave only the normal scheduled launch task
plus the active fixture staging state described above. The twelve family
suites contribute 384 experimental case executions
across replaced and persistent connections, the four two-phase identity
lifecycles contribute 56, and the three Delivery-only suites contribute 116.

`conformance/fixtures/generated/empty-pre-default-mytags/` is the preserved
pre-baseline empty fixture that triggered factory My Tag provisioning. It and
`data/rekordbox-provisioned-empty-master.db{,-wal,-shm}` form the before/after
evidence pair. They are cleanup candidates only after the provisioning evidence
and exact 28-row tree are retained elsewhere.

The guest switcher creates these files under
`%APPDATA%\Pioneer\rekordbox`:

| File | Cleanup rule |
| --- | --- |
| `link-export-conformance-original.db` | Restore through `switch-fixture.ps1 -Restore` before deleting |
| `link-export-conformance-active.json` | Removed by the restore path |
| `master.db-wal`, `master.db-shm` | Removed during each stopped-database switch |

Confirm rekordbox opens the original library after restoration. Only then may
`link-export-conformance-original.db` be deleted. A failed or interrupted switch
must be recovered by copying that backup to `master.db` while rekordbox is
stopped and removing the WAL/SHM pair.

The Search Category-matrix recorder leaves the final disabled-Category fixture
active until its trap stops the synthetic identity. After a Search capture,
activate `conformance/fixtures/generated/play-paths/` and relaunch rekordbox so
the guest returns to the lab's ordinary deterministic baseline. Retain the
Search fixture directories, declarations, recordings, goldens, and
`data/experiments/search/summary.json`; they are conformance evidence rather
than cleanup candidates.

The smart-playlist experiment retains its generated fixture, exploratory
recording, canonical golden, post-startup database copy, static disassembly,
and machine summary as evidence. It creates no guest files outside the normal
fixture staging directory. After the canonical repeat, the guest was restored
to `play-paths` SHA-256
`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`
and Rekordbox was relaunched. The copied post-startup database intentionally
remains under `data/experiments/smart-playlists/`; its equality with the source
fixture is part of the rematerialization control.

The smart-rule matrix likewise retains its fixture, 39-case exact suite,
repeated golden, replay, and machine summary. It creates no guest state beyond
the standard fixture staging directory. After both exact recordings, the guest
was restored to the same `play-paths` database hash.

The stored-numeric matrix retains its fixture, 60-case exploratory capture,
exact suite and repeated golden, replay, and machine summary. Its single first
click LINK timeout was handled by the recorder's bounded retry and left no
partial golden. The guest was restored to `play-paths` afterward.

The numeric-boundary matrix retains its encrypted ten-track fixture, 100-case
exploratory recording, promoted exact suite, repeated canonical golden, replay,
and machine summary. The exploratory run reached LINK on its sixth bounded
attempt; the canonical run reached it immediately. The recorder restored
`play-paths` after both runs, so neither requires manual database cleanup.

The filename-boundary fixture, suite, golden, and generated summary are also
retained evidence. They create no files outside the standard guest fixture
staging directory. After recording and repeating all 18 sort cases, the guest
was restored to the same `play-paths` hash and Rekordbox was relaunched.

`edb_streamd.exe` is part of rekordbox's database process set. It can survive
after `rekordbox.exe` and `rekordboxAgent.exe` exit and keep `master.db` locked.
The checked-in switcher stops all three names before replacement or restore;
manual cleanup must do the same.

## Guest sampler guard cleanup

The deterministic oracle preparation preserves the factory Groove Circuit
preset as:

```text
C:\Users\Research\Music\rekordbox\Sampler\GROOVE CIRCUIT\PRESET.link-export-original
```

The active `PRESET` directory is empty and inherits an explicit deny rule for
`Write` and `DeleteSubdirectoriesAndFiles` from its `GROOVE CIRCUIT` parent.
After restoring the original database, remove the guard with:

```sh
guest-control/guestctl powershell \
  '& "C:/Users/Research/link-export-conformance/prepare-oracle.ps1" -Remove'
```

Three retained directories record the failed provisioning experiments and are
cleanup candidates after reviewing the evidence:

```text
PRESET.link-export-regenerated-1
PRESET.link-export-regenerated-2
PRESET.link-export-regenerated-3
```

Each contains a regenerated copy of the same eight factory samples. They are
not used by the conformance lab. Remove them only after the guard has been
removed, and retain `PRESET.link-export-original` until `-Remove` restores it.

The disposable investigation fixture
`conformance/fixtures/generated/full-sampler-tombstone-test/` and the archived
pre-system-playlist fixtures named `*-pre-system-playlist/` may be removed after
their failed hypotheses have been recorded elsewhere. `data/seeded-full-master.db`
and its WAL/SHM companions are retained evidence for the injected-row analysis.

## Key-notation matrix cleanup

The key-notation recorder temporarily replaces only
`%APPDATA%/Pioneer/rekordbox6/rekordbox3.settings` and the standard staged
`master.db`. Its EXIT trap restores the exact retained baseline settings and
reactivates `conformance/fixtures/generated/play-paths/` on success or failure.
The completed run left `ShowOriginalKey=1`, `KeyStringSetting=1`, and active
database SHA-256
`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`.

Transient LINK activation and port-query timeouts occurred during the
Alphanumeric captures. The bounded retry loop succeeded, all four goldens
passed their cold-process repeats, and no candidate or partial golden remains.
Retain the generated fixture, four settings variants, baseline preference
copies, suites, goldens, screenshot, disassembly, summary, and rbxport results;
they are the reproducible evidence. There is no key-notation-specific guest
file or user service left to remove.

The local-device-style recorder additionally replaces
`%APPDATA%/Pioneer/rekordbox6/DEVSETTING.DAT`. Its EXIT trap restores the exact
retained baseline with SHA-256
`68fea233ec9dcc077204687ddc108cbe9f4272e003d789a0534857eaf4c9c85d`
and reactivates the same `play-paths` database on success or failure. The
Classic and Alphanumeric runs plus the ordinary/Smart persisted-BPM controls
all passed cold-process repeats. Retain the baseline/generated device-setting
files, suites, goldens, static extracts, and machine summary as reproducible
evidence. Backend replay is deferred. No Windows PE copy is retained in
`/tmp`; reproduce it from the installed guest only when another static extract
is needed. The isolated VM is inactive after the completed capture, and no
`rekordbox-identity-*` service remains active.

## Link-visibility matrix cleanup

The link-visibility recorder stages only the encrypted `link-visibility`
database through the existing guest fixture switcher. It creates no media
files. Its EXIT trap restores `conformance/fixtures/generated/play-paths/` on
success or failure. The completed canonical run left active database SHA-256
`8f197208a18a301980b039f3b688306b558a0f7667da75096ea6c082cd7591b6`.

The bounded services `rekordbox-link-visibility-20261001a.service`,
`rekordbox-link-visibility-20261001b.service`, and
`rbxport-replay-20261001c.service` completed successfully and are inactive.
Their transient journals may be vacuumed with the rest of the user journal;
they own no persistent working state.

Retain the generated fixture, suite, canonical golden, static disassembly and
xref report, machine summary, and rbxport replay. Also retain
`data/experiments/link-visibility/diagnostic-v1-invalid-smart/`: it records the
initial non-native `title` Smart property and explains why that diagnostic
Smart case is empty. There is no link-visibility-specific guest directory or
host service to remove.

## Windows static-analysis cleanup

The focused Windows audit extracts `rekordbox.exe` from the retained
`../rekordbox-windows/shared/Install_rekordbox_x64_7_2_19.exe` NSIS archive.
Any host executable, temporary 7zip package, `/tmp/rekordbox-7zip/`, and
`.tmp-windows-pe/` directory are disposable after the generated artifacts and
exact executable hash have been verified. The canonical source remains both
the installer member and the installed guest copy.

Retain `tools/analyze_windows_pe.py`,
`tools/generate_windows_device_predicate_audit.py`,
`tools/audit_windows_device_semantics.py`,
`tools/generate_windows_static_manifest.py`, and
`data/static-analysis/windows/`. `windows/manifest.json` binds all 20 retained
extracts to their producer and arguments, all three producer hashes, the
executable identity, and the installer/member identity. Static regeneration does not
start, stop, or otherwise access the isolated VM.

The completed static cross-check removes its temporary extraction directory.
No Windows-static-analysis process or host-side executable copy remains active.

## Hot Cue setter parser cleanup

The extended `UINT32_MAX` lifecycle recorder stages only the fingerprinted
`hot-cue-bank-mutation-duplicate-slot` fixture and restores `play-paths` from
its EXIT trap. Retain the two discovery captures, generated matrix and suites,
three observations per timing/topology cell, reducer, final summary, and the
experiment README together. `summary.partial.json` is disposable after all 60
observations produce `summary.json`. The initial bounded unit was stopped after
15 observations during the documented recorder-interruption recovery. The
resumed service is named
`codex-rekordbox-hot-cue-ffffffff-matrix-20261002b.service`; after it finishes,
confirm that service and every `rekordbox-identity-*` unit are inactive and
that the active guest manifest is the documented `play-paths` SHA-256.
`codex-rekordbox-hot-cue-parser-handoff-20261002b.service` is a bounded waiter:
it polls only the resumed lifecycle unit, requires the strict 60/60 reducer to
succeed, and then executes the resumable extended-parser recorder. Stop this
handoff unit as well if the queued follow-up should be cancelled.

The discovery directory contains canonical `record.json` and `repeat.json`
captures. `original-record-candidate.json` is byte-identical to `record.json`,
and `original-repeat-actual.json` is byte-identical to `repeat.json`; the two
`original-*` aliases are disposable after their hashes are rechecked. Keep the
canonical pair because they preserve the observation that motivated the
lifecycle matrix. The main 57-variant matrix delegates
`declared-length-ffffffff` to the final lifecycle summary and records the other
56 variants as repeat-verified goldens. Its recorder skips existing goldens on
resume rather than replacing them.

`conformance/record_hot_cue_legacy_setter_parser_matrix.sh` stages only the
fingerprinted `hot-cue-bank-legacy-ordinals` database and restores `play-paths`
from its EXIT trap on success or failure. It creates no media. Each completed
probe directory under
`data/experiments/hot-cue-bank/legacy-setter-parser/<variant>/run-{1,2}/`
contains setter output/log, process health, a live database snapshot and
sidecars, plus either a getter output/log or an explicit process-exit skip
record. Retain complete pairs as parser evidence.

`summary.partial.json` and `matrix.partial.csv` are disposable after
`summary.json` and `matrix.csv` validate all 57 repeat pairs. The strict
reducer removes both partial files after complete validation. An interrupted
run directory without `complete.json` is incomplete and must be inspected,
moved to `discovery/`, or removed before resuming that variant; completed run
directories are resume markers. The recorder leaves no golden candidate. Stop
its bounded user service after completion, confirm no `rekordbox-identity-*`
unit remains, verify the active guest database has the documented `play-paths`
SHA-256, and stop the isolated VM when no other recorder needs it.
The bounded queue unit
`codex-rekordbox-hot-cue-legacy-handoff-20261002a.service` waits for the
extended-parser handoff, requires the strict 57-variant extended summary, and
then executes this legacy recorder. Stop it to cancel the queued legacy batch.

The legacy recorder retains an incomplete pre-permissive-getter discovery run
under
`data/experiments/hot-cue-bank/legacy-setter-parser/discovery/actual-cue-length-00000000-run-1-pre-permissive-getter/`.
It contains a setter timeout, responsive-process health capture, and failed
strict-getter log, but no database snapshot or completion receipt. Retain it
only as discovery provenance; the revised two-run variant now closes the same
boundary, so the directory may be removed after its provenance is accepted.
Revised runs accept immediate-getter timeout as evidence and add same-database
restart getter, health, and database captures. Every completed run has a receipt
binding each retained JSON artifact. An interrupted directory without
`complete.json` remains noncanonical and must be inspected before moving or
removing it.

The October 2 queue generation `i` also retains a transport-only discovery log
at
`data/experiments/hot-cue-bank/legacy-setter-parser/discovery/actual-extension-length-00000008-run-1-eagain/setter.log`.
The first port query returned Linux `EAGAIN` before any setter artifact,
health capture, or database snapshot existed. The recorder's EXIT trap stopped
Rekordbox and restored `play-paths`; this log is noncanonical failure
provenance and must never count as experiment evidence. `oracle_record.sh`
classifies that port-query error as a bounded LINK-activation retry for the
resumed queue.

Generation `j` retains a second noncanonical discovery run at
`data/experiments/hot-cue-bank/legacy-setter-parser/discovery/declared-extension-length-00000001-run-1-dbserver-timeout/`.
Its setter, health, and logical database snapshot completed, but the immediate
getter failed while opening the advertised dbserver port and no completion
receipt exists. The cleanup trap restored `play-paths`. Retain the directory
only as failure provenance; generation `k` reruns both cold processes from
fresh fixtures, and `oracle_record.sh` treats this connect timeout as another
bounded LINK-activation retry.

Generation `k` retains the incomplete independent repeat at
`data/experiments/hot-cue-bank/legacy-setter-parser/discovery/declared-extension-length-00000001-run-2-generation-k-dbserver-timeout/`.
The setter timed out, but process health logged the same `ntdll.dll`
heap-corruption event as canonical run 1 and the live database snapshot
is likewise pristine. Ten LINK clicks continued to advertise
the dead dbserver port, proving that this post-setter state is not an activation
race. Generation `l` probes that immediate getter once, binds the failure log
and a second health sample into `getter-skipped.json`, and proceeds through the
same-database restart path. The strict reducer preserves both raw transport
observations and reports whether they are exact transport repeats separately
from their stable crash/restart lifecycle equivalence.

Generation `l` retains the incomplete length-eight run at
`data/experiments/hot-cue-bank/legacy-setter-parser/discovery/declared-extension-length-00000008-run-1-generation-l-port-query-timeout/`.
Its setter, health, and pristine logical database snapshot completed before the
immediate getter's port query timed out. The recorder stopped without a receipt
because only the later dbserver-connect form was then admitted. Generation `m`
records this port-query form separately, captures process/Application health
after the failure, and still rejects Link-disabled, `EAGAIN`, and unrelated
getter errors.

The Hot Cue buffer-disconnect recorder uses transient identity units named
`rekordbox-hot-cue-buffer-*`, stages only the `hot-cue-banks` fixture, and
restores `play-paths` through its EXIT trap. Retain both warmup/post files for
the two control and two rejoin runs under
`data/experiments/hot-cue-bank/buffer-disconnect/`. After completion, confirm
all named identity units are inactive and stop the isolated VM unless the next
real-Rekordbox experiment is already queued.
Each phase is first written as `*.json.next`; the pair is promoted only after
both phases complete. These candidates are removed by the EXIT trap and at the
start of a retry. They are incomplete transport artifacts, not evidence or
cleanup-sensitive captures.
The bounded queue unit
`codex-rekordbox-hot-cue-buffer-handoff-20261002a.service` waits for the legacy
handoff, requires the strict 57-pair legacy summary, and then executes the
buffer-disconnect recorder. Stop it to cancel the queued lifecycle batch.

The genuine CDJ-2000nexus recorder writes unpromoted goldens as `*.json.next`.
It promotes one only after an independent fixture/process repeat and writes a
receipt under `data/experiments/device-status/cdj-2000nexus/repeats/` binding
the variant ID plus suite, fixture manifest, identity, and golden SHA-256
values. A golden without a receipt is re-verified on resume; a candidate is
also resumed through verification. `*.actual.json` files from failed repeat
attempts and orphaned `*.json.next` candidates are disposable after the cause
is recorded or the candidate is successfully re-verified.
The bounded queue unit
`codex-rekordbox-cdj2000nexus-handoff-20261002a.service` waits for the buffer
handoff, requires the strict two-mode buffer summary, and then executes the
native-status recorder. Stop it to cancel the queued device-status batch.

The persisted secondary-column legacy recorder writes unpromoted goldens as
`*.json.next`, promotes them only after a fresh fixture/process repeat, and
writes hash-bound receipts under
`data/experiments/secondary-column-legacy/repeats/`. It restores `play-paths`
through its EXIT trap. A golden without a receipt is re-verified on resume;
orphaned candidates and failed-repeat `*.actual.json` files are disposable
after their failure is understood. All 15 canonical goldens, receipts, and the
strict `summary.json` are persistent evidence; `summary.partial.json` is now
disposable. Consolidated queue generation `p` completed this matrix. The older
dedicated handoff unit is collected and requires no process cleanup.

The BPM tolerance fixture and suite are persistent research artifacts, not
runtime residue. Retain
`conformance/fixtures/generated/bpm-tolerance-boundaries/`,
`conformance/suites/bpm-tolerance-boundaries.json`, and any promoted
`conformance/goldens/rekordbox-7.2.19/xdj-rx3/bpm-tolerance-boundaries.json`
together. During a recording, the unpromoted `.json.next` file is disposable
after a failed record/repeat attempt is understood. The recorder restores the
`play-paths` baseline from its EXIT trap and creates no media files.
The bounded queue unit
`codex-rekordbox-bpm-tolerance-handoff-20261002a.service` waits for the setter
seek handoff, validates its strict summary, and then runs this recorder. Stop it
to cancel the queued BPM batch.

The extended setter mutable-field recorder writes candidates as `*.json.next`
and promotes each only after a second fixture activation and Rekordbox process
start produces an exact normalized match. It stages only
`hot-cue-bank-mutation-duplicate-slot`, restores `play-paths` from its EXIT
trap, and creates no media. Each run copies the encrypted base and optional
WAL/SHM files into a temporary directory, retains only a logical row snapshot
with the source hashes, and removes the temporary database files on function
exit. Orphaned candidates, `receipt.json.next`, and failed-repeat
`*.actual.json` files are disposable after their failure is understood. A
paired candidate plus record snapshot is a resumable atomic state and must not
be removed independently; the next run performs only the fresh repeat before
promotion. `oracle_record.sh` uses the pinned conformance runner directly, so
capture does not rebuild or inspect the separate rbxport checkout. The strict
reducer replaces `summary.partial.json` with `summary.json` after all 56
variants are present. The bounded queue unit
`codex-rekordbox-setter-fields-handoff-20261002a.service` waits for the legacy
secondary-column handoff, requires its strict summary, and then records this
matrix. Stop it to cancel the queued mutable-field batch.

The extended setter seek recorder uses setter-only suites because valid
inbound seek data can terminate Rekordbox in the reply getter. Every variant
has `run-{1,2}` directories containing the setter result/log, process and
Application health, logical database snapshot with source hashes, and a
hash-bound completion receipt. The encrypted base/WAL/SHM copies exist only in
a temporary directory removed when each snapshot function exits. An
interrupted run directory without `complete.json` is incomplete and must be
removed before resuming that run. `summary.partial.json` is disposable after
the strict 17-variant `summary.json` exists. The bounded queue unit
`codex-rekordbox-setter-seek-handoff-20261002a.service` waits for the non-seek
field handoff, requires its strict summary, and records this health matrix.
Stop it to cancel the queued seek batch.

The slot-8 extended-setter lifecycle experiment retains three `run-N`
directories under
`data/experiments/hot-cue-bank/extended-setter-parser/slot-00000008-lifecycle/observations/`.
Each complete run contains the setter/immediate-getter transcript, process and
Application health, a logical database snapshot, the same-database
post-restart getter and health/snapshot, logs, and a hash-bound
`complete.json`. The encrypted base and optional WAL/SHM copies exist only in
temporary directories removed after snapshotting. An interrupted run directory
without `complete.json` must be inspected and removed before that run is
resumed. The checked-in baseline snapshot, matrix, suites, recorder, reducer,
and final `summary.json` are persistent evidence. Unit
`codex-rekordbox-hot-cue-slot8-lifecycle-20261002a.service` failed during its
first restart because the recorder launched a second application instance;
its valid first-half evidence is retained under `discovery/first-lifecycle-attempt/`.
The corrected bounded unit
`codex-rekordbox-hot-cue-slot8-lifecycle-20261002b.service` completed all three
runs. The strict `summary.json` is persistent evidence; any
`summary.partial.json` is disposable. The collected service and transient
guest staging files may be removed after its journal is no longer needed for
provenance.

The returned-slot `UINT32_MAX` lifecycle experiment has the same retention
shape under
`data/experiments/hot-cue-bank/extended-setter-parser/returned-slots-ffffffff-lifecycle/`.
Retain its baseline snapshot, matrix, two suites, recorder, strict reducer,
three receipt-bearing `run-N` directories, and final `summary.json` together.
Each run contains the setter/immediate-getter transcript, health and
Application-event capture, logical database snapshots, same-database restart
getter, logs, and hash-bound receipt. Raw encrypted base/WAL/SHM copies were
temporary and are not retained. `summary.partial.json` is disposable now that
the strict summary exists; an interrupted run directory without
`complete.json` would be noncanonical and require inspection before removal.

`conformance/finalize_real_rekordbox_queue.sh` reruns all ten strict reducers,
the focused Python tests, and the Rust harness tests after the final recorder.
It requires the `play-paths` guest marker and zero active synthetic identity
units, stops the isolated VM only after successful validation, and writes
`data/experiments/real-rekordbox-queue-finalization.json` only after complete
success. A `.next` receipt is disposable if finalization is interrupted.
The bounded queue unit
`codex-rekordbox-real-oracle-finalize-20261002a.service` was stopped before it
executed because it predated the legacy secondary-column stage. The replacement
`codex-rekordbox-real-oracle-finalize-20261002b.service` was stopped before it
executed because it predated the mutable-field stage. Its replacement,
`codex-rekordbox-real-oracle-finalize-20261002c.service`, was likewise stopped
before execution because it predated the seek-descriptor stage. The replacement
`codex-rekordbox-real-oracle-finalize-20261002d.service` was stopped before it
executed because it predated the BPM tolerance stage. The current
`codex-rekordbox-real-oracle-finalize-20261002e.service` and its downstream
handoff chain were stopped after the strict parser recorder exposed the slot-8
lifecycle boundary. The slot-8 summary now validates; replacement units must
begin with the resumable extended parser recorder and preserve the documented
serial ordering.

`conformance/run_remaining_real_rekordbox_queue.sh` is the replacement serial
orchestrator. It validates both completed lifecycle summaries, records each
remaining surface, runs that surface's strict reducer before advancing, and
invokes the finalizer only after the BPM stage validates. The bounded unit
Generation `h` completed the extended-setter matrix, then failed before legacy
recording because the interrupted discovery directory correctly blocked
overwrite. Generation `i` promoted 30 legacy repeat pairs, then ended when a
port query returned Linux `EAGAIN` before the eight-byte extension setter was
sent; its cleanup restored `play-paths`. Generation `j` adds that transport
condition to the bounded LINK-activation retry policy and resumes from the 30
completed pairs. Unit
`codex-rekordbox-real-oracle-queue-20261002j.service` runs this script. Stop
that unit to cancel the queue; the current recorder's cleanup trap restores
the `play-paths` fixture, and completed receipts remain resumable. The unit has
a 24-hour runtime ceiling and is the only active queue service after launch.

The mutable-field recovery ran as bounded unit
`codex-rekordbox-setter-fields-20261003r2.service`. Its guarded successor
`codex-rekordbox-after-setter-fields-20261003s2.service` failed in the strict
reducer after all 56 receipts existed. Generation `r`
stopped after 54 of 56 receipts because SQLCipher returned the deliberately
stored lone-high-surrogate Comment as invalid UTF-8. The response candidate
was complete, but its matching database snapshot was not written, so it was
not promotable. The snapshotter now preserves undecodable TEXT as an explicit
`{"encoding":"invalid-utf8","hex":"..."}` value. The recorder discards a
candidate without its database proof, and likewise discards a proof without
its candidate, before recapturing that variant. Focused tests exercise both
the SQLCipher text factory and the unbound-pair rule.

The reducer failure was confined to the maximum-even-length Comment. Rekordbox
returned an `0x4e02` message declaring a 65,656-byte record, while the raw
probe retains one 8,192-byte socket read and consequently cannot decode the
complete message. The reducer now validates the exact retained envelope,
echoed request, status, declared number/blob lengths, prefix hashes, full
32,766-character logical database value, and repeat only for this variant.
It continues to require decoded messages for the other 55. The repaired
summary validates 56/56 variants and 112 executions. Generations `t2` through
`ae2` failed closed because `s2` produced no queue-finalization receipt.

Generation `r3` waited 45 seconds so its successor could observe it active,
then revalidated all completed receipts without recapturing them and exited
successfully. Generation `s3` accepted the repaired summary and recorded seven
complete seek runs before the noVNC console transiently failed to import
`https://18006.prk.network/app/ui.js` while activating LINK for the eighth.
The recorder restored `play-paths`, but the incomplete run directory prevented
an unambiguous resume. It now preserves an incomplete attempt under a UTC-
timestamped `.interrupted-*` name and retries the entire fixture/process cycle
up to three times. The retained attempt is
`actual-length-00000079/run-2.interrupted-20261003T064738Z`; it did not reach
the setter and is a cleanup candidate after the replacement run validates.

Generation `s4` exposed a Bash failure-mode in the first retry implementation:
calling a function as an `if` condition suppressed `errexit` inside that
function. A console failure could therefore continue to receipt construction,
where absent artifacts produced empty strings. These receipts cannot pass the
strict reducer, but mere `complete.json` existence initially caused the
recorder to skip them. Generation `s4` and its successors were stopped before
any reducer or downstream finalization accepted this state.

The recorder now executes each cold attempt in a background subshell and waits
for its status from the parent, preserving `errexit` within the attempt. Its
preflight validator uses explicit guard returns, requires every artifact to be
nonempty, requires every bound hash to be 64 lowercase hexadecimal digits,
and recomputes all hashes before skipping a run. Invalid receipts are retained
as `.invalid-receipt-<UTC>` directories. Focused unit
`codex-rekordbox-seek-retry-proof-20261003b.service` proved this path against
descriptor length 43: it archived
`run-2.invalid-receipt-20261003T072800Z`, performed a fresh cold capture, and
raised the strict partial summary to 10/17 variants.

Generation `r6` revalidated the completed mutable-field receipts and handed
off to `s6`. Generation `s6` completed the 17-variant seek matrix and seven-
case BPM record/repeat, then exited 126 because
`finalize_real_rekordbox_queue.sh` lacked its executable bit. Its `t6` tail
failed closed because no final receipt existed. The finalizer is now
executable and covered by a mode assertion. Generation `s7` reran all ten
reducers, focused Python tests, and the pinned Rust tests, restored/stopped the
isolated VM, and wrote the hash-bound final receipt without recapturing valid
evidence.

Generation `t7` completed an exact 196-case fileless record/repeat, then its
reducer rejected the runner's format-2 direct-response fixture object because
it still expected the earlier format-1 string. Generation `t8` proved the
repaired reducer and focused tests without recapture, but its cleanliness gate
caught a premature identical-history identity. The history handoff had been
checking the initial queue receipt instead of its immediate generated-payload
predecessor receipt. The stopped premature run retained only
`legacy-identical-request-history/cycle-1.next/`; inspect that directory before
removal. It has since been inspected: it contains only the pre-cycle VM-restart
marker and an incomplete `setter.log`, with no setter JSON, health capture,
database snapshot, or phase receipt, so it is not promotable. The recorder now
renames any such pending cycle to a timestamped `.interrupted-*` directory
before beginning a clean cycle; retain that quarantine until the replacement
cycle validates. The handoff now accepts an explicit receipt and scope and validates
the immediate predecessor. Generation `t9` finalized the existing golden,
asserted all 176 replies and 20 timeouts, stopped the isolated VM, and wrote
the hash-bound fileless finalization receipt.

The first `u9` malformed-payload attempt promoted the complete record/repeat
pair for `kind-2003--no-arguments`, then failed when a guest command consumed
the process-substitution stream that supplied the remaining 95 declarations.
The recorder now materializes that declaration list with `mapfile` before any
guest process starts, and a focused test rejects the streaming-loop form. The
first replacement launch then failed closed because the successful `t9`
predecessor was queryable but had not been observed active by that new process.
The handoff now accepts the exact validated finalization receipt for this
resume case while continuing to require a successful predecessor result when
systemd retains the unit. The rebuilt `u9` skipped the promoted first pair and
continued at `kind-2003--context-only`. Its downstream waiters were stopped
and re-armed front-to-back after the transient failure cascade; none had begun
capture. The failed attempts retain only journal provenance and introduce no
additional candidate artifacts requiring removal.

That rebuilt generation accepted ten complete record/repeat pairs: all six
`0x2003` probes and the first four `0x2103` probes. The record phase for
`kind-2103--string-identifier` then completed, but its independent repeat
ended with runner error `EAGAIN` (`WouldBlock`) before a post-request health
capture or receipt existed. The resumed generation retained the valid record
candidate, moved the partial repeat artifacts to
`repeat.interrupted-20261003T094645Z-attempt-0/`, and ran a new cold repeat.
That repeat matched, wrote the health-bound receipt, and promoted the canonical
golden. The quarantine is retained as interruption provenance and is not part
of the canonical pair. The following `kind-2103--extra-number` pair also
completed, bringing the malformed campaign to twelve accepted receipts before
it advanced to `0x2004`.

The next six `0x2004` preview-wave probes completed as clean exact repeats,
bringing the campaign to eighteen accepted receipts before it advanced to
`0x2104`. Their final health pairs each contain one responsive Rekordbox
process and no Windows Application events. No interrupted `0x2004` artifacts
require cleanup.

All six following `0x2104` legacy-cue probes also completed as exact repeats,
bringing the campaign to 24 accepted receipts before it advanced to `0x2204`.
The first context-only repeat failed during cold setup before a response or
post-health capture. Its sole pre-health file remains at
`kind-2104--context-only/repeat.interrupted-20261003T103031Z-attempt-1/`.
Fresh attempt 2 matched the retained record candidate and produced the
canonical receipt. Retain the interrupted directory as retry provenance or
remove it during final cleanup after preserving this ledger; it is not part of
the canonical health pair.

The six `0x2204` quantize-data probes completed next, bringing the campaign to
30 accepted receipts before it advanced to `0x2304`. One repeat needed the
bounded Link activator through retry 3, then matched its record candidate. It
created no quarantine or partial evidence. All final health pairs contain one
responsive Rekordbox process and no Windows Application events.

The six `0x2304` recognized-log-only probes completed next, bringing the
campaign to 36 accepted receipts before it advanced to `0x2404`. No retry
quarantine or partial evidence was created. All final health pairs contain one
responsive Rekordbox process and no Windows Application events.

The six `0x2404` disc-cue log-only probes completed next, bringing the campaign
to 42 accepted receipts before it advanced to `0x2504`. No retry quarantine or
partial evidence was created. All final health pairs contain one responsive
Rekordbox process and no Windows Application events.

The six `0x2504` VBR-information probes completed next, bringing the campaign
to 48 accepted receipts before it advanced to `0x2604`. No retry quarantine or
partial evidence was created. All final health pairs contain one responsive
Rekordbox process and no Windows Application events.

The six `0x2604` disc-eject log-only probes completed next, bringing the
campaign to 54 accepted receipts before it advanced to `0x2704`. The first
`extra-string` record setup stopped after its pre-request health capture and is
retained at `kind-2604--extra-string/record.interrupted-20261003T125634Z-attempt-1/`.
Fresh attempt 2 produced the canonical record and matching cold repeat. All
six final health pairs contain one responsive Rekordbox process and no Windows
Application events; the interrupted directory is provenance rather than part
of the canonical pair.

The six `0x2704` disc-ID registration-status probes completed next, bringing
the campaign to 60 accepted receipts before it advanced to `0x2804`. The first
32-tag-slot record setup stopped after its pre-request health capture and is
retained at
`kind-2704--thirty-two-tag-slots/record.interrupted-20261003T133020Z-attempt-1/`.
Fresh attempt 2 produced the canonical record and matching cold repeat. All
six final health pairs contain one responsive Rekordbox process and no Windows
Application events; the interrupted directory remains retry provenance.

The six `0x2804` quantize-offset probes completed next, bringing the campaign
to 66 accepted receipts before it advanced to `0x2904`. The first blob-context
record setup stopped after its pre-request health capture and is retained at
`kind-2804--blob-context/record.interrupted-20261003T135208Z-attempt-1/`.
Fresh attempt 2 produced the canonical record and matching cold repeat. All
six final health pairs contain one responsive Rekordbox process and no Windows
Application events; the interrupted directory remains retry provenance.

The six `0x2904` partial-waveform probes completed next, bringing the campaign
to 72 accepted receipts before it advanced to `0x2a04`. The first blob-context
repeat setup stopped after its pre-request health capture and is retained at
`kind-2904--blob-context/repeat.interrupted-20261003T142230Z-attempt-1/`.
Fresh repeat attempt 2 matched the retained record candidate and produced the
canonical receipt. All six final health pairs contain one responsive Rekordbox
process and no Windows Application events; the interrupted directory remains
retry provenance.

The six `0x2a04` segmented-key probes completed next, bringing the campaign to
78 accepted receipts before it advanced to `0x2b04`. The first blob-context
repeat setup stopped after its pre-request health capture and is retained at
`kind-2a04--blob-context/repeat.interrupted-20261003T145057Z-attempt-1/`.
Fresh repeat attempt 2 matched the retained record candidate and produced the
canonical receipt. All six final health pairs contain one responsive Rekordbox
process and no Windows Application events; the interrupted directory remains
retry provenance.

Each phase now has at most three attempts. A failed attempt moves its health
artifacts and any phase-owned candidate into a timestamped
`<phase>.interrupted-*-attempt-<n>/` directory; a repeat failure preserves the
validated record candidate. Only a successful independent repeat may write
the receipt and promote the candidate. The complete `u9` through `ae10` chain
was re-armed front-to-back after the failed generation was collected.

The same stdin-consumption audit found the streaming-loop form in the queued
identical-request history, parser-boundary, cue-payload, XDJ-RR location-9,
and old-Key matrix recorders. All five now materialize their declarations
before invoking guest commands, and the phase-boundary tests cover all six
affected nested recorders. Their
strict reducers now require health schema 2, matching
`capture_rekordbox_health.ps1`; the earlier schema-1 expectations existed only
in synthetic reducer fixtures and would have rejected valid future captures.
The malformed aggregate reducer also revalidates the identity and all four
health hashes per case, requires a clean responsive cold-process start, and
requires normalized record/repeat post-request health equivalence.
The missing-file, generated-success, and status/setup-success reducers now use
the same shared health validator. They also revalidate receipt identities,
suite/fixture/golden hashes, case/service counts, and, for generated assets,
all three guest asset inventories against the declared asset manifest.
The fileless reducer now performs the same receipt and health validation when
run against its canonical evidence. Its sealed summary and finalization hashes
remain unchanged while the downstream queue is active; an in-memory
revalidation accepted the current receipt and the one-responsive-process,
zero-Application-event post-request class.
The queued 256-pair location-2 malformed-history recorder had no process-health
binding before capture. It now writes four schema-2 health documents beneath
`malformed-history-pairs/repeats/<pair>/`, binds them and the authentic RX3
identity in `receipt.json`, and refuses partial promoted evidence. Its reducer
requires a clean responsive start and normalized record/repeat post-request
health equivalence for every pair. No history-pair capture existed when this
layout was introduced, so there is no legacy receipt layout to migrate or
remove.

The waiting `y10` through `ae10` tail was stopped and re-armed after the
compatibility final receipt gained explicit extended/legacy setup-receipt
hashes. No tail recorder had started. Re-arming ensures the eventual receipt
is produced by the same wrapper source retained in the lab rather than the
function body parsed by the earlier waiting Bash process.

The active recovery tail as of 2026-10-03 is `u9 -> v9 -> w9 -> x10 -> y10 ->
z10 -> aa10 -> ab10 -> ac10 -> ad10 -> ae10`. The bounded units are:

```text
codex-rekordbox-adjacent-malformed-20261003u9.service
codex-rekordbox-adjacent-missing-20261003v9.service
codex-rekordbox-adjacent-success-20261003w9.service
codex-rekordbox-identical-history-20261003x10.service
codex-rekordbox-track-compatibility-20261003y10.service
codex-rekordbox-location2-malformed-history-20261003z10.service
codex-rekordbox-adjacent-success-status-20261003aa10.service
codex-rekordbox-adjacent-boundaries-20261003ab10.service
codex-rekordbox-adjacent-cues-20261003ac10.service
codex-rekordbox-xdj-rr-location9-20261003ad10.service
codex-rekordbox-xdj-rr-old-key-20261003ae10.service
```

The `ac10`, `ad10`, and `ae10` invocations started at 05:48 exited at 09:00
after their wait guards observed a predecessor transient unit disappear before
its required finalization receipt existed. None of the three recorders had
started and none created candidate evidence. They were re-armed front to back
after the upstream `u9` through `ab10` chain was verified active. The live
replacement invocation IDs are `626c01dd06b44fef971e430826b59bfa`,
`c75d24bf94764c14a522f8cb438635ef`, and
`d5bc6012e4b040f2854ce7052ec5baff`; their limits remain 216, 240, and 264
hours. All eleven units remained active after a complete 30-second predecessor
poll. Preserve the failed-unit journal entries as handoff provenance; the live
replacement units are the cleanup targets named above.

The first `x3` through `ae3` tail was replaced before capture because its
uniform 168-hour ceiling was shorter than the documented cumulative bounds.
The `x10` through `ae10` replacements use 120, 144, 168, 192, 216, 216, 240,
and 264 hours respectively. The successor ceilings include predecessor wait
time. Cancel from `ae10`
backward through `u9` so no successor observes an intentionally stopped
predecessor as successful. After every recorder is
terminal, require zero `rekordbox-identity-*` units, restore `play-paths`, stop
the isolated VM, remove the generated-success guest directories listed below,
and inspect every `.next` artifact before removal.

The exhaustive compatibility declaration retains
`conformance/fixtures/generated/compatibility-exhaustive/`, its 382-row matrix,
two generated suites, recorder, reducer, and tests. The encrypted fixture and
manifest are persistent reproducibility artifacts. A `.next` golden is an
interrupted candidate and may be resumed only through
`record_track_compatibility_exhaustive.sh`; both canonical goldens and the
strict summary are persistent after promotion. Each setup also retains a
`setups/<setup>/receipt.json` plus four schema-2 health captures. The reducer
binds those files, the backend version, suite, fixture, ordinary RX3 identity,
and golden before comparing all 382 legacy prefixes. It follows the identical-
history recorder in the active serial chain.

The parser-boundary, cue-payload, XDJ-RR location-9, and old-Key reducers use
the same semantic health validator. Their hash-bound captures must begin with
one responsive process and produce the same normalized process/Application-
event class in the record and repeat phases; a matching protocol golden alone
does not promote a variant.

`conformance/run_track_compatibility_after_queue.sh` is its guarded handoff.
Despite its retained filename, it waits for the identical-request-history unit
to become terminal, requires that service's successful result and strict
two-cycle finalization receipt, starts only the isolated VM, waits for
project-key SSH, reruns the isolation gate, records both setup modes, reduces
them, and runs the focused tests. It then requires the `play-paths` marker and
zero identity units before stopping the VM and writing
`data/experiments/track-compatibility-exhaustive/finalization.json`. Stop
bounded generation `codex-rekordbox-track-compatibility-20261003y.service` to
cancel the current handoff. Its 84-hour runtime ceiling includes the complete
predecessor chain.

The focused RX3 sort/secondary-column cross completed successfully in bounded
unit `codex-rekordbox-sort-secondary-render6-20261003af5.service`. Generations
`af`, `af2`, and `af3` were stopped while waiting and produced no capture.
Generation `af4` used the physical RX3 player-11 packed context and timed out
at the response header; retain its before-health capture as the admission
control. Generation `af5` ran standalone with the admitted lab player-1
context, recorded and repeated the 11 visible RX3 track sorts with the exact
six-argument `0x3000` request, restored `play-paths`, stopped all identities,
and stopped the isolated VM. Its finalization receipt binds the 11-case golden,
88-row summary, physical request extraction, and source PCAP.

The malformed-payload generation `u9` was stopped while retrying repeat case
`kind-2b04--blob-context` so the focused experiment could own the VM. Its
completed receipts and partial record/repeat health are resumable evidence,
not cleanup candidates. Waiting successors `v9`, `w9`, `x10`, `y10`, `z10`,
`aa10`, `ab10`, `ac10`, `ad10`, and `ae10` were stopped before VM ownership.

Generations `u11` and `v11` completed the malformed and missing-path matrices.
Generation `w11` completed and promoted its record/repeat capture, then stopped
at a reducer assumption that every valid-asset reply contained a nonempty
blob. Its waiting successors `x11` through `af12` exited without capture.
Generation `w12` resumed the hash-matched capture at reduction, verified the
observed 12 payload-bearing and three empty/scalar replies, checked cleanup,
and wrote the successful finalization receipt.

The continuation chain `z18 -> aa18 -> ab18 -> ac18 -> ad18 -> ae18 -> af18
-> ag18 -> ah18 -> ai18 -> aj18 -> ak18 -> al18 -> am18 -> an18 -> ao18 -> ap18 -> aq18 -> ar18` stopped at `z18`, following the successful terminal compatibility generation
`y15`. Generation `z15` promoted two malformed-history pairs, then stopped
during the third pair when the noVNC client could not fetch `/app/ui.js`. Its
EXIT path restored `play-paths`; replacement `z16` reused both receipts and the
complete record-side candidate. The RFB click now reloads and retries a failed
module fetch three times. Generation `z16` promoted 24 receipt-backed pairs,
then stopped before recording pair 25 when Windows retained a transient sharing
lock on `master.db` after Rekordbox shutdown. Its EXIT path restored
`play-paths`, and it left no partial candidate. `switch-fixture.ps1` now retries
only Windows sharing and lock violations 15 times at two-second intervals;
hash verification and active-manifest publication remain unchanged. Generation
`z18` resumed from those 24 receipts and promoted 47 total pairs before pair 48
returned Delivery totals 13 and 0 across record and repeat. Every successor
failed closed without capture because its predecessor receipt was absent. The
standalone timing recovery is `z19`. The lifecycle-aware `z27` replacement
provides the corrected predecessor boundary. `arm_post_lifecycle_queue.sh`
starts `aa18` through `ar18` as bounded user services only while `z27` is
observably active; it rejects pre-existing successor units and verifies every
new waiter reaches the active state. The first successor consumes the lifecycle
finalization receipt, and every later successor observes its predecessor live
and validates that stage's exact receipt before taking VM ownership.
Retain `data/experiments/post-lifecycle-queue-arming.json`; it binds the
launcher hash, `z27` invocation, all 18 successor invocations, their runtime
ceilings, scripts, and observed active state. Stop the named successor units
together if abandoning the chain before `z27` finalizes. A successor that has
taken VM ownership follows its stage-specific restoration procedure below.
Generation `y13`
failed closed before VM startup because its resume guard required observing
the already-terminal `x14` finalizer while active. Successors `z13` through
`af14` consequently exited without capture. The guarded recovery now accepts
the exact finalization receipt when systemd retains a successful terminal
predecessor, and a focused test pins that condition. Retain the `w11` failure
log with the corrected reducer and `w12` receipt: together they record why real
Rekordbox, rather than the declaration's optimistic description, defines the
baseline payload-bearing split.

Retain the suite, golden, capture receipt, four health files, `summary.json`,
`rows.csv`, source PCAP, decoded physical requests, failed player-11 control,
recorder, reducer, handoff, and finalization receipt together. An
interrupted `sort-secondary-render-6.json.next` or `receipt.json.next` requires
inspection before removal. The recorder's EXIT path restores `play-paths`; if
the handoff is terminated after VM startup, first confirm that no
`rekordbox-identity-*` unit remains, restore `play-paths`, and stop the isolated
VM. The successful standalone unit had an eight-hour ceiling.
A `finalization.json.next` file is an interrupted receipt and is disposable
after the failure is understood.
Set `REKORDBOX_HISTORY_UNIT` when arming a replacement history generation; the
current override names generation `x`.

The location-2 malformed-history declaration retains
`conformance/data/song-info-location2-malformed-history-matrix.json`, all 256
generated suites, generator, recorder, reducer, and declaration tests. Its
recorder stages only the fingerprinted `full` fixture, uses the authentic RX3
player-11 status identity, and restores `play-paths` from its EXIT trap. Each
promoted golden has a matching receipt under
`data/experiments/song-info-status-location2/malformed-history-pairs/repeats/`.
`summary.partial.json` and `matrix.partial.csv` are regenerable progress views;
they include only final golden/receipt pairs and never promote the active
`.next` candidate. The final reducer replaces their role with `summary.json`
and `matrix.csv` after all 256 pairs are complete.
An orphaned `.next` golden or receipt is disposable only after its failed
record/repeat is understood. Keep `summary.json` and `matrix.csv` with the
complete golden/receipt set after strict reduction.

`conformance/run_status_location2_malformed_history_after_compatibility.sh`
waits for the compatibility service and its strict finalization receipt. The
active bounded user unit is
`codex-rekordbox-location2-malformed-history-20261003z18.service`. It has a
120-hour ceiling including predecessor wait time.
Its `REKORDBOX_COMPATIBILITY_UNIT` names compatibility generation `y15`.
After the wait, it records four resumable 64-pair batches and restarts only the
isolated VM between batches, renewing the 12-hour VM lease and rerunning the
isolation gate each time. It reduces all 256 pairs, runs focused Python and
Rust tests, requires `play-paths` plus zero identity units, stops the isolated
VM, and writes
`data/experiments/song-info-status-location2/malformed-history-pairs/finalization.json`.
Its `.next` finalization receipt is disposable after an interrupted closeout.

The fileless adjacent-payload matrix is handed off by bounded unit
`codex-rekordbox-adjacent-payload-20261002t.service`. Stop that unit together
with `codex-rekordbox-after-setter-fields-20261002s.service` and
`codex-rekordbox-setter-fields-20261002r.service` when abandoning the current
serial chain. The handoff waits for generation `s` to finish successfully and
for `data/experiments/real-rekordbox-queue-finalization.json`, starts only the
isolated VM, reruns the isolation gate, and records two cold-process passes.
Its recorder restores the `play-paths` fixture from an EXIT trap. The handoff
requires the baseline marker and zero active identity units before stopping
the VM and writing
`data/experiments/adjacent-payload/fileless/finalization.json`.

Retain the canonical adjacent-payload golden, `receipt.json`, four guest-health
captures, `summary.json`, `matrix.csv`, suite, generator, recorder, reducer,
and finalization receipt together. An interrupted `*.next` golden or receipt
must be inspected before removal because it can identify the request that
ended a Rekordbox process. If the handoff fails before its explicit VM stop,
run `rekordbox-windows/vmctl isolated-stop` after confirming that no recorder
or synthetic identity unit is active. The unit has a 12-hour runtime ceiling,
including its wait for generation `s`.

The malformed adjacent-payload successor is bounded unit
`codex-rekordbox-adjacent-malformed-20261002u.service`. Stop it when cancelling
the payload chain. It waits for generation `t` and its fileless finalization
receipt, then records 96 one-case suites with independent cold-process record
and repeat phases. Each promoted golden has a receipt and four health captures
under `data/experiments/adjacent-payload/malformed/repeats/<case-id>/`.
Incomplete case evidence fails closed: inspect any `.next` golden, health-file
subset, or receipt candidate before removal. Retain all promoted goldens,
per-case evidence, the aggregate `summary.json` and `matrix.csv`, declaration
matrix, suites, generators, recorder, reducer, and finalization receipt. The
same explicit isolated-VM cleanup rule applies after failure. The bounded unit
has a 30-hour ceiling, including its wait for generation `t`.

The missing-file path-state successor is bounded unit
`codex-rekordbox-adjacent-missing-20261002v.service`. Stop it when cancelling
the payload chain. It waits for generation `u` and its malformed-payload
finalization receipt, then records the 31-case `payload-paths` suite twice from
cold Rekordbox processes. Its EXIT trap restores `play-paths`; the guarded
handoff requires the baseline marker and zero synthetic identity units before
stopping the isolated VM. Retain the promoted golden, capture receipt, four
health files, `summary.json`, `matrix.csv`, suite, fixture and manifest,
generator, recorder, reducer, and finalization receipt together. Inspect any
`.next` golden or receipt before removal after a failure. The unit has a
36-hour ceiling, including its wait for generations `t` and `u`.

The completed generated-success capture was recorded by generation `w11` and
finalized by recovery unit
`codex-rekordbox-adjacent-success-20261003w12.service`. Generation `w11`
recorded the 15-case `payload-valid` suite twice from cold Rekordbox processes,
then stopped at the superseded nonempty-payload reducer assumption. Generation
`w12` reused only the hash-matched capture receipt, ran the corrected reducer,
rechecked cleanup inside the isolated VM, and wrote the final receipt. The
recorder creates and owns exactly these two guest directories:

```text
C:\Users\Research\AppData\Roaming\Pioneer\rekordbox\share\PIONEER\Artwork\000\deterministic
C:\Users\Research\AppData\Roaming\Pioneer\rekordbox\share\PIONEER\USBANLZ\000\deterministic
```

It verifies all four guest files against
`conformance/payload-assets/generated/manifest.json` before each pass. Its EXIT
trap restores `play-paths` and removes only those two directories. After an
uncatchable termination, confirm that no recorder or Rekordbox process is using
the files, remove those exact `deterministic` directories through `guestctl`,
reactivate `play-paths`, and stop the isolated VM. Do not remove either parent
`000` directory. Retain the promoted golden, capture receipt, staged/record/
repeat asset inventories, four health files, `summary.json`, `matrix.csv`,
suite, fixture, generated assets and manifest, recorder, reducer, and
finalization receipt together. Inspect any `.next` artifact before removal.
The unit has a 48-hour ceiling, including its waits for generations `t`, `u`,
and `v`.

The successful-payload status/setup cross is declared for bounded unit
`codex-rekordbox-adjacent-success-status-20261003aa18.service`. It waits for
generation `z18` and the complete 256-pair malformed-history finalization
receipt. It then records the same 15 generated-asset successes under genuine
RX3 player-11 status and matched CDJ-3000 player-1 status, each in extended and
legacy setup, for 60 total observations. Each of the four recorder invocations
independently creates, hashes, and removes the two exact guest directories
listed above and restores `play-paths`. The aggregate reducer preserves any
status/setup differences and writes per-case normalized response hashes.

Retain the four suites, four goldens, four capture receipts, twelve guest-asset
inventories, sixteen health files, aggregate `summary.json` and `matrix.csv`,
recorder, reducer, finalization receipt, identities, generated assets, and
fixture manifest together. An interrupted cell follows the same exact-path
guest cleanup and `.next` inspection rules as generation `w`. The guarded
handoff requires the baseline marker, absent deterministic guest directories,
and zero identity units before stopping the VM. Its 144-hour ceiling includes
the complete predecessor chain.

The payload parser-boundary matrix is declared for bounded unit
`codex-rekordbox-adjacent-boundaries-20261003ab18.service`. It waits for
generation `aa18` and its four-variant status/setup finalization receipt. It then
records 30 independently staged profiles and 57 focused requests, each with a
cold record and repeat process. The profiles live under
`conformance/payload-assets/boundaries/<variant>/`; their matching suites live
under `conformance/suites/generated/adjacent-payload-boundaries/`. Each
invocation uses the same two exact guest directories as generation `w`, binds
all four guest files and four health captures into a per-variant receipt,
restores `play-paths`, and removes the directories before advancing.

Retain the asset and declaration indexes, all 30 asset manifests and suites,
30 goldens, 30 capture receipts, 90 guest-asset inventories, 120 health files,
aggregate `summary.json` and `matrix.csv`, generator, recorder, reducer,
handoff, and finalization receipt together. A variant with a receipt is
resumable and skipped; any `.next` golden or receipt requires inspection
before removal. After an uncatchable termination, remove only the two exact
`deterministic` guest directories documented above, reactivate `play-paths`,
stop the isolated VM, and confirm that no `rekordbox-identity-*` unit remains.
The 192-hour ceiling includes the complete predecessor chain.

The successful cue-payload matrix is declared for bounded unit
`codex-rekordbox-adjacent-cues-20261003ac18.service`. It waits for generation
`ab18` and its 30-profile parser-boundary finalization receipt. It activates the
encrypted `adjacent-payload-cues` fixture and records eight resumable variants:
one 63-case safe matrix, three one-case extended seek states, and four
12-case RX3/CDJ status x setup-width crosses. Each variant receives an
independent cold record and repeat process, four health captures, a canonical
golden, and a hash-bound receipt. Its EXIT path restores `play-paths`.

Retain the encrypted fixture and manifest, eight suites, declaration index,
eight goldens, eight capture receipts, 32 health files, aggregate
`summary.json` and `matrix.csv`, generator, recorder, reducer, handoff, and
finalization receipt together. The three one-case seek suites may legitimately
record process exits; their health and transport evidence is canonical and
must be inspected before removing any `.next` file. A receipt-backed variant
is resumable. After an uncatchable termination, reactivate `play-paths`, stop
the isolated VM, and confirm that no `rekordbox-identity-*` unit remains. The
216-hour ceiling includes the complete predecessor chain.

The XDJ-RR source-defined location-9 Delivery matrix is declared for bounded unit
`codex-rekordbox-xdj-rr-location9-20261003ad18.service`. It waits for generation
`ac18` and its cue-payload finalization receipt. Six variants cross the ordinary
XDJ-RX3 envelope, genuine RX3 status, and derived CDJ-3000 status with both
setup widths. Each variant contains six Delivery cases: location-1 and
location-2 controls, a location-9 second-track render, both directions of the
location-1/location-9 stale-buffer cross, and a location-9 first-track render.
The two tracks have distinguishable metadata so the reducer can prove which
location buffer was rendered.

Retain the generated XDJ-RR client-call inventory, six suites, declaration
index, six goldens, six capture receipts, 24 health files, aggregate
`summary.json` and `matrix.csv`, generator, recorder, reducer, handoff, and
finalization receipt together. A receipt-backed variant is resumable. An
interrupted `.next` golden or receipt requires inspection before removal. Its
EXIT path restores `play-paths`; after an uncatchable termination, restore that
fixture, stop the isolated VM, and require zero `rekordbox-identity-*` units.
The 240-hour ceiling includes the complete predecessor chain.

The XDJ-RR old-Key and CueTrack matrix is declared for bounded unit
`codex-rekordbox-xdj-rr-old-key-20261003ae18.service`. It waits for generation
`ad18` and its location-9 finalization receipt. Six variants cross the ordinary
XDJ-RX3 envelope, genuine RX3 status, and derived CDJ-3000 status with both
setup widths. Each variant contains old-Key roots and concrete-key track lists
at locations 1 and 2, two bounded silent CueTrack probes, and a fresh-connection
old-Key health control immediately after each timeout.

Retain the six generated suites, declaration index, six goldens, six capture
receipts, 24 health files, aggregate `summary.json` and `matrix.csv`, generator,
recorder, reducer, handoff, and finalization receipt together. A receipt-backed
variant is resumable. Inspect an interrupted `.next` golden or receipt before
removal. Its EXIT path restores `play-paths`; after an uncatchable termination,
restore that fixture, stop the isolated VM, and require zero
`rekordbox-identity-*` units. The 264-hour ceiling includes the complete
predecessor chain.

The corroborating XDJ-XZ status matrix is declared for bounded unit
`codex-rekordbox-xdj-xz-corroborating-20261003af18.service`. It waits for
generation `ae18` and validates that stage's finalization receipt before
starting the isolated VM. Thirteen variants cover 249 ordinary, Display,
Play, class-2, and Hot Cue catalog/getter cases using the exact analyzed
292-byte XDJ-XZ fixture. Every variant receives an independent fresh-fixture,
cold-process record and repeat, four health captures, a canonical golden, and
a hash-bound receipt. The packet remains classified as a corroborating fixture
because its parent capture is unavailable.

Retain the matrix declaration, analyzed and unanalyzed packet fixtures,
corroborating identity, 13 goldens, 13 receipts, 52 health files, aggregate
`summary.json`, recorder, reducer, handoff, and finalization receipt together.
A receipt-backed variant is resumable. Inspect an interrupted `.next` golden,
receipt, or partial health set before removal. The recorder's EXIT path restores
`play-paths`; after an uncatchable termination, restore that fixture, stop the
isolated VM, and require zero `rekordbox-identity-*` units. The 288-hour ceiling
includes the complete predecessor chain.

The same-process LINK buffer-lifetime matrix is declared for bounded unit
`codex-rekordbox-hot-cue-buffer-link-toggle-20261003ag18.service`. It waits for
corroborating XDJ-XZ generation `af18` and validates that stage's finalization
receipt before starting the isolated VM. Two control and two toggle runs each
use a fresh `hot-cue-banks` fixture and Rekordbox process. The toggle runs keep
the identity and process alive while LINK is deactivated and reactivated, and
retain explicit dbserver-listener plus process/Application health evidence.

Retain the recorder, reducer, handoff, declaration tests, reused warmup/post
suites, four run directories, eight typed response files, four transition
files, 20 health captures, four run receipts, aggregate `summary.json`, and
`finalization.json` together. A run directory containing files without a valid
receipt is incomplete evidence and requires inspection before removal. The
recorder's EXIT path stops its exact `rekordbox-identity-hot-cue-buffer-link-
toggle-*` unit and restores `play-paths`. After an uncatchable termination,
stop only that identity unit, reactivate `play-paths`, stop the isolated VM,
and verify that no `rekordbox-identity-*` unit remains. The 336-hour ceiling
includes the complete predecessor chain.

## Played-state follow-up boundary

The reset-option Link-played transition oracle is assigned to bounded unit
`codex-rekordbox-link-played-state-20261003ah18.service`. It waits for `ag18`
and validates that stage's finalization receipt before starting the isolated
VM. The recorder snapshots the exact guest `rekordbox3.settings` and optional
`AnotherHistories.xml`, installs the deterministic reset-option settings,
removes the played-state file, and records 19 cases in two fresh fixture and
Rekordbox processes. It requires the played-state file to remain absent at
both process shutdowns, then restores both guest files byte-for-byte.

Retain the settings generator and three settings artifacts, suite, golden,
capture receipt, summary, four health files, guest baseline snapshots and
state metadata, option captures, recorder, reducer, handoff, and finalization
receipt together. A partially populated `transition-reset` directory, `.next`
golden, or `.next` receipt is incomplete evidence and requires inspection
before removal. The recorder's EXIT path restores the guest files and
`play-paths`; the handoff also stops the isolated VM on failure. After an
uncatchable termination, stop any `rekordbox-identity-*` unit, reactivate
`play-paths`, restore guest files from `guest-baseline` according to its state
metadata, stop the isolated VM, and preserve the incomplete evidence. The
360-hour ceiling includes the complete predecessor chain.

The played-option persistence/restart cross is assigned to bounded unit
`codex-rekordbox-link-played-persistence-20261003ai18.service`. It waits for
`ah18`, then executes all four ordinary/Link reset-persist combinations twice.
Each run uses a fresh fixture, primes one Link-played ID, proves an accepted
main-window shutdown without force-terminating Rekordbox, snapshots the exact
properties file, and observes the scalar and row-bit channels after starting
a distinct PID against the same database.

Retain both suites, the four-setting manifest and settings files, eight
prime/restart golden pairs, eight run directories, all settings/options,
shutdown, properties-file, and health evidence, per-run and per-variant
receipts, aggregate summary, recorder, reducer, handoff, and finalization
receipt together. An incomplete run directory or `.next` golden/receipt must
be inspected rather than promoted or deleted. The recorder owns restoration
of the exact guest settings and optional properties file; the handoff restores
`play-paths` and stops the isolated VM on failure. The 384-hour ceiling
includes the complete predecessor chain.

The same-process Link-played refresh cross is assigned to bounded unit
`codex-rekordbox-link-played-link-toggle-20261003aj18.service`. It waits for
`ai18`, then runs two uninterrupted controls and two LINK toggle arms with a
fresh fixture and reset settings. Each run retains one responsive Rekordbox PID
across five health checkpoints; toggle arms require port 12523 to disappear
and return before querying both played-state protocol channels.

Retain the reused prime suite, post-boundary suite, four prime/post golden
pairs, four run directories, options, transitions, 20 health files, response
and empty diff artifacts, all receipts, aggregate summary, recorder, reducer,
handoff, and finalization receipt together. Incomplete run directories or
`.next` goldens/receipts require inspection. The recorder restores the exact
guest settings and optional properties file; the handoff restores `play-paths`
and stops the isolated VM on failure. The 408-hour ceiling includes the full
predecessor chain.

The two-player Link-played ownership sequence is assigned to bounded unit
`codex-rekordbox-link-played-multiplayer-20261003ak18.service`. It waits for
`aj18`, then starts simultaneous player-1 and player-2 RX3 identities from
distinct isolated addresses. Four player-correct suites alternate two inserts
and two removals while retaining both state channels before and after every
mutation. Two fresh-fixture runs require exact protocol repetition, one stable
Rekordbox PID, and both stable identity PIDs at five checkpoints.

Retain the generator, declaration index, four suites, player-2 identity, eight
response files, four canonical goldens, live identity manifests, ten identity
checkpoints, ten health files, empty verification diffs, run receipts,
aggregate receipt and summary, recorder, reducer, handoff, and finalization
receipt together. Incomplete run directories or `.next` goldens/receipts
require inspection. The recorder restores exact guest state; the handoff
restores `play-paths` and stops the isolated VM on failure. The 432-hour
ceiling includes the full predecessor chain.

The five-argument active-sort sequence is assigned to bounded unit
`codex-rekordbox-sort-secondary-render-5-20261003al18.service`. It waits for
`ak18` and validates the two-player finalization receipt before starting the
isolated VM. Eleven fresh-connection cases cross every visible RX3 sort with
`0x3000 [context, offset, count, 0, total]`; record and repeat each begin from
the full fixture and a cold Rekordbox process.

Retain the generated suite, canonical golden, four health captures, capture
receipt, `summary.json`, `rows.csv`, recorder, reducer, handoff, and
finalization receipt together. The summary's comparison with the six-argument
golden is descriptive evidence, not a promotion gate. An interrupted
`sort-secondary-render-5.json.next`, `receipt.json.next`, or
`finalization.json.next` requires inspection. The recorder restores
`play-paths`; the handoff restores it and stops the isolated VM on failure.
The 456-hour ceiling includes the full predecessor chain.
Corpus golden totals, result prose, and `data/SHA256SUMS` are reconciled only
after the new evidence has been interpreted; the capture handoff deliberately
does not rewrite them while the serial queue is live.

The seven-argument active-sort sequence is assigned to bounded unit
`codex-rekordbox-sort-secondary-render-7-20261003am18.service`. It waits for
`al18` and validates the five-argument finalization receipt. Thirty-three
fresh-connection cases cross every visible RX3 sort with seventh values zero,
one, and `UINT32_MAX`; record and repeat each begin from the full fixture and a
cold Rekordbox process.

Retain the generated suite, canonical golden, four health captures, capture
receipt, `summary.json`, `rows.csv`, recorder, reducer, handoff, and
finalization receipt together. The summary's comparison with the six-argument
golden tests the static decoder prediction but does not gate promotion on
equality. Inspect interrupted `.next` goldens or receipts before cleanup. The
recorder restores `play-paths`; the handoff restores it and stops the isolated
VM on failure. The 480-hour ceiling includes the full predecessor chain.
Corpus golden totals, result prose, and `data/SHA256SUMS` remain a post-capture
finalization step for the same reason.

The complete valid-header render-arity sweep is assigned to bounded unit
`codex-rekordbox-render-arity-boundaries-20261003an18.service`. It waits for
`am18` and validates the seven-argument finalization receipt. Seventy
fresh-connection cases cover Default at every total argument count 3-32 and
all non-default visible sorts at counts 3, 4, 9, and 32. Each declaration
accepts any terminal outcome so parser rejection and transport behavior remain
authority observations.

Retain the generated suite, canonical golden, four health captures, capture
receipt, `summary.json`, recorder, reducer, handoff, and finalization receipt
together. Inspect interrupted `.next` goldens or receipts before cleanup. The
recorder restores `play-paths`; the handoff restores it and stops the isolated
VM on failure. Corpus totals, interpretation, and `data/SHA256SUMS` remain
post-capture work. The 504-hour ceiling includes the full predecessor chain.

The correctly framed render-underflow sequence is assigned to bounded unit
`codex-rekordbox-render-arity-underflow-20261003ao18.service`. It waits for
`an18` and validates the 3-32 sweep finalization receipt. Three groups each
open a fresh connection, materialize the Default Track list, send a raw-result
`0x3000` with total argument count zero, one, or two on the same connection,
then prove Track service health on another fresh connection. Record and repeat
each begin from the full fixture and a cold Rekordbox process.

Retain the generated suite, hash-pinned parser audit JSON/Markdown/disassembly,
canonical golden, four health captures, capture receipt, `summary.json`,
recorder, reducer, handoff, and finalization receipt together. Inspect
interrupted `.next` goldens or receipts before cleanup. The recorder restores
`play-paths`; the handoff restores it and stops the isolated
VM on failure. Corpus result prose and `data/SHA256SUMS` remain post-capture
work. The 528-hour ceiling includes the full predecessor chain.

The render argument-type matrix is assigned to bounded unit
`codex-rekordbox-render-argument-types-20261003ap18.service`. It waits for
`ao18` and validates the initialized-list arity-underflow finalization receipt.
Sixteen independently resumable probes cross each of the eight ordinary
render positions with string and blob wire types. Every probe uses a fresh
full fixture and cold Rekordbox process for both record and repeat, warms a
valid Default Track list on the same connection, records the unconstrained raw
outcome, and retains before/after process and Application-event health.

Retain the declaration index, 16 generated suites, hash-pinned parser audit
JSON/Markdown/disassembly, 16 canonical goldens, 16 capture receipts, 64
health files, aggregate `summary.json` and `matrix.csv`, recorder, reducer,
handoff, and finalization receipt together. A receipt-backed probe is
resumable. Inspect any `.next` golden or receipt and any partial health set
before removal. The recorder restores `play-paths`; the handoff restores it
and stops the isolated VM on failure. Corpus result prose and
`data/SHA256SUMS` remain post-capture work. The 552-hour ceiling includes the
full predecessor chain.

The render numeric-field matrix is assigned to bounded unit
`codex-rekordbox-render-numeric-fields-20261003aq18.service`. It waits for
`ap18` and validates the argument-type finalization receipt. One 42-case suite
uses fresh connections to cross the low-word first-row character seek, the
statically unread client total, the complete sparse category-map domain, and
high-word aliases. Record and repeat each start from the full fixture and a
cold Rekordbox process; four health captures bind process and Application-event
state.

Retain the generated suite, hash-pinned numeric-field audit
JSON/Markdown/disassembly, canonical golden, capture receipt, four health
files, aggregate `summary.json` and `matrix.csv`, recorder, reducer, handoff,
and finalization receipt together. Inspect interrupted `.next` goldens or
receipts before cleanup. The recorder restores `play-paths`; the handoff
restores it and stops the isolated VM on failure. Corpus result prose and
`data/SHA256SUMS` remain post-capture work. The 576-hour ceiling includes the
full predecessor chain.

The render override-control matrix is assigned to bounded unit
`codex-rekordbox-render-override-controls-20261003ar18.service`. It waits for
`aq18` and validates the numeric-field finalization receipt. One 17-case suite
uses fresh connections to cross five override-gate boundaries and eleven
selector boundaries around an Artist control. The selector cases include zero,
one, the reserved hole, the upper valid and first invalid values, low-byte wrap,
a high-word Artist lookalike, and signed/unsigned 32-bit boundaries. Record and
repeat each start from the full fixture and a cold Rekordbox process; four
health captures bind process and Application-event state.

Retain the generated suite, hash-pinned override-control audit
JSON/Markdown/disassembly, canonical golden, capture receipt, four health
files, aggregate `summary.json` and `matrix.csv`, recorder, reducer, handoff,
and finalization receipt together. Inspect interrupted `.next` goldens or
receipts before cleanup. The recorder restores `play-paths`; the handoff
restores it and stops the isolated VM on failure. Corpus result prose and
`data/SHA256SUMS` remain post-capture work. The 600-hour ceiling includes the
full predecessor chain.

The focused malformed-history timing study is assigned to bounded units whose
generation suffix records each correction.
It preserves the conflicting `.json.next` and `.actual.json` captures for
`play-extra-argument__then__delivery-blob-content`, then records four cold-
process observations at each 0, 50, 100, 250, 500, 1000, and 3000 ms delay
before the final probe connection. It owns the isolated VM directly and has no
failed-chain predecessor dependency.

Retain both original conflict captures, their four health files, all 28 timing
observations, per-observation receipts and health files, `summary.json`,
`observations.csv`, the seven suites, recorder, reducer, handoff, and
finalization receipt together. An incomplete observation is intentionally a
hard stop for inspection. The EXIT path restores `play-paths` and stops the
isolated VM; no successor starts until the result has been interpreted.
Generation `z19` first failed before protocol traffic because its recorder
passed a descriptive label where `oracle_record.sh` accepts only the phase
`record`; the lone before-health file is retained with a `.failed-z19` suffix.
Generation `z20` corrected the phase but inherited generic player-1 precursor
context `0x01010301`; its four completed zero-delay observations are retained
under
`data/experiments/song-info-status-location2/malformed-history-timing-invalid-player1-z20/`
as rejected mismatch evidence. They must not be merged into the timing summary.
Generation `z21` pins device 11 and precursor context `0x0b010301`; both the
focused test and reducer verify all three decoded request contexts. It
completed six receipt-backed observations, then failed during RFB activation
for 50 ms observation three. The partial before-health file is preserved at
`malformed-history-timing/attempts/probe-delay-0050ms-observation-3-rfb-activation-z21/`
with a failure receipt. Its EXIT cleanup restored `play-paths`, removed all
identity units, and stopped the isolated VM.

Generation `z22` resumes the same recorder as bounded unit
`codex-rekordbox-location2-malformed-history-timing-20261003z22.service`,
invocation `2561f163acc848fba5fc931ac1ea0a91`, with a six-hour ceiling. The
recorder verifies and skips the six completed receipts. A manually stopped
transient unit does not reliably run its EXIT cleanup because systemd signals
the complete cgroup. Verify the active guest manifest, restore `play-paths`
with the isolated VM running when necessary, stop the VM, and confirm that no
`rekordbox-identity-*` unit remains.

The player-routed delayed-reply study is gated on the completed timing-study
finalization receipt and is run by
`conformance/run_song_info_delayed_reply_routing.sh`. It records six variants:
the malformed Delivery blob precursor and a valid extra-argument Delivery
control, each crossed with 0, 50, and 100 ms before the replacement
connection. Four cold-process observations per variant retain the replacement
setup exchange, the raw no-send read after setup, a same-connection valid
Delivery probe, and a later fresh-connection health probe.

The first recording generation was bounded unit
`codex-rekordbox-song-info-delayed-reply-routing-20261003z23.service`,
invocation `c710b1ec06214bda93ffaae5d4679cab`, with a three-hour ceiling. It
completed 18 receipt-backed observations, then exhausted ten LINK activation
attempts before the third 50 ms valid-control observation. The lone before-
health file and a failure receipt are retained under
`delayed-reply-routing/attempts/delivery-extra-argument-control--0050ms-observation-3-link-activation-z23/`.
Its EXIT cleanup restored `play-paths`, stopped the isolated VM, and left no
active `rekordbox-identity-*` unit.

Generation `z24` resumed from those 18 verified receipts as bounded unit
`codex-rekordbox-song-info-delayed-reply-routing-20261003z24.service`,
invocation `deb69e77e68f47039656a95d39be7f96`, with a two-hour ceiling. It
completed the remaining six observations, strict reduction, 49 focused tests,
and 13 pinned Rust tests. Finalization verifies baseline restoration, zero
active identity units, and stopped isolated VM. The successful aggregate
contains 24 observation receipts, 48 health files, `summary.json`,
`observations.csv`, and `finalization.json`.

The runner owns the isolated VM after startup. A manual unit stop can bypass
the shell EXIT trap for the complete cgroup; after any forced stop, inspect
partial evidence, restore `play-paths`, stop the isolated VM, and confirm that
no `rekordbox-identity-*` unit remains.

Retain the declaration, six generated suites, 24 canonical captures, all
per-observation receipts and health files, `summary.json`, `observations.csv`,
recorder, reducer, runner, static lifecycle artifact, and finalization receipt
along with both hash-pinned measurement binaries and their manifest. A
receipt-backed observation is resumable. A partial observation is an
intentional hard stop: inspect its capture and health files before removal.
The runner restores `play-paths` and stops the isolated VM on failure after VM
startup. On completion it also verifies that no `rekordbox-identity-*` unit is
active before writing the finalization receipt and updating checksums.

The lifecycle-aware 256-pair rerun uses distinct canonical roots:

```text
conformance/goldens/rekordbox-7.2.19/xdj-rx3-status/song-info-location2-malformed-history-lifecycle/
data/experiments/song-info-status-location2/malformed-history-lifecycle/
```

Each pair retains three setup exchanges and three 1200 ms pre-request drains,
then records and repeats the three declared request outcomes. Keep the earlier
`song-info-location2-malformed-history` goldens, `malformed-history-pairs`
receipts, and pair-48 `.next`/`.actual.json` conflict captures; they are the
provenance that motivated the corrected corpus.

Generation `z25`, invocation `a92fa734e1754b78bf0759b7153b3e16`, promoted
the first two lifecycle-aware pairs. It was frozen immediately after receipt
two and manually stopped solely to replace its insufficient 12-hour runtime
bound. The empty pair-three evidence directory contains no capture or health
file and is safe for the recorder to reuse. No QEMU or identity process
remained after the stop.

Generation `z26` was bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261003z26.service`,
invocation `be9680b0720a414ca02a65a302938c43`, with a 30-hour ceiling. It
promoted receipts three through fifteen, then halted at pair 16 because the
final pre-request drain captured the delayed Delivery reply in record but not
repeat. Its EXIT path restored `play-paths`; the unit was collected, and no VM
or identity unit remained. The record/repeat candidates and available health
captures are retained under
`malformed-history-lifecycle/attempts/immediate-open-orphan-race-20261004T004125Z/`.

Generation `z27` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z27.service`,
invocation `8d86980e160641568d998f3a03a4a2eb`, promoted 55 ordered-pair
receipts before its effective 3.5-hour runtime ceiling terminated it. Suites
containing blob-valued Delivery leave a 3000 ms interval with no matching
client before opening the next connection, then retain the ordinary 1200 ms
drain. Its EXIT
path restored `play-paths`; the interrupted pair had produced only one
pre-request health capture. That file is preserved at
`malformed-history-lifecycle/attempts/runtime-ceiling-20261004T041825Z/` and
was removed from the resumable receipt directory.

Generation `z28` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z28.service`,
invocation `13fffcb667d74723ac33dd782f2731b3`, with an effective 30-hour ceiling.
It resumes from the 55 verified receipts. The 18 serialized successor units
`aa18` through `ar18` were re-armed behind `z28`; their replacement invocation
IDs and the launcher hash are recorded in
`data/experiments/post-lifecycle-queue-arming.json`. The same interruption
cleanup applies: preserve partial `.next` or health evidence, restore
`play-paths`, stop the isolated VM, and verify zero active synthetic identity
units before retrying.

The user-info/DJ-ID authority stage is declared by
`conformance/run_user_info_djid_after_render_controls.sh` and waits for the
render-control finalization before it starts the isolated VM. Its recorder
temporarily owns these guest paths:

```text
C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/djprofile.nxs
C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/djprofile.bin
C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/djprofile.nxs.link-export-oracle-backup
C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/djprofile.bin.link-export-oracle-backup
```

The recorder moves any original files to the two backup paths before staging
self-authored profiles. Its EXIT trap removes staged files, restores the
originals, compares their type, size, and SHA-256 metadata, and restores the
`play-paths` fixture. The finalizer additionally requires both backup paths to
be absent, zero active `rekordbox-identity-*` units, and a stopped isolated VM.

After a forced service stop, start the isolated VM, move each existing backup
path back to its corresponding original path after removing the staged path,
activate `conformance/fixtures/generated/play-paths`, stop the VM, and verify
that no synthetic identity unit remains. Preserve partial profile-state,
health, golden `.next`, and receipt `.next` files until the interruption is
understood; a partial execution is intentionally not auto-resumed.

The bounded waiting unit is
`codex-rekordbox-user-info-djid-20261004as18.service`, invocation
`a9f86ad2900444f9af2c48fea9471b46`, with a 624-hour ceiling. It is a
standalone successor of `ar18`, so it is not part of the 18-stage
`post-lifecycle-queue-arming.json` receipt. Stopping it while it is only
waiting does not affect the VM. Once recording begins, use the forced-stop
recovery procedure above.

The production-shaped streaming-provider-path authority stage is bounded unit
`codex-rekordbox-streaming-provider-paths-20261004at18.service`, invocation
`4d2e3b80ce554e3b8c06c9f838fc464c`, with a 648-hour ceiling. It waits for the
successful `as18` finalization receipt before starting the isolated VM. The
stage activates only the deterministic `streaming-provider-paths` fixture,
records and repeats seven real-Rekordbox cases, restores `play-paths`, stops the
VM, verifies the baseline and zero synthetic identities, then writes
`data/experiments/streaming-provider-paths/finalization.json` before updating
checksums.

Stopping `at18` while it is waiting has no guest side effects. If it is stopped
after recording begins, activate
`conformance/fixtures/generated/play-paths`, stop the isolated VM, and verify
that no `rekordbox-identity-*` unit remains active. Preserve partial golden,
capture receipt, summary, matrix, and finalization `.next` files until the
interruption is understood; the authority results must be regenerated from a
fresh fixture and Rekordbox process before promotion.

The Play Song Info zero-sync-method authority stage is bounded unit
`codex-rekordbox-play-cloud-sync-zero-20261004au18.service`, invocation
`c99ee35964204de48f143007f6b39da0`, with a 672-hour ceiling. It waits for the
successful `at18` finalization receipt before starting the isolated VM. Its
recorder snapshots the guest's exact `rekordbox3.settings`, changes only
`CLSSyncMethod` and `MovedFromCloudDir`, records and repeats ten cases from
fresh `cloud-sync-zero` fixture/process state, restores the original settings
byte-for-byte, restores `play-paths`, and writes a hash-bound capture receipt.
The finalizer reduces the authority rows, runs the focused and pinned gates,
requires zero synthetic identities, and stops the VM before writing
`data/experiments/song-info-cloud-sync-zero/finalization.json`.

Stopping `au18` while it is waiting has no guest side effects. After an
uncatchable termination during recording, copy
`data/experiments/song-info-cloud-sync-zero/guest-baseline-rekordbox3.settings`
back to
`C:/Users/Research/AppData/Roaming/Pioneer/rekordbox6/rekordbox3.settings`,
activate `conformance/fixtures/generated/play-paths`, remove the disposable
guest directories `cloud-sync-zero` and `moved-from-cloud`, stop the isolated
VM, and verify zero `rekordbox-identity-*` units. Preserve all partial golden,
settings snapshots, receipts, summary, and matrix files until the interruption
is understood; resume only from fresh fixture, settings, and process state.

The physical RX3 session-envelope authority stage is bounded unit
`codex-rekordbox-physical-rx3-envelope-20261004av18.service`, invocation
`2fd101c548b544a99767a037c1f3c64e`, with a 696-hour ceiling. It waits for the
successful `au18` finalization receipt before starting the isolated VM. The
stage activates only the deterministic `full` fixture, uses the captured
status-backed player-11 identity, records and repeats the exact physical root
and Default-track envelopes, restores `play-paths`, stops the VM, and requires
zero active synthetic identities before writing
`data/experiments/physical-rx3-session-envelope/finalization.json`.

Stopping `av18` while it is waiting has no guest side effects. If interrupted
after VM startup, preserve the golden `.next`, health captures, receipt,
summary, matrix, and finalization `.next`; activate
`conformance/fixtures/generated/play-paths`, stop the isolated VM, and verify
zero `rekordbox-identity-*` units before a fresh retry. The source PCAP and
`data/experiments/physical-rx3-session/session-envelope.json` are immutable
retained evidence and are never cleanup targets.

`PHYSICAL_RX3_SESSION.md`,
`data/experiments/physical-rx3-session/navigation-transcript.json`, and
`tools/summarize_physical_rx3_navigation.py` are the compact, deterministic
full-session index for that same immutable packet capture. Retain them together
with the source PCAP; they create no guest, network, or host state.

On 2026-10-04, `/tmp` was 81% full (13 GiB used of a 16 GiB tmpfs) and
reproducibility tests received `EDQUOT` while creating ordinary temporary
files. No retained evidence was deleted. The focused tests were rerun with
`TMPDIR` pointed at `conformance/runtime/test-tmp`; that directory was removed
after the successful run. Before another broad campaign, review the existing
owners and retention requirements of large `/tmp` trees and reclaim only
confirmed scratch data. Do not treat the immutable physical PCAP, canonical
goldens, receipts, or active queue state as cleanup targets.

The first malformed-history continuation (`z28`) stopped during LINK UI
activation for pair `play-string-content__then__play-alternate-location` after
88 complete pair receipts. Rekordbox never began that pair's protocol record;
the only partial artifact was its pre-record health snapshot. It is retained as
`record-health-before.failed-link-ui-20261004T124108.json` in the pair evidence
directory and must not be interpreted as a record execution. The recorder's
browser flow now retries the complete noVNC activation up to five times around
its existing per-click retries. Recovery generation `z29` resumes from the 89th
pair after verifying the baseline `play-paths` fixture, zero active synthetic
identities, and the still-isolated VM. Preserve `z28`'s journal and the renamed
snapshot until the 256-pair final receipt is promoted.

Recovery generation `z29` successfully recorded, repeated from a fresh
Rekordbox process, and promoted the previously interrupted
`play-string-content__then__play-alternate-location` pair on 2026-10-04. The
retained `z28` health snapshot remains failure provenance rather than canonical
protocol evidence. Generation `z29` advanced through 98 promoted pair receipts,
then stopped at `play-blob-content__then__play-extra-argument`. The record pass
observed a delayed `0x4000` reply in the second request's pre-request drain;
the fresh-process repeat reached `WouldBlock` there instead. The guarded
comparison retained the candidate `.next`, repeat `.actual.json`, and three
health snapshots without promoting a receipt. Its exit restored the
`play-paths` fixture and stopped Rekordbox; zero synthetic identity units remain
active. The isolated VM remains running for diagnosis or a fresh recovery
generation. Preserve the partial pair directory, both generated protocol
files, and the `z28`/`z29` journals through the 256-pair finalization audit.

Recovery generation `z30` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z30.service`,
invocation `97249e977ea74a29bd42eaa3fdcb7e33`, with a 30-hour ceiling. Before launch,
the partial reducer verified 98 promoted pair receipts, 294 request executions,
and 158 pending pairs, beginning with
`play-blob-content__then__play-extra-argument`. The idle isolated VM was stopped
so the handoff could start it cleanly. Generation `z30` reuses the complete
record-side candidate, performs the repeat from a reset fixture and cold
Rekordbox process, and promotes only exact equality. It exact-repeat promoted
that pair, then exact-repeat promoted
`play-blob-content__then__play-string-context`,
`play-blob-content__then__play-blob-context`, and
`play-blob-content__then__play-string-content`, followed by
`play-blob-content__then__play-blob-content`, bringing the partial authority
to 103 receipts and 309 request executions. It then advanced to pair 104,
`play-blob-content__then__play-zero-context`. Its record pass received delayed
player-routed frame `0x4000 [0x2102, 0]` in the second pre-request drain; the
cold repeat reached `WouldBlock` there. The guarded comparison preserved both
sides under
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-race-pair104-20261004T142450Z/`, retained the complete
record candidate in the canonical `.next` path, restored `play-paths`, stopped
Rekordbox, verified zero active synthetic identities, and stopped the isolated
VM before recovery.

Recovery generation `z31` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z31.service`,
invocation `08b1e7495dc44569ae756ad10f796ed0`, with a 30-hour ceiling. It starts the
isolated VM cleanly, reuses the complete pair-104 record candidate, and performs
only the cold repeat needed for exact comparison before continuing. That
repeat reproduced the retained delayed `0x4000 [0x2102, 0]` frame exactly,
promoted pair 104, and advanced the partial authority to 104 receipts and 312
request executions before beginning
`play-blob-content__then__play-alternate-location`. It independently recorded
and repeated pair 105 exactly, including the delayed Play reply in the second
drain and the normal seven-row alternate-location result, bringing the partial
authority to 105 receipts and 315 request executions before beginning
`play-blob-content__then__delivery-no-arguments`. Its record received delayed
`0x4000 [0x2102, 0]` in the second drain, while the cold repeat received no
frame; both later probes returned the correct 13 rows. The guarded comparison
preserved both sides and three health captures under
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-race-pair106-20261004T145314Z/`. It restored
`play-paths`, stopped Rekordbox, verified zero synthetic identities, and stopped
the isolated VM before exiting.

Recovery generation `z32` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z32.service`,
invocation `6fc141d518ed44819dc82908c0ba690d`, with a 30-hour ceiling. It starts the
isolated VM cleanly, reuses the complete pair-106 record candidate, and performs
the cold repeat required for exact comparison before continuing. The repeat
reproduced delayed `0x4000 [0x2102, 0]` in the second drain exactly, promoted
pair 106, advanced the partial authority to 106 receipts and 318 request
executions, and continued with
`play-blob-content__then__delivery-missing-content`. That pair independently
recorded and repeated the same delayed Play reply in the second drain, followed
by the zero-row missing-content Delivery and normal 13-row health probe. It
promoted pair 107, advanced the partial authority to 107 receipts and 321
request executions, and continued with
`play-blob-content__then__delivery-extra-argument`. Pair 108 independently
repeated the delayed frame, 13-row extra-argument Delivery, and 13-row health
probe exactly. It advanced the partial authority to 108 receipts and 324
request executions, then continued with
`play-blob-content__then__delivery-string-context`. Pair 109 independently
repeated the delayed frame, string-context menu outcome without a total, and
13-row health probe exactly. It advanced the partial authority to 109 receipts
and 327 request executions, then continued with
`play-blob-content__then__delivery-blob-context`. Pair 110 independently
repeated the delayed frame, blob-context menu outcome without a total, and
13-row health probe exactly. It advanced the partial authority to 110 receipts
and 330 request executions, then continued with
`play-blob-content__then__delivery-string-content`. Pair 111's record received
the same delayed frame before a zero-row string-content Delivery, while its
cold repeat timed out in that drain; the subsequent Delivery remained zero and
both health probes returned 13. The guarded comparison did not promote either
side. Both protocol envelopes and three health captures are hash-bound under
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-race-pair111-20261004T152613Z/`. Generation `z32`
restored `play-paths`, stopped Rekordbox, and exited after the mismatch. The
isolated VM was then stopped and zero active `rekordbox-identity-*` units were
verified.

Recovery generation `z33` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z33.service`,
invocation `47a1d6ed66e64530bd96ab6637e1db6c`, with a 30-hour ceiling. It starts the
isolated VM cleanly, reuses the complete pair-111 record candidate, and performs
only the fresh-fixture cold-process repeat required for exact comparison before
continuing. That second independent repeat also timed out in the drain while
returning the same zero-row successor and 13-row health result. It therefore
did not promote the record candidate. Its response and health snapshot were
added to the hash-bound pair-111 attempt bundle, the unpromoted active candidate
and health files were archived there, and the isolated VM was stopped.

Recovery generation `z34` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z34.service`,
invocation `6ae13e30e7cd40089a42588a9cc1324d`, with a 30-hour ceiling. It starts from
an empty pair-111 work slot and requires a wholly fresh record and cold-process
repeat before promotion. Both runs received delayed `0x4000 [0x2102, 0]` in
the second drain, the zero-row string-content Delivery, and the 13-row health
probe exactly. It promoted pair 111, advanced the partial authority to 111
receipts and 333 request executions, and continued with
`play-blob-content__then__delivery-blob-content`. Pair 112 independently repeated
the same delayed Play frame before blob-valued Delivery; after the declared
three-second no-client interval, the health connection drained no Delivery
frame and returned 13 rows. It promoted pair 112, completed all 16 successors
after blob-valued Play, advanced the partial authority to 112 receipts and 336
request executions, and continued with
`play-zero-context__then__play-no-arguments`. Pair 113 independently repeated
two timed-out malformed requests, three timed-out no-send drains, and a 13-row
health Delivery exactly. It promoted that first zero-context-Play successor,
advanced the partial authority to 113 receipts and 339 request executions, and
continued with `play-zero-context__then__play-missing-content`. Pair 114
independently repeated silent drains, a timed-out zero-context precursor, a
zero-row missing-content successor, and 13-row health. It promoted the second
zero-context-Play successor, advanced the partial authority to 114 receipts and
342 request executions, and continued with
`play-zero-context__then__play-extra-argument`. Pair 115 independently repeated
silent drains, a timed-out zero-context precursor, a seven-row extra-argument
successor, and 13-row health. It promoted the third zero-context-Play
successor, advanced the partial authority to 115 receipts and 345 request
executions, and continued with
`play-zero-context__then__play-string-context`. Pair 116 independently repeated
silent drains, a timed-out zero-context precursor, a header-without-total
string-context successor, and 13-row health. It promoted the fourth
zero-context-Play successor, advanced the partial authority to 116 receipts and
348 request executions, and continued with
`play-zero-context__then__play-blob-context`. Pair 117 independently repeated
silent drains, a timed-out zero-context precursor, a header-without-total
blob-context successor, and 13-row health. It promoted the fifth
zero-context-Play successor, advanced the partial authority to 117 receipts and
351 request executions, and continued with
`play-zero-context__then__play-string-content`. Pair 118 independently repeated
silent drains, a timed-out zero-context precursor, a zero-row string-content
successor, and 13-row health. It promoted the sixth zero-context-Play
successor, advanced the partial authority to 118 receipts and 354 request
executions, and continued with
`play-zero-context__then__play-blob-content`. Pair 119 independently repeated
silent first and second drains, then the health connection drained the delayed
`0x4000 [0x2102, 0]` created by the second blob-content Play before returning 13
rows. It promoted the seventh zero-context-Play successor, advanced the partial
authority to 119 receipts and 357 request executions, and continued with
`play-zero-context__then__play-zero-context`. Pair 120 independently repeated
two zero-context timeouts, three silent drains, and 13-row health. It promoted
the eighth zero-context-Play successor, advanced the partial authority to 120
receipts and 360 request executions, and continued with
`play-zero-context__then__play-alternate-location`. If interrupted, preserve `summary.partial.json`,
`matrix.partial.csv`, the candidate, repeat actual, health captures, archived
pair-104, pair-106, and pair-111 attempts, and all recovery journals; restore
`play-paths`, stop the isolated VM, and verify zero active
`rekordbox-identity-*` units before another generation.

Pair 121 independently repeated a timed-out zero-context precursor, a seven-row
alternate-location Play successor, three silent drains, and 13-row health. It
promoted the ninth zero-context-Play successor, advanced the partial authority
to 121 receipts and 363 request executions, and continued with
`play-zero-context__then__delivery-no-arguments`. Preserve its canonical golden,
receipt, and four health captures with the partial summary and matrix.

Pair 122 independently repeated two request timeouts, three silent drains, and
13-row health for zero-context Play followed by argumentless Delivery. It
promoted the tenth zero-context-Play successor, advanced the partial authority
to 122 receipts and 366 request executions, and continued with
`play-zero-context__then__delivery-missing-content`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 123 recovered LINK activation on the seventh bounded record attempt, then
independently repeated a timed-out zero-context precursor, zero-row
missing-content Delivery successor, three silent drains, and 13-row health. It
promoted the eleventh zero-context-Play successor, advanced the partial
authority to 123 receipts and 369 request executions, and continued with
`play-zero-context__then__delivery-extra-argument`. Preserve its canonical
golden, receipt, four health captures, and activation-retry journal with the
partial summary and matrix.

Pairs 210 through 214 independently repeated the blob-context Delivery header
without a total before missing-content Play's zero rows, extra-argument Play's
seven rows, string- and blob-context Play headers without totals, and
string-content Play's zero rows. Every pair had three silent drains and
13-row health. Their canonical golden / receipt SHA-256 pairs are:

- pair 210: `173aa599c5b86df273992ab6396409b68195b5a2744d282d83778b9f47c276b3` / `025561942fe236f46bf2a96acd62c2a44d1d5d993816f800a1e73d816da249fb`
- pair 211: `27c04c085c7fcc09737c183328d7d4a7f2d29c66a969e081a76124f9992fe245` / `01c53dcf1cf73940ad2ad5ad0ba180e85e6e822e75e98f904a0256cff1c16205`
- pair 212: `09474247c73f59ecfb98218da349960edf399898695560ace2775c98f456e645` / `42e78ccf61d8b7eb9214afc422f35d668fa23a0fe1d88c7dd4a5b6fa375235ad`
- pair 213: `c13ca8c8f1de3714389c85ea07b31dfc93ebf8f459813b6b3b0ed4e2568c0fe1` / `b4eca2804de643fa18d8619115555472401abd99a6cb292cda5d957376bcb851`
- pair 214: `1acc51786ad39cfdb0a9100f3469166543284bb705b51f2ebdaab08be63182f2` / `75b55cfc33f4632616213e73819abe38b6ffb9827b2a61f45271faabb558694a`

The reducer advanced partial authority to 214 receipts and 642 request
executions.

Pair 215 did not promote from generation `z40`. Its record run timed out while
the cold repeat drained the delayed `0x4000 [0x2102, 0]` frame from
blob-content Play on the health connection. The precursor response, successor
response, and 13-row health result otherwise matched exactly. Both protocol
observations, the three available health captures, and the complete service
journal are quarantined under
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-race-pair215-20261005T052641Z/`.
Preserve that attempt independently from the wholly fresh generation `z41`
record/repeat.

Recovery generation `z41` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261005z41.service`
(invocation `a6c61eecaae444deb442f9fff896ecb2`) with a finite 30-hour runtime.
Stop it after the lifecycle queue finishes or if it is explicitly abandoned.

Generation `z43` independently recorded and repeated pair 215 with both fresh
processes draining the delayed `0x4000 [0x2102, 0]` frame from blob-content
Play on the health connection before the normal 13-row response. It promoted
with canonical golden SHA-256
`139bc0e74efa5b0240a1fc663e542bffb8c0fe33fc5e28cadc2f388baa225013`
and receipt SHA-256
`b8a75ed9ce9d0984561197e8dbe36cc0c86c11a40264c03edda4ddd9d70d7883`.
The reducer advanced partial authority to 215 receipts and 645 request
executions, with `delivery-blob-context__then__play-zero-context` next.
Preserve the canonical evidence and all three prior race attempts; together
they distinguish the stable delayed-frame payload from nondeterministic
connection admission.

Pair 216 independently repeated the blob-context Delivery header without a
total, zero-context Play timeout, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`0d22526b9c044be12a60bd2d843b91beb0f8e2efd5be901c2707b1388d378eb8`
and receipt SHA-256
`da9d6939e62b8edd77278e1ab9df8bde28bb2db112030f54f5bbd5ded85e6af3`.
The reducer advanced partial authority to 216 receipts and 648 request
executions, with `delivery-blob-context__then__play-alternate-location` next.

Pair 217 independently repeated the blob-context Delivery header without a
total, seven-row alternate-location Play result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`02d1c63e4292d2440cf235e63d1f33b09ce2ef0d0ad794704f3307506a9ee071`
and receipt SHA-256
`82aef5029c19921f2fbda3cc15d68a37f4ca34f0b5a4048bcea35ad67592259c`.
The reducer advanced partial authority to 217 receipts and 651 request
executions, with `delivery-blob-context__then__delivery-no-arguments` next.

Pair 218 independently repeated the blob-context Delivery header without a
total, argumentless Delivery timeout, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`c5dcf50fdbd2489a660e61c64b009e5c81ae495f69fd403c6f132b6158329357`
and receipt SHA-256
`087727fb572ab5ec2c57d834b8262fc470c29d9d40f94d375f16dd4f5c152459`.
The reducer advanced partial authority to 218 receipts and 654 request
executions, with `delivery-blob-context__then__delivery-missing-content` next.

Pair 219 independently repeated the blob-context Delivery header without a
total, zero-row missing-content Delivery result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`abddb2eb6d4f7469570f5784a3fe8f1e8a175fd505699a26175a8223ab9b1ef2`
and receipt SHA-256
`1c1da1b6d6e1c86017d7d9370abf2f6e9ec680af206bf71f157898a771af5f97`.
The reducer advanced partial authority to 219 receipts and 657 request
executions, with `delivery-blob-context__then__delivery-extra-argument` next.

Pair 220 independently repeated the blob-context Delivery header without a
total, 13-row extra-argument Delivery result, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`1d94e19bbef36152159f4fd09c71c880b764963568789db527234186b2e0332e`
and receipt SHA-256
`1a456898b592034687f7531908dab461e54b90b77e493ad081e174b1032c1d8c`.
The reducer advanced partial authority to 220 receipts and 660 request
executions, with `delivery-blob-context__then__delivery-string-context` next.

Pair 221 independently repeated blob-context and string-context Delivery
headers without totals, three silent drains, and 13-row health. It promoted
with canonical golden SHA-256
`d030a657a4789a8d3ff100392b26fe7c90c74a8ba970be8813ec83cf65939f00`
and receipt SHA-256
`82caaafc73461ac7f270c19f443fb4bddd9fc605e957ebcb01017a0922a62db2`.
The reducer advanced partial authority to 221 receipts and 663 request
executions, with `delivery-blob-context__then__delivery-blob-context` next.

Generation `z42` reproduced the same direction as `z41`: its record drained
the delayed frame and its repeat timed out, while every ordinary result and
the 13-row health total matched. Preserve the third quarantined attempt at
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-repeat-timeout-pair215-20261005T135600Z/`.
Generation `z43` performs a fourth wholly fresh record/repeat. The three
failed attempts remain race-distribution evidence rather than authority.

Generation `z43` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261005z43.service`
(invocation `2edb8af02ca3481b92b708c1669ad4f0`) with a finite 30-hour runtime.
Stop it after the lifecycle queue finishes or if it is explicitly abandoned.

Generation `z41` reproduced pair 215's health-connection race in the opposite
direction: its fresh record drained the delayed `0x4000 [0x2102, 0]` frame,
while its cold repeat timed out. The ordinary precursor, successor, and
13-row health results still matched. Preserve the second quarantined attempt
at
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-reverse-race-pair215-20261005T134949Z/`.
Together the `z40` and `z41` attempts directly demonstrate nondeterministic
health-connection admission. Generation `z42` performs a third wholly fresh
record/repeat; neither side of either failed attempt is canonical authority.

Pair 222 independently repeated two blob-context Delivery headers without
totals, three silent drains, and 13-row health. It promoted with canonical
golden SHA-256
`5c56729fa0c70fc6d76c67e9b4f5d0d8e8d647e899750f94a1ef9d21ea2fda9b`
and receipt SHA-256
`7e7ee5995cc64349cb011dcb9a593c05f7fc7d7dd7d5c691adf03c34485dde8f`.
The reducer advanced partial authority to 222 receipts and 666 request
executions, with `delivery-blob-context__then__delivery-string-content` next.

Pair 223 independently repeated the blob-context Delivery header without a
total, zero-row string-content Delivery result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`c1e10b5652dfc8e03b25c876ac72a17e7cb9b83d1dcc68c6779c2f0de51cac13`
and receipt SHA-256
`69dc18b59f4ce43a6c3da14ac15be81648975cc6e6a857d1f46d64e7501431d2`.
The reducer advanced partial authority to 223 receipts and 669 request
executions, with `delivery-blob-context__then__delivery-blob-content` next.

Pair 224 independently repeated blob-context and blob-content Delivery headers
without totals, the declared 3000 ms no-client interval before health, three
silent drains, and 13-row health. It promoted with canonical golden SHA-256
`cbf98149da6d587d47a411f449dd842a6e19ff981a851f1aa19fcd3fcd8812a2`
and receipt SHA-256
`20adb77d99b180d4dbbe777d704803840058531b062b2707b642678004377e73`.
The reducer advanced partial authority to 224 receipts and 672 request
executions, completing the blob-context Delivery row, with
`delivery-string-content__then__play-no-arguments` next.

Pair 225 independently repeated the zero-row string-content Delivery
precursor, argumentless Play timeout, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`b70749ef6995e43aebdcf3bf24f198ef41e01d24741580906895bb316605bbb2`
and receipt SHA-256
`0261c45f25f37474e266701a9bffca3aa61f1c3170c0ae6d6ab7fcf2cf3c0236`.
The reducer advanced partial authority to 225 receipts and 675 request
executions, with `delivery-string-content__then__play-missing-content` next.

Pair 226 independently repeated the zero-row string-content Delivery
precursor, zero-row missing-content Play result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`83e40034f121785a15568d51f68211ce2fbdb88cb95cb7b7829e90712f41cbae`
and receipt SHA-256
`034a4662969515ed6e1390a0ba189431c7233ac78cfc2958c4b815848e8e7153`.
The reducer advanced partial authority to 226 receipts and 678 request
executions, with `delivery-string-content__then__play-extra-argument` next.

Pair 227 independently repeated the zero-row string-content Delivery
precursor, seven-row extra-argument Play result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`4eac281d901f32bc09234864d89cefcbf60852b950b96bf1d4e34449d1c76177`
and receipt SHA-256
`f185dd94f003dde13ad3e0ba4a6a2584236afdc2ad950efbefccc14ff8e94258`.
The reducer advanced partial authority to 227 receipts and 681 request
executions, with `delivery-string-content__then__play-string-context` next.

Pair 228 independently repeated the zero-row string-content Delivery
precursor, header-only string-context Play result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`48d25eeab2ecccca5a1b976ad523bbb433e320a232ffe7d03b04e19add9f98ba`
and receipt SHA-256
`e4f681779317f9b18f915e92a60e87903734ae330d32519d72a6bfb456a8a5ca`.
The reducer advanced partial authority to 228 receipts and 684 request
executions, with `delivery-string-content__then__play-blob-context` next.

Generation `z42` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261005z42.service`
(invocation `f4c8dd816c3246a0ba54f0007f01306d`) with a finite 30-hour runtime.
Stop it after the lifecycle queue finishes or if it is explicitly abandoned.

Pair 209 independently repeated the blob-context Delivery header without a
total, argumentless Play timeout, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`e4407179223b46d7b21bdb43e069d164c14000a7fb0547521bf76dbafc604a54`
and receipt SHA-256
`efb839e5cec1f7d0bf1f33b2462aabaa5f65f331d7672cfb249cded4c6a4b6a2`.
The reducer advanced partial authority to 209 receipts and 627 request
executions, with `delivery-blob-context__then__play-missing-content` next.
Preserve its canonical golden, receipt, four health captures, and the updated
partial summary and matrix.

Pair 206 independently repeated string-context and blob-context Delivery
headers without totals, three silent drains, and 13-row health. It promoted
with canonical golden SHA-256
`d1803c692153bf2a921b2819d339599447862b106de1929fa3116430139ec033`
and receipt SHA-256
`bec923db667d31f16585b56ffed393ba5d9a26917931d25d1f0a96f98c9fffa9`.
The reducer advanced partial authority to 206 receipts and 618 request
executions, with `delivery-string-context__then__delivery-string-content`
next. Preserve its canonical golden, receipt, four health captures, and the
updated partial summary and matrix.

Pair 208 independently repeated the string-context and blob-content Delivery
headers without totals, the declared 3000 ms no-client settle interval, three
silent drains, and 13-row health. It promoted with canonical golden SHA-256
`8849dd5df2c70fc907d4c96092ea904164903d1c8c6e4866576c25922e494614`
and receipt SHA-256
`61d95d689585f2caecbe4e1263047fbbbd2e345dfe362d9ad832b77e0ea33ebd`.
The reducer advanced partial authority to 208 receipts and 624 request
executions, completing all sixteen string-context Delivery successors and
continuing with `delivery-blob-context__then__play-no-arguments`. Preserve its
canonical golden, receipt, four health captures, and the updated partial
summary and matrix.

Pair 207 independently repeated the string-context Delivery header without a
total, zero-row string-content Delivery result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`264d60d99424cd2b53dee1a68f1d9ec5a91b011b3d6ec6aa6014edba94520059`
and receipt SHA-256
`3b4b364bc1e7e44d2da2bb8fba41b87c51e7c530cb3f3579dfe846e6d8a80de5`.
The reducer advanced partial authority to 207 receipts and 621 request
executions, with `delivery-string-context__then__delivery-blob-content` next.
Preserve its canonical golden, receipt, four health captures, and the updated
partial summary and matrix.

Pair 202 independently repeated the string-context Delivery header without a
total, argumentless Delivery timeout, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`940e273e221ac578265da7c25a39b38d22facf905b2ba1dd3d8ac5973607eec9`
and receipt SHA-256
`5c0a2cbbbf4e45796f11ff3adf4f0d1d14eab073c91ce139d165e4cd39f0de0f`.
The reducer advanced partial authority to 202 receipts and 606 request
executions, with `delivery-string-context__then__delivery-missing-content`
next. Preserve its canonical golden, receipt, four health captures, and the
updated partial summary and matrix.

Pair 205 independently repeated two consecutive string-context Delivery
headers without totals, three silent drains, and 13-row health. It promoted
with canonical golden SHA-256
`0cd588e61f0974db49d30f5a6afd1d5996bd20fd77f412e10577964e18c10456`
and receipt SHA-256
`0f239e6fabdede153704a6cd0c7a3960719ee8c04109e5b48b777514346e6e65`.
The reducer advanced partial authority to 205 receipts and 615 request
executions, with `delivery-string-context__then__delivery-blob-context` next.
Preserve its canonical golden, receipt, four health captures, and the updated
partial summary and matrix.

Pair 204 independently repeated the string-context Delivery header without a
total, 13-row extra-argument Delivery result, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`bb5852566e69642e2ead850d1d9d64fe2ea49bee760ac09a282f6fa1a2e37ce7`
and receipt SHA-256
`424283fc806550714cdbb9a0a3a46591afa3b4b051af7bf6cd3a6b0cafabc4ea`.
The reducer advanced partial authority to 204 receipts and 612 request
executions, with `delivery-string-context__then__delivery-string-context`
next. Preserve its canonical golden, receipt, four health captures, and the
updated partial summary and matrix.

Pair 203 independently repeated the string-context Delivery header without a
total, zero-row missing-content Delivery result, three silent drains, and
13-row health. Its cold repeat needed bounded LINK activation retries and then
produced the same protocol result. It promoted with canonical golden SHA-256
`020702e72de6bf061e7fd1b9faf95fdc415598a91977eb37f2c572595cd98f98`
and receipt SHA-256
`020114628b20eb66a5e45ed830617abb8f2385542321d72819427a500cb43e8d`.
The reducer advanced partial authority to 203 receipts and 609 request
executions, with `delivery-string-context__then__delivery-extra-argument`
next. Preserve its canonical golden, receipt, four health captures, and the
updated partial summary and matrix.

Pair 200 independently repeated the string-context Delivery header without a
total, zero-context Play timeout, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`dab390f2d3e1fd4dc371f0daec4ce6f5a6c23af4087a635fe1e01f2239c919a4`
and receipt SHA-256
`c799e7a5c43736b47dc378410688090ac994ecb2a77dbd590629cc25f83689c6`.
The reducer advanced partial authority to 200 receipts and 600 request
executions, with `delivery-string-context__then__play-alternate-location`
next. Preserve its canonical golden, receipt, four health captures, and the
updated partial summary and matrix.

Pair 201 independently repeated the string-context Delivery header without a
total, seven-row alternate-location Play result, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`296583dcbd2b383fcfd6cd5700e1b274e7a3375a368f5505877c0bb4f1eaecd8`
and receipt SHA-256
`edfdaf429484ca9e4d5f6d1f1d9806cb9f98354868e2f30af2079362502c9e91`.
The reducer advanced partial authority to 201 receipts and 603 request
executions, with `delivery-string-context__then__delivery-no-arguments` next.
Preserve its canonical golden, receipt, four health captures, and the updated
partial summary and matrix.

Pair 124 independently repeated a timed-out zero-context precursor, 13-row
extra-argument Delivery successor, three silent drains, and 13-row health. It
promoted the twelfth zero-context-Play successor, advanced the partial authority
to 124 receipts and 372 request executions, and continued with
`play-zero-context__then__delivery-string-context`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 125 independently repeated a timed-out zero-context precursor, a
string-context Delivery header without a total, three silent drains, and
13-row health. It promoted the thirteenth zero-context-Play successor, advanced
the partial authority to 125 receipts and 375 request executions, and continued
with `play-zero-context__then__delivery-blob-context`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 126 independently repeated a timed-out zero-context precursor, a
blob-context Delivery header without a total, three silent drains, and 13-row
health. It promoted the fourteenth zero-context-Play successor, advanced the
partial authority to 126 receipts and 378 request executions, and continued
with `play-zero-context__then__delivery-string-content`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 127 independently repeated a timed-out zero-context precursor, zero-row
string-content Delivery successor, three silent drains, and 13-row health. Pair
128 independently repeated the same precursor followed by a blob-content
Delivery header without a total; after the measured three-second no-client
interval, all three drains remained silent and health returned 13. Together
they completed the zero-context-Play precursor row, advanced the partial
authority to 128 receipts and 384 request executions, and continued with
`play-alternate-location__then__play-no-arguments`. Preserve both canonical
goldens, receipts, eight health captures, and the partial summary and matrix.

Pair 129 independently repeated a seven-row alternate-location Play precursor,
an argumentless Play timeout, three silent drains, and 13-row health. It
advanced the partial authority to 129 receipts and 387 request executions and
continued with `play-alternate-location__then__play-missing-content`. Preserve
its canonical golden, receipt, and four health captures with the partial
summary and matrix.

Pair 130 independently repeated a seven-row alternate-location Play precursor,
a zero-row missing-content Play successor, three silent drains, and 13-row
health. It advanced the partial authority to 130 receipts and 390 request
executions and continued with
`play-alternate-location__then__play-extra-argument`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 131 independently repeated a seven-row alternate-location Play precursor,
a seven-row extra-argument Play successor, three silent drains, and 13-row
health. It advanced the partial authority to 131 receipts and 393 request
executions and continued with
`play-alternate-location__then__play-string-context`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 132 independently repeated a seven-row alternate-location Play precursor,
a string-context Play header without a total, three silent drains, and 13-row
health. It advanced the partial authority to 132 receipts and 396 request
executions and continued with
`play-alternate-location__then__play-blob-context`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 133 independently repeated a seven-row alternate-location Play precursor,
a blob-context Play header without a total, three silent drains, and 13-row
health. It advanced the partial authority to 133 receipts and 399 request
executions and continued with
`play-alternate-location__then__play-string-content`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 134 independently repeated a seven-row alternate-location Play precursor,
a zero-row string-content Play successor, three silent drains, and 13-row
health. It advanced the partial authority to 134 receipts and 402 request
executions and continued with
`play-alternate-location__then__play-blob-content`. Preserve its canonical
golden, receipt, and four health captures with the partial summary and matrix.

Pair 135 did not promote in generation `z34`. Its record health drain timed
out, while its cold repeat health drain received the exact delayed transaction-1
`0x4000 [0x2102, 0]` frame queued by the blob-content Play successor. The
seven-row precursor, successor header without a total, and 13-row health result
otherwise matched. The guarded comparison stopped the service with status 1;
its EXIT path restored `play-paths`, and the isolated service cgroup removed the
VM and identity helper. Both protocol envelopes and three available health
captures are hash-bound under
`malformed-history-lifecycle/attempts/delayed-frame-race-pair135-20261004T215947Z/`.
The resumable pair-135 work slot is empty. Preserve this attempt directory and
require a wholly fresh record and cold repeat before canonical promotion.

Recovery generation `z35` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z35.service`,
invocation `b2947157bd7048a4836aebf820b198e1`, with a 30-hour ceiling. It started
only after verifying the active guest manifest matched `play-paths`, no
`rekordbox-identity-*` unit was active, no isolated Rekordbox container
remained, and the pair-135 work slot was empty. The standard handoff validates
and skips every receipt in matrix order, recycles the isolated VM at each
64-pair boundary, and performs a wholly fresh record and cold repeat when it
reaches pair 135. On interruption, preserve any new pair-135 candidate and
health captures separately from the quarantined `z34` attempt before retrying.

Generation `z35` independently recorded and repeated pair 135 with the exact
delayed transaction-1 `0x4000 [0x2102, 0]` frame in both health drains. The
blob-content Play successor returned its header without a total, both health
requests returned 13 rows, and the pair promoted with canonical golden SHA-256
`49a7bb584ab1464e9f7dc941b4651467a68d9529b395ea14ab8e8d083c84cf6c` and
receipt SHA-256
`affc4f136697a23baf5b76dbe90701121424df95bfa8f61105cc931a86a58bcc`.
It advanced partial authority to 135 receipts and 405 request executions and
continued with `play-alternate-location__then__play-zero-context`. Preserve the
canonical pair and the separate hash-bound `z34` race attempt.

Pair 136 independently repeated a seven-row alternate-location Play precursor,
a zero-context Play timeout, three silent drains, and 13-row health. It promoted
with canonical golden SHA-256
`68f0687dda0e4bd23e1c8049c6cf93e3af46b718b6fc28197533144c35e7e7cc`
and receipt SHA-256
`9cfdde005f868c2c22280d78907a1c93d601fa2343cf08b06f6fd0492a538588`.
It advanced partial authority to 136 receipts and 408 request executions and
continued with `play-alternate-location__then__play-alternate-location`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 137 independently repeated two seven-row alternate-location Play menus,
three silent drains, and 13-row health. It promoted with canonical golden
SHA-256
`172497c0350f8fedfb324575f087e0a9074ee1994639dcf20b5820318d7f72a3`
and receipt SHA-256
`85310e002c375a8855604942c6f43852882eab40065ebe02b17716425133ac47`.
It advanced partial authority to 137 receipts and 411 request executions and
continued with `play-alternate-location__then__delivery-no-arguments`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 138 independently repeated a seven-row alternate-location Play precursor,
an argumentless Delivery timeout, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`51abd574b7e903c155a412c403060afed2cba8a9e42edb35d2668954e72b7529`
and receipt SHA-256
`385414c67b8391dc7a76334f8d9629884465f07b22b3bcef9bfa4eee09ffe240`.
It advanced partial authority to 138 receipts and 414 request executions and
continued with `play-alternate-location__then__delivery-missing-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 139 independently repeated a seven-row alternate-location Play precursor,
a zero-row missing-content Delivery menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`c9f70d5637090d8faffaf301c718d308eafd4eca25b77ba889144b9c41835f12`
and receipt SHA-256
`401949bcaef81b556e6e2a5f18d4e9687a5482f7ffcfcb58da4b2728a0c41f03`.
It advanced partial authority to 139 receipts and 417 request executions and
continued with `play-alternate-location__then__delivery-extra-argument`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 140 independently repeated a seven-row alternate-location Play precursor,
a 13-row extra-argument Delivery menu, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`bea9bf36c922ba184ddb6341aedda5054bdbcc5ae5012639511726ce401db498`
and receipt SHA-256
`99382d39dbdf3c2b869104d07c23e29bb8dc19b260045d50de2de61b5a72b8ab`.
It advanced partial authority to 140 receipts and 420 request executions and
continued with `play-alternate-location__then__delivery-string-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Generation `z35` stopped before pair 141's protocol recording after all ten
bounded UI activation attempts found the synthetic RX3 but Link Export remained
disabled. No protocol candidate or repeat was created. Its pre-record health
capture and complete service journal are hash-bound under
`malformed-history-lifecycle/attempts/link-activation-failure-pair141-20261004T224720Z/`.
The EXIT path restored the exact `play-paths` guest manifest and database, and
removed the isolated VM and identity helper. Preserve this attempt directory;
pair 141 still requires a wholly fresh record and repeat.

Recovery generation `z36` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z36.service`,
invocation `20d541a77045462b9224b4f222a80909`, with a 30-hour ceiling. It started
from the verified `play-paths` baseline with no identity helper or isolated VM
remaining. The resumable runner validates and skips all 140 canonical receipts
before attempting a wholly fresh pair-141 record and repeat. Preserve the
activation-failure archive separately from any `z36` candidate or canonical
result.

Generation `z36` verified and skipped 128 receipts but timed out during the
bounded 300-second guest-readiness wait after its third rapid VM recycle. It
never entered pair 141's recorder and created no pair artifact. Its complete
journal is hash-bound under
`malformed-history-lifecycle/attempts/guest-readiness-timeout-pair141-20261004T225522Z/`.
The EXIT path again restored the exact `play-paths` baseline and removed the
VM and identity helper. The lifecycle wrapper now validates each completed
64-pair batch's golden against its receipt on the host and skips its VM startup;
missing or mismatched evidence still enters the recorder's fail-closed path.

Recovery generation `z37` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z37.service`,
invocation `ddd838a262ab45739764b0f540797e0e`, with a 30-hour ceiling. It uses the
host-side completed-batch validation above, so the first 128 canonical pairs
require no guest lifecycle. Its first VM starts for the third batch containing
pair 141. Preserve both prior failure archives independently from any `z37`
candidate or promoted result.

Generation `z37` skipped the first 128 canonical pairs without starting their
VMs and reached the third batch directly. The recorder then stopped at its
fail-closed incomplete-work-slot guard because `z35` had left the pre-record
health capture in pair 141's live evidence directory. No protocol candidate or
repeat was created. The stale capture and complete `z37` journal are hash-bound
under
`malformed-history-lifecycle/attempts/stale-work-slot-pair141-20261004T230030Z/`;
the capture hash matches its independently preserved `z35` archive copy. The
live pair-141 work slot is now empty for a wholly fresh record and repeat.

Recovery generation `z38` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261004z38.service`,
invocation `7fd92c2c506a46c4b1e11b3f98773809`, with a 30-hour ceiling. It starts from
the exact `play-paths` baseline, skips the first 128 pairs by host-side receipt
validation, and enters pair 141 with an empty work slot. Preserve all three
pair-141 failure archives independently from any `z38` candidate or promoted
result.

Generation `z38` independently recorded and repeated pair 141. String-context
Delivery returned a header without a total after the seven-row
alternate-location Play precursor; all three drains timed out and both health
requests returned 13. It promoted with canonical golden SHA-256
`6d79445cc766bbb1d2eae0e8988bf41752c135f0435597a1e208e58af4d28c68`
and receipt SHA-256
`08deb167c0df0f162bfa5e6f54a29b36ea6674202861c987a92e72a549721985`.
It advanced partial authority to 141 receipts and 423 request executions and
continued with `play-alternate-location__then__delivery-blob-context`.
Preserve the canonical pair, four health captures, partial reducer outputs, and
all three separately hash-bound pre-authority failure archives.

Pair 142 independently repeated a seven-row alternate-location Play precursor,
a blob-context Delivery header without a total, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`8926faeade785e6a320f3c0a492637ac81901c97cb338bfe202cbd1e767d760d`
and receipt SHA-256
`9bc624eb03f104c26935aa8d1c6cf22a7beb7ce5c9041e30619efa88b81c6a83`.
It advanced partial authority to 142 receipts and 426 request executions and
continued with `play-alternate-location__then__delivery-string-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 143 independently repeated a seven-row alternate-location Play precursor,
a zero-row string-content Delivery menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`5a328a6dab0c5a6dc8d652db99e62ac45ea06e22a7e6187290c71f7970d573d7`
and receipt SHA-256
`9a4319553db645ba2db450e8fee990d0d4aa2b0c88eedbccda6e1a0d1fb65405`.
It advanced partial authority to 143 receipts and 429 request executions and
continued with `play-alternate-location__then__delivery-blob-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 144 completed the alternate-location-Play precursor row. It independently
repeated the seven-row precursor, a blob-content Delivery header without a
total, the measured three-second no-client interval, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`d881d7a87f233bacc44f8abe2a8e6651c0d1c26c176f3b4e024909fd40cd4215`
and receipt SHA-256
`f71dd3b83cf3282bc44c579c07bb206ca920c92466c30547906040ea3a7df369`.
It advanced partial authority to 144 receipts and 432 request executions and
continued with `delivery-no-arguments__then__play-no-arguments`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 145 began the argumentless-Delivery precursor row with two silent
timeouts: argumentless Delivery followed by argumentless Play. All three drains
timed out and health returned 13. It promoted with canonical golden SHA-256
`ebf9e72015dce63cc8a89a689c5b87554921878da3f411a997e3d07565b41d79`
and receipt SHA-256
`3f0b08a14cad04a78a2a78ce8229376bdb213f1ceb723a03c31e90acc57b2471`.
It advanced partial authority to 145 receipts and 435 request executions and
continued with `delivery-no-arguments__then__play-missing-content`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 146 independently repeated a silent argumentless-Delivery timeout, a
zero-row missing-content Play menu, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`9c70650be03fcfec833240bab2faff0801f55dd8e980e0bfe9c8ee93d644aa48`
and receipt SHA-256
`9fc4b50bf1fd361fc98c7216aaaf9a6bc873c558c77ac1ce5f89b772f6779df9`.
It advanced partial authority to 146 receipts and 438 request executions and
continued with `delivery-no-arguments__then__play-extra-argument`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 147 independently repeated a silent argumentless-Delivery timeout, a
seven-row extra-argument Play menu, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`6c9c664cb8730d8b4891e9a092d9381348e11b9a1b0ce1e245def9d9edd32998`
and receipt SHA-256
`437b71569e8ccbe254a8b2ee8c5b7506b0b1f8186855d0fa77f4837dc75c35a8`.
It advanced partial authority to 147 receipts and 441 request executions and
continued with `delivery-no-arguments__then__play-string-context`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 148 independently repeated a silent argumentless-Delivery timeout, a
string-context Play header without a total, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`37d13665cb3b0b2b922c3c1bdb5ae4463327f4753a12760d8222f25d1f051638`
and receipt SHA-256
`7d5089d7cf92387d23a63190c416a374796aeb48f135e0b3f8c61ed375f0b303`.
It advanced partial authority to 148 receipts and 444 request executions and
continued with `delivery-no-arguments__then__play-blob-context`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 149 independently repeated a silent argumentless-Delivery timeout, a
blob-context Play header without a total, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`4a2b9c59f8fd8d6c3e09616071e811bf1a4c575392920623fb671dcbdda52392`
and receipt SHA-256
`3e188658489f44ad67487b8a96a5f3311426885219c284f5e30cc6a791f04817`.
It advanced partial authority to 149 receipts and 447 request executions and
continued with `delivery-no-arguments__then__play-string-content`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 150 independently repeated a silent argumentless-Delivery timeout, a
zero-row string-content Play menu, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`b99edc3d7111e8c92fec77094298b51a00d4ea81c52a6f51de50c0da14de6b19`
and receipt SHA-256
`6298c28b1ab6dac8bca17f56f10bc1766f48f48416accd0c428c83f546207060`.
It advanced partial authority to 150 receipts and 450 request executions and
continued with `delivery-no-arguments__then__play-blob-content`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 151 independently repeated a silent argumentless-Delivery timeout, a
blob-content Play header without a total, and 13-row health. Its first two
drains were silent; the health drain received the successor's exact delayed
transaction-1 `0x4000 [0x2102, 0]` frame. It promoted with canonical golden
SHA-256
`205adaa2bbc1b9ee4336a00a85d890fa7036797dc96095335b67512f5fac72b5`
and receipt SHA-256
`1ea8e2e58c09658327dfa00b5295c820fb52f8f47312d3b90e6e9b6ad37df34f`.
It advanced partial authority to 151 receipts and 453 request executions and
continued with `delivery-no-arguments__then__play-zero-context`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 152 independently repeated a silent argumentless-Delivery timeout, a
silent zero-context Play timeout, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`ca47776f6c99d846993bee01e48b4b5f151b38e869448ab1f4efd65b92d5c533`
and receipt SHA-256
`34a1d18e5b8d954dc9a9d1a60cd7dec3fe4f4ec7e2bdaa340ecf45a0b84d4ee3`.
It advanced partial authority to 152 receipts and 456 request executions and
continued with `delivery-no-arguments__then__play-alternate-location`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 153 independently repeated a silent argumentless-Delivery timeout, the
ordinary seven-row alternate-location Play menu, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`06425e971082c63af6cbde0a178567be55bc1091de2f3808a4a8090ff86593b2`
and receipt SHA-256
`72e1cf8a70e0667800ff1e2c58ad70851e2e06b10697977ee895c2776b0f5315`.
It completed all nine Play-shaped successors after argumentless Delivery,
advanced partial authority to 153 receipts and 459 request executions, and
continued with `delivery-no-arguments__then__delivery-no-arguments`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 154 independently repeated two silent argumentless-Delivery timeouts,
three silent drains, and 13-row health. It promoted with canonical golden
SHA-256
`9288f4252261bcb3a022082264eeb96975bdb86248b15225cb9e7be19a7d27bd`
and receipt SHA-256
`4c6389b9ae8c6be49bda03edf0ba206885c587d3c397d003cdfe6dc1d783c895`.
It began the Delivery-shaped successor block, advanced partial authority to
154 receipts and 462 request executions, and continued with
`delivery-no-arguments__then__delivery-missing-content`. Preserve its canonical
golden, receipt, four health captures, and the partial summary and matrix.

Pair 155 independently repeated a silent argumentless-Delivery timeout, a
zero-row missing-content Delivery menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`146b826eb1b310c62a26b2dd38ce08add52cd4ebc3307e355b86d87211cf231f`
and receipt SHA-256
`040e3add3634d5bf33355ddf7e8d6e0493ea103e56115fd82d2a0c2ac85491db`.
It advanced partial authority to 155 receipts and 465 request executions and
continued with `delivery-no-arguments__then__delivery-extra-argument`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 156 independently repeated a silent argumentless-Delivery timeout, the
full 13-row extra-argument Delivery menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`37c09cc7f2e52d631ad8a3389d6fae3f03c35814548181e534954d256d137507`
and receipt SHA-256
`167c825d4fa1640bef1e04bbdc541ac2e5dd4a42e80966e3aa42653e788fdafc`.
It advanced partial authority to 156 receipts and 468 request executions and
continued with `delivery-no-arguments__then__delivery-string-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 157 independently repeated a silent argumentless-Delivery timeout, a
string-context Delivery header without a total, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`d41aa50611a315d555a059546c44edc47b9d4721b0d83932c9ca2408547a68dd`
and receipt SHA-256
`85b5a20cc12686050b1ee5f69d7e7a0d90286fec3ce6c9388ae01f14a47dc98e`.
It advanced partial authority to 157 receipts and 471 request executions and
continued with `delivery-no-arguments__then__delivery-blob-context`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 158 independently repeated a silent argumentless-Delivery timeout, a
blob-context Delivery header without a total, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`2be872d1042c0d23fe6ecbb7b52a8ebe967d6948623b2710583ba24242fd7508`
and receipt SHA-256
`8c1c197ca7c6f0e7083478e93a5cd65ed9b791c1f2c880d29ae3ec33317ee5f1`.
It advanced partial authority to 158 receipts and 474 request executions and
continued with `delivery-no-arguments__then__delivery-string-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 159 independently repeated a silent argumentless-Delivery timeout, a
zero-row string-content Delivery menu, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`870db88c68302f8e9cf4a1abd6510ce4b1f229f14bb6d4d907d26ff28e6c47fe`
and receipt SHA-256
`a0ac12867b1d23e84acadaa17ba726a4028fbcce93f49137a94395426f5dc5a6`.
It advanced partial authority to 159 receipts and 477 request executions and
continued with `delivery-no-arguments__then__delivery-blob-content`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 160 independently repeated a silent argumentless-Delivery timeout, a
blob-content Delivery header without a total after the measured no-client
interval, three silent drains, and 13-row health. It promoted with canonical
golden SHA-256
`3403b55668daf6f59554e4a534379216e09b38b69af514dc418e120c68e5dac4`
and receipt SHA-256
`4bda7b95b1e1f1f3194b3ac6af6d31ca9e232dfae4997cd228e3312a385a5eca`.
It completed the argumentless-Delivery precursor row, advanced partial
authority to 160 receipts and 480 request executions, and continued with
`delivery-missing-content__then__play-no-arguments`. Preserve its canonical
golden, receipt, four health captures, and the partial summary and matrix.

Pair 161 independently repeated a zero-row missing-content Delivery precursor,
a silent argumentless-Play successor, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`719f74864b1dd632e835a4bcb08e052cfb9f380cb46f0abcc0142a85d5774fd8`
and receipt SHA-256
`e0114ed2edadf761f5abbb55c18716a3f1de4fff770204b81ab4331fcc506874`.
It advanced partial authority to 161 receipts and 483 request executions and
continued with `delivery-missing-content__then__play-missing-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 162 independently repeated a zero-row missing-content Delivery precursor,
a zero-row missing-content Play successor, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`72028eabe96978a2bf6ca78264af52b1eecfc4d219fba0b6e5eeaf34ef5f3832`
and receipt SHA-256
`2b2b26ac261546035e2ba55e79e96aa9633c60a4f25463f1a57d3c8c0de02082`.
It advanced partial authority to 162 receipts and 486 request executions and
continued with `delivery-missing-content__then__play-extra-argument`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 163 independently repeated a zero-row missing-content Delivery precursor,
the seven-row extra-argument Play menu, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`40d8c2354565e4efa9744ec934c45b86cc94fdec1bbf6c308b148fc9b8ecc4ca`
and receipt SHA-256
`90be0601df40e60a139c03bc2be05948a9c9c9347386100c559fac9f729668f5`.
It advanced partial authority to 163 receipts and 489 request executions and
continued with `delivery-missing-content__then__play-string-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 164 independently repeated a zero-row missing-content Delivery precursor,
a string-context Play header without a total, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`121dbbeac36ecbadbf7220c3994066ed7d6dcd44028c5228e841ddfd846e557b`
and receipt SHA-256
`fd6d6959e4af36b6db6b649aeb8f5365a34c5bfd07471fc5bb01bad4340e8d71`.
It advanced partial authority to 164 receipts and 492 request executions and
continued with `delivery-missing-content__then__play-blob-context`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 165 independently repeated a zero-row missing-content Delivery precursor,
a blob-context Play header without a total, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`c0e5d01e4323fed696aba2d350f9e45e7909f2aa3054f45c509807cee4235c2f`
and receipt SHA-256
`5312e686959d5b42376a118afd5b50f2eeb6f3e366f7c080bdab85685139d501`.
It advanced partial authority to 165 receipts and 495 request executions and
continued with `delivery-missing-content__then__play-string-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 166 independently repeated a zero-row missing-content Delivery precursor,
a zero-row string-content Play menu, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`e6a6fb9be190847a08b00a7e9e662973c4b06772d38ca705d46f1c10e2b4d14c`
and receipt SHA-256
`3c0dae266882717aea977ab0c7584e6c7605ab8e30ae5ca7761e0c8151c96ada`.
It advanced partial authority to 166 receipts and 498 request executions and
continued with `delivery-missing-content__then__play-blob-content`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 167 independently repeated a zero-row missing-content Delivery precursor,
a blob-content Play header without a total, and 13-row health. The first two
drains were silent; the health drain received the successor's exact delayed
transaction-1 `0x4000 [0x2102, 0]` frame. It promoted with canonical golden
SHA-256
`6a9d4954a07ae56caa0820e0e6d7b2beca0ddc9f79554a22e08650a2887b8d55`
and receipt SHA-256
`3d4f618e9eef1dd3c8f1188847d9525befc36435d9bdf80d6534320abf2550c2`.
It advanced partial authority to 167 receipts and 501 request executions and
continued with `delivery-missing-content__then__play-zero-context`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 168 independently repeated a zero-row missing-content Delivery precursor,
a silent zero-context Play timeout, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`ce90d56b951ca3529697cadd6b5c7f0ffdb8c994f5da18a96ce0678d5a669fc6`
and receipt SHA-256
`65093931a18d790da7247187f0327c079de5b0662ca67e79c2adc3b0e0684ca5`.
It advanced partial authority to 168 receipts and 504 request executions and
continued with `delivery-missing-content__then__play-alternate-location`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 169 independently repeated a zero-row missing-content Delivery precursor,
the seven-row alternate-location Play menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`7b052f32fa5267e1aa5ab960955d74f56b396ea4e29262a942c525444a369aec`
and receipt SHA-256
`d8154d7ef0cbda42d37ed2363cc23fc657ca86f7e9756d430d91b303c8923295`.
It completed all nine Play-shaped successors for the missing-content Delivery
precursor, advanced partial authority to 169 receipts and 507 request
executions, and continued with
`delivery-missing-content__then__delivery-no-arguments`. Preserve its canonical
golden, receipt, four health captures, and the partial summary and matrix.

Pair 170 independently repeated a zero-row missing-content Delivery precursor,
a silent argumentless Delivery timeout, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`6a475000ec0e242302c5553948ab321a36572ae97c5784168fe83dca349a4078`
and receipt SHA-256
`50278727cc364d39c7eda824cda62c86490f39d1581aba5872f751092b0261a5`.
It advanced partial authority to 170 receipts and 510 request executions and
continued with `delivery-missing-content__then__delivery-missing-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 171 independently repeated two zero-row missing-content Delivery menus,
three silent drains, and 13-row health. It promoted with canonical golden
SHA-256
`e709b6cf8ab23200cd16394594534875f0193509b2dbefbf84b4f1665ca2cbdf`
and receipt SHA-256
`e1ebc5bf43a45d80e94a58553fbdcc67ca753a85a3bdd5a38d90ea5c261d566f`.
It advanced partial authority to 171 receipts and 513 request executions and
continued with `delivery-missing-content__then__delivery-extra-argument`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 172 independently repeated a zero-row missing-content Delivery precursor,
the full 13-row extra-argument Delivery menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`fea5e75c32332f914f75dcc3ff5fd6a3cced50bc5e05ffc4f0b4853e45fd6deb`
and receipt SHA-256
`ecc57d2f618c71d1804363ac0fb12328738249684a80924745d83d48f05ea6bc`.
It advanced partial authority to 172 receipts and 516 request executions and
continued with `delivery-missing-content__then__delivery-string-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 173 independently repeated a zero-row missing-content Delivery precursor,
a string-context Delivery header without a total, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`96291fd78ad08438668077677fd5b1ed2fcf00f236aaf0ae82f0e83265f478e4`
and receipt SHA-256
`e679cee21ef3279d5ab2bf75add2003913421a9429ee74ec95c402c6f1a27c75`.
It advanced partial authority to 173 receipts and 519 request executions and
continued with `delivery-missing-content__then__delivery-blob-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 174 independently repeated a zero-row missing-content Delivery precursor,
a blob-context Delivery header without a total, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`436447f7d14d4c9dfa22272970692f60b9c2a0c0519c766b0607e53d6376bc96`
and receipt SHA-256
`161800c8da4983aa2f46fc8c67b974414a8caf096373af16e4f4d15693c1a36a`.
It advanced partial authority to 174 receipts and 522 request executions and
continued with `delivery-missing-content__then__delivery-string-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 175 independently repeated two zero-row Delivery menus: missing-content
then string-content. All three drains were silent and health returned 13 rows.
It promoted with canonical golden SHA-256
`d31185e57c7d2c15599e80ce5673a4aa100e9c89af479186dc0b4f45832fad67`
and receipt SHA-256
`5dbbb3efc03905a569a77f8c42f1c33c0bd53bc06da665084caee89b0d79c698`.
It advanced partial authority to 175 receipts and 525 request executions and
continued with `delivery-missing-content__then__delivery-blob-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 176 independently repeated a zero-row missing-content Delivery precursor,
a blob-content Delivery header without a total after the measured no-client
interval, three silent drains, and 13-row health. It promoted with canonical
golden SHA-256
`8284c9edc2a50e4ac7a7609e8b1582cfef57da6419ef9ff8932532db4859ce26`
and receipt SHA-256
`25a2403de63af59571ff9c6b860d3fc8e6422fa667c0a75d548b02c2fcaaeda1`.
It completed the missing-content Delivery precursor row, advanced partial
authority to 176 receipts and 528 request executions, and continued with
`delivery-extra-argument__then__play-no-arguments`. Preserve its canonical
golden, receipt, four health captures, and the partial summary and matrix.

Pair 177 independently repeated the full 13-row extra-argument Delivery
precursor, a silent argumentless Play timeout, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`94f534f008cd9387825505be6332797b10799f5d676ce16d99501c84c15bd857`
and receipt SHA-256
`7573190c2b5e86eff8fd81ffee7a88663ebbc42a9166c61d41042eb41df6e87a`.
It advanced partial authority to 177 receipts and 531 request executions and
continued with `delivery-extra-argument__then__play-missing-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 178 independently repeated the full 13-row extra-argument Delivery
precursor, a zero-row missing-content Play menu, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`99b2a5dedfabfb08dd87fb7beed062c467377c0c96606e49ab0f059368856d9c`
and receipt SHA-256
`8349b1dac41b57239d6c0b03afbca3e0b1577a5c7996f1c79541be7384dbaaab`.
It advanced partial authority to 178 receipts and 534 request executions and
continued with `delivery-extra-argument__then__play-extra-argument`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 179 independently repeated the full 13-row extra-argument Delivery
precursor, the seven-row extra-argument Play menu, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`d8a68d776f92af31659d9bd6036fe28772b09df64cbda3cdb42083da2ce4fc24`
and receipt SHA-256
`ed447f7670ff389e2a937510f0edb2cd9b24506987aad7fd4b0bc486c1447598`.
It advanced partial authority to 179 receipts and 537 request executions and
continued with `delivery-extra-argument__then__play-string-context`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 180 independently repeated the full 13-row extra-argument Delivery
precursor, the string-context Play header without a total, three silent drains,
and 13-row health. It promoted with canonical golden SHA-256
`37b6522cf78759efb98143b3571c1eab17fc2768c40409d5b3a075c3fdf423ee`
and receipt SHA-256
`20213153e6a074a2ab8a53cbd5866121702d63920e3c560720cea1dd3b77a0db`.
It advanced partial authority to 180 receipts and 540 request executions and
continued with `delivery-extra-argument__then__play-blob-context`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 181 independently repeated the full 13-row extra-argument Delivery
precursor, the blob-context Play header without a total, three silent drains,
and 13-row health. It promoted with canonical golden SHA-256
`0991e078ca75f657ff49a1bcc6dbc4f0f302b0924d9bc0c347d40f36f35a68d2`
and receipt SHA-256
`a690b6ba03a350e1e9e7854d2b2ce098561ca03b95ddf6059bfe2b79fa325119`.
It advanced partial authority to 181 receipts and 543 request executions and
continued with `delivery-extra-argument__then__play-string-content`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 182 independently repeated the full 13-row extra-argument Delivery
precursor, the zero-row string-content Play menu, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`91bbbdf7f80850556977e3701c2937969c01d73ff270ca03bb49eb79c7381a52`
and receipt SHA-256
`6f94d86a41dcfe64ef40fdcea237a78daa236815c7e7e12cdd9566cbd955e5f9`.
It advanced partial authority to 182 receipts and 546 request executions and
continued with `delivery-extra-argument__then__play-blob-content`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 183 independently repeated the full 13-row extra-argument Delivery
precursor and the blob-content Play header without a total. Both health drains
received the successor's exact delayed `0x4000 [0x2102, 0]` frame before
normal 13-row health. It promoted with canonical golden SHA-256
`d5b5e44e9ec05599a72acafd37044fc9c51e238e9d8f932f1c97c7e22d0aeecf`
and receipt SHA-256
`812d742b400fcdc1a9bb5b7e5649d943a7902df687497bce7174514f7e8d6eaa`.
It advanced partial authority to 183 receipts and 549 request executions and
continued with `delivery-extra-argument__then__play-zero-context`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 184 independently repeated the full 13-row extra-argument Delivery
precursor, a zero-context Play timeout, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`e0964a4c9ec58bf207cd222ed3adb4ff4b660be1702c9636468ebe21edb7439c`
and receipt SHA-256
`5890d226bedd9b0fb63b2dbbbb3141658830b6e1f3262e21ce445587b2aedf84`.
It advanced partial authority to 184 receipts and 552 request executions and
continued with `delivery-extra-argument__then__play-alternate-location`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 185 independently repeated the full 13-row extra-argument Delivery
precursor, the seven-row alternate-location Play menu, three silent drains,
and 13-row health. It promoted with canonical golden SHA-256
`32f295478901ad432fef192692fc1f5ba3116c5047d9a187ab7cbe414a2119f7`
and receipt SHA-256
`eaf881d196d773463dca023829bf977759004699a4c10b849d71affd41844bba`.
It advanced partial authority to 185 receipts and 555 request executions and
continued with `delivery-extra-argument__then__delivery-no-arguments`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 186 independently repeated the full 13-row extra-argument Delivery
precursor, an argumentless Delivery timeout, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`446cd62c7a0827465ca4feba9e3cf53b3b952a342fb071d2f40ec056a68ee681`
and receipt SHA-256
`3e42197140e5842a5af703374ee22428fb68ad2f66544d8b39d8ca32d0e75737`.
It advanced partial authority to 186 receipts and 558 request executions and
continued with `delivery-extra-argument__then__delivery-missing-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 187 independently repeated the full 13-row extra-argument Delivery
precursor, the zero-row missing-content Delivery menu, three silent drains,
and 13-row health. It promoted with canonical golden SHA-256
`0905ed672f5078d6b5dff74c1e05eb57b0e07a3a850757e6a5a40753a407ab81`
and receipt SHA-256
`341261d4454d211948715bb83109e7e38832bf4bac329935369be54f2a18fe62`.
It advanced partial authority to 187 receipts and 561 request executions and
continued with `delivery-extra-argument__then__delivery-extra-argument`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 188 independently repeated two consecutive 13-row extra-argument
Delivery results, three silent drains, and 13-row health. It promoted with
canonical golden SHA-256
`0e9e2371ab0443ab2abb6bc901e1aa6021d0506f173e8a2b4e588c43964159fb`
and receipt SHA-256
`6dfc900b0f671a19d08b8a98c1b990cbeeb2f52f2de002c86432360caada1edd`.
It advanced partial authority to 188 receipts and 564 request executions and
continued with `delivery-extra-argument__then__delivery-string-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 189 independently repeated the full 13-row extra-argument Delivery
precursor, the string-context Delivery header without a total, three silent
drains, and 13-row health. It promoted with canonical golden SHA-256
`157d25f325e2ebe08d8ca875df188d56995a8e7b75342d686ca44c86f21db15b`
and receipt SHA-256
`31d752952a4999eba7a67ee33afa891b9f8ed1532589866c3560be40527fd563`.
It advanced partial authority to 189 receipts and 567 request executions and
continued with `delivery-extra-argument__then__delivery-blob-context`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 190 independently repeated the full 13-row extra-argument Delivery
precursor, the blob-context Delivery header without a total, three silent
drains, and 13-row health. It promoted with canonical golden SHA-256
`9d320b8f7acac9b6f6bbe6132b7adda8d0917de975b12286520646ec95b3a902`
and receipt SHA-256
`383845d81077d43fae8f26e15d09b631c3b55fa41f300a4488380f88cb41b5c5`.
It advanced partial authority to 190 receipts and 570 request executions and
continued with `delivery-extra-argument__then__delivery-string-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 191 independently repeated the full 13-row extra-argument Delivery
precursor, the zero-row string-content Delivery menu, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`15c85acb106f661e0b29b34c0dab32276f36ebb04e5a42480a71b43cf5c28325`
and receipt SHA-256
`8b3032edcb1b26e4afb6d9eb3de51c3ef40b043493dc886ac64d7df12d09a838`.
It advanced partial authority to 191 receipts and 573 request executions and
continued with `delivery-extra-argument__then__delivery-blob-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Pair 192 independently repeated the full 13-row extra-argument Delivery
precursor and the blob-content Delivery header without a total. Its measured
three-second no-client interval and all three drains were silent; health
returned 13 rows. It promoted with canonical golden SHA-256
`befa97c9b381e08ffe69fa0b1c54463a1826f0fd1efc2c270b97405fd038f509`
and receipt SHA-256
`ef462548cc059774628cd3a826ee1962cd4cab7fe1d74f247abc6d0298c8bb12`.
It completed the extra-argument-Delivery precursor row, advanced partial
authority to 192 receipts and 576 request executions, and continued with
`delivery-string-context__then__play-no-arguments`. Preserve its canonical
golden, receipt, four health captures, and the partial summary and matrix.

Pair 193 independently repeated the string-context Delivery header without a
total, an argumentless Play timeout, three silent drains, and 13-row health.
It promoted with canonical golden SHA-256
`ccd90bed28a830d71c2ed29a783e6b0dade3510b45d46977f2f5bd97c1cc65c0`
and receipt SHA-256
`131d93497157c8ae3bae42910c95f41b57c1d1be934be483e36d47ed584737b4`.
It advanced partial authority to 193 receipts and 579 request executions and
continued with `delivery-string-context__then__play-missing-content`.
Preserve its canonical golden, receipt, four health captures, and the partial
summary and matrix.

Generation `z38` stopped during pair 194's repeat after all ten bounded UI
activation attempts recognized the synthetic RX3 while Link Export remained
disabled. The record candidate was complete, but the repeat produced only its
pre-record health capture and never issued a protocol request. The candidate,
three health captures, complete service journal, and hash-bound manifest are
quarantined under
`malformed-history-lifecycle/attempts/link-activation-failure-pair194-20261005T033128Z/`.
The EXIT path restored the exact `play-paths` database, removed the isolated VM
and identity helper, and the live pair-194 slot is empty. Preserve this archive
independently from the wholly fresh recovery record and repeat.

Recovery generation `z39` is bounded unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261005z39.service`,
invocation `8a48aa0c79f04a3abd544f4ebd0f3afa`, with a 30-hour ceiling. It starts from
the exact `play-paths` baseline, validates and skips all 192 promoted receipts,
and enters pair 194 with an empty work slot. Preserve the `z38` activation
failure archive independently from any `z39` candidate or promoted result.

Generation `z39` independently recorded and repeated pair 194 from a clean
slot. String-context Delivery returned a header without a total,
missing-content Play returned a zero-row menu, all three drains timed out, and
health returned 13 rows. It promoted with canonical golden SHA-256
`3c6e2c3209eded40efd3b595190e7681d966c03eadb3eb588e69bd18505d5880`
and receipt SHA-256
`cbd1c9a672c8475c96876b79f071f6cef417aeb3bc2c6df44442594772425981`.
It advanced partial authority to 194 receipts and 582 request executions and
continued with `delivery-string-context__then__play-extra-argument`. Preserve
the canonical result and the separate `z38` failure archive.

Pair 195 independently repeated the string-context Delivery header without a
total, the seven-row extra-argument Play menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`625cd86c25c6adf2480641272f6dd2ea03f66fd63fcd325ebf610c69abcb2b30`
and receipt SHA-256
`a97a59298d2acff981c521b3bcae315475aad658cd5aaacf5e1fbed0fd03d682`.
It advanced partial authority to 195 receipts and 585 request executions and
continued with `delivery-string-context__then__play-string-context`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 196 independently repeated two consecutive headers without totals from
string-context Delivery and string-context Play, three silent drains, and
13-row health. It promoted with canonical golden SHA-256
`23f4f56b8af8b907852865d9eaccf247d36d0c39097c5117f0d2b27175a1fc5b`
and receipt SHA-256
`59bd817dd0d0a163cdc7ac2660ceef1c057822cfcb6d25b7a5e004ca63b8422c`.
It advanced partial authority to 196 receipts and 588 request executions and
continued with `delivery-string-context__then__play-blob-context`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 197 independently repeated the string-context Delivery and blob-context
Play headers without totals, three silent drains, and 13-row health. It
promoted with canonical golden SHA-256
`cbc4c22ee002145c71b9861a9770f7148c14d88304ddcc56295b16ba79a705ed`
and receipt SHA-256
`4aaa994e2882f2e27c35d3dd8f1f490b5f6bd0358179aa076486d2e7481cfa7e`.
It advanced partial authority to 197 receipts and 591 request executions and
continued with `delivery-string-context__then__play-string-content`. Preserve
its canonical golden, receipt, four health captures, and the partial summary
and matrix.

Pair 198 independently repeated the string-context Delivery header without a
total, the zero-row string-content Play menu, three silent drains, and 13-row
health. It promoted with canonical golden SHA-256
`be16ce4713bacfdd11e43a45da57884742a2be97e5987bbb3013ac0dfb25e1de`
and receipt SHA-256
`15a4b94c6d45936fdf96cdd0b620a364e9862f4ac0012da79b3c61ed8e0bca99`.
It advanced partial authority to 198 receipts and 594 request executions and
continued with `delivery-string-context__then__play-blob-content`. Preserve its
canonical golden, receipt, four health captures, and the partial summary and
matrix.

Pair 199 did not promote from generation `z39`. Its record run drained the
delayed `0x4000 [0x2102, 0]` frame from blob-content Play on the health
connection, while its cold repeat timed out at the same boundary. The
precursor response, successor response, and 13-row health request otherwise
matched exactly. Both protocol observations, the three available health
captures, and the complete service journal are quarantined under
`data/experiments/song-info-status-location2/malformed-history-lifecycle/attempts/delayed-frame-race-pair199-20261005T040132Z/`.
Its manifest hash-binds every artifact and records the restored `play-paths`
baseline, stopped synthetic identities, stopped isolated VM, and empty live
pair work slot. Preserve this failed attempt independently from the fresh
generation `z40` record/repeat. Unit
`codex-rekordbox-song-info-malformed-history-lifecycle-20261005z40.service`
(invocation `5f0a13d92b5d4e3595ea4c025264c950`) has a finite 30-hour runtime and
should be stopped after the lifecycle queue finishes or if it is explicitly
abandoned.

Generation `z40` independently recorded and repeated pair 199 from clean
fixture and process state. Both runs drained the delayed
`0x4000 [0x2102, 0]` frame from blob-content Play on the health connection,
then returned the normal 13-row health result. It promoted with canonical
golden SHA-256
`16d063ceb6339679fd77e8df39a8327e0cf08459696ed070933791117c6c4114`
and receipt SHA-256
`a44457a817ab1fbb678be4e04efdd390dd09a95870ebc217c367cb7711281c84`.
The reducer advanced partial authority to 199 receipts and 597 request
executions, with `delivery-string-context__then__play-zero-context` next.
Preserve its canonical golden, receipt, four health captures, and updated
partial summary and matrix.

`data/static-analysis/link-export-navigation-graph.json` is deterministic
host-side output from `tools/generate_link_export_navigation_graph.py`. It
creates no guest, network, service, or decrypted-database state. Regenerate it
after changing the request/database-path map, and retain it with the generator
and `conformance/test_link_export_navigation_graph.py`; it is documentation
evidence rather than runtime scratch. Its checksum entry should be added only
after the active real-Rekordbox queue reaches a stable checksum update point.

`REQUEST_SHAPES.md` is likewise deterministic host-side output, generated by
`tools/generate_link_export_request_shapes.py` from the navigation graph. It
includes per-position symbolic and literal declaration evidence, creates no
runtime state, and should be retained with its generator and
`conformance/test_link_export_request_shapes.py`. Regenerate the graph first,
then this document, after changing any suite declaration or database-path
classification. Defer both checksum-ledger additions while the live queue is
actively producing canonical evidence.

`data/device-behavior-matrix.json` is deterministic host-side output from
`tools/generate_device_behavior_matrix.py`. It reads canonical goldens and
summary/audit artifacts but creates no guest, network, or service state. Keep
it with `conformance/test_device_behavior_matrix.py`; regenerate after a device
oracle or provenance tier changes, and add its checksum only at the same stable
post-queue checksum update point as the navigation artifacts.

`DATABASE_FIELD_REFERENCE.md` and
`data/database/link-export-schema.json` are deterministic schema-only output
from `tools/generate_database_field_reference.py`. Generation opens the
encrypted full fixture read-only, decodes the SQLCipher key from the project
options file in memory, and retains neither the key nor options contents. The
generated table and semantic-field entries include their concrete request-kind
sets, and the inverse index covers every classified request kind. Keep both
outputs with `conformance/test_database_field_reference.py`;
they create no guest, network, service, or database mutation. Defer their
checksum-ledger entries until the active real-Rekordbox queue reaches the same
stable update point as the other generated indexes.

`ITEM_TYPE_REFERENCE.md` and `data/item-type-reference.json` are deterministic
host-side indexes generated by `tools/generate_item_type_reference.py` from the
canonical Rekordbox 7.2.19 golden corpus and the audited item-type domain. They
create no guest, network, service, or database state. Retain both outputs with
`conformance/test_item_type_reference.py`, regenerate them after changing a
row-bearing golden, and defer their checksum-ledger entries until the active
real-Rekordbox queue reaches a stable checksum update point.

`OBSERVED_RESPONSE_SHAPES.md` and `data/observed-response-shapes.json` are
deterministic host-side indexes generated by
`tools/generate_observed_response_shapes.py` from canonical Rekordbox 7.2.19
goldens only. Generation creates no guest, network, service, or database state.
Retain both outputs with `conformance/test_observed_response_shapes.py` and
regenerate them after promoting a golden. Failed attempts, `.next` candidates,
backend replays, and pre-request drain frames are excluded from request-reply
attribution. Pre-request drains remain in a separate asynchronous ledger, and
request, setup, render, and drain device coverage use only identity, status,
and setup fields already retained in each canonical golden. The generator also reads final JSON suite
declarations without executing them, records a separate declaration-corpus
hash, and associates every classified response gap with its exact declared
cases and suite files. Defer checksum-ledger entries while the live authority
queue is changing the corpus.
