# Public device-status source audit

This audit asks a narrow question: which public repositories contain original
device-status bytes that can be replayed to Rekordbox without presenting
modeled packets as physical hardware traffic? The machine-readable result is
`data/static-analysis/public-status-source-audit.json`.

The audit inspected pinned revisions through October 3, 2026. Support claims,
parsers, reverse-engineered field descriptions, and packets constructed by a
test builder are useful secondary evidence. They do not satisfy the native
status-source requirement by themselves.

## Admission rule

A source is eligible for the native matrix when it preserves a UDP status
payload from an identified physical model and enough acquisition context to
distinguish the payload from generated or model-string-mutated data. The
desired record also includes the parent capture hash, packet timestamp,
address tuple, firmware, and paired keepalive.

An incomplete historical fixture can be retained as corroborating evidence.
It remains outside the strongest `Captured verbatim` tier until its missing
capture context is recovered.

## Results

| Repository | Pinned revision | Finding | Native-matrix result |
| --- | --- | --- | --- |
| `anweiss/prodjlink-rs` | `4fc2bb302b0c3f8a07bb27598f64bd38aa1ce4ea` | Its advertised golden fixtures call `MockCdjStatusBuilder` and the README describes them as modeled after hardware | Rejected as modeled |
| `chrisle/alphatheta-connect` | `38aee4413391a0172e04b6bc9ae8b3df6f46460f` | One test fixture is explicitly called real and contains a distinct CDJ-2000nexus 1.43/player-3 status payload; no parent capture metadata survives | Retained as corroborating legacy evidence |
| `grantHarris/prolink-cpp` | `47b0dd58b3fe3355fa559ec378f63cb9602a44c7` | Status tests call `BuildStatusPacket`; no device payload or pcap is committed | Rejected as constructed |
| `usr-ein/prolink` | `5065b1c8a69ae7a8e19a8215bd270413be1879b2` | The 37-capture corpus is authentic traffic from two CDJ-2000NXS players on firmware 1.44 | Corroborates an already-covered generation |
| `Deep-Symmetry/beat-link` | `ef0aaa1ea949f5c3b1e759973f784c488a12288a` | Source and changelog record observations from several modern products, but the audited tree contains no packet capture or byte fixture | Useful semantic source; no replayable payload |
| `fiverecords/SuperTimecodeConverter` | `cbd3d56c9e12d2c15fb3c3b2bddba4bb5eca7a08` | Hardware-tested implementation with capture-derived comments; capture files are excluded from the repository | External source lead only |
| `kyleawayan/opus-quad-pro-dj-link-analysis` | `d7459fdc0884b704cdd5540b5bf5ab6d003c4ded` | Physical OPUS-QUAD analysis preserves one exact kind-`0x10` port-50002 packet; subsequent status packets are processed dynamically but not retained | Corroborating modern non-status fixture only |
| `xxvw/Conduction` | `07ee2989c5e2363c4c59bba7670864bea65072c2` | Its captured fixtures come from the already-audited Dysentery generation; OPUS/export-source fixtures are explicitly transcribed references | Independent provenance corroboration; no new payload |
| `cinderblock/netBeat` | `399583fff849bddd8c8abd744d1d25e1656ba009` | Physical XDJ-XZ session notes plus two complete 292-byte kind-`0x0a` packets embedded in parser tests; parent JSONL is gitignored | Retained as two corroborating modern status fixtures; not captured-verbatim |

The audit therefore found no admissible native status payload for XDJ-XZ,
XDJ-AZ, XDJ-1000MK2, XDJ-RR/RX2, OPUS-QUAD, or CDJ-3000. This is a positive
source audit result, not an inference from an empty search: every named tree was
scanned for `pcap`, `pcapng`, binary fixture files, packet literals, and the
target model names, and the construction path of each apparent fixture was
read.

### XDJ-XZ corroborating status fixtures

`netBeat` documents an April 22, 2026 physical XDJ-XZ session. Its notes name
the unit address, two CDJ-class deck identities, mixer identity 33, packet
counts, packet lengths, and capture conditions. The full 12 MB JSONL remains
gitignored, but `packages/prolink/test/status.test.ts` embeds two complete raw
292-byte kind-`0x0a` packets from that session:

| State | Player | SHA-256 |
| --- | ---: | --- |
| Analyzed rekordbox track, master | 1 | `8eadeb284e6c0ed167cd1573ba0ed976d5c1abd85694de1299224b54519ff90f` |
| Unanalyzed track, non-master | 1 | `f596f7ed8e34b5b9ca16e3fc9a50c5d59118308f8055a9514e4562474051ff7b` |

