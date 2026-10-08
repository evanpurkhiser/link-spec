# Experiment log

## 2026-09-29: Windows VM installation and library

**Question:** Can a self-contained Windows/rekordbox environment preserve a
research copy of the current library?

**Result [OBS]:** Windows 11 runs under KVM/QEMU in the pinned Dockur container.
rekordbox 7.2.19 is installed and signed by AlphaTheta Corporation. The guest
contains the 39,514,112-byte prepared `master.db`, 25,822 analysis/artwork files,
and a read-only track share at `Z:\tracks`. Preparation relocated 4,274 of 4,342
track paths; 68 unresolved rows are listed in the relocation report.

**UI observation [OBS]:** rekordbox reached Export mode and displayed 4,356
Collection tracks. A later machine audit proves that the source and relocated
databases each contain exactly 4,342 live rows with identical ContentID and
ContentLink populations. The extra 14 are confined to the initial desktop
UI/session state; its guest database and WAL were not retained, so the precise
UI-only source is unrecoverable. `LINK_EXPORT_NAVIGATION.md` records the bounded
interpretation and machine receipt.

## 2026-09-29: LAN-capable guest NIC

**Question:** Can Windows participate in a LAN broadcast domain while management
ports remain loopback-only?

**Result [OBS]:** Rootful Podman attaches the container to a management bridge
and a macvlan on `lan0`; QEMU uses a macvtap child with guest MAC
`02:cc:70:d3:5c:03`. Windows holds `10.0.0.96/24`. A host macvlan shim at
`10.0.0.63` supplies scoped DNS/forwarding. Guest ping, DNS, and internet access
worked; no USB device is attached.

This proves network capability, not Link Export activation. Physical RX3
exposure is excluded from subsequent tests. The topology must move to a private
synthetic-player segment before emitting discovery traffic.

## 2026-09-29: No-player Export baseline

**Question:** Does rekordbox expose Link Export without a player present, and
are the lower-left Export controls Link controls?

**Result [OBS]:** The two tested controls opened Mobile Library Sync and
"Connect to a mobile device" dialogs. No LINK source appeared, TCP 12523 was
closed, and the short control capture contained no PDJL activation exchange.
Artifacts were renamed `rekordbox-mobile-library-sync-popup.png`,
`rekordbox-connect-mobile-device-popup.png`, and
`rekordbox-mobile-controls.pcap` to avoid overstating them.

## 2026-09-29: Agent-independent lifecycle control

**Question:** Can routine VM/capture actions avoid Evan's SSH agent?

**Result [OBS]:** Fixed root-owned systemd units perform the privileged Podman,
network, DNS, and packet-capture work. A polkit rule authorizes user `evan` to
manage only `rekordbox-windows.service` and
`rekordbox-windows-capture.service`. `./vmctl start` and `./vmctl capture`
succeeded as the ordinary user without SSH-agent access.

The first bounded capture exposed an ownership bug: GNU `timeout` returned 124,
and `set -e` skipped `chown`. The helper now treats 124 as normal after handing
the file to `evan`; its installed copy was reconciled on September 30.
`rekordbox-no-player-5min.pcap` contains 3,695
packets and none on UDP 50000-50002 or TCP 12523, confirming the negative
no-player baseline.

## Existing exhaustive traversal imported

The September 28 traversal was normalized into this folder. It records 90 menu
nodes, 41 request signatures, 43 item types, all 20 root rows, and the confirmed
drilldowns summarized in `LINK_EXPORT_NAVIGATION.md`. This is the current live
behavior baseline until the isolated synthetic-client lab is ready.

## 2026-09-30: Isolated-network helper validation

**Question:** Does the installed host-only network fail closed before the
Windows oracle can transmit?

**Result [OBS]:** The first isolated start failed before QEMU launched because
the installed helper targeted a nonexistent `ufw-user-forward` chain. The
source helper now uses two exact rules in the standard `FORWARD` chain, has no
dependency on the iptables comment extension, and invokes its teardown path on
an `up` failure. The corrected helper is installed and survived a full service
restart. No isolated Link Export traffic was emitted during the failed start.

Windows was subsequently given `172.31.96.96/24` without a gateway. The address
is present in both ActiveStore and PersistentStore **[OBS]**.

## 2026-09-30: Guest-control bootstrap

**Question:** Can repeated guest operations use a persistent channel without
Evan's SSH agent?

**Result [OBS]:** A dedicated ED25519 key was generated under
`guest-control/state/`. `guestctl` uses `-F /dev/null`, forces
`IdentityAgent=none` and `IdentitiesOnly=yes`, and cannot fall back to host SSH
configuration or an ambient agent. The guest
bootstrap is designed to configure the built-in Windows OpenSSH server for
key-only access,
binds it to `172.31.96.96`, and limits the firewall source to host shim
`172.31.96.50`. Bootstrap is performed from the rootless QEMU user-network mode,
which has no physical-LAN broadcast attachment, with rekordbox closed.

The built-in capability, host keys, key-only config, authorized-key ACL, and
scoped firewall rule are installed **[OBS]**. The rootless QEMU network marks
`172.31.96.96` invalid because it is outside that temporary passt subnet, and
OpenSSH's debug mode confirms that this is the sole bind failure. `sshd` uses
delayed automatic start with bounded retries. The endpoint is not considered
verified until the isolated host helper is installed, the address becomes
valid on `rekordbox-lab`, the isolation gate passes, and `guestctl wait`
succeeds from the host-only bridge. Those checks now pass **[OBS]**.

## 2026-09-30: Isolated discovery and LINK activation

**Question:** Can a synthetic player activate real rekordbox Link Export
without any route to the physical RX3?

**Result [OBS]:** The private `rekordbox-lab` bridge has only one end of a
closed carrier veth as a member. Its peer is unattached and unaddressed. The
Windows guest has `172.31.96.96/24` without a default route; the host shim has
`172.31.96.50/32`; standard-`FORWARD` drops cover both directions. The isolation
gate passed before every oracle run.

The captured XDJ-RX3 keepalive shape was replayed as player 11, type 7,
generation 3, presence 2, peer count 1, and model code 0. Broadcast frames sent
by a host macvlan do not reach another child on this topology **[OBS]**. Sending
the same keepalive directly to `172.31.96.96:50000` in addition to broadcast
caused rekordbox to expose the large `LINK` source and open TCP 12523 **[OBS]**.
The direct packet remains on the same isolated bridge.

Before the user clicks `LINK`, the six-byte port query returns `0xffff` and no
dynamic dbserver can be used **[OBS]**. After the click, the UI shows player 1
above `LINK`, the query returns a dynamic TCP port, setup succeeds, and typed
menu requests are served **[OBS]**.

## 2026-09-30: Deterministic database baselines

**Question:** Does rekordbox preserve an installed encrypted fixture exactly
enough to use it as a behavioral oracle?

**Result [OBS]:** A normal startup imported eight bundled Groove Circuit WAVs
into both empty and full fixtures. The rows had `SamplerTrackInfo`, sampler
gain, `Loop Samples` genre, `GROOVE CIRCUIT FACTORY SAMPLES` album, and paths
under `Music\rekordbox\Sampler\GROOVE CIRCUIT\PRESET`. Removing the preset and
disabling both the Groove Circuit enable and visible-panel settings did not
prevent reprovisioning. Soft-deleting the imported rows caused rekordbox to
revive them on the next start.

Denying the Research user `Write` and `DeleteSubdirectoriesAndFiles` on the
`GROOVE CIRCUIT` parent prevented extraction and database insertion while
leaving rekordbox responsive **[OBS]**. `prepare-oracle.ps1` now preserves the
factory preset, creates an empty guarded directory, installs that narrow ACL,
and supplies a checked cleanup path.

rekordbox also creates root playlist ID `200000`, `CUE Analysis Playlist`, when
it is absent and resequences existing root playlists **[OBS]**. Every fixture
now includes that invariant with fixed values. The reachable empty profile has
zero tracks and exactly that one system playlist.

## 2026-09-30: First real conformance goldens

**Question:** Can the declarative runner record stable behavior from real
rekordbox through the complete network protocol?

**Result [OBS]:** With the XDJ-RX3 player-11 identity, the `full.json` suite
recorded 47 cases and an independent repeat verified all 47. The `empty.json`
suite recorded 21 cases and an independent repeat verified all 21. Both runs
used rekordbox 7.2.19, the real port-query listener, its returned dynamic
dbserver port, extended setup, and rendered typed menu messages. Goldens live
under `conformance/goldens/rekordbox-7.2.19/xdj-rx3/`.

The host shim now uses fixed MAC `02:00:00:60:00:50`. A complete isolated-VM
restart recreated that address, passed the gate, restored dedicated-key SSH,
and retained the guest ACL **[OBS]**.

## 2026-09-30: XDJ-RX3 versus CDJ-3000

**Question:** Does rekordbox serve different Link Export menus when discovery
classifies the client as an XDJ all-in-one rather than a CDJ?

**Result [OBS]:** The CDJ-3000 identity used player 1, keepalive device type 1,
presence 1, and model code 100. It activated Link Export on the same isolated
topology. rekordbox displayed a `MASTER` indicator and 120.00 BPM control beside
the CDJ player; the XDJ-RX3 presentation omitted those controls. Both UI states
are retained under `data/`.

The CDJ-3000 `full.json` run recorded 47 cases and independently repeated all
47. With the fixture, extended setup, root mask, and render form held constant,
its normalized behavior envelope is byte-for-byte identical to the XDJ-RX3
envelope. Sorted serialization of either envelope has SHA-256
`11f9f64344a85aab202ca2002dfb8cbe779e76e5a89b4d7c814d4b3baab396bf`.

This establishes a live UI classification difference and menu invariance for
the tested request surface. Later setup-width, mask, render, compatibility,
reconnect, eight-identity, and status-backed matrices cover the remaining
declared model rows. The decompiled `isAIO` caller belongs specifically to the
Display Song Info path, whose order difference is documented separately.

## 2026-09-30: Legacy setup exchange and row width

**Question:** What exact reply does rekordbox send to the one-argument setup,
and is the result affected by the RX3/CDJ discovery classification?

**Result [OBS]:** The one-argument request
`fffffffe:0000 [1]` received `fffffffe:4000 [0, 0x11]`. The two-argument
request `fffffffe:0000 [1, 0x14]` received
`fffffffe:0000 [0x11, 0x14]`. The runner now retains these typed transactions
in every golden instead of only validating and consuming them.

`legacy.json` recorded and independently repeated two cases under both the
XDJ-RX3 and CDJ-3000 discoveries. Track rows contained 12 arguments, including
their secondary key/BPM text and composite item type. Root mask `0x00ffffff`
returned 19 rows and included Hot Cue Bank. The two discovery identities had
identical normalized behavior, SHA-256
`5d6c4942accad219aa06b52082f173945b503eb66bbdea0fa9e89f0d28ef8e15`.

The suite held query device 1 and packed-context high byte 1 constant while
changing discovery player/model fields. This isolates discovery classification.
The retained physical RX3 capture closes the separate native-envelope question:
legacy setup device 11, packed-context requester 11, menu locations 1/3/5/8,
Rekordbox media slot 4, track type 1, root mask `0x05fdffff`, and six-argument
rendering. The deterministic
reducer and authority-only replay suite are
`data/experiments/physical-rx3-session/session-envelope.json` and
`conformance/suites/generated/physical-rx3-session-envelope.json` **[CAP]**.

## 2026-09-30: Extended request families

**Question:** Are the statically recovered Play Count, Prepare, Date Added, and
My Tag handlers reachable, and what do they render from the deterministic
database?

**Result [OBS]:** The first run exposed a harness bug rather than a rekordbox
allocation: an unavailable My Tag request returned `4000 [..., ffffffff]`, and
the runner treated that sentinel as 4,294,967,295 rows and attempted to
prebuild 1,431,655,765 three-row render requests. The transient service reached
10.2 GB before the kernel OOM killer stopped it. The runner now classifies
`ffffffff` as unavailable, caps automatic rendering at 100,000 rows, caps
undecoded input at 16 MiB, caps one render at 100,000 messages, and reports the
case ID before execution. The corrected run peaked at 207 MB.

All 21 populated cases then recorded and independently repeated. Play Count
returned selector IDs 0–7 with item type `0x2a`; Prepare used membership order
for sort 0 and reordered by Key when requested; Date Added returned five years,
numeric month/day rows of type `0x2e`, and `0xa0` ALL rows. My Tag mode 0
returned groups/leaves, while mode 1 and leaf-as-hierarchy-selector returned
the unavailable sentinel. Tags-on-track returned group+leaf pairs and treated
both untagged and unknown content IDs as empty menus. The canonical behavior
SHA-256 is
`85cf7627be2e5902017e841ceab9328ebfec71df88dddccf5a23e2c763692e0c`.

## 2026-09-30: Empty My Tag provisioning and extended families

**Question:** Is a database with zero `djmdMyTag` rows a stable empty oracle,
and how do the extended request families behave with zero tracks?

**Result [OBS, DB]:** The pre-start fixture contained zero My Tag rows. After
one startup, rekordbox had persisted 28 factory definitions: root groups
`Genre`, `Components`, `Situation`, and `Untitled Column` (IDs 1–4), plus 24
leaves with generated numeric IDs. The empty Link Export root returned those
four groups as `0x4a` rows. The stopped database, WAL, and SHM are retained as
`data/rekordbox-provisioned-empty-master.db{,-wal,-shm}`.

The builder now inserts the exact observed tree for the empty profile. After a
fresh start, all tables except `agentRegistry` matched the generated database;
that registry rewrote macOS source paths to Windows paths, timestamps, and an
opaque credential. Track count remained zero and all 28 My Tag rows were
unchanged. The new empty database SHA-256 is
`84e2fa7fed8b10fe184f098c6f1ae5fa06d12f3b1d6fd0a582404fd58790d59b`;
its logical fingerprint is
`2014daa8c58dcbc12d911b13e8dd52cebcaff5579f0001853f25a9db77cae664`.

The nine-case empty extended-family suite recorded and independently repeated.
Play Count, Prepare, Date Added years/tracks, and tags-on-track returned valid
zero-row menus. Date Added month and day each returned one `0xa0` ALL row. My
Tag root returned the four factory groups. Its canonical behavior SHA-256 is
`940ae06884f32bca34996d5b923f4f14a82b26167d8383ff6432fc3e30be74d4`.

Fixture activation now stops rekordbox in a separate `-StopOnly` invocation,
waits for guest SSH, and performs the database transaction with `-SkipStop`.
This removes the SSH interruption observed when shutdown and replacement shared
one remote PowerShell process.

## 2026-09-30: Canonical `rbxport` replay

**Question:** Can the same declarative suites run exhaustively against the
current `rbxport` implementation without discovery, NFS, media, or physical
network access?

**Result [OBS, RBX]:** A loopback-only adapter opened each encrypted fixture
read-only, built the real `rbl-link::IndexCatalog`, and served it through the
real `rbl-dbserver::CatalogHandler`. It bound only port query and RemoteDBServer
to `127.0.0.1`. All 19 retained rekordbox goldens completed, covering 291
case executions. No backend process remained afterward.

The tested dirty source tree is
`c144f19+tree.80e87ec8aace`, full SHA-256
`80e87ec8aacecbb46b9607e4fe196905039fa01aef0099992167bf9ec237309f`.
The manifest records the SHA-256 and size of every source file in the compiled
dependency closure. Actual envelopes, path-level diffs, logs, and summaries are
under the matching `conformance/results/rbxport/` directory.

The populated full suite matched outcome, total, and row count in 29 of 47
cases but was wire-exact in only History and the empty playlist. The empty
suite matched those three shape fields in 20 of 21 cases and was exact in 16.
The RX3 and CDJ-3000 shared suites produced identical `rbxport` behavior.

The first exploratory replay used Comment, the headless server's default, while
the fixture and oracle selected Key. The canonical replay explicitly selected
Key. Remaining track differences then isolated rekordbox's database key names
(`Am`, `C`) from `rbxport`'s Camelot display (`8A`, `8B`). Other measured gaps
include two extra numeric footer arguments, synthetic lookup IDs in place of
database IDs, missing populated Play Count/My Tag/Original Artist/Remixer
branches, Hot Cue Bank empty-versus-error behavior, search result construction,
legacy root composition, and playlist root ordering.

## 2026-09-30: Returned-selector chained navigation

**Question:** Do `rbxport`'s synthetic selector IDs remain usable when a player
feeds each returned ID into the next genre, artist, album, or label request?

**Result [OBS]:** Real rekordbox recorded and immediately repeat-verified the
16-case `chained-navigation.json` suite on the full fixture with the isolated
XDJ-RX3 player-11 identity. The suite SHA-256 is
`7e150fa4477c1aa3c8d2f0c345613977a39a768c06620a07b751ade518c55de2`.
The identical rbxport replay matched outcome, total, and row count in 14 cases.
The two differences were genre and label album menus using the ALL-artist
sentinel: rbxport returned an additional `Unknown` album row. Exact equality
was zero because selector values, extended footers, and Key strings differ.

## 2026-09-30: Capability, render, and transport oracle batch

**Question:** What does real rekordbox do across root masks, explicit sort IDs,
packed contexts, render shapes and overrides, invalid ranges, malformed
requests, framing errors, and simultaneous sessions?

**Result [OBS]:** Eleven additional XDJ-RX3/full-fixture suites, 126 cases in
total, were recorded and immediately repeated. Together with the earlier eight
goldens, the canonical rbxport replay now executes 291 cases across 19 suites.

The root sweep validated zero, every individual menu-item bit, legacy,
captured, and all-bit masks. The sort sweep returned all eight tracks for every
ID 0-17. Packed contexts accepted only requester byte 1, all tested menu
locations 1-8, and all tested slots 0-4. Requester bytes 2-6 timed out.

Under Default sort, five-, six-, and eight-argument renders all used the
database-selected Key secondary column. In eight-argument form, a zero gate ignored a nonzero
override but retained the database selection; nonzero gate plus nonzero
override selected IDs 2-17. This corrected the prior interpretation of the
field as a secondary enable/disable gate: it gates only the explicit override.

Pagination normalized `(0,0)` to the first row, clamped offsets 8 and 9 to the
last row, wrapped `(7,10)` to all eight rows, preserved overlap, and timed out
only for offset `ffffffff`. Request-shape and raw framing outcomes are detailed
in `PROTOCOL_REFERENCE.md` and retained byte-for-byte in their goldens.

The first concurrency design retained an unmeasured setup connection and used
a three-second burst deadline, producing scheduler-dependent transport
timeouts. The final suite closes the bookkeeping connection, releases twelve
identical workers from a barrier, uses a declared ten-second setup deadline,
stores raw worker observations, and compares a canonical multiset. All twelve
sessions returned eight rows in both oracle passes and the rbxport replay.

One setup contamination was caught before recording: restoring the factory
sampler preset caused rekordbox to provision eight bundled tracks, showing 16
instead of the fixture's 8. The reversible sampler guard was reapplied, the
fixture reinstalled, and only the clean eight-track launch was used. Cleanup
restored the original database and preset and removed both staging copies.

## 2026-09-30: Persisted secondary-column oracle sweep

**Question:** What exact Sort menu and track-row wire data does rekordbox serve
for every persisted secondary-column choice, including malformed zero- and
multiple-selection database states?

**Result [OBS, DB]:** Seventeen deterministic encrypted settings fixtures were
installed one at a time in the isolated Windows guest. The 15 valid variants
selected Artist, Album, BPM, Rating, Genre, Comment, Time, Remixer, Label,
Original Artist, Key, Bitrate, Color, DJ Play Count, and Date Added. Each valid
suite recorded the complete Sort menu and all eight track rows. The missing-
and multiple-selection suites each recorded all eight track rows. All 32 cases
matched an immediate repeat verification.

Each valid fixture selected its row, explicitly enabled it, and moved it to
sequence 20. Rekordbox moved an ordinarily visible row to the end of the
11-row menu; Comment, Time, Remixer, Original Artist, Bitrate, or Color became
visible as a twelfth row. Numeric
columns carried their raw database value in argument 0 and an empty argument
5. Lookup/string columns carried a raw ID in argument 0 and formatted text in
argument 5. Every packed type matched `(secondary_type << 8) | 0x04`.

With no selected row, rekordbox returned ordinary membership with title-only
`0x0004` rows, argument 0 zero, and empty argument 5. With both Comment and Key
selected, it chose Comment (`0x2304`) on both runs. The static query lacks
`ORDER BY`, so the latter remains an observed SQLite-layout result rather than
a general priority rule. `SECONDARY_COLUMN_ORACLE.md` records the complete
matrix.

One Genre attempt exposed a lifecycle issue: after a failed LINK activation,
rekordbox retained the departed synthetic player visually but did not
rediscover the same identity or reopen port query. Stopping rekordbox,
reinstalling the same fixture, relaunching, and emitting a fresh identity
restored deterministic operation. The noVNC page must remain connected; a page
reload immediately before the coordinate click can prevent mouse forwarding.

The canonical rbxport replay was expanded from 19/291 to 36 goldens/323 case
executions. Each settings replay now supplies its effective secondary column
and representable sort order. All 32 settings cases execute; 26 preserve
outcome, total, and row count; none is field-exact. Rbxport cannot represent an
absent secondary column or the six enabled non-default sorts, and its extended
argument 12, footer, Key spelling, and several formatter results differ.

### Category configuration oracle

The settings fixture generator produced every persisted category disabled
alone, a complete reversed sequence, and a special-bit control. Rekordbox
7.2.19 recorded and immediately repeat-verified all 24 cases in 23 suites on
the isolated XDJ-RX3 identity. Every visible category disappeared alone;
Folder was the sole no-op because it is already suppressed. Reversed `Seq`
became exact root order. Matching remained visible at `Disable = 2`, while
Track and Hot Cue Bank at `Disable = 1` stayed hidden under captured and
all-bits masks.

The canonical rbxport replay now covers 59 goldens and 347 cases. The category
suites contribute no field-exact cases and two same-shape cases: Folder's
no-op and reversed ordering. The adapter currently returns a fixed root rather
than consuming category visibility and sequence settings. Full artifacts and
the reproduction envelope are in `CATEGORY_ORACLE.md`.

### Sort visibility, hidden selection, and color oracle

All 17 persisted sort rows were toggled independently and repeat-verified.
Visible rows disappeared; the six hidden `Seq = 0` rows appeared before
Default. Complete sequence reversal produced the exact reverse visible order.
The hidden-selected Comment fixture proved that visibility bit 0 and selection
bit 1 are independent: Comment stayed out of the Sort menu and still rendered
on all eight track rows.

The custom-color fixture renamed IDs 1 and 8 to `Fixture Magenta` and `Fixture
Violet`. Both the Color root and track secondary values returned the configured
strings, including adjusted UTF-16 length fields. This tranche adds 20 goldens
and 22 cases, bringing the oracle to 79 goldens and 369 cases.

The rbxport adapter can express the 11 baseline sorts, ten removals, and their
ordering, but it cannot add the six hidden rekordbox sort types. Rbxport also
serves fixed Pink/Purple strings rather than `djmdColor` labels. After making
the 11-sort control explicit, 16 of the 22 cases preserve shape and none is
field-exact. `SORT_AND_COLOR_ORACLE.md` records the full matrix and evidence.

### Boundary, invalid-data, compatibility, and History oracle

Four deterministic encrypted fixture profiles exercised numeric limits,
malformed database values, file compatibility metadata, and UTF-16 width. Nine
suites added 99 oracle executions. Every suite was recorded through real rekordbox 7.2.19
and repeated after the required fixture reset; the History suite additionally
required a rekordbox restart because it mutates current-session state.

The 30-case numeric suite established BPM half-up grouping, release-year and
duration root ceilings that do not constrain direct drilldowns, and a DJ Play
Count mismatch in which selectors above 255 are advertised but narrowed to one
byte during selection. The deleted control row remained absent. The 15 invalid
queries retained null/empty/dangling track rows while filtering invalid values
from family roots. The eight lookup-backed secondary strings cap at 127
characters. Comment and Date Added each return total eight and then stall their
mixed-row render connection. Fresh-connection, direct-year cases isolate every
value: 256 ASCII characters succeed after truncation to 255, 255 UTF-16 code
units are preserved, and 256 UTF-16 units are the first repeatable render
timeout.

The compatibility fixture returned all eight metadata-only rows without media.
Track argument 10 was `0x100` for the four supported combinations and `0x101`
for both FLAC rows, high-rate WAV, and high-rate AIFF. This assigns bit 0 as the
tested compatibility-failure flag and agrees with the pinned decompiled branch.

The exhaustive follow-up records and independently repeats 382 metadata-only
rows under both extended and legacy setup. All 256 FileType bytes prove that
only 5 and 6 reject unconditionally. Fourteen wide controls prove signed-byte
narrowing, including 261/262 rejecting as 5/6 and 267/268 entering the 11/12
branch. Across 56 rate controls, types 11 and 12 accept only exact 44100 and
48000; types 5 and 6 reject every value. Fifty-six BitDepth controls preserve
the result across supported and rejected branches. The final partition is 298
supported and 84 unsupported rows, every legacy row is the exact first 12
arguments of its extended counterpart, and all four process phases retain one
responsive Rekordbox process with no Application events **[OBS, DB, DEC]**.

