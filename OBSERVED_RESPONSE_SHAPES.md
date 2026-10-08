# Observed Link Export response shapes

This chapter is the inverse of `REQUEST_SHAPES.md`: it indexes what
canonical Rekordbox 7.2.19 goldens actually returned for every observed
request kind. It is generated from complete typed messages, not inferred
from another backend or from request declarations.

The initial request and the later page request are separate protocol
transactions. `header` and `raw_response` messages are attributed to the
declared request. Messages inside `pages` are attributed to `0x3000`.
Pre-request drain messages are asynchronous lifecycle evidence and are not
assigned to the following request.

The machine-readable authority is `data/observed-response-shapes.json`.
It covers 804 canonical golden files, 5734 cases, and 90 observed protocol request kinds across setup and ordinary cases. It is bound to corpus SHA-256
`8b90ea40d6b25e39293cf45b1c58ca945001eb495feb9ed6a63214a95ccfb87f`.

The ledger also defines 17 exact identity profiles. Each request
links to the keepalive/status packet identity and setup widths under which
its response was observed. Profiles retain model, player, class, generation,
presence, model code, packet hashes, and status provenance; model text alone
is never treated as proof of status-backed behavior.

## Identity profiles

Each row is an exact observed protocol identity, not a product-name alias.
Two rows with the same model remain distinct when player number, class,
generation, presence, model code, keepalive packet, or status packet differs.
The full packet hashes and status-template provenance are retained in the
machine ledger.

| Profile | Model | Player | Class | Generation | Presence | Model code | Status-backed |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| `identity-07b852397a78` | XDJ-1000MK2 | 11 | cdj | 2 | 1 | 100 | yes |
| `identity-0a0cc3d9ea31` | CDJ-2000NXS2 | 2 | cdj | 2 | 1 | 100 | no |
| `identity-194d0bbef651` | XDJ-1000MK2 | 5 | cdj | 2 | 1 | 100 | no |
| `identity-2acaf0e0024d` | UNKNOWN-FIXTURE | 6 | djm | 0 | 1 | 0 | no |
| `identity-4bda011e82ec` | UNKNOWN-FIXTURE | 6 | mixer | 0 | 1 | 0 | no |
| `identity-5930de13dd2a` | XDJ-XZ | 11 | type7 | 2 | 2 | 0 | yes |
| `identity-5a62e3f2df7f` | XDJ-RX3 | 11 | type7 | 3 | 2 | 0 | no |
| `identity-73c0b4cf4dad` | CDJ-3000 | 1 | cdj | 3 | 1 | 100 | yes |
| `identity-78aca70d5505` | XDJ-RX3 | 11 | type7 | 3 | 2 | 0 | yes |
| `identity-93ad45bebb5e` | XDJ-RR | 11 | type7 | 3 | 2 | 0 | yes |
| `identity-acabab86eeee` | CDJ-3000 | 1 | cdj | 3 | 1 | 100 | no |
| `identity-ad91bba11261` | UNKNOWN-FIXTURE | 1 | mixer | 0 | 1 | 0 | yes |
| `identity-b0fd6351be37` | CDJ-2000nexus | 1 | cdj | 2 | 1 | 0 | yes |
| `identity-b15f49264a8b` | XDJ-AZ | 11 | type7 | 3 | 2 | 0 | yes |
| `identity-d8df44307646` | XDJ-XZ | 3 | type7 | 2 | 2 | 0 | no |
| `identity-ea1cce3e54ea` | XDJ-RX3 | 1 | type7 | 3 | 2 | 0 | no |
| `identity-f60f05721a8d` | XDJ-AZ | 4 | type7 | 3 | 2 | 0 | no |

## Classified coverage

The navigation graph classifies 95 request kinds; 90 currently have canonical response evidence.
The following classified kinds have no canonical response recording:

| Request | Declared cases | Suite files |
| ---: | ---: | ---: |
| `0x100B` | 24 | 6 |
| `0x110B` | 12 | 6 |
| `0x130C` | 12 | 6 |
| `0x3006` | 142 | 10 |
| `0x3B03` | 32 | 8 |

This is an evidence boundary, not an unsupported-command claim. These
kinds have declarations but remain queued authority work. Exact suite paths
are retained in the machine ledger, which is bound to declaration corpus
SHA-256 `4d217334c92c427b652ea1738195cdcd639968db683fc94ad50e085ab039e6d7`. The
generator also requires that no observed kind fall outside the classified
namespace.