The lab retains both under `conformance/status-packets/`. Their model, kind,
player, length, and dynamic states are byte-verifiable. Missing parent-capture
bytes, firmware, packet timestamps, address tuple, and paired keepalive keep
them in the corroborating-fixture tier. They can support a clearly labeled
real-Rekordbox admission/behavior matrix, but do not close the stronger native
capture-provenance requirement.

### OPUS-QUAD partial packet evidence

`opus-quad-pro-dj-link-analysis` documents a physical OPUS-QUAD interaction
and preserves the exact first packet it receives from the unit on UDP 50002.
The 36-byte payload identifies `OPUS-QUAD` and packet kind `0x10`; its retained
SHA-256 is
`845014dfceb62648cfcb4c0c0a12c013f41fe9e541e828c78a0fd90d47d2b801`.
The source then relays kind-`0x0a` CDJ-status messages dynamically, but commits
neither those bytes nor a parent capture, firmware version, address tuple, or
timestamp. The packet is retained at
`conformance/status-packets/opus-quad-first-50002.hex` as physical-device
corroboration. Its kind excludes it from the status-backed Link Export matrix.

The independent Conduction provenance ledger links the same OPUS analysis and
carefully marks its OPUS/export-source vectors as transcribed references. Its
unchanged hardware packets are from the already-audited Dysentery
CDJ-2000nexus sources. It corroborates the evidence boundary without adding a
modern status payload.

### XDJ-XZ acquisition lead

SuperTimecodeConverter issue 12 contains a July 20, 2026 link to a corrected
Wireshark capture from a physical XDJ-XZ after the PC and unit were placed on
the same subnet. The maintainer later records the capture's central finding:
the unit announces one device identity while sending deck data for two player
numbers. This is consistent with the implementation change that followed.

The linked Google Drive object currently redirects unauthenticated downloads
to sign-in. Evan's existing command-line Google token has no Drive scope, so
the lab has not obtained, hashed, or parsed the capture. It is therefore
classified `source-lead-only`; it supplies neither native packet bytes nor a
Rekordbox result. The issue and exact Drive file ID are retained in the
machine-readable audit so access can be retried without repeating discovery.

### Rejected CDJ-3000 Stagehand lead

`chrisle/alphatheta-connect` pull request 2 records capture-derived findings
from a physical CDJ-3000 on firmware 3.18, using the official Stagehand iPad
application and layer-2 MAC takeover. It identifies Stagehand registration,
state synchronization, control, preference, beat-stream, and announcement
packets. This is useful real-hardware semantic evidence for that control plane.

It does not provide the ordinary UDP 50002 player-status payload needed by the
Link Export model matrix. The author offered pcap hex dumps, but the pull
request, comments, and merged commit contain no attachment or raw dump. The
merged commit `01befaad76c247dd6e99654ea45e49f88c39703e` changes only
`docs/STAGEHAND.md`; a recursive scan of the pinned repository tree found no
additional CDJ-3000 capture or status fixture. The lead is retained as an
explicit protocol-plane rejection, not counted as an acquisition lead or
eligible payload.

## Firmware-1.43 fixture

`conformance/status-packets/cdj-2000nexus-player-3-firmware-1.43.hex` preserves
the exact 284-byte `status-simple.dat` payload from the original
`prolink-connect` history. Its properties are:

| Property | Value |
| --- | --- |
| SHA-256 | `42a45b82ea4965e1effc327167141ffa1f60983c3fdba1889b60a98a2b52c0aa` |
| Model | `CDJ-2000nexus` |
| Firmware | `1.43` |
| Player fields | `3` |
| First retained commit | `ec8b012642bf366f495e0cdd498dc5084057af85` |
| Commit author/date | Evan Purkhiser, 2020-10-11 |

The source test calls it a real packet. The repository does not retain the
parent pcap, timestamp, source/destination tuple, or paired keepalive. The
fixture is consequently stronger than a generated packet and weaker than the
fully attributed RX3 and Dysentery sources. It is not yet scheduled for the
real-Rekordbox matrix because the active genuine CDJ-2000nexus campaign uses
the fully attributed firmware-1.44 capture.

## What would close the gap

For each unresolved model, retain the original capture rather than extracting
only a convenient payload. Select at least one stable status packet and its
paired keepalive, record both hashes and timestamps, document the physical
device and firmware, then derive the isolated-lab rewrite from those retained
bytes. A fresh Rekordbox process and an independent repeat are still required;
the source packet alone does not establish menu behavior.

`DEVICE_STATUS_PROVENANCE.md` defines the evidence tiers and current dynamic
coverage. `DEVICE_PREDICATE_AUDIT.md` explains why model-specific status is
needed even though the recovered ordinary-menu builders expose almost no
model branches.