The ten-step History lifecycle created a date-named current-session history on
the first `3001`, preserved insertion order after the second, renumbered the
remaining row after `3401`, and removed the history after `3101`. Rekordbox
generates a different history ID on clean runs, so the harness executes with
the live ID and canonicalizes only saved typed-number occurrences. Rbxport
accepts the insert messages but never produces the root row; compare mode now
records the four dependent operations as `dependency_unavailable` and keeps the
semantic diff complete.

The canonical replay now covers 86 goldens and 436 cases. Thirty-seven are
field-exact and 265 preserve outcome, total, and row count. The detailed tables,
fixture hashes, and exact edge behavior are in
`BOUNDARY_INVALID_LIFECYCLE_ORACLE.md`.

### Named model, class, generation, and setup sweep

**Question:** Does discovery model, keepalive class, generation, or player
number change ordinary Link Export menus when the database and dbserver request
envelope remain fixed?

**Result [OBS]:** Six concrete models and one unknown control were exercised.
An additional unknown control separated mixer class 2 from DJM class 3. Together
the eight identities cover XDJ and non-XDJ model prefixes, CDJ/type-7/mixer/DJM
classes, generations 0/2/3, and discovery players 1-6 and 11. Rekordbox was
fully restarted between identities to clear discovery and AIO caches.

Every identity exposed LINK. For each identity, `full.json` recorded and
repeated 47 extended cases, `legacy.json` recorded and repeated two cases, and
`device-capabilities.json` recorded and repeated the three required masks plus
render arities 5/6/8. The compatibility fixture was then installed once and
its two menus recorded and repeated under every identity.
All extended behavior envelopes are identical with canonical SHA-256
`d8c262a03cb6d38a486bd096be3e2a196773d4c60fb407ebbc2d689f470404b5`;
all legacy envelopes are identical with SHA-256
`d9c5ccd1fefb28c14b40e6aee23d8519ff1947b56164c00db9d24fab4c74f181`.
All capability envelopes are identical with SHA-256
`0176da8936565b53d392d1c3050bf92776d611597850243dd78a7799939d3dc4`.
All compatibility envelopes are identical with SHA-256
`cab4d111a7f27985fe249a1ced865926383077baca2d4f1571493315d1ef0c98`.

A clean-process XDJ-RX3 root/track probe was also repeated after replacing the
identity with CDJ-3000 without restarting rekordbox. The first replacement
attempt after 12 seconds did not reopen the dbserver port before the runner
timeout. A fresh emission after a further 25 seconds succeeded, and both
before/after envelopes have SHA-256
`d3f39e6f494696a6dc2b619e3193cc840c47e84a2515e43aaa29078844eb2cfb`.
This establishes eventual same-process identity recovery while leaving the
precise internal timeout unassigned.

The declaration itself exposed a protocol constraint: the original
`unknown-fixture-model` name was 21 bytes and could not fit the 20-byte keepalive
field. It was replaced with the valid `UNKNOWN-FIXTURE` control. The checked-in
identity adapter rejects oversized names.

At this checkpoint the expanded backend replay covered 117 goldens and 828
cases, with 49 field-exact and 517 same-outcome/total/row-count cases. Every
identity had the same per-suite result as RX3 and CDJ-3000.
`DEVICE_MATRIX_ORACLE.md` records the identity table, hashes, and proof
boundary. The later status-backed Display Song Info experiment extends these
totals below.

### Supported settings refresh boundary

**Question:** Can Category, Sort, or Column settings change while Link is
active, and does a new Link session require restarting rekordbox to observe
their changes?

**Result [OBS]:** Preferences -> DJ System exposes Category, Sort, and Column.
During an active Link session all three tabs are darkened and overlaid with
`Not allowed while link is active.` Deactivating LINK unlocks them immediately.
The Column list contains the 15 modeled values plus Not Specified.

Three supported mutations were observed with Link inactive and consumed after
reactivation without restarting the application. Column changed from Key to
Comments and produced composite type `0x2304`. Album moved from Active to
Inactive Categories and disappeared from the exact 19-row root. Comments moved
from Inactive to Active Sort Options and appeared as the twelfth and final sort
row. The latter two captures share PID 8; their retained encrypted DB/WAL state
contains Album `(Seq=0, Disable=1)` and Comments `(Seq=12, Disable=0)`.
`SETTINGS_SESSION_REFRESH_ORACLE.md` records the concise declarations, exact
typed results, lifecycle proof, screenshots, database snapshot, validator, and
restoration boundary.

### Search construction and Category-domain gates

**Question:** How does `0x1300` match text, combine entity and content domains,
validate request fields, paginate results, and consume Category settings?

**Result [OBS, DB, DEC, RBX]:** A 44-case full-fixture suite and four 4-case
Category-fixture suites were recorded and immediately repeated. Search folds
ASCII case, splits on spaces, requires all tokens as order-independent
substrings, preserves non-ASCII code points, and returns mixed Artist, Album,
title-track, and file-name-track rows. Artist, Album, Track, and File Name
Category settings independently disable those four domains. Declared UTF-16
lengths below the encoded string are rejected with `0x0100`; larger lengths
are accepted. Search also exhibits zero-count-first-row and past-end-last-row
pagination normalization.

The pinned implementation confirms the token loop, Category jump table,
visible-track filter, content-ID deduplication, and 1,000-row wrapper ceiling.
A deterministic 1,005-track fixture then proved that ceiling live: the broad
query returns exactly rows 0001 through 1000, while narrow queries retrieve
rows 1001 and 1005. At/past-end single-row requests clamp to row 1000, and
overrun five-row windows right-align to rows 0996 through 1000. A second
focused fixture proves precomposed/decomposed distinctions, ASCII-only case
folding inside combining sequences, no `ß` expansion or dotted-I folding,
zero matches for exact supplementary-plane symbols, six-byte UTF-16 length for
one emoji plus its terminator, and first-NUL query termination. The seven
canonical suites add 95 cases. Rbxport replay found three exact and fourteen
same-shape cases; it exposes all 1,005 broad matches, applies broader Unicode
normalization/folding, treats emoji/NUL-only input as an empty filter, and
otherwise returns track-only results with different empty-query, token,
Category, malformed-length, and pagination behavior.
`SEARCH_ORACLE.md` contains the complete request/result tables, static trace,
artifacts, and remaining Search-specific boundaries.

### Search Track request, sort, and ceiling

**Question:** What is request `0x1500`, how does its sort field behave, and is
its larger result budget a global cap?

**Result [OBS, DB, DEC, RBX]:** Static formatter recovery establishes exactly
four arguments: context, sort ID, UTF-16 byte length, and query string. Live
Rekordbox accepts sorts 0-17, consumes the signed low byte, aliases 256 to 0,
and rejects 127/128/255 as unavailable. The eight-track fixture produces eight
distinct exact orders across the 18 sort IDs. Short declared lengths return
argumentless `0x0100`; a missing string yields an empty menu; an extra ordinary
Search flag is ignored.

A 5,005-track fixture proves default-sort Search Track truncates to 5,000 and
right-aligns at/past-end windows, while sort 17 returns all 5,005. A second
10,005-track fixture gives every sort a distinct title token: ordinary Search
returns 1,000, sort 0 returns 5,000, and every explicit sort 1-17 returns all
10,005. Immediate repeats match. A paired SearchStr-only fixture returns zero,
excluding `djmdContent.SearchStr` as a direct domain. The three canonical
suites add 65 cases. Across all ten Search suites, rbxport is exact on 23 of
160 cases and preserves outcome/total/row-count shape on 61.

### Rating, Bitrate, and Color selector domains

**Question:** Do scalar submenu roots and direct track selectors accept the
same value domains, and does every advertised selector reach its tracks?

**Result [OBS, DB, DEC, RBX]:** A 32-case full-fixture suite records direct
Rating 0-5, Bitrate 0/32/128/160/192/256/320/1411, Color 1-8, and absent or
maximum controls. Every valid selector returns exactly the expected content
membership. All 32 rbxport cases preserve outcome, total, and row-count shape;
ten are field-exact.

A second encrypted fixture stores Rating 99, Bitrate `INT32_MAX`, ColorID 0,
and dangling ColorID 999999. Rekordbox hides Rating 99 from its root but direct
selector 99 returns the track. It hides `INT32_MAX` and direct Bitrate also
returns zero. The Color root remains the fixed palette 1-8; direct Color 0
returns the unassigned track, while direct 999999 returns zero. All seven cases
repeat exactly. Rbxport is exact on one and preserves shape on three. The
machine validator and hashes are in
`data/experiments/scalar-selectors/summary.json`.

### Status-backed Display Song Info classification

**Question:** Can the model-dependent `getDispSongInf` branch be reached over
the real dbserver protocol, and which discovery message populates its model
cache?

**Result [OBS, DEC]:** Request `0x2002 [context, content_id]` returned a
16-field metadata menu. A keepalive-only XDJ-RX3/player-11 identity retained
ordinary ordering. Replaying the captured 292-byte RX3 player-status shape on
UDP 50002 caused the same request and player context to move Comment from
position 11 to position 6. Patching that status template to CDJ-3000/player-1
restored ordinary ordering. Every run was immediately repeated against the
same encrypted `full` fixture.

The four canonical Display Song Info goldens add 13 oracle executions. At this
checkpoint the expanded rbxport replay covered 121 goldens and 841 cases: 58
were field-exact and 530 preserved outcome, total, and row count. All nine
missing-content controls are exact; populated fixed-field rows and AIO order
differ. `DISPLAY_SONG_INFO_ORACLE.md` records every row and packet hash.

### Category flags in Display Song Info

**Question:** Does a persisted Category setting remove the corresponding
Display Song Info row, or alter its serialized state?

**Result [OBS, DEC]:** Each of the 21 one-category-disabled fixtures was
extended with a populated `0x2002` request. Real Rekordbox recorded and
immediately repeated every two-case root/display suite. The refresh runner
also compared the original root case before promoting each new golden, and all
21 roots remained exact.

Every Display Song Info response retained the same 16 rows and ordering.
Disabling Genre, Artist, Album, BPM, Rating, Year, Remixer, Label, Original
Artist, Key, Color, Time, or Bitrate changed only argument 0 of the associated
simple row from `1` to `0`. The other eight root categories, Folder, and
Matching left the complete display response unchanged. Comment and Date Added
already carry zero because their menu-item IDs have no persisted category rows
in the fixture. Static inspection confirms that the builder stores membership
in its enabled-MenuItemID vector as the simple row's argument-0 flag.

The corpus remains 121 goldens but expands to 862 recorded case executions.
The refreshed rbxport replay has 58 field-exact and 551 same-outcome/total/
row-count cases. All 21 new backend cases preserve the 16-row shape and none is
field-exact. `CATEGORY_ORACLE.md` contains the complete mapping.

### Display Song Info render, pagination, error, and legacy matrix

**Question:** Does request `0x2002` share ordinary track-list render semantics,
and how does it handle legacy setup, range boundaries, and malformed typed
arguments?

**Result [OBS]:** Four generated suites added 43 cases. Every case was recorded
from Rekordbox 7.2.19 on the isolated network and immediately repeated against
its candidate golden before promotion. The full fixture hash remained
`e8c45a7020a70103d6a15d5cf9aaa32a3d8c758c6c1f3f33b2a8d80872f7c812`.

Five- and six-argument renders and eight-argument renders with a zero gate
produce a title-only composite first row. Gate one with selector zero loads the
database-selected Key; selectors 2-17 map to the same secondary extractors as
ordinary track rows, including the selector-14 hole. Only the Title row changes;
the other 15 metadata rows are byte-identical.

Pagination is intentionally non-conventional. Count zero returns row zero;
offsets 16 and 17 clamp to row 15; offset 15 with count 18 resets to the complete
16-row list; overlapping windows retain the duplicate; offset `0xffffffff`
times out during rendering. The server's `0x4001` header reports each normalized
offset.

A request with no arguments times out. Missing or string content IDs return a
zero-row menu, an extra numeric argument is ignored, and a location-2 context
is accepted. String/blob contexts and a blob content ID return generic `0100`
with no arguments. Zero numeric context returns a zero-row menu. Legacy setup
preserves all 16 fields and ordinary ordering while narrowing every row from 16
arguments to 12.

The corpus now contains 125 goldens and 905 recorded cases. The canonical
rbxport replay has 65 field-exact cases and 584 with the same outcome, total,
and row count. Across the eight Display Song Info replays, 16 of 56 cases are
exact and 46 preserve shape. `DISPLAY_SONG_INFO_ORACLE.md` contains the complete
selector, range, error, and replay tables.

### Display Song Info field boundaries

**Question:** How does `0x2002` serialize null, dangling, numeric-edge, maximum
ASCII, and supplementary-Unicode values for every displayed field?

**Result [OBS]:** Three eight-track suites reused the deterministic boundary,
Unicode-boundary, and invalid fixtures. Four additional one-track profiles set
every string source to 254, 255, or 256 ASCII characters, or 128 supplementary
characters (256 UTF-16 units). All 28 real-Rekordbox cases returned complete
16-row menus and matched an immediate repeat.

Primary Title and simple lookup rows cap at 127 UTF-16 units. Comment and Date
Added cap at 255 UTF-16 units. Both can split a surrogate pair and expose
U+FFFD. The composite Title row's secondary Key text follows a distinct
127-Unicode-character limit and preserves 127 complete supplementary
characters. Display Song Info therefore does not reproduce the ordinary track
renderer stall at 256 UTF-16 units.

Null/empty strings remain present as empty row values. Dangling lookup IDs are
preserved numerically with empty text. Negative Length, BPM, and Release Year
become `0xffffffff`; Rating 99 and Bitrate `2147483647` survive. Color ID
999999 remains numeric and produces type `0x52` from its low byte. Malformed
Stock Date text is returned verbatim.

The corpus then contained 132 goldens and 933 recorded cases across 101 suite
files and 524 declarations. That replay had 65 exact and 612 same-shape cases.
All 28 new backend cases preserved their complete 16-row shape and none was
field-exact.

### Display Song Info status-shape/model consistency

**Question:** Does replacing only the model and player fields in the captured
RX3 status transport produce the `isAIO` ordering predicted by the model-prefix
predicate for other XDJ products?

**Result [OBS]:** Four fresh-connection suites exercised populated, deleted,
zero, and unknown content IDs. Canonical XDJ-XZ, XDJ-AZ, and XDJ-1000MK2
identities used requester 11 so the ordinary player-number rejection boundary
could not explain the result. All 12 requests timed out. The player-1
`UNKNOWN-FIXTURE` control returned an ordinary populated menu and three
ordinary zero-row missing-ID menus. Every candidate matched an immediate
repeat before promotion.

The result proves that an RX3-shaped status packet with one of those three XDJ
model names is insufficient for this API. It does not predict behavior from a
genuine status packet emitted by that model. The four status-packet hashes and
the earlier player-number controls remain in `DISPLAY_SONG_INFO_ORACLE.md`.

At this checkpoint the corpus contained 136 goldens and 949 recorded cases
across 105 suite files and 540 declarations. The canonical rbxport replay had
68 exact and 616
same-shape cases. Rbxport serves menus for the 12 Rekordbox timeout controls;
the unknown control contributes three exact missing-ID cases and one matching
populated shape.

### Play/Delivery Song Info sibling family

**Question:** What do the `0x2102` through `0x2602` sibling requests return,
how do rendering and pagination alter them, and do malformed forms expose
connection or parser state?

**Result [OBS, DEC]:** Five generated suites added 109 canonical cases. Play
Song Info (`0x2102`) returns seven rows; Delivery Info (`0x2602`) returns
thirteen. Deleted, zero, and unknown content IDs return zero-row menus. The four
intermediate recognized kinds return request-specific `4003` errors. Every
candidate matched an immediate independent repeat before promotion, and no
actual media file was present.

Play ignores all 21 tested render controls. Delivery uses the ordinary
secondary-selector map on its composite Title row. Its heterogeneous order
varied at each position in this original combined suite; the later controlled
order experiment proves the selector was not the cause. Both builders share Display Song
Info's non-conventional pagination: count zero returns row zero, end offsets
clamp, overrun resets to the complete list, overlap duplicates survive, and
maximum offset times out. Legacy setup keeps the seven/thirteen-row memberships
while narrowing rows to twelve arguments.

Cold and sequenced audits showed numeric zero context timing out for both
builders. A 28-case precursor bisection proved that only an immediately prior
blob-valued content ID changes the next zero-context request into a zero-row
menu. Two fresh-process prefix runs matched behavior SHA-256
`ed06d4efe39c1eb6f088822d0474b70dc2c6e46b119f0ec11f3cd1afe2e468fb`.
The broad first recording retained both the timeout and state-mutated result.

Static analysis recovered the active AppSync and fallback builders, their
content query, field sources, lookup tables, wrapper vtable offsets, and the
13-versus-19 Delivery insertion-path distinction. At this checkpoint the corpus
contained 141 goldens and 1,058 recorded cases across 110 suite files and 649
declarations. The canonical rbxport replay had 87 exact and 689 same-shape
cases.
`SONG_INFO_SIBLINGS_ORACLE.md` is the complete behavioral and static reference.

### Delivery-only field and string boundaries

**Question:** How do ComposerID, DeliveryControl, DeliveryComment, Lyricist,
and ISRC encode nulls, dangling lookups, case, ASCII limits, and split
supplementary characters?

**Result [OBS, DEC]:** Two eight-track encrypted profiles recorded and matched
fixture-reset-and-Rekordbox-restart repeats. Null and empty values collapse to
empty strings. A dangling ComposerID remains numeric with empty text. Composer
lookup text and Lyricist cap at 127 UTF-16 units; DeliveryComment and ISRC cap
at 255. Both limits can split a surrogate pair and expose U+FFFD. The row byte
lengths include the terminating UTF-16 NUL. DeliveryControl sets its wire flag
only when the value case-insensitively equals `ON`; `OFF` and mixed-case `Off`
remain clear.

The first same-process repeat was rejected rather than promoted: its first two
cases changed row order, while cases three through eight were exact. The repeat
continued a process-scoped four-order cycle despite identical render arguments.
The pair is retained under `data/experiments/song-info-delivery-boundaries/`.

Three follow-up suites repeated one request 16 times and ran all 21 controls in
forward and reversed order. Each suite matched a second cold-process run
byte-for-byte. Cold Delivery-only requests 1-3 use A, then B/C/D/A repeat.
Reversing the controls makes each selector inherit its new ordinal pattern
while preserving its composite value/type. Fresh connections do not reset the
state; process restart does. The original Play-then-Delivery suite contains
additional permutations.

Six 16-case follow-ups alternated one precursor family with one populated
Delivery probe and repeated exactly from separate cold processes. Missing
Delivery and recognized `0x2202` errors preserve the standalone probe sequence
`AAABCDAB`. Missing Display, missing Play, and populated Play force every
following probe to baseline A. Populated Display produces `AAEAEAEA`; its new
E permutation is
`0002 0f04 0023 000f 004f 0037 0007 000e 0006 0012 000d 0036 000b`.
The state is therefore shared builder/list-buffer state, not a single request
counter. Complete patterns, precursor results, reproducible analysis, and all
fifteen paired behavior hashes are retained in
`data/experiments/song-info-delivery-order/`.

Six same-socket companion suites were also recorded twice from cold processes.
Each holds one dbserver connection across all 16 cases. Every case array is
exactly equal to its per-case reconnect counterpart, including precursor
responses, complete row payloads, and pattern sequences. TCP connection
lifetime is not an input to the observed builder/list-buffer state **[OBS]**.

Two discovery-identity lifecycles then warmed Delivery with six calls
(`AAABCD`), removed the RX3 identity, and reintroduced either the same RX3 or a
CDJ-3000 without restarting Rekordbox. Both were repeated from separate cold
processes. The first query after 40 seconds of absence still timed out in all
automated runs; another 30 seconds and renewed emission reopened Link Export.
Every post-rejoin phase returned `ABCDABCD`, the exact continuation after call
six. Warm-up behavior SHA-256 is
`3b27099d46537d61fe3d9a2f2d4dc530d372ce36cfe7392468b24ba65867861e`;
post-rejoin SHA-256 is
`56132f1cea4b5f002555a5158e6da8a608f3f4ee4f402d7d4b37666140f9ba11`
for both identities and repeats. Discovery expiry and XDJ-to-CDJ model, class,
presence, and model-code changes do not reset Delivery ordering **[OBS]**.

At this checkpoint the corpus contained 143 goldens and 1,074 recorded cases
across 112 suite files and 665 declarations. The canonical rbxport replay has
87 exact and 705
same-shape cases; all 16 new cases preserve shape and none is field-exact.

### Status-backed Play and Delivery matrix

**Question:** Do the recovered Display AIO/model-cache branch or genuine player
status packets change Play/Delivery rows, rendering, pagination, setup width,
or malformed dispatch?

**Result [OBS, DEC]:** Five suites were recorded and independently repeated
under authentic RX3 player-11 status and the RX3-template-derived CDJ-3000
player-1 control. After normalizing only the requester byte, all 106 stable
cases per identity are
exact. Baseline, render, pagination, and legacy results also equal the ordinary
no-status oracle. No AIO classifier appears in either recovered builder.

The 14-case stable malformed core exposed one status-presence branch.
Argumentless Delivery times out under the ordinary identity, but both status
identities return an empty menu header that echoes Play kind `0x2102` for the
Delivery `0x2602` request. The other thirteen cases equal ordinary behavior.

The location/context forms remain ordered experiments. Two CDJ cold runs are
exact: zero-context Play is empty, location-2 Play has seven rows, and
location-2 Delivery has thirteen. Two RX3 runs with matched player-11 location
2 both return seven Play rows, while zero-context Play changes from timeout to
empty and Delivery changes from thirteen rows to empty. With the inherited
player-1 location-2 context, RX3 Play times out and Delivery remains empty.
This distinguishes requester mismatch from RX3 process-state variation.

`tools/summarize_status_siblings.py` asserts every canonical equality and
experimental outcome. At this checkpoint the corpus contained 166 goldens and
1,499 recorded cases across 130 suite files and 986 declarations. Its replay
at that checkpoint had 157 exact and 959 same-shape cases.

### RX3 status menu-location-2 bisection

**Question:** Which immediate request history makes matched player-11 Delivery
at menu location 2 return thirteen rows or an empty menu?

**Result [OBS]:** Seventeen declarations produced thirty-two successful
cold-process recordings, 496 completed case executions, and two expected
failure transcripts. All paired behavior envelopes are byte-identical. The
seven regular families repeat eight times each: no precursor, zero-context Play,
primary/location-2 Play, primary/location-2 Display, and primary Delivery all
leave the following `0x0b020301` Delivery total at 13.

The seven regular families were also repeated twice with one dbserver socket
per suite. Every case result and setup exchange equals the reconnect control,
including the Delivery probe after each Play timeout. The malformed shared-
socket suite reaches the wrong-typed string-context Play request, after which
Rekordbox closes dbserver before the paired Delivery probe completes. Both cold
attempts terminate at the same boundary.

A 16-precursor malformed bisection repeats exactly. Only a blob content ID sent
to Play or Delivery makes the immediate next location-2 Delivery menu empty;
all fourteen other malformed forms leave it at 13. The older broad sequence
shows that a longer malformed history can suppress this direct effect in one
cold state, so the focused result is a direct-precursor rule rather than a
claim that earlier history is irrelevant.

The first two recordings intentionally retain a declaration error as a useful
render control: their menu requests use location 2, advertise total 13, then
their default-location-1 render requests time out on all eight cases. The
corrected header-only pair records eight 13-row headers without rendering.

`tools/summarize_status_location2.py` verifies declaration hashes, repeat
equality, reconnect/shared-socket equality, the expected connection cutoff,
every expected outcome, and the render control. Artifact roles and hashes are in
`data/experiments/song-info-status-location2/README.md`.

### Play path, cloud identity, and file state

**Question:** Which `djmdContent` path/cloud fields and host file states alter
Play Song Info's path row or suppress the menu?

**Result [OBS, DEC]:** A fourteen-track encrypted fixture was recorded and
then repeated from a fixture reset and independent Rekordbox process. All
behavior matched. Null and empty `FolderPath` suppress the complete menu.
`FileSize` is serialized modulo `2^32`; null maps to zero. `HotCueAutoLoad`
tests string nonemptiness, so null and empty map to zero while `OFF`, `0`, a
space, `ON`, `on`, and Unicode all map to one.

For a positive cloud `ServiceID`, matching local and master DBIDs plus an
existing regular `OrgFolderPath` selects the original path. A zero-byte file
passes, while an existing directory fails and enters cloud fallback. The
fallback can concatenate the AppData cloud base directly with an absolute
`C:/...` path. Paired schema `ContentLink` values 0 and `0x80` have equal path
fields in the active configuration.

