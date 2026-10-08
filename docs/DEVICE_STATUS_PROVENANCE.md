# Device-status provenance

This chapter separates authentic device traffic from deliberately derived
identities in the Rekordbox Link Export oracle. That distinction matters
because a model string can select a Rekordbox predicate even when the rest of
the status packet did not come from that hardware.

The machine-readable inventory is
`data/static-analysis/device-status-source-inventory.json`. Regenerate it with:

```sh
python3 tools/inventory_device_status_sources.py
```

The inventory fingerprints every bundled Dysentery packet capture, extracts
fixed-width Pioneer/AlphaTheta model strings directly from its bytes, and
classifies every `conformance/runs/*-status.json` identity by packet source.
It performs no network activity and invokes no backend.

## Evidence tiers

| Tier | Meaning | Permitted conclusion |
| --- | --- | --- |
| Captured verbatim | UDP 50002 payload is byte-for-byte hardware traffic; the paired keepalive changes only isolated-network address/MAC fields where documented | Rekordbox behavior under that captured status shape and model |
| Corroborating fixture | UDP 50002 payload is identified as physical hardware traffic and retained byte-for-byte, but its parent capture or required acquisition metadata is unavailable | Clearly labeled admission and behavior experiments under those bytes; not a hardware-representative lifecycle claim |
| RX3-template-derived | The captured 292-byte RX3 status packet has only its fixed-width model and player bytes replaced | Rekordbox parsing/classification for that synthetic combination; not the named hardware's native packet layout |
| Keepalive only | UDP 50000 membership is emitted without player status | Ordinary discovery behavior and the negative status-lifecycle control; not status-backed model classification |

## Authentic sources

The physical RX3 capture contributes the 292-byte `XDJ-RX3` player-11 status
payload with SHA-256
`49d262852bc10cbed30f9cd1f40283047b2423d4865ec5d1b240ae5fe6e20987`.
It proves the AIO Display order, matched requester behavior, and the RX3 side of
the packed-context/status crosses **[CAP, OBS]**.

Dysentery's `S05-link-browse/run.pcapng` contributes the unmodified 284-byte
`CDJ-2000nexus` player-1 payload with SHA-256
`8e9c36049a85be2f31c989bfbff415d989bdb0f395987135eb35f53f1d8fb70b`.
Its 249-case real-Rekordbox matrix is complete across 13 fresh-process variants,
and every variant has an independent-repeat receipt. All 13 normalized semantic
envelopes match the paired derived CDJ-3000 controls. Twelve raw envelopes also
match exactly; the Display baseline differs only because its declaration pages
the same 16 response rows as `3/3/3/3/3/1` instead of one 16-row render
**[CAP, OBS]**.

The complete bundled Dysentery capture scan finds 18 capture files. Their
fixed-width device strings contain only `CDJ`, `CDJ-2000nexus`, and
`DJM-2000nexus`. The standalone `CDJ` token occurs in `to-virtual.pcapng`; the
hardware model represented throughout the player captures is
`CDJ-2000nexus`. No bundled capture supplies a native XDJ-XZ, XDJ-AZ,
XDJ-1000MK2, XDJ-RR, OPUS-QUAD, or CDJ-3000 status payload **[CAP]**.

Two corroborating 292-byte `XDJ-XZ` player-1 status packets come from the
dated physical-unit capture session documented by `cinderblock/netBeat` at
revision `399583fff849bddd8c8abd744d1d25e1656ba009`. The analyzed/master packet
has SHA-256
`8eadeb284e6c0ed167cd1573ba0ed976d5c1abd85694de1299224b54519ff90f`;
the unanalyzed/non-master packet has SHA-256
`f596f7ed8e34b5b9ca16e3fc9a50c5d59118308f8055a9514e4562474051ff7b`.
Both are exact kind-`0x0a` test vectors, but the gitignored parent JSONL,
firmware, timestamps, address tuple, and paired keepalive are unavailable.
They therefore occupy the corroborating tier rather than Captured verbatim.
The admitted lab identity records that tier explicitly so the inventory does
not infer provenance merely from the presence of a `.hex` file.

## Derived status identities

The CDJ-3000 control and the XDJ-XZ, XDJ-AZ, XDJ-1000MK2, XDJ-RR, and unknown
controls use the captured RX3 packet shape with the model field and both player
bytes replaced. Their exact hashes are retained in the run manifests and the
machine inventory. These are controlled parser/classifier experiments, not
claims about the named device's real UDP 50002 format.

This derived matrix proves two Rekordbox facts:

1. A keepalive model alone does not populate the status-backed model lookup
   used by Display Song Info.