## Setup exchange

The corpus contains 1488 typed setup exchanges from golden-level session setup and lifecycle cases that open independent
connections. Setup is indexed separately because it precedes ordinary
request dispatch. Exact request and reply signatures and every source file
are retained in the machine ledger.
Setup coverage spans 17 exact identity profiles, 9 model strings, 8/17 status-backed identities, and extended/legacy setup widths.

## Asynchronous drains

The corpus contains 684 pre-request drain observations. 29 retained bytes before the declared request was sent. Their outcomes, exact message signatures,
and source files are indexed separately in the machine ledger. These frames
belong to prior asynchronous work and are never counted as the following
request's immediate reply.
Drain provenance spans 1 exact identity profile, 1 model string, 1/1 status-backed identities, and extended setup widths.

## Request index

Reply argument counts below are part of the signature. Exact ordered type
vectors, occurrence counts, render outcomes, item types, and every source
golden are retained in the JSON ledger.

The identity columns count exact profiles and distinct model strings. Status
coverage reports `status-backed/total` for those profiles. Setup lists every observed
setup width for the request.

| Request | Cases | Outcomes | Immediate replies | Render pages | Render replies | Item types | Identities | Models | Status coverage | Setup | Evidence files |
| ---: | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | --- | --- | ---: |
| `0x1000` | 141 | menu 139, timeout 2 | `0x0100` (0 args); `0x4000` (2 args) | 539 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 20 | 9 | 8 | 1/9 status-backed | extended/legacy | 71 |
| `0x1001` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 16 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1002` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 16 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1003` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 16 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1004` | 593 | menu 548, render_timeout 3, timeout 42 | `0x0100` (0 args); `0x4000` (2 args) | 920 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 24 | 10 | 8 | 1/10 status-backed | extended/legacy | 114 |
| `0x1006` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 26 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1007` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 26 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1008` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 27 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x100A` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 16 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x100D` | 20 | menu 18, timeout 2 | `0x4000` (2 args) | 42 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 8 | 9 | 8 | 1/9 status-backed | extended | 14 |
| `0x100E` | 3 | menu 3 | `0x4000` (2 args) | 6 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 3 |
| `0x100F` | 3 | menu 3 | `0x4000` (2 args) | 2 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x1010` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 27 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1011` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 35 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x1012` | 20 | menu 18, timeout 2 | `0x4000` (2 args) | 1 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x1013` | 45 | menu 43, timeout 2 | `0x4000` (2 args) | 114 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 10 | 8 | 1/10 status-backed | extended | 22 |
| `0x1014` | 24 | menu 22, timeout 2 | `0x4000` (2 args) | 111 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 10 | 8 | 1/10 status-backed | extended | 18 |
| `0x1015` | 6 | error 3, menu 3 | `0x4000` (2 args) | 4 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x1017` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 14 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1018` | 17 | error 15, timeout 2 | `0x4003` (1 args) | 0 | none | 0 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1101` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1102` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1103` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1105` | 913 | menu 899, render_timeout 1, timeout 13 | `0x4000` (2 args) | 932 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 25 | 10 | 8 | 1/10 status-backed | extended/legacy | 58 |
| `0x1106` | 16 | menu 14, timeout 2 | `0x4000` (2 args) | 32 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 10 |
| `0x1107` | 26 | menu 24, timeout 2 | `0x4000` (2 args) | 21 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x1108` | 19 | menu 17, timeout 2 | `0x4000` (2 args) | 26 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x110A` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x110D` | 30 | menu 28, timeout 2 | `0x4000` (2 args) | 23 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x110E` | 11 | menu 11 | `0x4000` (2 args) | 9 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 3 |
| `0x1110` | 21 | menu 19, timeout 2 | `0x4000` (2 args) | 19 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1111` | 28 | menu 26, timeout 2 | `0x4000` (2 args) | 22 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x1112` | 4 | menu 4 | `0x4000` (2 args) | 4 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 2 | 1 | 0/2 status-backed | extended | 2 |
| `0x1114` | 22 | menu 20, timeout 2 | `0x4000` (2 args) | 20 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 10 | 8 | 1/10 status-backed | extended | 16 |
| `0x1201` | 18 | menu 16, timeout 2 | `0x4000` (2 args) | 16 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1202` | 18 | menu 16, timeout 2 | `0x4000` (2 args) | 26 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1206` | 27 | menu 25, timeout 2 | `0x4000` (2 args) | 26 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x1208` | 54 | menu 40, render_timeout 12, timeout 2 | `0x4000` (2 args) | 52 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 3 | 9 | 8 | 1/9 status-backed | extended | 13 |
| `0x120A` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1214` | 22 | menu 20, timeout 2 | `0x4000` (2 args) | 38 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 10 | 8 | 1/10 status-backed | extended | 16 |
| `0x1300` | 148 | menu 146, timeout 2 | `0x0100` (0 args); `0x4000` (2 args) | 137 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 3 | 10 | 8 | 1/10 status-backed | extended/legacy | 38 |
| `0x1301` | 98 | menu 96, timeout 2 | `0x4000` (2 args) | 106 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended/legacy | 27 |
| `0x1302` | 18 | menu 16, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x130A` | 17 | menu 15, timeout 2 | `0x4000` (2 args) | 25 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 11 |
| `0x1315` | 5 | menu 5 | `0x4000` (2 args) | 3 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x1400` | 50 | menu 50 | `0x4000` (2 args) | 200 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 17 | 2 | 1 | 0/2 status-backed | extended/legacy | 50 |
| `0x1402` | 16 | menu 14, timeout 2 | `0x4000` (2 args) | 23 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 10 |
| `0x1500` | 62 | error 3, menu 59 | `0x0100` (0 args); `0x4000` (2 args) | 42 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 3 |
| `0x1502` | 16 | menu 14, timeout 2 | `0x4000` (2 args) | 14 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 10 |
| `0x1602` | 18 | menu 16, timeout 2 | `0x4000` (2 args) | 15 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 12 |
| `0x1702` | 16 | menu 14, timeout 2 | `0x4000` (2 args) | 23 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 9 | 8 | 1/9 status-backed | extended | 10 |
| `0x1708` | 2 | menu 2 | `0x4000` (2 args) | 2 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x1802` | 16 | menu 14, timeout 2 | `0x4000` (2 args) | 14 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 9 | 8 | 1/9 status-backed | extended | 10 |
| `0x1808` | 2 | menu 2 | `0x4000` (2 args) | 2 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x1908` | 3 | menu 3 | `0x4000` (2 args) | 3 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 2 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x1A08` | 3 | menu 3 | `0x4000` (2 args) | 2 | `0x4001` (2 args); `0x4101` (16 args); `0x4201` (0 args) | 1 | 1 | 1 | 0/1 status-backed | extended | 2 |
| `0x2001` | 267 | menu 126, render_timeout 141 | `0x4000` (2 args) | 311 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 3 | 4 | 3 | 3/4 status-backed | extended/legacy | 19 |
| `0x2002` | 200 | error 54, menu 132, render_timeout 1, timeout 13 | `0x0100` (0 args); `0x4000` (2 args) | 500 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 39 | 9 | 7 | 7/9 status-backed | extended/legacy | 56 |
| `0x2003` | 28 | raw_reply 21, timeout 7 | `0x0100` (0 args); `0x4002` (4 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2004` | 26 | raw_reply 25, timeout 1 | `0x0100` (0 args); `0x4402` (4 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2101` | 123 | raw_reply 123 | `0x4702` (9 args) | 0 | none | 0 | 5 | 4 | 4/5 status-backed | extended/legacy | 13 |
| `0x2102` | 548 | error 42, menu 417, render_timeout 3, timeout 86 | `0x0100` (0 args); `0x4000` (2 args) | 298 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 7 | 5 | 3 | 3/5 status-backed | extended/legacy | 263 |
| `0x2103` | 19 | raw_reply 12, timeout 7 | `0x0100` (0 args); `0x4002` (4 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2104` | 22 | raw_reply 21, timeout 1 | `0x0100` (0 args); `0x4702` (9 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 7 |
| `0x2201` | 45 | raw_reply 43, timeout 2 | `0x4702` (9 args) | 0 | none | 0 | 3 | 2 | 2/3 status-backed | extended/legacy | 7 |
| `0x2202` | 61 | error 61 | `0x4003` (1 args) | 0 | none | 0 | 5 | 3 | 3/5 status-backed | extended/legacy | 10 |
| `0x2204` | 19 | raw_reply 18, timeout 1 | `0x0100` (0 args); `0x4602` (5 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2301` | 270 | raw_reply 270 | `0x4E02` (5 args) | 0 | none | 0 | 4 | 3 | 3/4 status-backed | extended/legacy | 128 |
| `0x2302` | 61 | error 61 | `0x4003` (1 args) | 0 | none | 0 | 5 | 3 | 3/5 status-backed | extended/legacy | 10 |
| `0x2304` | 15 | raw_reply 12, timeout 3 | `0x0100` (0 args); `0x4003` (1 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 7 |
| `0x2401` | 139 | raw_reply 139 | `0x0100` (0 args); `0x4E02` (5 args) | 0 | none | 0 | 3 | 2 | 2/3 status-backed | extended/legacy | 115 |
| `0x2402` | 61 | error 61 | `0x4003` (1 args) | 0 | none | 0 | 5 | 3 | 3/5 status-backed | extended/legacy | 10 |
| `0x2404` | 15 | raw_reply 12, timeout 3 | `0x0100` (0 args); `0x4003` (1 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 7 |
| `0x2502` | 61 | error 61 | `0x4003` (1 args) | 0 | none | 0 | 5 | 3 | 3/5 status-backed | extended/legacy | 10 |
| `0x2504` | 19 | raw_reply 18, timeout 1 | `0x0100` (0 args); `0x4502` (4 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2602` | 690 | error 42, menu 611, render_timeout 3, timeout 34 | `0x0100` (0 args); `0x4000` (2 args) | 522 | `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args) | 28 | 5 | 3 | 3/5 status-backed | extended/legacy | 305 |
| `0x2604` | 15 | raw_reply 12, timeout 3 | `0x0100` (0 args); `0x4003` (1 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 7 |
| `0x2704` | 15 | raw_reply 12, timeout 3 | `0x0100` (0 args); `0x4003` (1 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 7 |
| `0x2804` | 19 | raw_reply 18, timeout 1 | `0x0100` (0 args); `0x4000` (2 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2904` | 19 | raw_reply 18, timeout 1 | `0x0100` (0 args); `0x4A02` (4 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2A04` | 19 | raw_reply 18, timeout 1 | `0x0100` (0 args); `0x4C02` (4 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2B04` | 15 | raw_reply 14, timeout 1 | `0x0100` (0 args); `0x4E02` (5 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 7 |
| `0x2C04` | 40 | raw_reply 39, timeout 1 | `0x0100` (0 args); `0x4F02` (5 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x2D04` | 33 | raw_reply 32, timeout 1 | `0x0100` (0 args); `0x4F02` (5 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 9 |
| `0x3000` | 1 | menu 1 | `0x4001` (2 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 1 |
| `0x3001` | 2 | sent 2 | none | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 1 |
| `0x3101` | 1 | sent 1 | none | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 1 |
| `0x3401` | 1 | menu 1 | `0x4000` (2 args) | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 1 |
| `0xFFFF` | 1 | timeout 1 | none | 0 | none | 0 | 1 | 1 | 0/1 status-backed | extended | 1 |

## Render index

The corpus contains 5556 explicit `0x3000` page
transactions following 59 distinct
menu-selection kinds. The exact render request type signatures are:

| Arguments | Wire types | Pages |
| ---: | --- | ---: |
| 5 | `number`, `number`, `number`, `number`, `number` | 57 |
| 6 | `number`, `number`, `number`, `number`, `number`, `number` | 110 |
| 8 | `number`, `number`, `number`, `number`, `number`, `number`, `number`, `number` | 5389 |

Observed render outcomes: reply 5392, timeout 164.
Observed render reply signatures: `0x4001` (2 args); `0x4101` (12/16 args); `0x4201` (0 args).
Render coverage spans 13 exact identity profiles, 8 model strings, 4/13 status-backed identities, and extended/legacy setup widths.
The `0x4101` rows contain 85 distinct composite item types.
Their exact values and counts are in the JSON ledger and the semantic
definitions remain in `ITEM_TYPE_REFERENCE.md`.

## Reproduction

```sh
python3 tools/generate_observed_response_shapes.py
python3 -m unittest conformance/test_observed_response_shapes.py
```

Regenerate this index after promoting or modifying a canonical
Rekordbox golden. Do not update it from `.next`, failed-attempt, or
backend-replay artifacts.