`PLAY_SONG_INFO_PATH_ORACLE.md` contains the complete input/output matrix,
reconstructed control flow, fingerprints, rbxport differences, reproduction,
and cleanup. `tools/summarize_play_paths.py` validates the retained golden.

### Smart playlist rule and membership precedence

**Question:** Does Link Export serve an intelligent playlist from
`djmdPlaylist.SmartList`, from materialized `djmdSongPlaylist` rows, or from a
startup-generated cache?

**Result [OBS, DB, DEC]:** The `smart-playlists` fixture contains five root
leaves. Two Attribute 4 rows carry the same valid House rule: one has no
membership, while the other deliberately contains only two Techno tracks.
Other controls combine Attribute 4 with malformed XML, Attribute 4 with a null
rule, and Attribute 0 with a valid rule. The malformed and null controls have
stored membership rows so an implementation cannot pass by treating empty
rules as ordinary playlists.

Real Rekordbox returns the four House tracks for both valid Attribute 4 rows.
It returns zero for malformed and null Attribute 4 rules despite their stored
memberships, and zero for the rule-bearing Attribute 0 row without membership.
All five root leaves render as ordinary playlist type `08`; `folder_flag = 1`
returns zero children for each. The copied database after startup and the
first repeated oracle is byte-identical to the generated source
(`2b2a5ca560be7190931ca31a1bcad3c47e00b70e3e652dde46d71d600a2e9ab8`),
excluding persisted membership regeneration as the explanation.

The canonical 12-case suite was recorded and immediately repeated after its
assertions were tightened. Rbxport replays six cases exactly and seven with the
same outcome/total/row-count shape. Its Link Export catalog follows stored
membership: rule-only is empty, contradictory membership returns Techno, and
malformed/null rules expose their stored rows. This differs from rbxport's
separate smart-rule parser and identifies the missing integration boundary.

`tools/summarize_smart_playlist_oracle.py` verifies suite/golden/fixture hashes,
root row types, every precedence result, the unchanged database, and the
rbxport comparison. The machine summary is
`data/experiments/smart-playlists/summary.json`. Static artifacts preserve the
Link wrapper/rowset path and the distinct desktop smart-list getter.

At this checkpoint the corpus contained 167 goldens and 1,511 cases. Its
rbxport replay had 163 exact and 966 same-shape cases.

### File Name formatting and UTF-16 boundaries

**Question:** Does `1013` derive display text from a path or short filename,
strip extensions, normalize Unicode, and where does its primary-string width
limit fall under every requested sort?

**Result [OBS, DB]:** A 20-row fixture makes `FileNameL`, `FileNameS`, and all
three path fields disagree. It covers null, empty, case, leading/trailing and
multiple dots, absent extensions, forward/backslash separators, composed and
decomposed accents, a supplementary character, embedded NUL, and ASCII/non-BMP
values at 254, 255, and 256 UTF-16 units. The 18-case suite requests every sort
ID 0-17 and was immediately repeated exactly.

Every row uses `FileNameL` as primary text. Extensions and separators remain
literal; embedded NUL truncates; null and empty both become an empty string.
The wire preserves 254 and 255 units, then caps at 255. A 256-unit ASCII string
loses its last character. A 256-unit string of supplementary characters is cut
between surrogate halves, and the final half-pair becomes U+FFFD. Argument 2
equals twice the rendered UTF-16-unit count plus the terminating NUL. The 18
sorts form nine exact order classes while retaining identical ID-to-label
mapping.

Rbxport preserves menu shape for all 18 cases and is exact for none. It returns
the full 256-unit values and differs in ordering, Key display, extended fields,
and footers. `tools/summarize_filename_oracle.py` verifies every rendered
label, byte length, ordering class, provenance hash, and replay result; its
machine summary is `data/experiments/filename/summary.json`.

At this checkpoint the corpus contained 168 goldens and 1,529 cases. The
canonical rbxport replay had 163 exact and 984 same-shape cases.

### Smart rule operator, grouping, and parser matrix

**Question:** Once Attribute 4 selects `SmartList`, which operator codes,
nesting rules, and root attributes does the Link Export evaluator honor?

**Result [OBS, DB]:** The `smart-rule-matrix` fixture adds 39 intelligent
playlists with no materialized membership over eight controlled tracks. Eleven
Genre rules and eleven decimal-BPM rules exercise every operator code. The
remaining rules cross all/any, two nested shapes, empty groups, unknown
operator/property, a condition outside the root, two roots, missing/unknown
logic, `AutomaticUpdate` zero/absent, and root Id mismatched/absent.

Genre codes 1, 2, 8, 9, 10, and 11 behave as equal, not-equal, contains,
not-contains, starts-with, and ends-with. Codes 3-7 return empty on Genre.
The two nested cases were initially attributed to recursive evaluation. The
later XML structure matrix and direct `getSmartlistNode` disassembly prove the
nested `NODE` is ignored; each result comes entirely from its direct sibling
condition. Empty all and any groups both return empty. The first of two roots
wins; missing, zero, and unknown root logic all
behave as all-of. Root Id and `AutomaticUpdate` do not change results.

The decimal BPM probes expose the storage scale. Against values 12000-12350,
`121.5` is below every row: equality is empty, not-equal and greater-than admit
all rows, and less-than/range are empty. The evaluator does not multiply the
XML value into hundredths. The following stored-scale numeric profile supplies
the exact range-inclusivity and invalid-conversion results.

The exact 39-case suite passed during canonical recording and its immediate
repeat. Rbxport is exact for the 19 empty-result controls and diverges for all
20 nonempty results because its Link Export path does not call the separate
smart evaluator. `tools/summarize_smart_rule_matrix.py` validates every ordered
set and writes `data/experiments/smart-rule-matrix/summary.json`.

At this checkpoint the corpus contained 169 goldens and 1,568 cases. The
canonical rbxport replay had 182 exact and 1,003 same-shape cases.

### Smart stored-numeric comparison and conversion matrix

**Question:** What units and inclusivity do numeric conditions use, and how
does the evaluator handle reversed ranges, blanks, invalid text, negatives,
and values outside signed 32-bit?

**Result [OBS, DB]:** The 60-playlist `smart-numeric-matrix` has no materialized
membership. It crosses operator codes 1-5 over BPM, Rating, Play Count,
Duration, and Year, then adds reversed ranges, empty and malformed text for
equality/inequality, plus negative and above-`INT32_MAX` BPM thresholds.

Codes 1 and 2 are equality and inequality. Codes 3 and 4 are strict greater
and strict less. Code 5 includes both ordered endpoints. Every reversed range
returns empty rather than swapping bounds. Empty and `not-a-number` values both
coerce to zero: the controlled zero Rating rows 10001/10007, Play Count row
10001, and Year row 10001 prove this directly. BPM and Duration have no zero
row and therefore return empty for zero equality.

Negative values preserve sign. With every BPM positive, `> -1` returns all
eight rows and `< -1` returns none. `2147483648` remains a positive value above
every BPM, so `< 2147483648` returns all rows; it does not wrap through signed
32-bit. Both ordered extreme ranges contain no controlled row.

The exploratory 60-case result repeated exactly. After every ordered set was
promoted into the declaration, the canonical golden and immediate repeat also
passed all exact assertions. The first canonical LINK click timed out, and the
recorder's single bounded retry succeeded without leaving a partial golden.

Rbxport is exact for 15 empty-result controls and differs for all 45 nonempty
results because Link Export still bypasses its rule evaluator. The validator
`tools/summarize_smart_numeric_matrix.py` writes the provenance-bound summary
at `data/experiments/smart-numeric-matrix/summary.json`.

### Smart numeric database conversion boundaries

**Question:** How do SQL `NULL`, fractional SQLite REAL values, wide stored
integers, fractional rule text, and omitted numeric attributes enter each
SmartList numeric comparison path?

**Result [OBS, DB, INF]:** The `smart-numeric-boundaries` fixture stores ten
controlled values identically in BPM, Rating, Play Count, Duration, and Year.
The 100 rules cross zero and fractional comparisons, inclusive ranges,
`INT32_MAX`/`UINT32_MAX` thresholds and their successors, and missing left or
right XML values across all five properties. Direct encrypted-database checks
confirmed the intended null, integer, and REAL storage classes.

The live result separates three comparison domains. BPM treats null, 0, 0.5,
-0.5, and `UINT32_MAX + 1` as zero, accepts 1.5 and `INT32_MAX` as positive,
and excludes -1, `INT32_MAX + 1`, and `UINT32_MAX`. Rating has a zero class
that also contains both successor values, a positive 1.5 row, and a negative
class containing -1, `INT32_MAX`, and `UINT32_MAX`. Play Count, Duration, and
Year share Rating's zero class but treat -1, `INT32_MAX`, and `UINT32_MAX` as
positive. Signed-low-byte and unsigned-like labels explain the partitions but
remain an inference; the exact ordered row sets are the oracle.

Rule text `0.5` and a missing `ValueLeft` are equivalent to explicit zero.
Missing range endpoints also become zero. Every tested positive rule threshold
from `INT32_MAX` through `UINT32_MAX + 1` equals the stored BPM `INT32_MAX`
row, establishing saturation rather than wraparound.

The exploratory 100-case result repeated exactly. The symbolic suite promoted
from it then recorded and immediately repeated as a canonical golden. The
first probe required all six bounded activation attempts before LINK appeared;
the canonical run succeeded on its first recording attempt. Both EXIT paths
restored `play-paths`. Rbxport is exact for 29 empty controls and differs for
71 populated cases. `tools/summarize_smart_numeric_boundaries.py` validates
all partitions and writes the provenance-bound machine summary. The complete
corpus now contains 189 goldens and 2,327 cases; 365 are field-exact and 1,186
preserve outcome, total, and row count.

### Smart property vocabulary and storage mapping

**Question:** Which property names does a Rekordbox-written SmartList use,
which database fields do they read, and what ID representation does My Tag
expect?

**Result [OBS, DB]:** The 33-playlist `smart-property-matrix` covers all 23
property names in the written vocabulary and six alias/representation
controls. Its eight tracks carry deliberately conflicting scalar, lookup,
date, audit, subtitle, filename, and tag values. No smart playlist has a
materialized membership row.

All 23 canonical names produce their controlled set. `dateCreated` reads the
track `DateCreated` field, while a rule matching the conflicting `created_at`
audit timestamp is empty. `mixName` reads `Subtitle`; `producer` reads the
composer/producer lookup. Raw custom My Tag IDs 8502 and 8504 return the exact
stored memberships, while their signed values after subtracting 2^32 return
empty. Lowercase `filename` works alongside `fileName`. The aliases `title`,
`color`, `playCount`, `remixer`, and `composer` return normal empty menus.

The exploratory capture repeated all 33 cases. The exact declaration then
passed canonical recording and an immediate repeat. Rbxport is field-exact for
the eight empty controls and returns empty for all 25 nonempty Rekordbox cases
because Link Export still bypasses its SmartList evaluator. The validator
`tools/summarize_smart_property_matrix.py` writes the provenance-bound summary
at `data/experiments/smart-property-matrix/summary.json`.

### Smart fixed-date comparison matrix

**Question:** Do the three SmartList date properties share comparison
semantics, are range endpoints inclusive, and how do blank or malformed track
dates participate?

**Result [OBS, DB]:** The 30-playlist `smart-date-matrix` applies operators
1-5, a reversed range, blank equality/inequality, and malformed
equality/inequality independently to `stockDate`, `dateCreated`, and
`dateReleased`. The eight controlled rows span 2024 leap day, month and year
boundaries, a blank value, and `not-a-date`. No playlist has materialized
membership.

All three properties agree. Codes 1 and 2 are equality and inequality; codes
3 and 4 are strict later-than and earlier-than; code 5 includes both ordered
endpoints. Reversing the endpoints returns empty. Blank and malformed track
values are excluded from both equality and inequality. A blank or malformed
rule value returns empty for equality and admits only the six parseable dates
for inequality.

The exploratory capture repeated all 30 results exactly. The exact declaration
then passed canonical recording and an immediate repeat. Rbxport is exact for
the nine empty controls and returns empty for all 21 populated oracle cases
because Link Export still bypasses its evaluator. The validator
`tools/summarize_smart_date_matrix.py` writes the provenance-bound summary at
`data/experiments/smart-date-matrix/summary.json`.

The expanded corpus contains 176 goldens and 2,023 cases. The canonical
rbxport replay has 276 exact and 1,097 same-shape cases.

**Question:** How do relative-date operators 6 and 7 interpret units, counts,
calendar boundaries, invalid dates, future dates, and `ValueRight`?

**Result [OBS, DB, DEC]:** The guest clock was fixed at
`2032-03-31T12:00:00-04:00` while the 56-playlist
`smart-relative-date-matrix` exercised all three date properties. The ten
tracks span today, day/week/month/year and leap-day boundaries, tomorrow,
blank, and malformed values. Every declaration passed an immediate repeat.

Only case-insensitive singular `month` uses calendar-month arithmetic. All
other unit spellings use the day helper. Counts 2 and 31 expose strict lower
day boundaries; two months exposes the calendar-month boundary. Zero,
negative, blank, malformed, and fractional counts share the zero-count result.
`ValueRight` is ignored. Operator 6 admits tomorrow; blank and malformed track
dates match neither operator.

The disassembly in
`data/static-analysis/smart-condition-evaluator.disasm.txt` independently
shows the `month` comparison and `pastMonthToDay`/`pastDayToDay` dispatch. The
wrapper restored current Eastern time and the `play-paths` fixture after the
canonical recording. Its `clock.log` retains all three states. The 56-case
rbxport replay has zero exact and zero same-shape cases because the Link Export
playlist path does not invoke its SmartList evaluator. The validator
`tools/summarize_smart_relative_date_matrix.py` writes the complete sets and
provenance hashes to
`data/experiments/smart-relative-date-matrix/summary.json`.

### Smart fixed-date format matrix

**Question:** Which exact strings enter Rekordbox's fixed-date comparison
domain, and does it validate separators, digits, or calendar ranges?

**Result [OBS, DB, DEC]:** The 40-track `smart-date-format-matrix` applies 38
equality strings and one canonical inequality rule to each of `stockDate`,
`dateCreated`, and `dateReleased`, for 117 playlists. Embedded-NUL and SQL
`NULL` rows are additional track-only controls. No playlist has materialized
membership. The canonical recording and its immediate repeat agree on all 117
ordered results.

All three properties are identical. Exactly ten characters are required.
Positions 4 and 7 are ignored, so hyphen, slash, dot, space, ASCII letters,
Greek omega, and newline separators all normalize to the same January 31
value. Consumed positions are not digit-checked. Invalid leap days, February
30/31, April 31, month 0/13/99, day 0/32/99, and `202A-01-31` each produce a
parseable normalized day. Wrong lengths, timestamps, surrounding spaces,
arbitrary letters, all-zero/fullwidth digits, signed years, empty, embedded
NUL, SQL `NULL`, epoch, pre-epoch, year zero, and year 9999 do not enter the
measured comparison domain.

The complete `db::dateToDay` body at `0x102335b20` independently shows the
length gate, the eight consumed positions, the two skipped positions, raw
character arithmetic, time-runtime conversion, and nonpositive-result gate.
`data/static-analysis/smart-date-conversion.disasm.txt` also preserves the
relative month/day helpers. `tools/summarize_smart_date_format_matrix.py`
validates every live row set and writes provenance hashes to
`data/experiments/smart-date-format-matrix/summary.json`.

Rbxport returns empty for all 117 cases. Its 54 exact results are empty
controls; all 63 populated Rekordbox results diverge. The full corpus now has
176 goldens and 2,023 cases, with 276 field-exact and 1,097 same-shape cases.

### Smart text collation matrix

**Question:** What equality classes and substring boundaries does Rekordbox
apply to SmartList text rules, including Unicode, expansions, empty/null, and
embedded-NUL values?

**Result [OBS, DB, DEC]:** The 43-track `smart-text-matrix` applies operators
1, 2, and 8-11 to Comments values spanning ASCII case, precomposed and
decomposed accents, width, kana, Greek sigma, Turkish I, sharp-S and AE
expansions, combining-mark order, punctuation, whitespace, XML entities,
supplementary emoji, empty, SQL `NULL`, and embedded NUL. Its 55 declarations
have no materialized playlist membership. The exploratory recording repeated
all cases, and the promoted exact suite passed both canonical recording and an
immediate repeat.

The `Alpha` equality class contains case variants, the tested precomposed and
decomposed accented candidates, diaeresis, fullwidth text, the two Angstrom
forms, a trailing combining-mark candidate, and `Alpha` followed by embedded
NUL data. A rule that itself contains combining marks returns empty, including
the byte-identical candidate and both tested combining orders. Hiragana and
katakana compare equal. Uppercase sigma, normal sigma, and final sigma compare
equal. Dotted Turkish I joins ASCII I, while dotless I remains distinct.

Expansion matching is directional: a `straße` rule admits both `straße` and
`STRASSE`, while a `STRASSE` rule admits only the expanded spelling; the AE
ligature behaves the same way against AETHER. Punctuation and whitespace are
significant. Tabs and newlines match their own rows rather than spaces. XML
entities decode before comparison, and emoji work in exact, contains, prefix,
and suffix positions. Stored text is truncated at embedded NUL. Empty equality
admits empty and SQL `NULL`, empty inequality admits all 41 nonempty rows, and
empty contains/not-contains/starts/ends all return empty.

`data/static-analysis/smart-collation.disasm.txt` independently shows ICU 51
`StringSearch` construction with the US locale, primary collator strength, and
the equality/contains/prefix/suffix boundary helpers. The validator
`tools/summarize_smart_text_matrix.py` binds every asserted set to fixture,
suite, golden, and replay hashes. Rbxport returns empty for every case: eight
empty controls are exact and all 47 populated Rekordbox results diverge. The
complete corpus has 176 goldens and 2,023 cases, with 276 field-exact and
1,097 same-shape results.

### Smart string-property cross

**Question:** Do lookup-backed SmartList strings use the same collation and
empty/null behavior as direct content fields, or does each database path have
property-specific semantics?

**Result [OBS, DB]:** The ten-track `smart-string-property-matrix` assigns the
same value sequence to nine lookup-backed properties (`artist`, `album`,
`albumArtist`, `originalArtist`, `producer`, `genre`, `key`, `label`, and
`remixedBy`) and four direct properties (`comments`, `fileName`, `mixName`, and
`name`). Its 104 rule-only playlists cross equality, inequality, contains,
not-contains, prefix, suffix, empty equality, and empty inequality over all 13
properties. An empty lookup-name row and a zero/missing lookup relation are
paired with direct empty-string and SQL-`NULL` controls.

All 13 properties return identical ordered sets for every rule. Case,
precomposed accent, candidate-side decomposition, and fullwidth variants form
the same five-track equality class. Contains adds both longer boundary values;
prefix and suffix select their corresponding longer value. Nonempty
not-contains returns only `Beta`. Empty equality returns both the empty and
missing/null tracks, while empty inequality returns all eight nonempty tracks.
The missing relation also participates in nonempty inequality and is excluded
from nonempty not-contains exactly like SQL `NULL`.

The loose exploratory recording repeated all 104 cases. The same sets were
promoted into the exact declaration, and the canonical golden passed another
immediate repeat. `tools/summarize_smart_string_property_matrix.py` validates
the shared-set invariant and all provenance hashes. Rbxport returns empty for
every rule, yielding zero exact and zero same-shape cases. The complete corpus
is now 176 goldens and 2,023 cases, with 276 field-exact and 1,097 same-shape
results.

### Smart My Tag operator and signed-boundary matrix

**Question:** Which SmartList operators apply to `myTag`, how is the XML value
converted to a database tag ID, and how do multiple positive and negative tag
conditions compose?

**Result [OBS, DB, DEC]:** The eight-track `smart-mytag-matrix` assigns tag IDs
0, 1, `INT32_MAX`, `0x80000000`, and `UINT32_MAX` singly and in overlapping
pairs, plus one untagged control. Forty-nine rule-only playlists sweep
operators 1-11, signed and unsigned boundary spellings, overflow, blank,
malformed, padded, prefixed, and comma-suffixed input, ignored `ValueRight` and
`ValueUnit`, and six all/any multi-condition forms.

Only operators 8 and 9 produce populated results; they mean membership and
non-membership. Raw positive values above `INT32_MAX` saturate to
`INT32_MAX`, including 2147483648, 4294967295, and 4294967296. `-1` preserves
the `UINT32_MAX` bit pattern and `-2147483648` preserves the high-bit tag ID;
negative underflow saturates to `INT32_MIN`. Blank produces empty results for
both operators, while malformed nonblank text and `0x1` become zero. Leading
zeroes, plus signs, surrounding spaces, and a leading decimal before a comma
are accepted. Right and unit attributes are ignored. All/any groups compose
the individual membership predicates without merging tag operands.

The exploratory run recorded and repeated all 49 cases. The exact promoted
suite then passed a canonical recording and immediate independent repeat. Its
database SHA-256 is
`3a4a804f062488b0c5c1285cbbb1fef0cc96c1ff355bad0906c29d2064d42728`;
the logical fingerprint is
`1bf993c2ad6ce52d30b454675f0ddecfdb7fc1ccf74cf4a674b6a276549a4861`.
One earlier invocation exhausted six bounded LINK UI activation attempts and
wrote no partial golden; its EXIT trap restored `play-paths`. The successful
run used the unchanged inputs and performed the same cleanup.

The decompiled `db::operate` body independently dispatches property type
`0x40`, accepts only operators 8/9, and reads the track tag array/count at
offsets `0x440`/`0x44c`. The `myTag` parser branch calls JUCE
`XmlElement::getIntAttribute`, explaining the signed conversion. The validator
`tools/summarize_smart_mytag_matrix.py` binds these addresses and every ordered
set to the fixture, suite, golden, and replay hashes.

Rbxport returns empty for all 49 declarations: the 12 empty Rekordbox controls
are field-exact and same-shape, while all 37 populated results diverge. At this
checkpoint the corpus contained 177 goldens and 2,072 cases; 288 were
field-exact and 1,109 preserved outcome, total, and row count.

### Smart XML document and direct-child parser matrix

**Question:** Which XML document forms reach the SmartList evaluator, how are
root/condition attributes parsed, and are nested nodes recursive?

**Result [OBS, DB, DEC]:** The eight-track `smart-xml-matrix` adds 73 rule-only
playlists covering case variants, declarations, comments, processing
instructions, whitespace, quoting and attribute order, character references,
empty/truncated/mismatched documents, namespaces and wrappers, nested/unknown
children, multiple roots, leading/trailing text and NUL, missing/blank/invalid
attributes, signed and padded integers, duplicate attributes, and ignored
condition content.

Only direct `CONDITION` children of the first case-insensitive `NODE` root are
collected. Nested `NODE`, wrapper, and unknown children are ignored. A root
with no valid direct condition returns an ordinary empty menu. Element names
and property values are case-insensitive; attribute names are case-sensitive.
Missing, blank, and invalid logical values become all-of after a condition is
accepted. Duplicate attributes use the first value. Signed, padded, and
leading-zero integer spellings are accepted.

Declarations, comments, processing instructions, whitespace, single quotes,
reordered attributes, numeric character references, the first of two roots,
trailing text, and trailing NUL are accepted. Leading BOM/text/NUL, namespaces,
unknown/invalid entities, wrappers, and the measured incomplete forms return
empty. The measured mismatched root close is accepted by the pinned JUCE
parser. Every parser failure remains a normal menu response.

`db::getSmartlistContentData` at `0x102334b00` calls JUCE XML parsing and then
`db::getSmartlistNode` at `0x102335130`. The latter walks the direct-child list,
compares only `CONDITION`, calls `getSmartlistCondition`, and contains no
recursive node-parser call. Its final block rejects zero conditions and
rewrites logic outside 1/2 to 1. The live results and disassembly therefore
correct the earlier interpretation of the two nested cases.

The exploratory v1 fixture is retained because its one-condition logical
operator probes could not distinguish all-of from any-of. The corrected v2
fixture recorded and repeated all 73 exploratory cases, then the exact suite
passed canonical recording and an immediate independent repeat. The fixture
database SHA-256 is
`f5a1179c0f37b1616d2fc9e154ce67a6cce74ace5e4d3140675130cb527aeea1`;
its logical fingerprint is
`07a3c5bd928fe7d10c17bc4c53ce44ce4475963ad1bf21cabf3c06c12ad3d0e8`.
One canonical invocation exhausted the bounded LINK activation retries and
wrote no partial golden; the unchanged retry succeeded and both paths restored
`play-paths`.

Rbxport is field-exact for the 40 empty controls and returns empty for all 33
populated Rekordbox cases. At this checkpoint the corpus contained 178 goldens
and 2,145 cases; 328 were field-exact and 1,149 preserved outcome, total, and row count.
`tools/summarize_smart_xml_matrix.py` validates every partition, ordered set,
static address, provenance hash, and replay result.