2. Once a status packet is admitted, `PSvDBMain::isAIO(player)` classifies the
   stored model by its `XDJ` prefix. The exact-model mutations also reveal
   requester/status admission limits before the builder runs.

The decompiled ownership path explains why these are distinct controls. The
status parser owns the model buffer: `PSvLinkNormalInterval::messageReceived`
maps raw packet kind `0x0a` to `PSvLinkPlayerLinkInfo`, stores a per-player
record, and emits internal message type `0x6e` when the model changes. The
membership path uses internal type `0x04` and does not write that buffer.
`PSvDBMain::isAIO` later reads the status record through the model-accessor
chain and caches only the resulting boolean. This is direct executable
evidence for the state boundary, while the capture tier still determines what
may be claimed about any particular hardware packet **[DEC]**.

The CDJ-3000 result is therefore a matched non-XDJ control for the recovered
prefix predicate, while the genuine CDJ-2000nexus run tests an independent
native status layout and generation.

## Dynamic coverage boundary

| Surface | Authentic RX3 | Derived CDJ-3000 | Authentic CDJ-2000nexus | Corroborating XDJ-XZ | Other derived models |
| --- | --- | --- | --- | --- | --- |
| Ordinary full/legacy menus | Recorded and repeated | Recorded and repeated via matching ordinary identity | 49 cases recorded and repeated | 49-case matrix declared and queued | Ordinary keepalive matrix recorded |
| Display Song Info | AIO order recorded | Ordinary order recorded | Baseline and packed setup cross recorded and repeated | Baseline declared and queued | Four-case admission matrix recorded |
| Play/Delivery/no-builder kinds | Complete matched packed-type/setup cross | Complete matched packed-type/setup cross | Complete packed-type/setup cross recorded and repeated | 98-case context cross declared and queued | Not promoted as native-model evidence |
| Hot Cue catalog/getters | Complete matched packed-type/setup cross | Complete matched packed-type/setup cross | Complete catalog/getter cross recorded and repeated | 98-case context cross declared and queued | Not promoted as native-model evidence |
| Hot Cue setters | Complete matched packed-type/setup cross | Complete matched packed-type/setup cross | Not in the current genuine matrix | Outside the initial corroborating matrix | Not promoted as native-model evidence |

No direct x86-64 predicate evidence indicates model-specific ordinary roots,
categories, sorts, queries, pagination, secondary columns, or row widths.
Authentic status shapes still matter for admission and lifecycle, so the
remaining model-source gap is recorded rather than generalized away.

## Acquisition gap

Captured-verbatim status packets are still needed for XDJ-XZ, XDJ-AZ, XDJ-1000MK2,
XDJ-RR/RX2, OPUS-QUAD, and CDJ-3000 before the corresponding status-backed
results can be called hardware-representative. Each future source must retain:

- the original capture hash and packet timestamp;
- the exact UDP payload and hash;
- source/destination addresses and ports;
- model and both player-number fields;
- paired keepalive class, generation, presence, model code, and peer count;
- any address/MAC rewrite made for the isolated lab;
- a fresh-process record and independent repeat receipt.

`PUBLIC_STATUS_SOURCE_AUDIT.md` records a pinned audit of nine public protocol
implementations and capture corpora. It found no captured-verbatim modern-model
payload. It did recover a distinct 284-byte CDJ-2000nexus firmware-1.43/player-3
fixture from the original `prolink-connect` history. That payload is retained
under `conformance/status-packets/`, but remains a corroborating fixture rather
than `Captured verbatim` evidence because its parent pcap, timestamp, address
tuple, and paired keepalive do not survive.

The audit also retains two corroborating XDJ-XZ status packets described above
and a separate acquisition lead for the complete parent capture: a corrected
physical-unit Wireshark capture linked from SuperTimecodeConverter issue 12.
Its Drive object currently requires Google sign-in, and the available local
token lacks Drive scope. Until the capture bytes are obtained and hashed, the
lead remains outside every packet-evidence tier.

A physical CDJ-3000 firmware-3.18 capture report in
`alphatheta-connect` pull request 2 was also reviewed. Its retained findings
describe the Stagehand control plane, and the merged change contains no pcap or
raw dump. It therefore supplies neither the ordinary player-status payload nor
replayable bytes required by this matrix. The machine audit keeps the exact PR
and commit as a reviewed nonqualifying lead.

`DEVICE_MATRIX_ORACLE.md` records dynamic outcomes,
`DEVICE_PREDICATE_AUDIT.md` records the decompiled predicate boundary, and
`DISPLAY_SONG_INFO_ORACLE.md` gives the field-level AIO proof.