### SmartList downstream serving crosses

**Question:** After rule evaluation, does a populated intelligent playlist use
the ordinary sort, secondary rendering, pagination, packed-context, and setup
width machinery?

**Result [OBS, DB, DEC]:** The generated `smart-serving-crosses` suite reuses
the established matrices but changes every request to `0x1105` for the
rule-only `logic_any` playlist. Its two direct conditions select all eight
tracks. The 65 cases cover sort IDs 0-17, the render gate and all selectors
2-17, nine pagination plans, requester bytes 1-6, locations 1-8, and slots
0-4. A separate case repeats the result under legacy setup.

All 18 sorts return exactly eight rule-selected tracks with stable,
repeat-verified orders. Every render selector preserves those rows and emits
the same composite item type as the ordinary track path. Pagination preserves
the established nonconventional behavior: count zero returns the first row,
at/past-end clamps to the last row, overrun wraps to all rows, overlap repeats
the overlapping row, and `UINT32_MAX` times out during render. Requesters 2-6
time out; requester 1, every tested location, and every tested slot succeed.
Extended and legacy setup emit 16 and 12 row arguments respectively.

The exploratory 65-case run recorded and repeated exactly. The promoted exact
suite initially exhausted six LINK activation attempts without writing a
partial golden; the unchanged retry recorded and repeated exactly. The legacy
suite also recorded and repeated exactly. Every exit path restored
`play-paths`. Static evidence independently places `SetTrackSort`,
`djmdTrackSort`, and `Sort_SortTrackTable` in `getRowset_Playlist` and preserves
the call to `getSmartlistContentData`.

Rbxport returns zero rows for all 66 populated cases, so none is exact or
same-shape. The complete corpus now contains 180 goldens and 2,211 cases; 328
are field-exact and 1,149 preserve outcome, total, and row count. The validator
`tools/summarize_smart_serving_crosses.py` binds every order, item type, edge
outcome, row width, static address, hash, and replay result.

There is no SmartList-scoped Search request to cross. Search kinds `0x1300`
and `0x1500` carry query data without a playlist ID; `0x1105` carries a
playlist ID without query data. Global Search remains covered independently.

### SmartList ordinary device cross

**Question:** Does ordinary Pro DJ Link discovery identity alter SmartList
rule membership or the resulting track rows?

**Result [OBS]:** `record_smart_device_matrix.sh` activated the same
`smart-rule-matrix` database and kept one Rekordbox UI process while recording
`smart-device-cross.json` under all eight declared identities. The suite pairs
the populated all-eight `logic_any` rule with the zero-condition `empty_all`
control. Each identity golden was immediately repeated before promotion.
Identity transitions occasionally required one bounded port-query retry; all
then completed and the EXIT trap restored the guest to the `play-paths`
fixture.

All eight identities returned Content IDs `10001` through `10008` for the
populated rule and zero rows for the empty rule. Their normalized behavior
objects are identical with SHA-256
`8a38e105670fb5942da59cbb2bbb9754d36dccc45ab1bdb53db0392b67b3f002`.
The identity set crosses XDJ/CDJ/unknown model strings, keepalive classes CDJ,
type 7, mixer, and DJM, generations 0/2/3, and players 1-6/11.

Rbxport replay is exact for all eight empty controls and differs for every
populated control. The full corpus contains 189 goldens and 2,327 cases; 365
are field-exact and 1,186 preserve outcome, total, and row count.
`tools/summarize_smart_device_cross.py` verifies the suite, fixture, every
golden and repeat claim, normalized equality, per-identity provenance, and
backend result, then writes
`data/experiments/smart-device-cross/summary.json`.

### SmartList persisted secondary columns

**Question:** Does a populated intelligent playlist use the same persisted
secondary-column selection and composite formatting as an ordinary track list?

**Result [OBS, DB]:** Seventeen deterministic databases cover every valid
secondary selection, the title-only state, and the invalid Comment+Key state.
All were recorded from real rekordbox and immediately repeated. The selected
column controls arguments 0, 5, and 6 exactly as on ordinary collection rows.
In particular, BPM renders `120.0 bpm - Am`, Key renders
`Am - 120.0 bpm`, and the invalid multiple-selection state resolves to Comment.
Those matrix captures use the Classic local CDJ style. The focused
Alphanumeric controls repeat ordinary and Smart persisted BPM as
`120.0 bpm - 8A` with unchanged numeric fields and ordering.

Matching by ContentID leaves one deliberate row delta: argument 9 is the
persisted SmartList membership sequence `1..8`, whereas the ordinary
ALL-albums collection path sends zero. Smart rows therefore retain membership
position even though `SmartList` evaluation, rather than materialized
membership, determines which tracks appear.

Rbxport returns zero tracks for all 17 populated cases. The canonical replay
therefore classifies all 17 as different. The full evidence, including all
fixture/golden hashes and first-row values, is bound by
`tools/summarize_smart_secondary_columns.py` in
`data/experiments/smart-secondary-columns/summary.json`.

### Classic, Alphanumeric, database, and Camelot key notation

**Question:** Which setting actually controls Classic versus Camelot text in
LAN Link Export, and which menu and metadata surfaces does it reach?

**Result [OBS, DB, DEC]:** The original four-state desktop-preference cross is
valid but incomplete. `KeyStringSetting` values 1/2 crossed with
`ShowOriginalKey` values 0/1 produce identical Classic responses because the
local CDJ device-setting file remains Classic. The normalized behavior SHA-256
for all four is
`339d9c825fd448a4d9b1924aeb2fd0500eb131d7bfb11f15016ff8fb7b401ecf`.

Windows and symbolized macOS static analysis identified the active serving
chain: `exchangeKeyNameIfNeed` calls
`DeviceSettingFile::isLocalKeyCatDispStyleNormal`. The input is
`%APPDATA%/Pioneer/rekordbox6/DEVSETTING.DAT`; byte `0x74` is 1 for Classic and
2 for Alphanumeric, and uint32 `0x88` contains a 16-bit CRC-CCITT over the
32-byte payload at `0x68`.

A second cold-process matrix changed only that style and CRC. Both 13-case
states repeated exactly. Classic `Am`, `C`, and `Am - 120.0 bpm` become
Alphanumeric `8A`, `8B`, and `8A - 120.0 bpm`. The entire 24-row key root
becomes `1A,1B,...,12A,12B`; distance labels, collection, Smart, Display, and
Delivery Key fields change consistently. Only strings and their UTF-16 lengths
change. Numeric IDs, BPM, membership, pagination, and sort order are identical.

The database stores `08A` and `08B`, proving both outputs are normalized rather
than raw lookup text. Focused persisted-BPM captures additionally prove literal
`120.0 bpm - 8A` output in both ordinary and Smart rows. The new local-style
suites have not been run against rbxport; they remain canonical Rekordbox
expectations for a later backend-conformance phase.

Both recorders restored their exact baselines and the `play-paths` fixture.
`KEY_NOTATION_ORACLE.md` is the detailed reference;
`data/experiments/key-notation/{summary,device-setting-summary}.json` bind the
retained hashes.

### Link Export streaming-path visibility

**Question:** Which content fields and provider protocols determine whether a
track appears in Link Export, and do Collection, File Name, playlists, Search,
and History share the same gate?

**Result [OBS, DB, DEC]:** Static inspection reduced both
`dsqlIsLinkExportVisibleTrack` overloads to
`!streaming::isStreamingProtocol(FolderPath)`. The common helper fetches content
column 1, and nine validated direct xrefs cover playlist, flex-sort, Search,
History, shared row insertion, and SmartList paths. The provider dispatcher
uses five fixed service slots constructed by `StreamingManager`.

A deterministic fourteen-track fixture crossed local paths, all six provider
forms compiled into the binary, an unknown scheme, uppercase and embedded
SoundCloud controls, a prefix-only near match, empty, and SQL null. Real
Rekordbox was cold-started after database replacement and independently
repeated. Collection under two sorts, File Name, ordinary playlist, Smart
playlist, and Search all returned the same ten IDs. Exact lowercase SoundCloud,
Tidal, Spotify, and Apple Music paths were filtered. The `beatport:tracks:` and
`beatsource:tracks:` syntax controls remained visible, as did every
false-positive control. A pinned manager audit subsequently proved that
Beatport is constructed but searches for `/v4/catalog/tracks/`, while the
Beatsource slot remains null; login state is a separate call. Persisted History
request `1112` returned all fourteen
IDs. A subsequent cross-platform static audit resolved the contradiction: the
pinned macOS function applies the helper in both content-row loops, while the
active Windows `PSvAppSyncDBIF` vtable target directly queries live content and
never reads `FolderPath`.

No media files were created or needed. Compatibility flags and Play Song Info
path resolution remain distinct gates. Rbxport replayed all seven cases; none
is field-exact and History alone preserves outcome, total, and row count. The
full corpus is now 211 goldens and 2,403 cases, with 365 field-exact and 1,223
same-shape cases. `LINK_EXPORT_VISIBILITY_ORACLE.md` is the detailed reference,
and `data/experiments/link-visibility/summary.json` binds the fixture, suite,
golden, static evidence, diagnostic capture, and backend result.

### Windows History static cross-check

**Question:** Is the streaming-row History result caused by runtime state, or
does the Windows binary differ from the symbol-rich macOS implementation?

**Result [OBS, DEC]:** The installed Windows 7.2.19.0 executable is a
103,540,656-byte x86-64 PE with SHA-256
`c9ed23e974c51c75e2ec069fbd2679a3dbe606be9e79e9cbbd13d6418ab11c37`.
MSVC RTTI recovers the `PSvAppSyncDBIF` vtable. The `0x1112` dispatcher invokes
slot `+0x230`, whose target is `0x14236c690`.

The complete target iterates history records, reads `TrackNo` and `ContentID`,
selects the matching live `djmdContent` row, derives the configured secondary
field, and inserts the result. It never reads `FolderPath` or invokes an
explicit streaming visibility gate. The pinned macOS function does both.
This establishes a platform-specific History query pipeline and exactly
explains the repeated Windows wire result.

`tools/analyze_windows_pe.py` makes PE metadata, `.pdata` function boundaries,
immediate references, function disassembly, and RTTI/vtable recovery
reproducible. The five focused outputs live under
`data/static-analysis/windows/`. The 103 MB executable was copied only to
temporary host storage and is not a retained lab artifact.

## 2026-10-01: Hot Cue Bank catalog discovery and matrix

**Question:** Which request serves the root's Hot Cue Bank category, how do
folder and leaf navigation differ, and what database/deletion/count behavior
does Rekordbox apply?

**Result [OBS, DB, DEC]:** The analogical `1018 [context, sort]` probe is a
rejected route that returns `4003`. Static Rekordbox dispatch and the decompiled
XDJ-RR client independently identify `2001` with four numeric arguments. A
populated discovery fixture confirmed `2001 [context, selector, mode, count]`
live: mode 1 returns immediate folder/bank children and mode 0 returns a bank's
ordinary track rows.

The dedicated `hot-cue-banks` profile then recorded and immediately repeated
31 cases. Tree rows use item type `01` for Attribute 1 folders and `2b` for
bank leaves, preserve Seq ordering, and exclude a deleted node. Track mode
orders by signed membership TrackNo, keeps duplicates and a locally deleted
membership, and drops dangling or soft-deleted content during content lookup.
Stored position -1 sorts first and renders as 65535. The fourth argument is a
result cap with a floor of three: 0/1/2/3 -> 3, 4 -> 4, 5 -> 5, 8 -> 8, and 16
-> all ten resolvable memberships. Unsupported modes and unknown selectors are
valid empty menus.

Locations 1, 2, 3, and 7 returned the same root count. The first exploratory
matrix kept these controls header-only after a location-3 follow-up timed out.
A later fresh-process, fresh-connection matrix represented render context
explicitly and proved both the six-argument legacy and eight-argument RX3
forms at all four matching locations. Its late location-2/7 -> location-3
controls also returned rows because earlier cases had already populated
location 3. The exhaustive follow-up below establishes that these are
process-wide location buffers, not connection-local or freely interchangeable
render streams. XDJ-RR call sites still show distinct left, right, reload, and
drag/drop UI consumers at locations 1, 2, 3, and 7. The cue-populated fixture database SHA-256 is
`066cfa954e435346f80e5abac35dac7631ac4e3023e662d12e0080382f6041dc`;
the repeated golden SHA-256 is
`d7e5a61ec20e1667a064c6b8e7e8216893284c3274b5706ae301f5ead9fc1dce`.
`HOT_CUE_BANK_ORACLE.md` contains the full rows, call chain, provenance, and
remaining cue-info/render questions. Rbxport was not run. The `play-paths`
fixture was restored and the isolated VM was stopped after capture.

## 2026-10-02: Hot Cue Bank render location and width matrix

**Question:** Which `0x3000` follow-up forms render Hot Cue Bank at locations
1, 2, 3, and 7, and must the render location match the header request?

**Method [OBS, DEV-DEC]:** Decompiled XDJ-RR `dbcl_GetLeftBuf` establishes the
six-number form `[context, offset, limit, 0, total, 0]`. The known RX3 form is
`[context, offset, limit, 0, total, 12, 1, secondary]`. Ten declarative cases
used fresh TCP sessions: both forms at all four locations, then location-2 and
location-7 headers followed by location-3 RX3 renders. The suite was recorded,
then repeated after a fixture reset and clean Rekordbox restart.

**Result [OBS]:** Every matching-location case returned a normal menu with
total 3 and the same three rows. Each render frame preserved its declared six-
or eight-argument shape. Both late mismatched controls also succeeded. The
exhaustive state experiment below shows that they read an already-populated
location-3 buffer rather than the current header's buffer. Before/after
captures for both runs show one unchanged, responsive Rekordbox process and no
new Windows Application events. The suite and golden hashes are
`01f1ce8431e76eaaa629c792a7df161b914530c990426fa648d7d83ce5cb79ed`
and `3a6c5ee462605963974eba9c4450fe049bd47e718a8d8c87bf7e443bbc9d69c5`.
Rbxport was not run. The `play-paths` fixture was restored afterward.

### Complete location cross and process-wide buffer state

**Question:** Is a foreign render location interchangeable with the current
header location, and where does its returned content come from?

**Method [OBS]:** A generated 32-case suite crossed header locations 1/2/3/7,
render locations 1/2/3/7, and both render widths. It ran in increasing
location order with a fresh TCP connection per case, then repeated after a
clean Rekordbox restart. A second ordered suite used root, Beta Folder, Alpha
Folder, and Deep Folder selectors so stale and current rows had distinct IDs.

**Result [OBS]:** At cold start, rendering a location before any query has
populated it times out with `WouldBlock`. After population, the location can be
rendered by later fresh TCP connections. The cross therefore produced the
same initialization triangle for both widths: header 1 rendered only 1;
header 2 rendered 1/2; header 3 rendered 1/2/3; and header 7 rendered all four.
The process stayed responsive after all twelve timeouts.

The selector sequence proves foreign renders return the target location's
stale rows. A location-2 Beta header rendered through location 1 returned root
ID 9002, while rendering location 2 returned Beta Bank 9032. A location-3
Alpha header rendered through location 2 returned stale 9032, while location
3 returned 9011/9012/9013. A location-7 Deep header rendered through location
3 returned stale 9011, while location 7 returned 9021. Finally, location 1
still returned its original root ID after every intervening query. The current
header total bounds the window read from the selected stale buffer.

Both suites repeated exactly after clean restarts. All four before/after
windows retained one responsive Rekordbox process and gained zero Application
events. The cross suite/golden hashes are
`3cb430b244210fde52e4f48037137f312e651c3fe3ef03ac938b384391627bd7`
and `699e6c6806a8ca2d83da92fcd6862806e5a71eb5ca1af68a49ebc16a1ea19f30`;
the state suite/golden hashes are
`16c534142f5251603a0be833ff2f922aaa5ff3a055db8eccfae390be5b7df061`
and `25d0b66e75ae1a00fbcd81a036022fd2bb311b260111c954a9795d4c571eed28`.
Rbxport was not run. The baseline fixture was restored after each recorder.

## 2026-10-01: Hot Cue Bank cue-information path

**Question:** What does the adjacent Hot Cue Bank cue-info request look like,
where does its data come from, and can the isolated synthetic player record
the direct response?

**Result [OBS, DB, DEC]:** XDJ-RR firmware, the macOS server, and the installed
Windows command-format table establish `2101 [context, bank_id]` and direct
reply kind `4702`. `SetHeader` supplies the context and the visible assignment
writes the bank ID. The handler queries slots 1-3 and serializes up to three
36-byte cue records plus 8-byte extended timing records. Static code contains
both a master-database `CueID` -> `djmdCue` getter and an AppSync getter that
reads `djmdSongHotCueBanklist` directly.

The profile clears inherited `djmdCue` state and inserts 17 unique matching cue
rows. Correct requests were recorded and immediately repeated for populated,
partial, empty, invalid, deleted, folder, and unknown selectors. Alpha Bank
returns three 36-byte cue records and three 8-byte extensions; Root Bank
returns two of each. Empty and invalid selectors return a valid empty `4702`.

Compact/fixed-12 tag areas, extended/legacy setup, keepalive/captured-status
identities, XDJ-RX3/XDJ-RR models, and a same-connection catalog sequence all
produce identical decoded payloads for equivalent selectors. Raw response fields
retain the complete response frame. Rbxport was not run.

### Hot Cue Bank field/source matrix

**Question:** Which database path supplies the live Windows payload, and what
does every byte in the legacy cue record mean?

**Method [DB]:** Two banks contain identical membership `ContentID`, timing,
and MPEG fields. Their stored frame, color, comment, active-loop, microsecond,
and seek-info values differ, and their `CueID` references point to entirely
different `djmdCue` content and timing rows. Three slots use `OutMsec=-1`,
`4004`, and `1`. Compact and fixed-12 request frames were each repeated.

**Result [OBS, DB, DEC]:** All four decoded payloads are identical. The live
Windows server therefore uses `djmdSongHotCueBanklist` directly. Each record is
little-endian flags/content/zero/cue-frame/loop-frame followed by
`InMpegFrame`, `OutMpegFrame`, `InMpegAbs`, and `OutMpegAbs`. The extension is
the original `InMsec, OutMsec` pair. Cue frames truncate `msec * 0.15`; a
positive loop frame is decremented after truncation. Slots 1-3 are labeled hot
cues D-F. A one-millisecond out-point has its loop flag set but loop frame zero.
The exact values and artifact hashes are machine-checked by
`tools/summarize_hot_cue_bank.py`. Rbxport was not run.

## 2026-10-01: Extended Hot Cue Bank getter and option records

**Question:** What do commands `2201` through `2401` mean, and how does the
new-format Hot Cue Bank getter serialize membership and option fields?

**Static result [DEC]:** The command table defines legacy setter
`2201 [context, bank_id, 36, cue_blob, 8, extension_blob]`, extended getter
`2301 [context, bank_id, slot_count]`, and extended setter
`2401 [context, bank_id, record_count, blob_bytes, blob, slot_count]`.
The active AppSync getter queries one live `djmdSongHotCueBanklist` row for each
requested TrackNo. The master alternative follows CueID into `djmdCue` and cue
option tables. Both mutation operations were subsequently tested with disposable
fixtures and are recorded below.

**Count result [OBS, DB]:** Nine read-only cases were recorded and repeated.
Reply kind `4e02` contains echoed `2301`, status, aggregate blob bytes, a
concatenated self-sized blob, and record count. Counts 1, 2, 3, 4, and 8 return
that many Alpha Bank records. Count zero, a folder selector, and an unknown
selector return status 1 with an empty blob. Compact and fixed-12 request tags
produce identical three-record payloads.

**Field result [OBS, DB, DEC]:** An isolated nine-bank fixture separates timing,
MPEG values, color, ASCII/Unicode comments, BeatLoopSize, CueMicrosec, inbound
seek, and outbound seek. The stable eight-case suite was recorded and repeated
after clean process starts. The fixed header is 56 bytes; option length controls
four-byte record alignment. Baseline records are 124 bytes, `A` comments make
128 bytes, and `é🙂` comments make 132 bytes. Color 7 emits 8,
BeatLoopSize `12345678` emits words `1234,5678`, CueMicrosec survives exactly,
and the chosen MPEG sentinels survive exactly.

**Seek edge [OBS, DB, DEC]:** The parser consumes three unsigned decimal UTF-16
components. An outbound-only string is skipped because inbound validity gates
the entire outbound branch. Inbound `1,2,3` produces no response and exits the
Rekordbox process; a process query immediately afterward returned no process.
Earlier prose-like inbound strings also exited the process. Crash captures are
kept outside routine goldens. The VM remained isolated from the physical RX3,
no media files were present, and rbxport was not run.

The fault is localized to the active AppSync getter. Its three numeric helpers
mutate a pointer-to-pointer cursor into the allocated UTF-16 copy. At
`0x1016d3664..0x1016d366d`, the getter loads that advanced cursor and passes it
to `djrfree`, not the allocation base. The outbound branch contains the same
defect at `0x1016d3842..0x1016d384b`, but inbound validity gates entry and the
inbound free occurs first. This proves that any nonempty inbound string can
trigger an invalid interior-pointer free regardless of whether its third
numeric component is valid **[RB-DEC, OBS]**.

## 2026-10-01: Extended Hot Cue Bank setter and durable mutation

**Question:** Does `2401` work against real Rekordbox, what row does it mutate,
what does it return, and does the result survive in database state?

**Controls [OBS, DB]:** The first disposable fixture had one active bank/slot
membership whose CueID differed from its membership ID. The second aligned
CueID with ID. Each before/set/after run returned status 50 with an empty setter
payload, left the immediate getter unchanged, and produced a stopped database
byte-identical to its fixture. The controls isolate the failure from CueID/ID
alignment.

**Resolver result [DEC, OBS]:** `HCBnkSong_GetCueID` queries active rows for one
bank and TrackNo. Its machine code branches to failure when `size() == 1`, but
otherwise indexes row zero. A third fixture therefore supplied two active rows
at bank 9060, TrackNo 1, with each CueID equal to its membership ID. This
bypassed the anomalous cardinality branch and deterministically targeted row
94001.

**Wire result [OBS]:** The three-case suite read the baseline with `2301`, sent
one 124-byte `2401` record, and read the slot again with `2301` on the same
connection. The setter returned `4e02 [2401, 0, 124, record, 1]`; the following
getter returned the exact same record with echoed kind `2301`. After resetting
the fixture and restarting Rekordbox, the independent repeat matched all three
canonical cases.

**Database result [DB]:** Before shutdown, the live encrypted base, WAL, and
SHM were copied together. The base retained fixture SHA-256
`9f0b8c2d4aaa1dfa6549b8f268ce3ee764392682ee1c7524644eed5cd991815e`;
the 206032-byte WAL contains the mutation. Reading the captured trio shows the
wire values persisted to membership 94001, including derived 150-fps frames,
MPEG positions, Color, BeatLoopSize, CueMicrosec, local USN, and timestamp.
Membership 94002 and both `djmdCue` rows remain unchanged. The stopped base was
byte-identical because the shutdown helper force-closed the process after its
grace period; the pre-shutdown WAL is the authoritative durable-state capture.

The guest was isolated from the physical RX3, no media files were present, the
prior `play-paths` fixture was restored afterward, and rbxport was not run.

## 2026-10-01: Legacy Hot Cue Bank change and track-cue response

**Question:** Does `2201` work against real Rekordbox, which row does its D
selector target, and why does its reply use the track-cue `4702` format?

**Static result [DEC]:** XDJ-RX3 `dbcl_ChangeHotCueBank` sends a fixed 36-byte
cue record plus 8-byte millisecond extension. D/E/F are encoded as ordinals
4/5/6. The AppSync setter passes that ordinal directly to
`HCBnkSong_GetCueID`; the master setter subtracts three. On success the command
handler replaces its selector with the cue record's ContentID and calls
`GetUsbCue`, producing a `4702` response.

**Controls [OBS]:** A first fixture with duplicate `TrackNo=1` rows timed out
for all three declared cases, proving D does not address slot 1 on the active
AppSync path. The canonical fixture instead has duplicate `TrackNo=4` rows.
Known content plus bank succeeds; known content plus unknown bank and unknown
content plus known bank time out. A fixture reset and clean Rekordbox restart
reproduced all three outcomes.

**Wire result [OBS]:** The success response is
`4702 [2201, 0, 72, blob, 36, 2, 0, 16, extension]`. Its two records are the
track's ordinary `djmdCue` rows, not the sentinel mutation record. Their cue
frames are 15000 and 13680; extension pairs are `(100001,100001)` and
`(91202,91202)`.

**Database result [DB]:** The encrypted base retained fixture SHA-256
`0fb84c41c4e344fa30c83aa2c889f40dda9ca7e13e4e9373891037f9e96c8604`.
Its 189552-byte WAL persisted every fixed-record sentinel to membership 94101:
frame words `11111111`/`22222222`, MPEG words `33333333` through `66666666`,
extension `77777777` as `InMsec`, `OutMsec=ffffffff`, and `Color=-1`.
Membership 94102 and both `djmdCue` rows remained unchanged. The VM was isolated
from the physical RX3, contained no media, restored `play-paths` afterward, and
rbxport was not run.

### Complete D/E/F ordinal matrix

**Method [DB]:** A second fixture supplies duplicate writable membership rows at
`TrackNo` 4, 5, and 6, associated with ContentIDs 10001, 10002, and 10003. One
suite sends otherwise identical `2201` records with ordinal 4/D, 5/E, and 6/F.

**Result [OBS, DB]:** All three requests succeed and independently repeat after
a fixture reset and Rekordbox restart. The live 230752-byte WAL changes
memberships 94201, 94203, and 94205, proving direct mappings 4->4, 5->5, and
6->6. Their duplicate partners and all six `djmdCue` rows remain unchanged.
The D response contains two cue records for ContentID 10001; E and F contain
one each for ContentIDs 10002 and 10003. This simultaneously separates the
membership target, chosen by ordinal, from the response source, chosen by
ContentID. No media files were present and rbxport was not run.

## 2026-10-01: Deleted Hot Cue Bank with a live member

**Question:** Does soft-deleting the bank itself invalidate direct Link Export
queries, or does it only remove the node from tree navigation?

**Method [DB]:** The fixture retains deleted bank 9031 under Beta Folder and
adds live membership 91450 at TrackNo 1 for live track 10005, plus live cue
191450. Four requests cover its parent tree, direct catalog tracks, legacy cue
information, and extended cue information.

**Result [OBS, DB, DEC]:** The parent tree returns only Beta Bank 9032, so the
deleted node remains hidden. Direct catalog request `2001` nevertheless returns
track 10005 at membership position 1. Direct `2101` returns one cue record with
`InMsec=91450`; direct `2301` returns one 124-byte record with the same timing
and MPEG values. The four cases matched on immediate repeat. Bank liveness is a
tree predicate only; direct paths query live memberships without validating the
owning bank row. The isolated VM used no media and rbxport was not run.

## 2026-10-01: Legacy Hot Cue Bank ordinal gate boundaries

**Question:** Does legacy setter `2201` accept ordinals outside D/E/F, reject
them, reinterpret them through an 8- or 16-bit signed conversion, or silently
ignore them?

**Method [DB, OBS]:** The deterministic fixture places two writable bank-9060
memberships at each `TrackNo` 0, 1, 2, 3, 7, 8, 255, 256, 32767, 32768, and
65535. Each pair has a live ContentID and uses its own membership IDs as CueIDs,
removing the known one-row resolver failure from the matrix. The suite sends
one otherwise identical 36-byte record and 8-byte extension for each ordinal.
It records once, copies the live encrypted base/WAL/SHM trio, resets the
fixture, restarts Rekordbox, and verifies all eleven cases independently.

**Wire result [OBS]:** Every request returns kind `4702`, status zero, and the
ordinary `djmdCue` rows selected by the request record's ContentID. The reply
counts are `2,1,1,1,1,2,1,1,2,1,1`, reflecting those ContentIDs rather than the
ordinal. Both passes are byte-identical. A successful-looking `4702` reply is
therefore insufficient evidence that `2201` performed a mutation.

**Database result [DB]:** The captured base remains at fixture SHA-256
`4b2f40ad3a9a0a7e246cb3c10243bc698b407bd97d00e5ce8701ddeafc88ce00`.
The 168952-byte WAL view leaves all 22 paired memberships and all 22 cue rows at
their fixture values: no sentinel field, local USN, or timestamp changed. The
WAL SHA-256 is
`d9be5defe53a37f2ce9243c08d695decd9681707fe00bec77db25398e0a6f161`.

**Static explanation [RB-DEC]:** `OnCueBnkCmd` admits the setter only when the
flag word is within `0x00040000..0x0006ffff`. For the observed low word
`0x0100`, this is exactly ordinals 4, 5, and 6. It implements the range by
subtracting `0x00070000` and taking the setter branch when the unsigned result
exceeds `0xfffcffff`. Outside the gate it skips `setHCBnkCuePoint`, but still
replaces the selector with ContentID and calls `GetUsbCue`. All eleven controls
are acknowledged no-ops.

Fixture fingerprint:
`4fb2783ac70af1c22d5b4e4e434f7bd13b079e6241c9368e770eda08c016bd7e`.
Suite SHA-256:
`ed5fc7eaa353cdfa6a5cfb517fcd44ec2179afa2900feb0875e020ca4ad35ca6`.
Golden SHA-256:
`a5705dc29f3d702f91ec6165e37fe7aaa02f70581511276eae65324ae808475a`.
The physical RX3 was unreachable, no media files were present, `play-paths`
was restored, and rbxport was not run.

## 2026-10-01: Hot Cue Bank catalog count width and signed boundary

**Question:** Is `2001` track mode's fourth argument narrowed to a device-sized
field, clamped to available rows, or retained as a full-width capacity?

**Method [OBS]:** The canonical `hot-cue-banks` fixture has ten resolvable Alpha
Bank memberships. One six-case suite uses counts 17, 255, 256, 65535, 65536,
and 1048576. Three single-case suites use `INT32_MAX`, `0x80000000`, and
`UINT32_MAX`. Every single-case probe began from a fresh Rekordbox process and
captured process memory, responsiveness, and timestamp-bounded Windows
Application events before and after the request. Every suite was recorded and
verified after a fixture reset and clean Rekordbox restart.

**Result [OBS]:** Every positive request through `INT32_MAX` returns the same
ten rows in the same order. `0x80000000` and `0xffffffff` return status-normal
headers with total zero. All nine cases match exactly on repeat. Each isolated
process remained present and responsive, and no before/after event-log pair
gained an application-error record. The request is not narrowed at 8 or 16
bits; bit 31 is the exact empty-result boundary.

**Static explanation [RB-DEC]:** The active behavior matches
`PSvAppSyncDBIF::getHCBnkList`, which runs a joined membership/content SQL query,
computes unsigned `max(count, 3)`, then compares its signed 32-bit row index to
that stored word with `jge`. A high-bit limit is negative and terminates before
row zero. The separate `PSvDBMain::GetHCBnkList` implementation does allocate
three `count * 4` arrays, but it is reached through a different database
interface path and does not explain the captured local-library responses.

Suite SHA-256:
`83e10f06961a544ad359a70121f7beb06e3aa571ddbee786baad218bd61bf387`.
Golden SHA-256:
`fbfe83cc65ff5df516ea7adbcdf969e1c4a5656587a490884886542998abd200`.
Signed-boundary suite SHA-256 values (`INT32_MAX`, high bit, `UINT32_MAX`):
`82663095fd8f5bebc615380b1dc843a399d0c1cc19d6aebef7f87ce769921e45`,
`54fd042dc5d5a183e4773ecb1eb60b70ec782ad7ffe5062509c00532700b4d0b`, and
`69485a66d376d7e920c0409c86e134a27ba72902274b6987321cc28143ca635c`.
Their golden SHA-256 values are
`a02ab37f1c4cbd4b178babfd1d0b67a7747de8469aa43d22fe1d9a08d1f65ed9`,
`c450fe7cb99d642b06d88937c7216414ba3482a1cd86ec0f37d1740d6ef1390e`, and
`f3f6532cf913e6c690b712c3db3b0b48b9da5a4c821bd9d5e734126079b6e40a`.
Fixture fingerprint:
`718db45aea9624ec7f8c6cd70140ec6ba4b99d0cae4739aa3830ca4d0528b9b7`.
The isolated VM restored `play-paths` afterward; no media or rbxport process was
used.

## 2026-10-02: Exhaustive ordinary-Track context type

**Question:** What does the final byte of the packed Link Export context do for
ordinary Track request `1004`, and does its client-side track-type meaning alter
membership or row rendering?

**Method [OBS]:** A generated 256-case suite held requester `0x01`, menu
location `0x01`, and media slot `0x03` fixed while exhausting the final byte
from `0x00` through `0xff`. Every case used a fresh TCP connection and repeated
the same context in its render request. The deterministic `full` fixture
contains eight tracks with nonempty `HotCueAutoLoad`. The suite was recorded
after a clean rekordbox start, then independently verified after reinstalling
the fixture and starting a second clean process. Before/after health snapshots
assert one responsive process with the same PID and zero Windows Application
events during each pass.

**Result [OBS]:** Exactly 254 values return a normal menu with total 8 and all
eight rows. Values `0x03` and `0x04` time out before a header with
`transport_error_kind = WouldBlock`. Only type `0x01` gives every row argument
10 value `0x00000100`; the 253 other successful values give
`0x00000000`. Every other row field is identical. Both clean-process runs agree
exactly. Dysentery names `0x00` no track, `0x01` rekordbox track, `0x02`
unanalyzed track, `0x05` audio CD track, and `0x06` streaming track. No name is
assigned to the two measured timeout values.

**Static explanation [RB-DEC]:** `OnTrackListCmd` at `0x101d2c6c0` passes the
complete context through database-interface slot `+0x48`.
`PSvAppSyncDBIF::getTrack_Root` at `0x1016bc8e0` uses the complete context as
the list-buffer identity and does not branch ordinary membership on its low
byte. `GetListBufContents` at `0x100fa1110` extracts the low byte and passes it
to `GetListBufRowContent` at `0x100f9fe40`. That renderer admits its cache and
`HotCueAutoLoad` enrichment path only when the value equals one, exactly
explaining the argument-10 difference. The inspected path does not localize the
`0x03`/`0x04` pre-header timeout decision.

Generator SHA-256:
`6d2a2b4a5e336bcc6847772415dad29c48d5c208846d25d1f446bfa7a57a9a12`.
Suite SHA-256:
`e3f5d29139f717634099fd6d4746c063f8f44a96d3272dcd7d90dbb629e99e49`.
Golden SHA-256:
`a020a12838ff23ee931225d81e09dfa38a26d37f95afef9c25d7c87b1105bd54`.
Static-evidence SHA-256:
`6fdc36560135ba42923c92f6d8897ec6e0383db951aca391c1cb2ea49c8a62b8`.
Fixture fingerprint:
`c7b0b834a1a1320faaa3526c4792f0d31430c617ea9b8b6008521c514b67853c`.
The physical-LAN VM remained inactive, no media files were present, the
`play-paths` baseline was restored, and rbxport was not run. The suite is
explicitly deferred from implementation replay.

## 2026-10-02: Packed context across all list families

**Question:** Are the ordinary Track final-byte results specific to request
`0x1004`, or do they describe the complete `0x1xxx` list dispatcher?

**Method [OBS]:** A generated 329-case suite crossed the 47 declarations in
`full.json` with client values `0x00..0x06`. Requester `0x01`, location
`0x01`, and slot `0x03` remained fixed. Every case used a fresh TCP connection.
The full fixture was reinstalled before each of two clean Rekordbox processes;
before/after health snapshots assert stable responsive PIDs 5520 and 9912 and
zero new Windows Application events.

**Result [OBS]:** Types `0x03` and `0x04` time out before a header for all 47
families. The other five types produce 46 menus plus the existing `0x1018`
error. Root and Search populate only for type `0x01`; direct category and leaf
queries continue to work. Genre, Artist, Album, Label, Original Artist,
Remixer, and Playlist track leaves copy `TT << 24` into argument 7 for 25 rows
per nonzero successful type. Type `0x01` alone adds argument-10 bit `0x100`,
covering 60 rows across 17 families. No other successful row fields differ.

**Static explanation [RB-DEC]:** `PSvDBMain::OnClientReq` at `0x102521340`
computes `request_kind >> 12`. For class 1 it tests `(TT - 3) <= 1` and diverts
exactly `0x03` and `0x04` to an internal observer path before
`OnListClientCmd`. Class 2 bypasses this gate.

Generator, suite, golden, and routing-evidence SHA-256 values are
`877d02c67a5958cbeeb418283b34483919e7132ba353e3b11ea4a9bd260fa6c6`,
`c3f2469a65045e2db7b9f9c307d80aef9933ed772a7107e9ad7561ecf68bc5b7`,
`09995fec3f849020c86a79d035edf1f75483210c2e904db55aec420dac53782c`,
and `6dde2e506bb52f84a121c19bcc527193076c98d006bd5211f61b7836bbff2f1e`.
Fixture fingerprint:
`c7b0b834a1a1320faaa3526c4792f0d31430c617ea9b8b6008521c514b67853c`.

## 2026-10-02: Packed context across Song Info

**Question:** Does the list-family `0x03`/`0x04` gate apply to `0x2xxx` Song
Info requests, and which client types produce local-library rows?

**Method [OBS]:** A 49-case suite crossed types `0x00..0x06` with Display
`0x2002`, Play `0x2102`, recognized no-builder requests `0x2202..0x2502`, and
Delivery `0x2602`. Both passes reinstalled `full`, started clean Rekordbox
processes, used a fresh TCP connection per case, captured health, and matched
exactly.

**Result [OBS]:** Every type receives a header, including `0x03` and `0x04`.
Only type `0x01` returns Display, Play, and Delivery rows, with totals 16, 7,
and 13. Every other type receives `0x4000` with total `0xffffffff` and no
render. Requests `0x2202..0x2502` return `0x4003` for every type. Both
processes remained responsive with zero Application events.

Generator, suite, and golden SHA-256 values are
`1b4bcda341bf3e003fb7e9cd78ca094e6d206fef13bbabcef3858bc05fc7ada3`,
`aa01b6fa16f5d53507b75a1b061d56662075f83a6694f4dc319f22ff9d2d3962`,
and `9b8c6ed36da66cd81c38d36bdd8ebdf8ccf36c8ae50c271ec6820e9cab84b2ed`.
The physical RX3 remained unreachable, no media was present, `play-paths` was
restored, and rbxport was not run.

## 2026-10-02: Packed context across Hot Cue Bank

**Question:** How does Hot Cue Bank `0x2001` consume the client track-type byte
for tree, populated-bank, and empty-bank requests?

**Method [OBS]:** A 21-case suite crossed the three request shapes with types
`0x00..0x06` against the deterministic `hot-cue-banks` fixture. Two clean
Rekordbox processes produced identical goldens and clean before/after health.

**Result [OBS]:** Type `0x01` returns normal totals 3, 8, and 0. Every other
type returns `0x4000` with total 50 for all three shapes. The runner then asks
for 32 rows and receives no messages before a `WouldBlock` timeout. This is a
post-header render timeout, not the list-family pre-header gate or the Song
Info `0xffffffff` result.

Generator, suite, and golden SHA-256 values are
`73b43314ac819077e184dcd174ab977d00c366bacf85ef1b7d3781cb6266f4ea`,
`58570369cf8e26e745132ea5c3640aad2f9b73a5ecff3535f84a1f800833d0e2`,
and `1427ad163a5635e391e49ff78e2055cd9e8622f9c55c020f83335a3aec4a198f`.
Fixture fingerprint:
`718db45aea9624ec7f8c6cd70140ec6ba4b99d0cae4739aa3830ca4d0528b9b7`.
The isolated network gate passed after a clean VM restart, no media was
present, `play-paths` was restored, and rbxport was not run.

## 2026-10-02: Packed context by device identity and setup width

**Question:** Do discovery model/class/generation/player identity or legacy
versus extended setup alter the established packed track-type behavior?

**Method [OBS]:** Two generated 16-case suites cover all seven known client
types on ordinary Track, normally dispatched types `0x00`, `0x01`, `0x02`,
`0x05`, and `0x06` on the Genre hierarchy Track leaf, and type `0x00`/`0x01`
Root/Search controls. One suite requests 16-field extended rows and the other
12-field legacy rows. Both suites were recorded and immediately repeated under
XDJ-RX3, CDJ-3000, CDJ-2000NXS2, XDJ-XZ, XDJ-AZ, XDJ-1000MK2, unknown mixer,
and unknown DJM identities. Rekordbox restarted and the fixture was reinstalled
between identities. The isolated network gate ran before every identity.

**Result [OBS]:** All eight extended behavior envelopes are byte-identical
after provenance removal, with SHA-256
`bea74aa6bfd2ce82f6bc423e30cfee7f2b523e76a83e4d519c0ebbe841e55d90`.
All eight legacy envelopes are likewise identical, with SHA-256
`6fe895b6474d5231d4ac1241c6b4426e072377e1753f1d88e3dc170b92911cc1`.
Types `0x03` and `0x04` time out before a header in every identity/setup cell.
Root and Search populate only for type `0x01`. Track argument 10 and hierarchy
argument 7 retain their established type-derived values. Every legacy row is
the exact first 12 arguments of its extended counterpart. Setup changes only
serialization width for this surface.

The 16 goldens contain 256 real-Rekordbox cases and the immediate verification
adds 256 repeat executions. Generator, recorder, extended suite, legacy suite,
summary, and journal SHA-256 values are
`35e26e5d4c9f6fa7adec75faac111acc2cd68318e65ab7b05acd43a73d072eb9`,
`d260eaafd2e8e0acc122e95a9f2976544835b25cbe31180b4d3a4a70cff03176`,
`9d4da69805fbbf1aadd4f26ac44d94011230cfe82f1307a65addbbb2e02e04a3`,
`c1e59469940ee6fb03b0487cbb43e9ff4c9e3ea1c92f55c47e6bad5fd8463053`,
`5cd134ed2657a07ab13a888c45d995b1579b6dad45476978f15715d49cb70502`,
and `69c497f48386e6c493dac3f777940e57430dc830e964198aae43f29fbf047573`.
Fixture fingerprint:
`c7b0b834a1a1320faaa3526c4792f0d31430c617ea9b8b6008521c514b67853c`.
No media or rbxport process was used, and the batch restored `play-paths`.

## 2026-10-02: Packed Display context with status-backed controls

**Question:** Does the packed track type, requester/player byte, or setup width
alter Display Song Info's status-derived AIO branch?

**Method [OBS]:** Generated seven-type suites used authentic RX3 player-11
status with requester 11, an RX3-template-derived CDJ-3000 player-1 control
with requester 1, and an RX3-status/requester-1 mismatch control. Extended and
legacy suites were
recorded and immediately repeated on the isolated VM. The first wrapper attempt
did not pass status-template fields and is retained only as an excluded journal;
its files were replaced by status-aware captures.

**Result [OBS, DEC]:** Only type `0x01` returns the 16 Display rows. Types
`0x00` and `0x02..0x06` return total `0xffffffff`. Matched RX3 requester 11
moves Comment from position 11 to position 6. Matched CDJ requester 1 and the
RX3-status/requester-1 control use ordinary order, proving that the query's
requester byte selects the player-number-keyed `isAIO` cache entry. Legacy rows
are exact 12-field prefixes of extended rows.

The six goldens contain 42 cases and 42 immediate-repeat executions. The
machine validator, hashes, and all three service journals are under
`data/experiments/packed-context/display-status-cross/`. The physical-LAN VM
remained stopped, no media was used, `play-paths` was restored, and rbxport was
not run.

## 2026-10-02: Packed Play context with status-backed controls

**Question:** Does packed track type, RX3/CDJ status classification,
or setup width alter Play Song Info admission or rows?

**Method [OBS]:** Four seven-type suites crossed authentic RX3 player-11 status
with requester 11 and an RX3-template-derived CDJ-3000 player-1 control with
requester 1 under extended and legacy setup. Every canonical capture was
immediately repeated
before promotion. The recorder restored the `play-paths` fixture afterward.

**Result [OBS]:** Only type `0x01` returns the seven Play rows. Types `0x00`
and `0x02..0x06` return `0x4000` with total `0xffffffff`. After normalizing
the requester byte in request and render contexts, the complete RX3 and
CDJ-3000 envelopes are identical within each setup. Extended and legacy
normalized behavior hashes are
`3a425319ea4322b578efd2c559984fc028e27c4c00b272c69d41c20b3ae0d0f0`
and `f205fd2bd1c4d143ed4be574d89cfec4c61d38d02481bde63c3fb7544d949f33`.
Legacy rows are exact 12-field prefixes of extended rows.

The four goldens contain 28 cases and 28 immediate-repeat executions. The
machine summary and successful journal are under
`data/experiments/packed-context/play-status-cross/`; the same directory keeps
the pre-capture executable-permission failure for provenance. The physical-LAN
VM remained stopped, no media was used, and rbxport was not run.

## 2026-10-02: Remaining class-2 context with status-backed controls

**Question:** Do Delivery or the recognized no-builder Song Info kinds change
their packed-type behavior with the RX3/CDJ status controls or setup width?

**Method [OBS]:** Four 35-case suites crossed Delivery `0x2602` and recognized
kinds `0x2202..0x2502` over types `0x00..0x06`, authentic RX3 player-11 status,
the RX3-template-derived CDJ-3000 player-1 control, and extended/legacy setup.
Every canonical capture was immediately repeated before promotion.

**Result [OBS]:** Delivery returns 13 rows only for type `0x01`; the other six
types return `0x4000` with total `0xffffffff`. Every recognized no-builder kind
returns `0x4003` with its request kind as the sole argument for every packed
type. Normalized RX3/CDJ envelopes are identical within setup, and legacy
Delivery rows are exact 12-field prefixes of extended rows. The extended and
legacy normalized hashes are
`2eff175f6049a229665d0df46aa00cddc2e4749f3b1358bb1b380f52e8053da6`
and `12a5195f55ead8d8f83021bac8cc278029796ad5ba0a2e3e5816cdde5b792d58`.

The four goldens contain 140 cases and 140 immediate-repeat executions. The
machine summary and service journal are under
`data/experiments/packed-context/class2-status-cross/`. The physical-LAN VM
remained stopped, no media was used, `play-paths` was restored, and rbxport was
not run.

## 2026-10-02: Packed Hot Cue getters with status-backed controls

**Question:** Do the legacy and extended Hot Cue Bank direct getters consume
the packed type byte, status-derived device identity, or setup shape?

**Method [OBS]:** Four 28-case suites crossed `0x2101` and `0x2301` over
populated and empty banks, types `0x00..0x06`, authentic RX3 player-11 status,
the RX3-template-derived CDJ-3000 player-1 control, and extended/legacy setup.
Every capture was immediately repeated before promotion.

**Result [OBS]:** Type `0x01` alone returns database payloads. Every other type
receives the getter's normal direct response kind (`0x4702` or `0x4e02`) with
status `50`, empty blobs, and zero records. All six rejected types are
byte-identical within each getter/selector family. Every decoded response is
also identical across identity and setup after removing the request envelope;
the shared normalized hash is
`820ec23cde0fa1d817f42ff8812fe1abca175d1a9885cb7c36279b01e2f06c6f`.

The four goldens contain 112 cases and 112 immediate-repeat executions. The
machine summary and service journal are under
`data/experiments/packed-context/hot-cue-getter-status-cross/`. The
physical-LAN VM remained stopped, no media was used, `play-paths` was restored,
and rbxport was not run.

## 2026-10-02: Packed extended Hot Cue setter with status-backed controls

**Question:** Does packed type, RX3/CDJ status identity, or setup width
alter admission or database effects for extended setter `0x2401`?

**Method [OBS, DB]:** Four 14-case suites crossed types `0x00..0x06`, authentic
RX3 player-11 status, the RX3-template-derived CDJ-3000 player-1 control, and
extended/legacy setup. Every rejected setter was followed on a fresh connection
by a type-1 getter. The
accepted type-1 setter and getter ran last. Every suite was reset to the
encrypted fixture, Rekordbox was restarted, and the complete run was repeated
before promotion.

**Result [OBS, DB]:** Type `0x01` alone returns the canonical mutated 124-byte
record, and its following getter matches. Types `0x00` and `0x02..0x06` return
`4e02 [2401, 50, 0, empty_blob, 0]`; all 24 following getters return the shared
pristine record. The decoded response sequences are identical across both
identities and setup shapes, with signature
`93cb7f88f8289a00ad3c4350421360ae830aad7ab2be1ada03f52a8e9b1b72e3`.

The generator, four declarations, four canonical goldens, exact-repeat
journal, hashes, and validator are under `conformance/` and
`data/experiments/packed-context/hot-cue-setter-status-cross/`. The physical
LAN VM remained stopped, no media was used, `play-paths` was restored, and
rbxport was not run.

## 2026-10-02: Packed legacy Hot Cue setter with status-backed controls

**Question:** Does packed type, RX3/CDJ status identity, or setup width
alter admission or database effects for legacy change operation `0x2201`?

**Method [OBS, DB]:** Four 14-case suites crossed types `0x00..0x06`, authentic
RX3 player-11 status, the RX3-template-derived CDJ-3000 player-1 control, and
extended/legacy setup. Every setter was followed by a fresh type-1 extended
getter over slots 1–6. The
accepted type-1 setter ran last. Each suite was independently repeated after
fixture reset and Rekordbox restart.

**Result [OBS, DB]:** Type `0x01` alone returns the canonical two-cue response
and changes slot 4 to the expected 56-byte mutation record while leaving slots
5 and 6 byte-identical. Types `0x00` and `0x02..0x06` return
`4702 [2201, 50, 0, empty_blob, 36, 0, 0, 0, empty_blob]`; all 24 following
getters return the shared pristine 372-byte D/E/F record set. The decoded
response sequences are identical across identities and setup shapes, with
signature
`fa283bebdfd95dcd54c234e1cb6e01a3dccff7f91de80c2e9ab6e07cc3260558`.

The generator, four declarations, four canonical goldens, exact-repeat
journal, hashes, and validator are under `conformance/` and
`data/experiments/packed-context/hot-cue-legacy-setter-status-cross/`. The
physical-LAN VM remained stopped, no media was used, `play-paths` was restored,
and rbxport was not run.

## 2026-10-02: Hot Cue Bank large pagination

**Question:** How does Rekordbox render a bank larger than two 32-row pages,
especially at page boundaries and invalid windows?

**Method [OBS, DB]:** The encrypted `hot-cue-bank-pagination` fixture contains
70 ordered tracks and memberships in bank 9070. Fifteen cases exercise
one-row and 32-row automatic walks, explicit 32/32/6 pages, both boundaries,
the final row, zero count, end/past-end offsets, overrun, overlap, and maximum
unsigned offset. The isolated XDJ-RX3 player-11 run was restarted and repeated
before promotion.

**Result [OBS]:** Every complete walk returns content IDs 40001 through 40070.
Zero count returns one row; end and past-end clamp to the final row; an overrun
window is right-aligned to its requested count; overlap repeats the shared row;
and offset `0xffffffff` times out during render after a successful total-70
header. The database SHA-256 is
`1cc3c7eb27d4ca792b9fa7f6cf0c06e6cf9a7eb9b6b8727374b492e4b048c05e`.

The declaration, canonical golden, exact-repeat journal, artifact hashes, and
machine validation are under `conformance/` and
`data/experiments/hot-cue-bank/pagination/`. The physical-LAN VM remained
stopped, no media was used, `play-paths` was restored, and rbxport was not run.

## 2026-10-02: Packed Hot Cue catalog with status-backed controls

**Question:** Does RX3/CDJ status identity or setup width alter the
packed-type behavior of Hot Cue Bank catalog request `0x2001`?

**Method [OBS]:** Four 21-case suites crossed the tree root, Alpha Bank tracks,
and an empty bank over types `0x00..0x06`, authentic RX3 player-11 status, the
RX3-template-derived CDJ-3000 player-1 control, and extended/legacy setup. Every
capture was immediately
repeated after fixture reset and Rekordbox restart.

**Result [OBS]:** Type `0x01` returns totals 3, 8, and 0 for the three paths.
Types `0x00` and `0x02..0x06` return a total-50 header, then receive zero rows
and `WouldBlock` after a 32-row render request. Normalized RX3 and CDJ-3000
responses are identical. Legacy rows are exact 12-field prefixes of extended
rows. The normalized extended and legacy signatures are
`3a1559bf7881415f56bf9db4b44a252de043bbbdf8bbf6b0d9c0800aa0ccc0ce`
and `bfbea6623b0f3cdd0ea5d712412cb12772d36c7a7ae622734d9e1523064db514`.

The four goldens contain 84 cases and 84 exact-repeat executions. The machine
summary and service journal are under
`data/experiments/packed-context/hot-cue-catalog-status-cross/`. The
physical-LAN VM remained stopped, no media was used, `play-paths` was restored,
and backend comparison is deferred.

## 2026-10-02: Extended Hot Cue setter parser matrix

**Question:** Which outer counts and lengths, fixed-record fields, variable
option lengths, and requested return counts are admitted by `0x2401`, and what
database state does each parser outcome leave behind?

**Method [OBS, DB]:** Fifty-seven generated suites vary one structural value at
a time. Every probe starts from the same encrypted duplicate-slot fixture,
restarts Rekordbox, sends one setter, then reads the stored record with a fresh
type-1 `0x2301` connection. Fifty-four deterministic variants must match a
second complete fixture-reset run before promotion. Declared length
`UINT32_MAX`, admitted slot 8, and returned-slot count `UINT32_MAX` are
delegated to lifecycle recorders because response ordering, process health,
and same-database restart behavior are part of their results.

**Result [OBS, DB]:** The strict reducer accepted all 57 variants, 54
fixture-reset golden pairs, 66 lifecycle observations, and 366 evidence cases.
Record count must equal one: 0, 2, and `UINT32_MAX` return
status 50 and leave the database pristine. Actual blob lengths 0, 1, and 55
also return status 50; length 56 succeeds as a fixed-only 56-byte record, while
123, 124, and 125 all canonicalize to the same 124-byte record. With an actual
124-byte blob, declared lengths 0, 55, 56, and 123 return the argument-free
`0xfffffffe/0x0100` connection-close sentinel and remain pristine; declared length 124
and 125 return the same canonical successful mutation. This distinguishes a
finite lower-bound rule from equality. The record-size word is ignored across
all seven controls through `UINT32_MAX`. Exactly cue types 1/2 and time units
75/150/1000 mutate. Invalid slot, cue-type, and time-unit values can still
return status zero with one pristine getter record, so wire status alone is
not mutation admission. Option lengths 0 and `UINT32_MAX` commit only the
56-byte fixed record; 1 and 65/66/67 produce the canonical 124-byte record.
Backend comparison is deferred.

The first `UINT32_MAX` record/repeat pair disagreed only because the immediate
getter consumed a status-50 reply echoing the earlier `0x2401`. A dedicated
lifecycle suite now reads without sending between the setter and getter. In
three independent zero-delay processes, two setters first returned `0100 []`
and the no-send read on the replacement socket received
`4e02 [2401, 50, 0, empty_blob, 0]`; the third setter received that rejection
directly and the no-send read timed out. Both later getters in all three runs
returned the pristine 124-byte record. This proves a response-timing race and
explains the original apparent getter mismatch. The complete 20-cell matrix
crosses same connection, waiting before reconnect, and waiting after reconnect
at 0/50/100/250/500/1000/3000 ms where applicable, with three independent
fixture/process observations per cell. All 60 declared observations completed.

Every same-connection arm returned transaction `0xfffffffe`, kind `0x0100`,
then EOF on the no-send read and on a getter attempted through that socket.
Waiting 50 through 3000 ms before reconnecting produced no late frame in all
18 observations. Reconnecting first exposed the queued status-50 `0x2401`
reply in 13 of 21 observations, including one of three after a 3000-ms wait;
the other eight timed out. Two setter reads received the correlated rejection
directly, while the other 58 received the generic close sentinel. Both fresh
getters returned the pristine record in every observation. This proves that
the generic envelope closes the request socket and that the correlated reply
is routed to an available connection rather than retained on the originating
socket. The static command-format table declares `0x2401` as
`number, number, number, number, blob, number`.
`PSvDBConnection::ReceiveCommand` takes the blob size from the preceding
numeric slot, admits only `1..0x4fffff`, and exits its argument loop without
invalidating the command for `UINT32_MAX`. The zero-initialized blob pointer
and record count reach the setter's status-50 guard. Drop/Listen/destructor
paths independently construct the `0xfffffffe/0x0100` close sentinel, while
the real transaction-1 rejection is queued by player/device identity and can
reach a replacement socket **[RB-DEC, OBS]**.

Admitted slot 8 has no matching membership. In three cold processes, setter
and immediate getter timed out while Rekordbox remained responsive, no new
Application events appeared, and the logical database stayed pristine. The
same-database restart getter returned the identical status-zero 124-byte
baseline in all three runs.

Returned-slot count `UINT32_MAX` has the inverse database result. All three
setters and immediate getters timed out with a responsive process and empty
Application log, but every logical snapshot contained the canonical mutation.
After a same-database restart, all three getters returned status zero and the
same 124-byte mutated record. A reproducible vtable audit binds setter method
slot `+0x288` to `getHCBnkCuePointExt`; the successful path completes its last
database update before loading the returned-slot count and calling that getter.
The extreme count therefore stalls reply construction after durable mutation
**[OBS, DB, RB-DEC]**.

## 2026-10-02: Legacy Hot Cue setter parser matrix design

**Question:** Which `0x2201` record, length, flag, extension, and ContentID
boundaries are admitted, which mutate membership state, and which terminate the
Rekordbox process after the handler's post-error ContentID read?

**Method [OBS, RB-DEC]:** Fifty-seven generated suites isolate nine actual
cue lengths, six declared cue lengths, twelve flag values spanning both edges
of `0x00040000..0x0006ffff` plus the observed `0x00040100`, six actual and six
declared extension lengths, four ContentIDs, and zero/maximum values for record
words 2-8. Each suite contains only the setter. The recorder requires two fresh
fixture/process runs, captures Windows process and Application-log health,
copies the live database with any WAL/SHM sidecars, and performs a six-slot
getter only after confirmed process survival. Getter timeout is a recordable
outcome. A timeout, exact post-setter dbserver-connect failure, or setter
process exit triggers a same-database process restart, second getter, health
capture, and logical snapshot so process-local serving state is separated from
durable mutation. Receipts preserve every raw observation. The reducer compares
stable crash signatures and durable restart state while reporting exact raw
transport repetition separately.

**Current evidence:** The encrypted baseline has database SHA-256
`360b18b44de76c47360f1f3f5c6193c895e053f08cad536a8e4d8872872cb0b3`
and six pristine D/E/F memberships. Generator/request/summary tests pass. The
strict machine summary has accepted all 57 repeat pairs across 114 independent
Rekordbox processes and reports no pending probes.
This completes the nine-variant actual-cue-length axis: all 18 processes remain
responsive, eight pairs are database-pristine, and length 36 alone mutates.
Actual cue length zero makes both setter and immediate getter time out while
the process stays responsive, the Application log stays empty, and the
database remains pristine. Same-database restart restores the identical
status-zero, three-record, 372-byte getter in both runs. Backend comparison
remains deferred **[OBS, DB]**.

Actual cue lengths one, three, and four return a status-1 `0x4702` with zero
records, leave the database pristine, and permit the canonical immediate
getter in all six runs. This establishes the lower boundary through four
bytes: zero stalls serving until process restart, while all three tested
nonzero short forms take the normal rejection path **[OBS, DB]**.

Seven, eight, 35, and 37 actual bytes produce a different repeat-verified envelope: status 0 and
two ordinary cue records, despite a pristine membership database. The rejected
short record contains enough ContentID material for the handler's unconditional
offset-`+4` dword read to resolve fixture track 10001; the subsequent
`GetUsbCue` call supplies that track's two `djmdCue` records. This is successful
post-error query serving, not a successful setter mutation **[OBS, DB, RB-DEC]**.

Exactly 36 actual bytes admit the mutation in both fresh-process runs. The
setter returns status 0 and the same two ordinary cue records, while the live
WAL-backed snapshot changes only membership 94201. Its nine legacy fixed
fields become the request sentinels: `InMsec=0x77777777`,
`InFrame=0x11111111`, `InMpegFrame=0x33333333`,
`InMpegAbs=0x55555555`, `OutMsec=0xffffffff`,
`OutFrame=0x22222222`, `OutMpegFrame=0x44444444`,
`OutMpegAbs=0x66666666`, and `Color=-1`. The immediate extended getter remains
status 0 with three records, but its payload is 304 bytes with record lengths
56/124/124 instead of the pristine 372-byte 124/124/124 shape. The reducer
validates every length prefix and binds this changed getter shape into repeat
equality. The 37-byte neighbor returns the canonical pristine 372-byte getter,
so the 35/36/37 cross proves that mutation requires actual record length equal
to 36 rather than merely at least 36 **[OBS, DB]**.

The complete declared-length axis keeps 36 actual bytes and tests declarations
0, 1, 35, 36, 37, and `UINT32_MAX`. Values 0/1/35 return the identical 20-byte
kind-`0x0100` message with zero arguments, preserve the database, and permit the
canonical immediate getter. Declaration 36 returns the ordinary status-zero
`0x4702` with two cue records, mutates membership 94201, and produces the
304-byte 56/124/124 getter. Declaration 37 also returns the ordinary two-record
reply, but its database and 372-byte getter stay pristine. Mutation therefore
requires declared length equal to 36, while the overlong neighbor still reaches
the post-error ContentID query **[OBS, DB]**.

Declared `UINT32_MAX` returns the same empty kind-`0x0100` message as the short
declarations and leaves the database pristine, but both immediate getters time
out while Rekordbox remains responsive with empty Application event windows.
Same-database restart restores the identical status-zero, three-record,
372-byte 124/124/124 getter in both runs. The extreme declaration therefore
creates process-local serving state without durable mutation **[OBS, DB]**.

The flag axis begins with 0, `0x0003ffff`, and exact static lower edge
`0x00040000`. All three return status-zero `0x4702` responses containing the
same two ordinary cue records. The first two leave the database and canonical
372-byte getter pristine. Exact `0x00040000` changes only membership 94201 and
produces the changed 304-byte 56/124/124 getter in both runs. This live
three-point cross proves that the decompiled mutation interval's lower bound is
inclusive **[OBS, DB, RB-DEC]**.

Accepted flags `0x00040000`, `0x00040001`, and observed `0x00040100` all
select and mutate membership 94201. Their persisted rows match in every
semantic field except `OutMsec`: the low-byte-one form stores extension word 1
as `0x88888888`, while the low-byte-zero forms store `0xffffffff`. The static
setter makes the same split at `0x1016d2954..0x1016d29aa`, testing cue byte 0
against 1 before choosing extension word 1 or `-1`. The high word therefore
selects the ordinal while the first low byte independently selects loop
semantics; the observed `0x0100` bit does not mark a loop **[OBS, DB, RB-DEC]**.

Flag `0x0004ffff` also mutates membership 94201 but stores
`OutMsec=0xffffffff`, proving the byte-0 test is equality with 1 rather than
nonzero truth. Raising the high word to `0x0005` with flag `0x00050000`
redirects the otherwise identical mutation to row-zero E membership 94203.
The extended getter's compact changed record follows the selected ordinal and
moves to its second position, yielding 124/56/124 record widths and the same
304-byte total. `0x0005ffff` repeats that E-membership route and getter layout
while storing `OutMsec=0xffffffff`, so the high-word route and byte-0 loop
predicate remain independent across ordinals 4 and 5. `0x00060000` completes
the admitted high-word cross by changing only row-zero F membership 94205;
the compact getter record moves to its third position, yielding 124/124/56
record widths and the same 304-byte total. `0x0006ffff` preserves that F route
and layout while storing `OutMsec=0xffffffff`, completing the low-byte-`0xff`
control across each admitted ordinal. Upper neighbor `0x00070000` and extreme
`0xffffffff` both return the ordinary status-zero, two-cue `0x4702` response
while preserving the database and canonical 124/124/124 getter. Together with
mutating `0x0006ffff`, they dynamically prove the exact inclusive upper edge;
all 24 flag-axis processes remained alive with empty Application event windows
**[OBS, DB, RB-DEC]**.

The first actual-extension-length control sends no extension bytes and declares
length zero. Both cold-process runs still mutate membership 94201 and return
the changed 56/124/124 getter, with `OutMsec=0xffffffff`. The live result
matches the decompiled zero-filled local-value path and proves that the
extension blob is optional for the non-loop cue form **[OBS, DB, RB-DEC]**.
A one-byte extension containing `0x77` also mutates in both runs, but stores
`InMsec=0x00000077`; its remaining semantic fields match the zero-byte case.
The pair directly demonstrates little-endian zero-padding of short extension
data. Seven actual bytes store `InMsec=0x77777777`; the partially present
second dword remains semantically unused by the non-loop flag, so
`OutMsec=0xffffffff`. Exact actual length eight produces the identical stored
row and getter, closing the short-copy branch at its boundary
**[OBS, DB, RB-DEC]**. Actual lengths 9 and 16 then produce the same semantic
membership row, setter-response signature, and getter payload hash as length
8. The alternate `>8` path therefore reads exactly the first eight bytes and
ignores the remainder **[OBS, DB, RB-DEC]**.

Declared extension length zero, with eight actual bytes still present, commits
membership 94201 using zero-filled `InMsec=0` and non-loop
`OutMsec=0xffffffff`. Both setters nevertheless return a generic empty
`0x0100`; the independent immediate getter returns the changed 56/124/124
records. Reply shape and durable effect are therefore independent on this
boundary **[OBS, DB]**.

Declared extension length one crashes Rekordbox before a reply in both
canonical cold runs. Each setter disconnects, each Windows Application event is
the same `ntdll.dll` heap-corruption exception `0xc0000374` at fault offset
`0x00000000001176e5`, and each logical database snapshot is pristine. The
process is absent before the immediate getter. Restarting Rekordbox against the
same database restores the canonical status-zero, three-record, 372-byte getter
with 124/124/124 record widths and no database change in both runs. Two retained
incomplete discovery runs caught the same crash as a setter timeout followed by
a stale advertised dbserver port. Those timing observations are provenance,
not canonical results **[OBS, DB]**.

Declared extension length seven reaches the same exception after a delayed
transport sequence. Both setters time out with two Rekordbox processes still
visible and no initial Application event. Both immediate getters then fail to
connect to the advertised dbserver port; the bound follow-up health captures
zero processes and the identical `ntdll.dll` exception `0xc0000374` at fault
offset `0x00000000001176e5`. Both logical databases remain pristine. Both
same-database restarts return the canonical 372-byte getter, making the complete
timeout/dead-port/crash/restart lifecycle an exact repeat **[OBS, DB]**.

Declared extension lengths eight and nine are semantically identical across
all four cold runs. Each setter returns the same status-zero, two-record
`0x4702`; each snapshot changes only membership 94201 to normalized row digest
`eeae79ab0e4d9506b78381c6a6acb431bb1242e1c1b6615bf52e4cb4b00c5dfe`;
and each immediate getter's port query times out while Rekordbox remains alive
with an empty Application-event window. Same-database restart returns the same
changed 56/124/124 getter blob, SHA-256
`ffccd8cf995f3ae589e82e349da64655e2f0a7cc40b2f88120118284cb9f6dd2`.
The one-byte overdeclaration is ignored semantically within this pair
**[OBS, DB]**.

The exact length-eight request has request fingerprint
`9b7300807e8244b915d869ae1e8269778a32579ead927f1d28444600b9740925`.
It is byte-for-byte identical to the neutral cells for actual cue length 36,
declared cue length 36, flag `0x00040100`, actual extension length eight, and
ContentID 10001 and fixed word 2 equal to zero. The four earlier pairs served
their immediate getters; the three later pairs did not. The strict reducer now reports the seven equivalent
variants as one request group with two lifecycle signatures. The declared
interleaved control places the same request before and after each crashing
probe, then repeats after a complete isolated-VM restart, while holding fixture,
identity, setup width, and request bytes fixed. Its executable two-cycle
recorder declares 12 request observations and four isolated-VM restarts,
captures helper/listener/process/Application/database/getter state, and binds
each phase and cycle with SHA-256 receipts **[OBS]**.

The completed control validates all 12 request observations and four restart
receipts. All eight canonical observations have lifecycle signature
`1d51b292ceb35074a916f9a1d708a7d8fabb9ecf926770cd7c7462be3d8cfd4f`:
the setter returns status-zero `0x4702`, commits the same membership mutation,
the immediate getter reaches a port-query timeout while Rekordbox remains
alive, and a same-database restart exposes the identical changed getter. The
signature is invariant before either malformed request, after each malformed
request, and after the full isolated-VM restart **[OBS, DB]**.

Both declared-length crash phases repeat their pristine database and restart
effects exactly. Transport and event telemetry vary: cycle 1 captures the
known `0xc0000374` Application Error in both phases, while cycle 2's event
windows are empty; declared length seven disconnects after process exit in
cycle 1 but times out before the process disappears in cycle 2. These are
separate lifecycle groups in the strict summary, not discarded outliers. The
final summary SHA-256 is
`8b2751c6aaf3e10c2377731fa4fcdc79f30f9f8ccd081024c62332ac81a5034c`.
Its finalization receipt binds both cycle receipts, records a successful
66-test gate, restores `play-paths`, verifies zero synthetic identities, and
stops the isolated VM **[OBS, DB]**.

ContentID zero is repeat-verified. It changes membership 94201 in both cold
processes, but `GetUsbCue(0)` returns status 1 and zero cue records in the
setter's `0x4702`. Both immediate port queries timed out in the late recording
epoch; same-database restart returned the durable changed 56/124/124 getter.
The zero-record response is attributable to ContentID resolution, while the
listener state remains assigned to the interleaved history question
**[OBS, DB]**.

ContentID 999999 is also a complete exact repeat. Both setters persist 999999
to membership 94201 and return status zero with one 36-byte cue record. The
late-epoch immediate port query times out; restart exposes the durable changed
56/124/124 getter. ContentID resolution therefore distinguishes zero records
with status one at ID zero, one record with status zero at 999999, and two
records with status zero at fixture ContentID 10001 **[OBS, DB]**.

ContentID `UINT32_MAX` completes the axis as an exact transport repeat. Both
setters persist decimal `4294967295` to membership 94201, return status one and
zero cue records in `0x4702`, and leave Rekordbox alive without an Application
event. Both immediate port queries time out; both same-database restarts return
the identical durable 304-byte getter with widths 56/124/124. The response
matches ContentID zero's unresolved status/count while the stored value remains
distinct, proving that persistence precedes and is independent of the
ContentID-keyed cue lookup **[OBS, DB]**.

Static setter analysis maps cue words 3-8 directly to `InFrame`, `OutFrame`,
`InMpegFrame`, `OutMpegFrame`, `InMpegAbs`, and `OutMpegAbs`. Word 2 at offset
`+0x08` is never loaded by `PSvAppSyncDBIF::setHCBnkCuePoint`. The fourteen
zero/maximum pairs dynamically confirm those seven word positions
**[RB-DEC, OBS, DB]**.

The word-2-zero pair is now complete. It sends the canonical zero word and is
therefore byte-identical to the six earlier neutral cells. Both setters return
the same two-cue response and persist the same semantic row; both immediate
port queries time out; both restarts return the same 56/124/124 getter. It adds
a seventh nominal variant to the request-equivalence group and a third pair to
its late lifecycle signature. Because it does not change the canonical word,
the result does not yet dynamically prove the static non-read; the maximum
control remains necessary **[OBS, DB, RB-DEC]**. That control is now also an
exact repeat: `UINT32_MAX` changes the request fingerprint to
`82f654925386a7db212c8ca28177dacaf0acd6343ca19ae5f76864a9abf245a5`
but leaves the setter response signature, complete semantic membership row,
port-query-timeout/restart lifecycle, and restarted getter blob identical to
the zero pair in all four observations. Word 2 is therefore dynamically ignored
on the active AppSync path **[OBS, DB, RB-DEC]**.

Both word-3 pairs are also complete. Changing only that word between zero and
`UINT32_MAX` changes only `djmdSongHotCueBanklist.InFrame`, storing `0` or
`4294967295` in both independent processes. The setter response signature and
every other semantic membership property remain identical; all four
observations share the same port-query-timeout followed by durable restart
getter. This live result exactly confirms the decompiled `+0x0c -> InFrame`
load **[OBS, DB, RB-DEC]**.

Both word-4 pairs then change only `djmdSongHotCueBanklist.OutFrame`, storing
zero or `4294967295` across their four cold-process observations. The setter
response signature and every other semantic property remain fixed, exactly
confirming the static load from cue offset `+0x10` **[OBS, DB, RB-DEC]**.

The word-5 zero/maximum pairs change only
`djmdSongHotCueBanklist.InMpegFrame`, again preserving the common setter
response and every other semantic membership field across four observations.
Stored values remain exact unsigned `0` and `4294967295`, confirming cue offset
`+0x14` **[OBS, DB, RB-DEC]**.

The word-6 zero/maximum pairs change only
`djmdSongHotCueBanklist.OutMpegFrame`. Both independent processes retain exact
unsigned `0` or `4294967295`; the common setter response and every other
semantic membership field are invariant. Their immediate port queries time
out while Rekordbox remains alive, and same-database restart exposes each
durable mutation through the extended getter. This confirms cue offset
`+0x18` **[OBS, DB, RB-DEC]**.

The word-7 zero/maximum pairs change only
`djmdSongHotCueBanklist.InMpegAbs`, storing exact unsigned `0` and
`4294967295` across their four cold-process observations. The setter response,
other semantic membership fields, immediate listener timeout, and durable
restart getter remain invariant. This confirms cue offset `+0x1c`
**[OBS, DB, RB-DEC]**.

The final word-8 zero/maximum pairs change only
`djmdSongHotCueBanklist.OutMpegAbs`, storing exact unsigned `0` and
`4294967295` across four cold-process observations. The common setter response,
other semantic membership fields, immediate listener timeout, and durable
restart getter remain invariant. This confirms cue offset `+0x20` and closes
the complete fixed-word map **[OBS, DB, RB-DEC]**.

Declared extension length `UINT32_MAX` returns empty `0x0100`, leaves the
database pristine, and keeps Rekordbox alive with no Application event in both
runs. The separate immediate getter records a protocol timeout. Restarting the
process against the same database restores the canonical 372-byte pristine
getter in both runs **[OBS, DB]**.

An earlier pre-revision run of actual cue length zero recorded setter and
immediate-getter timeouts while Rekordbox remained responsive with no new
Application events. It ended before database capture and has no completion
receipt, so it is retained only as discovery provenance under
`data/experiments/hot-cue-bank/legacy-setter-parser/discovery/`. The revised
recorder repeated it twice with database and same-database restart evidence;
the strict partial reducer now promotes the canonical result above **[OBS]**.

## 2026-10-02: Hot Cue Bank buffer lifetime across device disconnect

**Question:** Does Rekordbox clear the context-keyed `djmdLeftBuf` rows when a
player disappears, or only when another query clears that exact context or the
Rekordbox process restarts?

**Method [OBS, RB-DEC]:** The warmup suite populates location 1 with the
three-row root. The post suite sends a one-row Beta Folder header at location 2,
first renders old location 1, then renders current location 2 as a health
control. A control arm keeps the player identity present. The rejoin arm stops
the identity for 40 seconds before restarting the same XDJ-RX3/player-1
identity. Both arms use cold Rekordbox processes and run twice. Static
`PSvDBMain::Disconnect` clears filter and AIO state and requests a device drop,
but contains no direct `DsqlListBuf_Clear` call.

**Current evidence:** The strict reducer accepted both control runs and both
40-second disappear/rejoin runs. Every post sequence renders item 9002 from the
old location-1 root and item 9032 from the current location-2 Beta buffer, with
one common behavior signature across all four observations. Rekordbox therefore
retains the context-keyed list buffer across discovery disappearance and
same-identity rejoin. The first rejoin attempt used browser-space coordinates
and failed its port query; generation n repeated the arm with direct guest RFB
activation and retained bounded attempt logs. Only the completed captures enter
the strict summary. Backend comparison remains deferred **[OBS]**.

## 2026-10-02: Genuine CDJ-2000nexus status matrix

**Question:** Does a genuine generation-2 CDJ status shape alter ordinary
menus, Display classification, Song Info dispatch, or Hot Cue behavior relative
to the authentic RX3 and derived CDJ-3000 controls?

**Method [CAP, OBS]:** Dysentery's `S05-link-browse` capture supplies an
unmodified 284-byte `CDJ-2000nexus` player-1 status payload. The paired lab
keepalive preserves the captured CDJ class, generation 2, presence 1, model
code 0, and peer count 2 while using the isolated address and project MAC. A
validated raw-packet path rejects length, header, model, or player mismatch
before transmission. Thirteen existing backend-neutral suites declare 249
cases across ordinary extended/legacy menus, baseline and packed Display,
packed Play, Delivery and all recognized no-builder kinds, and Hot Cue catalog
and direct getters.

**Result [CAP, OBS]:** The strict reducer accepted all 13 variants and all 249
cases, with a fresh-fixture/process repeat and hash-bound receipt for every
golden. Every semantic response envelope matches its derived CDJ-3000 control.
Twelve raw envelopes match exactly. The Display baseline's raw envelope differs
only in render-request pagination: the genuine suite requests six pages of
`3/3/3/3/3/1`, while the reference requests one page of 16; both flatten to the
same ordered 16 rows with identical headers and outcomes. No tested ordinary,
Display, Play, Delivery/no-builder, Hot Cue catalog, or direct-getter behavior
diverges semantically for this authentic status shape. Backend comparison is
deferred.

## 2026-10-02: Persisted secondary columns in legacy setup

**Question:** Do all 15 persisted secondary-column selections preserve their
Sort-menu behavior and the first 12 extended track-row arguments when the
client negotiates legacy setup?

**Method [OBS, DB]:** Fifteen generated legacy suites reuse the exact
encrypted settings fixture and the `sort-menu` and `track-rows` cases from each
extended selection. Every suite is recorded against real Rekordbox 7.2.19 and
verified after a fresh fixture activation and process start. A hash-bound
receipt binds the suite, fixture manifest, identity, and promoted golden. The
strict reducer compares every legacy row with the exact 12-argument prefix of
its 16-argument extended partner.

**Result [OBS, DB]:** The strict reducer accepted 15/15 variants and all 30
cases. Every golden has a hash-bound fresh-fixture/process repeat receipt.
Sort-menu behavior, totals, row counts, and row kinds match the extended
partners, and every legacy row equals the exact first 12 arguments of its
16-field partner. This includes the unchanged server-authored BPM/Key and
Key/BPM composites in argument 5 and their packed types in argument 6. Backend
comparison is deferred.

## 2026-10-02: Extended Hot Cue setter mutable-field matrix

**Question:** How does real Rekordbox canonicalize or reject every mutable
non-seek field in an accepted `0x2401` record at zero, signed boundary, high-bit,
and maximum wire values?

**Method [OBS, DB]:** Fifty-six generated suites vary exactly one field in
the canonical duplicate-slot mutation record. Six signed 32-bit axes cover
`InMsec`, `OutMsec`, and all four MPEG frame/absolute values at `0`, `1`,
`INT32_MAX`, `INT32_MIN`, and `-1`. Complete byte controls cover color and
color-table index; the same five 32-bit bit patterns cover CueMicrosec and
BeatLoopSize. Six comment records cover empty, ASCII, Unicode, embedded NUL,
an unpaired high surrogate, and the maximum even `uint16` byte length. The
maximum record is 65,658 bytes and remains below the command blob ceiling.

Every variant starts from the same encrypted fixture, restarts Rekordbox,
sends one setter, and performs a fresh-connection `0x2301` database-backed
read. A second complete fixture reset and process restart must match before its
golden is promoted. After each run, the recorder copies the encrypted base and
any WAL/SHM sidecars to temporary host storage, extracts the complete logical
membership state, and retains the logical snapshot plus source hashes. This
proves `ColorTableIndex` and other database fields that the getter omits. The
strict reducer requires identical semantic membership state and a hash-bound
receipt across record and repeat. Nonempty seek descriptors are excluded from
this batch because the known process exit requires a health-aware recorder.

**Result [OBS, DB]:** The strict reducer accepted all 56 variants and 112
independent fixture/process executions. Every axis returns status zero and has
matching logical database state across record and repeat. The unpaired-high-
surrogate case persists bytes `ed a0 80` in the mutated Comment in both runs.
The snapshotter records undecodable TEXT as explicit encoding/hex data, so the
database proof remains lossless and JSON-safe.

The maximum-length request carries a 65,658-byte record containing 32,766
`A` code units and a terminator. Rekordbox persists all 32,766 characters and
returns status zero. Its setter and getter responses each declare a 65,656-byte
record, two bytes shorter than the request. The raw-probe API performs one
8,192-byte read, so neither response is complete enough for the ordinary
message decoder. The reducer admits this shape only for the exact maximum
variant and validates the protocol magic, `0x4e02` kind, five argument tags,
echoed `0x2401`/`0x2301` request, zero status, matching numeric/blob record
lengths, exact 8,192-byte prefix hashes, complete database value, and
independent repeat. All other 55 variants still require a decoded getter.

## 2026-10-03: BPM tolerance inclusion boundaries

**Question:** Are the special zero-percent whole-BPM bucket and percentage
boundaries inclusive on the Windows AppSync path, including their asymmetric
rounding and integer truncation?

**Method [OBS, DB, RB-DEC]:** A deterministic encrypted fixture contains 43
tracks at every lower endpoint, upper endpoint, and immediate one-hundredth
outside neighbor for selected BPM 120.00 and tolerances 0 through 6. Seven
`0x1206` requests were recorded and repeated after a complete fixture reset
and Rekordbox restart. The strict reducer requires exact response equality,
unique database-backed item IDs, nested result sets, and the statically
derived boundary map.

**Result [OBS, DB]:** Tolerance zero includes the asymmetric interval
119.50–120.49 and excludes 119.49/120.50. Tolerances 1–6 include both
`12000 * (100 - p) / 100` and `12000 * (100 + p) / 100` after integer
truncation, while excluding the values immediately outside. Fixture overlap
produces exact nested totals 5, 11, 17, 23, 29, 35, and 41. Record and repeat
are identical across all seven cases. This dynamically closes the predicate
already localized in `getRowset_Track` and `wherefuncGetRowset_Vals`.

## 2026-10-03: Fileless adjacent payload services

**Question:** What does each artwork, analysis, and cue-adjacent command expose
when its database selector exists but no corresponding payload file or cue row
can produce data?

**Method [OBS, DB, RB-DEC]:** The 196-case suite crosses all 16 exact service
kinds through packed types 0-6, zero/maximum selectors or contexts,
representative locations, and the specified-atom gates. Two complete
fresh-fixture/process passes must be byte-identical. Health snapshots bracket
each pass, and the reducer asserts the exact case outcome, reply message, wire
length, suite hash, database hash, and fixture fingerprint.

**Result [OBS]:** Record and repeat are identical: 176 cases return one direct
reply and 20 time out without bytes. Non-type-1 `2003`/`2103` controls are
silent. The four log-only analysis kinds return `0x4003` for ordinary packed
type controls but are silent for all-zero/all-ones contexts. Every remaining
case returns its service-specific empty/error envelope, including status-zero
`2504`, scalar-zero `2804`, status-one empty legacy/extended cue replies, and
status-50 empty specified-atom replies. Rekordbox remains one healthy process
with no Application events before and after both complete passes. The exact
16-service table is in `ADJACENT_PAYLOAD_SERVICES.md`.

## 2026-10-03: Malformed artwork `0x2003`

**Question:** How does the direct artwork handler distinguish absent arguments,
wrong tag types, missing or string identifiers, and trailing arguments?

**Method [OBS]:** Six generated one-case suites each receive an independent
fixture-reset Rekordbox process for record and repeat. Every receipt binds the
suite, fixture, RX3 identity, golden, and schema-2 health before and after both
requests. The strict reducer requires a clean responsive start and normalized
post-request health equivalence.

**Result [OBS]:** No arguments produces no bytes and ends in `WouldBlock`.
A numeric packed context without an identifier, a string identifier, and an
extra trailing number all return the same 39-byte
`4002(2003, 50, 0, empty)` response. A string or blob in the packed-context
position returns the generic 20-byte empty `0100()` message. All six record
and repeat phases end with one responsive Rekordbox process and no Windows
Application events. This closes the `0x2003` family; the remaining malformed
families continue in the guarded queue.

## 2026-10-03: Malformed waveform artwork `0x2103`

**Question:** Does the second artwork handler apply a distinct malformed-
argument policy, or does it preserve the `0x2003` dispatch shape while echoing
its own request kind?

**Method [OBS]:** The same six generated argument shapes run as independent
cold-process record/repeat pairs. Each canonical pair binds its suite, fixture,
identity, golden, and four schema-2 health captures. One interrupted repeat for
the string-identifier shape was quarantined without a receipt; the retained
record candidate was promoted only after a new cold repeat matched it.

**Result [OBS]:** The malformed policy is identical to `0x2003` apart from the
echoed kind. No arguments is silent through `WouldBlock`; string and blob
packed-context tags produce the 20-byte empty `0100()` message; and numeric
context alone, a string identifier, or an extra numeric argument produces the
39-byte `4002(2103, 50, 0, empty)` response. All six canonical pairs retain one
responsive Rekordbox process and zero Windows Application events before and
after both requests. Twelve of 96 malformed cases are complete; the remaining
84 continue in the guarded queue.

## 2026-10-03: Malformed preview waveform `0x2004`

**Question:** Which of the unusual five declared tag slots are required before
the preview-wave handler reaches its kind-specific empty response?

**Method [OBS, RB-DEC]:** Six cold-process record/repeat pairs vary absent
arguments, the packed-context tag, the ContentID tag, and the normally omitted
fifth zero-length-blob slot. The static service map binds the request to
`PSvDBMain::GetWave`, the database-interface analysis-path lookup, and the
sequential DAT `PWAV`/`PWV2` readers. Every receipt binds its golden and four
schema-2 health captures.

**Result [OBS]:** No arguments is silent through `WouldBlock`. String or blob
packed-context tags and a string ContentID return the 20-byte empty `0100()`
message. A numeric context alone inside the fixed five-slot declaration
defaults the later values and returns `4402(2004, 50, 0, empty)`. Supplying the
ordinary four numeric arguments plus a numeric fifth tag returns the same
39-byte kind-specific response, so the nominally omitted blob's tag type is
not enforced on this empty-data path. All six canonical pairs retain one
responsive process and zero Windows Application events. Eighteen of 96
malformed cases are complete; the remaining 78 continue in the guarded queue.

## 2026-10-03: Malformed legacy cue retrieval `0x2104`

**Question:** How does the legacy cue builder distinguish malformed context,
missing or wrong-type ContentID, and trailing arguments before its database
lookup?

**Method [OBS, DB, RB-DEC]:** Six independent cold-process record/repeat pairs
exercise the two-argument `CMD_GET_USB_CUE` contract. The static map binds it
to `PSvDBMain::GetUsbCue` and the AppSync callback or undeleted `djmdCue` rows
filtered by ContentID. One context-only repeat failed during cold setup before
a response, was quarantined with only pre-health evidence, and matched the
retained record candidate on fresh attempt 2.

**Result [OBS]:** No arguments is silent through `WouldBlock`. String and blob
context tags return empty `0100()`. Numeric context alone, numeric context plus
a string ContentID, and the ordinary request plus a trailing number all return
the same 64-byte empty legacy-cue `4702`: request kind `0x2104`, status 1,
record width 36, two empty blobs, and zero record/count fields. All six final
pairs retain one responsive process and zero Windows Application events.
Twenty-four of 96 malformed cases are complete; the remaining 72 continue in
the guarded queue.

## 2026-10-03: Malformed quantize data `0x2204`

**Question:** Does quantize-data retrieval share the legacy-cue parser gate,
and which malformed forms still reach its beat-grid builder?

**Method [OBS, DB, RB-DEC]:** Six cold-process record/repeat pairs cover the
two-argument context/ContentID contract. Static evidence binds the request to
`PSvDBMain::GetQtzInf`, database-interface analysis-path lookup, and DAT
`PQTZ` parsing through `MstLoadBeatGrid` and
`MstLoadBeatGridWithHeader`. Receipts bind every golden and health capture.

**Result [OBS]:** No arguments is silent through `WouldBlock`; string and blob
context tags return empty `0100()`. Numeric context alone, numeric context plus
a string ContentID, and the ordinary request plus a trailing number all return
the 45-byte `4602(2204, 50, 0, empty, 0)` envelope. Thus the first numeric tag
gates dispatch, while missing/wrong-type ContentID becomes an empty/default
lookup and trailing arguments are ignored. All six pairs retain one responsive
process and zero Windows Application events. Thirty of 96 malformed cases are
complete; the remaining 66 continue in the guarded queue.

## 2026-10-03: Malformed recognized log-only command `0x2304`

**Question:** How does a recognized arm without a payload builder distinguish
wrong context types, trailing tags, and an oversized tag-list declaration?

**Method [OBS, RB-DEC]:** Six cold-process pairs cover no arguments, string and
blob contexts, numeric context followed by a number or string, and one numeric
context carried by a header declaring 32 tag slots. The recovered arm reads
only the track-type byte, logs, and returns internal `-2`; it has no recovered
database or filesystem dependency.

**Result [OBS]:** No arguments is silent through `WouldBlock`. Wrong context
types return 20-byte empty `0100()`. With a valid numeric context, both numeric
and string trailing tags are ignored and return the recognized 26-byte
`4003(2304)` error. Declaring 32 slots returns `0100()` despite the valid
context, proving a framing-width rejection before the command arm. All six
pairs retain one responsive process and zero Windows Application events.
Thirty-six of 96 malformed cases are complete; the remaining 60 continue in
the guarded queue.

## 2026-10-03: Malformed disc-cue log-only command `0x2404`

**Question:** Does `CMD_GET_DISC_CUE` share the complete parser/framing policy
of adjacent log-only `0x2304`?

**Method [OBS, RB-DEC]:** The same six cold-process shapes cover no arguments,
wrong context types, two trailing-tag types, and the 32-slot header. Static
analysis identifies another arm that reads the track-type byte, logs, and
returns internal `-2`, with no recovered database or filesystem dependency.

**Result [OBS]:** The policies are equal after substituting the request kind.
No arguments is silent; string/blob contexts and the 32-slot declaration yield
empty `0100()`; a valid numeric context followed by either a number or string
yields `4003(2404)`. Every pair retains one responsive process and zero Windows
Application events. Forty-two of 96 malformed cases are complete; the
remaining 54 continue in the guarded queue.

## 2026-10-03: Malformed VBR information `0x2504`

**Question:** Does the fixed-size VBR builder reuse the quantize-data argument
gate, and what status does it assign to malformed/default lookups?

**Method [OBS, DB, RB-DEC]:** Six cold-process record/repeat pairs exercise the
context/ContentID contract. Static analysis binds the request to
`PSvDBMain::GetVbrInf`, database-interface analysis-path lookup, and DAT
`PVBR` loading through `MstLoadVBR`; successful data is fixed at 1,604 bytes.

**Result [OBS]:** No arguments is silent through `WouldBlock`; string and blob
contexts return empty `0100()`. Numeric context alone, numeric context with a
string ContentID, and an ordinary request plus a trailing number all return
the 39-byte `4502(2504, 0, 0, empty)` envelope. The parser gate therefore
matches `0x2204`, while VBR failure uses status zero instead of 50. Every pair
retains one responsive process and zero Windows Application events. Forty-
eight of 96 malformed cases are complete; the remaining 48 continue in the
guarded queue.

## 2026-10-03: Malformed disc-eject log-only command `0x2604`

**Question:** Does `CMD_INFO_DISC_EJECT` share the parser and framing policy
of the adjacent recognized log-only commands, and does it touch persistent or
file-backed state?

**Method [OBS, RB-DEC]:** Six independent cold-process record/repeat pairs
cover no arguments, string and blob contexts, numeric context followed by a
number or string, and a numeric context in a header declaring 32 tag slots.
Static analysis identifies a recognized arm that reads only the packed
context's track-type byte, logs, and returns internal `-2`; it has no recovered
payload builder, database query, or filesystem dependency.

**Result [OBS]:** No arguments is silent through `WouldBlock`. String and blob
contexts return the 20-byte empty `0100()`. A valid numeric context followed
by either trailing-tag type returns the 26-byte `4003(2604)`, while the 32-slot
declaration returns `0100()` before the command arm. All six canonical pairs
retain one responsive process and zero Windows Application events. Fifty-four
of 96 malformed cases are complete; the remaining 42 continue in the guarded
queue.

## 2026-10-03: Malformed disc-ID registration status `0x2704`

**Question:** Does `CMD_ASK_DISCID_REGSTAT` expose a distinct parser or wire
response despite being another source-level log-only arm?

**Method [OBS, RB-DEC]:** Six independent cold-process pairs exercise omitted
arguments, both wrong context tags, numeric context followed by numeric or
string data, and a valid context under a 32-tag-slot declaration. The recovered
arm reads only the packed context's track-type byte and returns internal `-2`,
without a payload builder, database query, or filesystem path.

**Result [OBS]:** It matches the adjacent log-only policy exactly after
substituting request kind `0x2704`: no arguments is silent, wrong first-tag
types and the 32-slot header return 20-byte `0100()`, and both trailing-tag
forms return 26-byte `4003(2704)`. Every canonical pair retains one responsive
process and zero Windows Application events. Sixty of 96 malformed cases are
complete; the remaining 36 continue in the guarded queue.

## 2026-10-03: Malformed quantize offset `0x2804`

**Question:** How does the scalar quantize-offset request gate malformed
arguments, and how does it differ from the full beat-grid request `0x2204`?

**Method [OBS, DB, RB-DEC]:** Six independent cold-process pairs cover omitted
arguments, numeric context alone, string/blob context tags, string ContentID,
and a valid request followed by an extra number. Static analysis binds `0x2804`
to `PSvDBMain::GetQtzInf`, the same database-interface analysis-path lookup and
DAT `PQTZ` parser as `0x2204`, but to a scalar `0x4000` response.

**Result [OBS]:** No arguments is silent through `WouldBlock`; string and blob
contexts return empty 20-byte `0100()`. Numeric context alone, numeric context
plus a string ContentID, and the ordinary request plus a trailing number all
return the 32-byte `4000(2804, 0)` response. Thus missing/wrong-type ContentID
becomes a default zero-offset lookup after the first numeric tag passes, while
trailing data is ignored. Every canonical pair retains one responsive process
and zero Windows Application events. Sixty-six of 96 malformed cases are
complete; the remaining 30 continue in the guarded queue.

## 2026-10-03: Malformed partial waveform `0x2904`

**Question:** Which argument tags gate EXT `PWV3` waveform loading, and what
empty response does `LoadParWav` return for default lookups?

**Method [OBS, DB, RB-DEC]:** Six independent cold-process pairs cover omitted
arguments, numeric context alone, string/blob context tags, a string ContentID
with the required third zero, and an ordinary three-number request followed by
another number. Static analysis binds the request to database-interface
analysis-path lookup at `+0x180`, substitution of the EXT sibling filename,
`PSvDBMain::LoadParWav`, and its `PWV3` scanner.

**Result [OBS]:** No arguments is silent through `WouldBlock`; string and blob
contexts return 20-byte `0100()`. Numeric context alone, numeric context plus a
string ContentID and zero, and the ordinary request plus a trailing number all
return the 39-byte `4a02(2904, 50, 0, empty)` envelope. The context tag is the
early gate; missing/wrong-type ContentID becomes a default lookup, and trailing
data is ignored. Every canonical pair retains one responsive process and zero
Windows Application events. Seventy-two of 96 malformed cases are complete;
the remaining 24 continue in the guarded queue.

## 2026-10-03: Malformed segmented-key information `0x2a04`

**Question:** Does EXT `PKEY` loading use the same argument gate as partial
waveforms, and what kind-specific envelope represents a default lookup?

**Method [OBS, DB, RB-DEC]:** Six independent cold-process pairs cover omitted
arguments, numeric context alone, string/blob context tags, string ContentID,
and an ordinary two-number request followed by another number. Static analysis
binds the request to database-interface analysis-path lookup at `+0x180`, EXT
filename substitution, `PSvDBMain::LoadKeyInf`, and its `PKEY` scanner. A
successful reply has a 24-byte header and 12 bytes per segmented-key entry.

**Result [OBS]:** No arguments is silent through `WouldBlock`; string and blob
contexts return 20-byte `0100()`. Numeric context alone, numeric context plus a
string ContentID, and the ordinary request plus a trailing number all return
the 39-byte `4c02(2a04, 50, 0, empty)` envelope. Missing/wrong-type ContentID
therefore becomes a default lookup after the numeric context gate, and trailing
data is ignored. Every canonical pair retains one responsive process and zero
Windows Application events. Seventy-eight of 96 malformed cases are complete;
the remaining 18 continue in the guarded queue.

## 2026-10-02: Extended setter seek-descriptor health matrix

**Question:** Which seek descriptor lengths are parsed, can a truncated blob
reach the fixed 44-byte copy, and does a nonzero inbound validity update the
WAL before the setter reply enters the getter's known invalid free?

**Method [OBS, DB, RB-DEC]:** Seventeen generated setter-only suites cover
available record lengths 74, 81, 82, 121, 122, 123, and 124; declared
descriptor lengths 0, 1, 43, 44, 45, and `UINT32_MAX`; inbound validity 0, 1,
and `UINT32_MAX`; and an outbound-only validity control. The short records set
their option length to exactly the available bytes, exposing the static
eight-byte admission check and the separately capped 44-byte copy.

Each case runs twice from a fresh encrypted fixture and Rekordbox process. The
recorder preserves the setter result, post-request process count, new Windows
Application events, and a logical snapshot from the encrypted base plus any
WAL/SHM sidecars. The reducer requires identical response, process state, and
semantic membership state across both cold runs. This design can prove a
database update even when Rekordbox exits before returning a response.

**Result [OBS, DB]:** The strict summary validates all 17 variants and 34 cold
process runs. Available lengths 74, 81, 121, 122, 123, and 124 all return
status zero with the same canonical 124-byte record, leave one Rekordbox
process, preserve empty seek strings, and produce identical logical database
state in both runs. With 124 available bytes, declared descriptor lengths 0,
1, 43, 44, 45, and `UINT32_MAX` are behaviorally identical: each returns the
same status-zero record and leaves both seek strings empty.

Length 82 is the first form containing the complete eight-byte descriptor-
length word (`44`) and zero descriptor payload bytes. Both cold runs time out,
commit nonempty `InPointSeekInfo` and `OutPointSeekInfo` unsigned-decimal
triplets assembled from bytes beyond the supplied record, and overlap the
original process with an automatically launched replacement. One health
capture contains the expected `ntdll.dll` `0xc0000374` Application Error;
the other captures the same two-process shape before that event is visible.
The leaked numeric components intentionally differ between processes. The
strict reducer preserves each exact string but compares only the three-
component unsigned shape for this exact variant; every deterministic field
and every other variant remains exact-repeat constrained.

Inbound validity zero and the outbound-only-valid control both return status
zero and preserve empty strings. Inbound validity one persists exact strings
`1,3,1` and `2,4,0`; `UINT32_MAX` persists `1,3,4294967295` and `2,4,0`.
Both nonzero inbound variants then time out with `WouldBlock` and show the
original process overlapping an automatic replacement. The reducer asserts
these exact deterministic values, reply envelopes, and health classes rather
than accepting repeat agreement alone.

Generation `s3` retained seven complete runs before a transient noVNC
`app/ui.js` import failure interrupted the second 121-byte run. Hardened
generation `s6` archived incomplete and invalid-receipt attempts, retried each
entire fresh-fixture/process cycle, recomputed every receipt hash, and
completed the matrix. The retained interrupted attempts document recorder
recovery and are cleanup candidates only after the final queue receipt.

## 2026-10-02: Hot Cue Bank setter callback sink

**Question:** Does a successful Hot Cue Bank setter emit a Link Export
notification packet after its database mutation?

**Result [RB-DEC]:** The callback installed in `PSvDBMain` is the embedded
`PSvDBServerCallback` subobject of `UiProDJLink`. `DeliverHCBankUpdate` invokes
its virtual update method with `(class=3, id=CueID, extra=0)`. The concrete
class-3 branch translates that call to the in-process application method
`DatabaseIF::notifyDBUpdated(0x1e, CueID, 0)`. The traced chain contains no
socket send, packet serialization, or peer selection, so the setter callback
is an application database invalidation rather than a Link Export wire
notification. The focused instruction trace is retained in
`data/static-analysis/hot-cue-bank-notification-callback.disasm.txt`.

## 2026-10-02: Extended setter slot-8 lifecycle boundary

**Question:** Does extended setter record slot 8 produce an ordinary rejection
or mutation, and does its immediate getter behavior survive a Rekordbox process
restart against the same encrypted database?

**Discovery [OBS]:** The strict parser recorder reached
`slot-00000008` after promoting 26 earlier finite variants. Its first two
bounded record attempts never made LINK available. The third attempt sent the
setter successfully enough to advance to the fresh-connection canonical
getter, which timed out after five seconds instead of satisfying the required
raw-reply control. The recorder promoted no golden, removed its temporary
candidate, restored the baseline fixture, and exited nonzero. This observation
identifies a lifecycle boundary but does not establish whether the setter
mutated the database, stalled a worker, or produced a delayed reply.

**Method [OBS, DB]:** Slot 8 is delegated from the ordinary 57-entry matrix to
a three-replicate cold-process experiment. Each run retains a typed
setter plus immediate fresh-socket getter transcript with permissive outcomes,
timestamp-bounded process and Windows Application health, and a logical
snapshot made from the encrypted base plus any WAL/SHM sidecars. Rekordbox is
then restarted without replacing that database; a second getter, health
capture, and logical snapshot determine whether the state is durable and
readable after process restart. Every run has a hash-bound completion receipt.

The persistent baseline snapshot, two generated suites, matrix, recorder,
strict reducer, and declaration tests live under the extended-setter parser
evidence tree. The strict reducer accepted all three receipts. Every setter and
immediate getter timed out; every process remained responsive; every
Application-event window was empty; and every logical database snapshot was
pristine. After a same-database process restart, all three getters returned
status 0 with the same one-record, 124-byte baseline payload. Slot 8 therefore
creates a process-local serving stall that restart clears, without durable
mutation or whole-process failure **[OBS, DB]**.

**Static correlation [RB-DEC]:** The active setter's unsigned gate admits
exactly slots 1 through 8. Slot 8 has zero matching membership rows, while
`HCBnkSong_GetCueID` rejects exactly one row and otherwise indexes row zero.
That empty-result access is consistent with the observed stall; the exact
causal step remains an inference because the experiment does not attach a
debugger to the blocked server path. Backend comparison is deferred.

## 2026-10-03: RX3 active sort and six-argument rendering

**Question:** Does the final value `12` in the RX3 six-argument `0x3000`
request select Key, or does a preceding non-default `0x1004` track sort change
the rendered right-hand column without changing the render request?

**Coverage audit [DEC]:** Before this experiment, the corpus contained only
two six-argument render declarations, both after Default sort. The existing
`sort-ids.json` matrix exercised non-default sorts only through the
eight-argument form `[context, offset, count, 0, total, 12, 1, 0]`. A focused
declaration test excludes the new suite and preserves this absence result so
the reason for the cross remains reviewable.

**Physical request evidence [PCAP]:** The retained physical RX3 capture
contains three Default-sort request pairs. Each pair sends
`0x1004 [0x0b010401, 0]` followed by
`0x3000 [0x0b010401, 0, 12, 0, 4342, 12]`. Thus the device itself uses the
six-argument form and final value `12`. The capture contains no non-default
sort interaction. Replaying its literal player-11 packed context against the
synthetic lab session timed out at the response header, consistently with the
separately established player-byte admission boundary. That failed control is
retained. The semantic recording therefore uses admitted lab context
`0x01010301` while preserving the RX3 render arguments.

**Method [OBS]:** A generated 11-case suite covers Default, Alphabet, Artist,
Album, BPM, Rating, Genre, Label, Key, Date Added, and DJ Play Count. Each case
opens a fresh connection, requests tracks with the selected sort, and renders
all eight fixture tracks in three pages using exactly
`[context, offset, count, 0, total, 12]`. Record and repeat each begin from a
fresh encrypted `full` fixture and cold Rekordbox 7.2.19 process. Four health
captures prove one responsive process and no new Application events across
both phases. The reducer preserves all 88 complete `0x4101` rows and emits a
field-level CSV. Backend replay is deferred.

**Result [OBS]:** All 33 render requests retain six arguments and final value
`12`. The active sort alone changes the right-hand column materialized by the
track-list builder. For fixture track `Alpha One`, the exact argument 0,
argument 5, and composite argument 6 results are:

| Sort | Arg 0 | Arg 5 | Arg 6 |
|---|---:|---|---:|
| Default | 5001 | `Am - 120.0 bpm` | `0x0f04` |
| Alphabet | 0 | `Alpha One` | `0x0404` |
| Artist | 0 | `Alpha Artist` | `0x0704` |
| Album | 0 | `Album One` | `0x0204` |
| BPM | 12000 | `120.0 bpm - Am` | `0x0d04` |
| Rating | 0 | empty | `0x0a04` |
| Genre | 0 | `Fixture House` | `0x0604` |
| Label | 0 | `Fixture Label One` | `0x0e04` |
| Key | 14 | `Am - 120.0 bpm` | `0x0f04` |
| Date Added | 0 | `2021-02-02` | `0x2e04` |
| DJ Play Count | 0 | empty | `0x2a04` |

Arguments 12-15 remain `5001, 6, "Am", 12000` in every row above. They are
content metadata independent of the visible right-hand column. Argument 0 is
also path-dependent: active Key sort supplies normalized sort key `14`, while
Default with persisted Key supplies raw KeyID `5001`; active lookup sorts use
zero here, while an eight-argument dynamic override can supply the entity ID.

The composites are cached builder results. Persisted Key under Default sort or
active Key under six-argument rendering produces `Key - BPM`; persisted BPM
under Default sort or active BPM produces `BPM - Key`. Classic notation yields
`Am - 120.0 bpm` and `120.0 bpm - Am`; Alphanumeric notation yields
`8A - 120.0 bpm` and `120.0 bpm - 8A`. Artist, Album, Genre, Label, Alphabet,
and Date Added are single values. In the eight-argument path, a selector that
matches the materialized row type preserves its cached composite. A mismatched
explicit or persisted-fallback Key selector regenerates a single key string;
a mismatched BPM selector returns the numeric BPM in argument 0 with empty
argument 5. The protocol and oracle documents therefore apply persisted Column
selection to Default/fallback paths and active-sort materialization to the
six-argument RX3 path.

**Provenance [OBS]:** The promoted golden SHA-256 is
`c104225b20b997d4ebf8992b3a7723322af6b4f2e17f9b798acf3c2d56b74a3f`; its
suite SHA-256 is
`d8ad7de60d327f8c7906e90ff5331e447b1579821362572fb703e18c2a6bdfe5`.
The retained physical PCAP SHA-256 is
`bee17ddfa72b093479a68c1590953ddc79629cdf43905769761c656a5149aa2b`.
`SECONDARY_COLUMN_ORACLE.md` links the canonical golden, complete row CSV,
strict summary, capture receipt, finalization receipt, decoded requests, and
source PCAP.

## 2026-10-03: Secondary-column controller ownership

**Question:** Does the Preferences Column selection provide the selected-row
ordering consumed by Link Export, and how does the supported writer maintain
the single-selection invariant?

**Method [DEC]:** `tools/disassemble_symbols.py` extracted every
`getSortSetting`, `resetSubColumn`, and `setSubColumn` implementation for the
Dev SQLite, AppSync, and desktop routing controllers, together with the
low-level Dev/Master mutators, from the hash-pinned Rekordbox 7.2.19 x86-64
executable. A focused test regenerates the 4,215-line trace byte-for-byte,
checks the executable SHA-256, pins the relevant SQL literals, and resolves the
AppSync setter's virtual call through the class vtable.

**Result [DEC]:** The AppSync Preferences reader selects every nondeleted
`djmdSort` row in `Seq` order. It builds the visible/hidden settings lists,
collects every `Disable & 2` row, returns the first selected ID in that order,
and logs `ERROR Right Column multiply-selected` when the collection has two or
more entries. Link Export does not consume that collection. Its list builder
and eight-argument configured fallback perform their own selected-row reads
without `ORDER BY`; six-argument non-default-sort rendering instead uses the
active list's materialized role.

`AppSyncDBController::setSubColumn(id)` calls the vtable slot bound to
`resetSubColumn`, which clears bit `0x02` on every selected nondeleted row, then
sets bit `0x02` on the requested ID. Both operations update AppSync status,
local-USN, and timestamp bookkeeping in a transaction. Visibility bit `0x01`
is preserved. The supported UI therefore maintains one selection; the zero-
and multiple-selection oracle fixtures are deliberately out-of-band database
states.

**Artifacts:** The canonical trace is
`data/static-analysis/subcolumn-controller-paths.disasm.txt`; its contract test
is `conformance/test_subcolumn_controller_paths.py`. `CONFIGURATION.md`,
`SECONDARY_COLUMNS.md`, `SECONDARY_COLUMN_ORACLE.md`, `DATABASE_QUERIES.md`,
and `PROTOCOL_REFERENCE.md` now distinguish the five owners explicitly.

## 2026-10-03: Status-owned model-name state

**Question:** Why does a keepalive-only XDJ identity expose Link membership
without selecting Display Song Info's XDJ/AIO order, while an admitted status
packet does?

**Method [DEC]:** A generated trace follows membership reception, player-status
parsing, model accessors, model-change notification, and the Display AIO cache
through the pinned Rekordbox 7.2.19 x86-64 executable. A focused test resolves
the `InnerLinkAPI::linkProc` jump table directly from binary bytes and
regenerates the 3,331-line trace byte-for-byte.

**Result [DEC, OBS]:** Membership and model text have different owners.
Internal message type `0x04` reaches `receiveLinkMember`; the resulting
`LinkDeviceManager` entry stores discovery class, presence, timing, address,
and version state. `PSvLinkNormalInterval::messageReceived` separately maps raw
packet kind `0x0a` to `PSvLinkPlayerLinkInfo`, stores a `0xb8`-byte record whose
model begins at offset `0x0b`, and emits message type `0x6e` when that string
changes. The `linkProc` type-`0x6e` arm calls
`noticeModelNameUpdate(player)`. Every public
model accessor delegates to that status record. `PSvDBMain::isAIO` reads it
lazily and caches only the XDJ-prefix boolean until disconnect clears the map.

This directly explains the observed keepalive/status distinction without
claiming that status emission alone guarantees admission for arbitrary
synthetic models. Packet layout and lifecycle claims remain limited by the
captured-verbatim, corroborating, and derived evidence tiers.

**Artifacts:** `data/static-analysis/model-name-state-path.disasm.txt` and
`conformance/test_model_name_state_path.py`. The device compatibility,
predicate-audit, status-provenance, static-analysis, source, and README chapters
now share this ownership model.

## 2026-10-03: Declared same-process LINK buffer lifetime

**Question:** Does the supported LINK deactivate/reactivate transition clear
the process-wide, context-keyed Hot Cue Bank list buffer without restarting
Rekordbox?

**Method:** The guarded `ag18` stage reuses the repeat-verified distinguishable
location suites. Each of two control and two toggle runs installs a fresh
`hot-cue-banks` fixture and starts a fresh Rekordbox process. It primes the
three-row location-1 root, keeps the synthetic RX3 identity present, and either
leaves LINK active or clicks the supported LINK control off and on. The toggle
arm requires dbserver port 12523 to disappear and return. It then populates the
one-row location-2 Beta folder while rendering the prior location-1 context,
followed by the current location-2 context.

Five schema-2 health captures per run require one responsive, unchanged
Rekordbox PID and zero Application events. Per-run receipts bind both typed
responses, the listener transition, every health capture, the encrypted
fixture, identity, suites, and pinned runner. The strict reducer accepts only
the previously characterized old-location outcomes: item 9002 means persisted;
a render timeout with the location-2 total means cleared. Both runs in each arm
must agree exactly before the result is promoted **[DECL]**.

**Artifacts:**
`conformance/record_hot_cue_bank_buffer_link_toggle.sh`,
`conformance/run_hot_cue_buffer_link_toggle_after_xdj_xz.sh`,
`tools/summarize_hot_cue_buffer_link_toggle.py`, and
`conformance/test_hot_cue_buffer_link_toggle.py`. Real-Rekordbox evidence will
be retained under `data/experiments/hot-cue-bank/buffer-link-toggle/`.

## 2026-10-03: Declared track-render argument-type matrix

**Question:** After a valid Track list has initialized the context buffer, how
does real Rekordbox handle a string or blob in each numeric position of the
ordinary eight-argument `0x3000` render request?

**Method [DECL, DEC]:** The declaration changes exactly one field in
`[context, offset, count, 0, total, 12, 1, 0]`. All eight positions are crossed
with protocol string and blob tags, producing 16 two-case suites. Every suite
first materializes the Default Track list, then sends the wrong-typed render on
the same connection. Each probe receives an independent cold record process,
an independent cold repeat process, and before/after schema-2 process and
Application-event captures. Outcomes remain unconstrained.

The hash-pinned x86-64 decoder audit resolves tags 2 and 3 to the variable-
width string and blob paths. Both consume the preceding decoded slot as a
length; position one is rejected because no such slot exists. Successful
decoding stores an allocation pointer in the ordinary eight-byte value slot,
while `GetListBufContents` reads render slots without consulting their tags.
This predicts possible parser rejection or pointer-as-number dispatch but does
not predict a wire reply, timeout, disconnect, or process result.

**Status [OBS plan]:** Bounded generation `ap18` is active as a guarded waiter
behind the complete arity queue through `ao18`. It runs only in the isolated
VM and does not use a backend comparison. Each receipt-backed probe is
resumable; the aggregate reducer preserves every transport and health class.

**Artifacts:** `conformance/data/render-argument-type-matrix.json`, the suites
under `conformance/suites/generated/render-argument-types/`,
`data/static-analysis/render-argument-types-parser.{json,md,disasm.txt}`, the
recorder, reducer, handoff, focused test, and eventual evidence under
`data/experiments/render-argument-types/`.

## 2026-10-03: Declared track-render numeric-field matrix

**Question:** What do numeric render positions 4-6 actually control, which
bits are consumed, and where are their live boundaries?

**Method [DECL, DEC]:** A hash-pinned audit covers the complete
`GetListBufContents` and `GetListBuf1stRow` bodies plus the 51-entry
`DBCommon_GetCateKind` table. A 42-case suite holds a normal eight-argument
Track render constant while varying one field: 15 first-row seek keys, six
client-reported totals, and 20 category IDs. The category cases cover every
mapped and zero-mapped range, both ends, out-of-range values, and a high-word
alias. Every case uses a fresh connection; record and repeat use cold
Rekordbox processes and retain four schema-2 health captures.

**Static result [DEC]:** Position 4 is not reserved. Rekordbox reads its low
16 bits as a normalized first-character seek key. Zero uses normal offset
pagination, ASCII lowercase is promoted to uppercase, `U`/`Unknown` has a
dedicated branch, and `0xffff` wraps to the ordinary path. Position 5 is the
client-reported total and is unread by the renderer. Position 6 is truncated
to 16 bits and mapped through the sparse category table: 1-24, 30-32, 40, and
50-51 map to themselves; every in-range hole and every out-of-range value map
to zero.

**Status [OBS plan]:** Bounded generation `aq18` follows the independently
isolated argument-type matrix. Outcomes are unconstrained. The reducer reports
the returned IDs, titles, and exact row equality against the normal control;
none of the static equivalences is used as a promotion expectation.

**Artifacts:** `conformance/suites/generated/render-numeric-fields.json`,
`data/static-analysis/render-numeric-fields.{json,md,disasm.txt}`, the recorder,
reducer, handoff, focused test, and eventual evidence under
`data/experiments/render-numeric-fields/`.

## 2026-10-03: Declared track-render override-control matrix

**Question [OBS plan]:** Do eight-argument renders treat every nonzero override
gate equally, and what rows result when the selector is one, outside 2-17, or
has a valid-looking low byte plus nonzero high bits?

**Method [DEC, OBS plan]:** A pinned x86-64 audit follows arguments 7 and 8 from
`GetListBufContents` through `GetListBufRowContent` and
`Get_SubCategoryValue`. Seventeen fresh-connection cases hold a Default Track
list and all other render fields fixed while varying one gate or selector.
Each outcome is unconstrained and will be recorded twice from fresh fixture
and process state.

**Static result [DEC]:** The 32-bit gate is canonicalized with `setne`.
The selector remains 32 bits: icon dispatch sees its signed low byte, while the
secondary extractor sees the full value and admits only 2-17. A high-word
Artist lookalike therefore reaches two different static classifications.

**Status [OBS plan]:** Bounded generation `ar18` waits for `aq18`; its guarded
handoff requires the numeric-field finalization receipt before starting the
isolated VM. No live row result is inferred from the decoder.

**Artifacts:** `conformance/suites/generated/render-override-controls.json`,
`data/static-analysis/render-override-controls.{json,md,disasm.txt}`, recorder,
reducer, guarded handoff, focused test, and eventual evidence under
`data/experiments/render-override-controls/`.

## 2026-10-03: Location-2 malformed-history 13-versus-zero conflict

**Observation [OBS]:** The ordered-pair recorder reached
`play-extra-argument__then__delivery-blob-content` after 47 promoted pairs.
Record and repeat returned the same two malformed-precursor envelopes, but the
matched location-2 Delivery probe returned total 13 in one cold process and
total zero in the other. Both raw responses and all four health captures are
retained. The mismatch halted the queue before promotion.

**Recovery method [OBS]:** Seven suites repeat that exact three-request
sequence using player-11 precursor context `0x0b010301` and player-11 location-2
probe context `0x0b020301`. Only the delay before the probe connection changes:
0, 50, 100, 250, 500, 1000, and 3000 ms. Each delay receives four independent
fixture-reset, cold-process observations with process and Application-event
health. The reducer verifies the decoded context of every request. Outcomes
remain unconstrained and every observation has its own hash receipt.

**Status [OBS]:** Generation `z19` failed before protocol traffic
because it supplied an invalid descriptive phase to `oracle_record.sh`; its
single before-health file is archived. Generation `z20` completed four 0 ms
observations with player-1 precursor context `0x01010301` and a player-11 final
probe. All four returned zero, but that mixed-player sequence does not repeat
the conflicted ordered pair and is quarantined under
`malformed-history-timing-invalid-player1-z20`. Generation `z21` is the first
admissible timing run. It completed four zero-delay and two 50 ms observations
before an RFB activation failure on the third 50 ms attempt. All six receipts
verify decoded contexts `0x0b010301`, `0x0b010301`, and `0x0b020301`; the four
zero-delay probes return zero and both 50 ms probes return 13. Its partial
before-health capture and failure receipt are retained under the timing
`attempts/` directory. Cleanup restored `play-paths`, removed the identity,
and stopped the isolated VM **[OBS]**.

Generation `z22` resumed from those six hash-verified receipts under invocation
`2561f163acc848fba5fc931ac1ea0a91` and completed all 28 observations. The
result is a strict timing partition: all four 0 ms probes return total zero,
while all four probes at each 50, 100, 250, 500, 1000, and 3000 ms return the
correct total 13. Every health window contains one responsive process and zero
Application events. The finalization receipt binds all observation receipts,
the summary and CSV, the original conflict captures, focused and pinned tests,
baseline restoration, zero active identities, and the stopped isolated VM
**[OBS]**.

Static lifecycle evidence identifies the mechanism: malformed commands first
expose the `0xfffffffe/0x0100` connection-close sentinel, while their correlated
response is routed asynchronously through the player-keyed communications
queue **[DEC]**. The follow-up six-variant routing matrix crosses malformed
blob Delivery and valid extra-argument Delivery with 0, 50, and 100 ms
replacement delays. Four cold-process observations per cell retain the
replacement setup exchange, a 1200 ms no-send read, a same-socket valid
Delivery probe, and a delayed fresh-socket health probe. Outcomes remained
unconstrained during capture.

**Routing result [OBS]:** All 24 setup exchanges contain only the normal
extended setup reply. The four immediate malformed-blob replacements then
receive the same raw transaction-1 frame, byte for byte:

```text
11872349ae11000000011040000f021400000002060611000026021100000000
```

It decodes as `0x4000 [0x2602, 0]`. The other 20 no-send reads time out: all
eight malformed-blob observations at 50/100 ms and all twelve valid controls
at 0/50/100 ms. Every same-socket observation probe and every fresh health
probe returns 13 rows. Thus the original zero-row follow-up consumed an
orphaned response to the prior malformed request; it did not observe a changed
Delivery result or persistent builder state. The tested live boundary is
presence under immediate replacement and absence at delays of 50 ms or more,
not an exact 50 ms lifetime.

Generation `z23` recorded 18 observations, then failed before protocol traffic
for the third 50 ms control because LINK remained disabled after ten activation
attempts. Its lone before-health file and failure receipt are retained.
Generation `z24` resumed from the 18 hashes and completed the matrix. The
finalization receipt binds all 24 observations, 48 health files, timing
predecessor, declaration, static trace, pinned binaries, summary, and CSV;
49 focused and 13 pinned tests pass, baseline state is restored, no identity
unit remains, and the isolated VM is stopped.

The ordered-pair corpus now represents that lifecycle explicitly. Each of its
three fresh connections retains the setup exchange, performs a 1200 ms no-send
read, stores the result as `pre_request_drain`, and only then sends the declared
request. This preserves the original 256 x 3 semantic matrix while separating
player-routed traffic from the response to the new transaction. The old 47
promoted pairs and the pair-48 conflict remain untouched; lifecycle-aware
goldens and receipts use distinct `malformed-history-lifecycle` roots.

Generation `z25` proved the revised envelope with two independently repeated
pairs, including normal setup-only exchanges, timeout drains, and a 13-row
valid Delivery probe. It was frozen at a receipt boundary and stopped because
its initial 12-hour finite ceiling was shorter than the measured cold-process
runtime. Generation `z26`, invocation
`be9680b0720a414ca02a65a302938c43`, verified and skipped both receipts and
promoted another thirteen pairs. Pair 16, with blob-valued Delivery second,
returned the correct 13-row final probe in both phases, but the final
connection's drain received the delayed `0x4000 [0x2602, 0]` frame in record
and timed out in repeat. This is the already measured immediate-replacement
routing race, now observed directly inside the exhaustive corpus **[OBS]**.

The failed pair-16 attempt is retained under
`malformed-history-lifecycle/attempts/immediate-open-orphan-race-20261004T004125Z/`.
Generation `z27` keeps the 1200 ms drain and adds a 3000 ms interval with no
matching client after every blob-valued Delivery before opening the following
connection. Only 31 not-yet-promoted suites need the conditional delay; all 15
existing suite and golden hashes still match their receipts. Invocation
`8d86980e160641568d998f3a03a4a2eb` resumed from pair 16 under a 30-hour
ceiling. The repaired pair 16 promoted exactly: every drain timed out in both
phases, the final probe returned 13, and the suite and golden hashes match its
receipt. The service continues from pair 17 **[OBS in progress]**.
