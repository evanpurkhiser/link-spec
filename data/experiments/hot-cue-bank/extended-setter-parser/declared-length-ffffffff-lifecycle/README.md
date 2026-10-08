# Declared length `UINT32_MAX` lifecycle experiment

The extended `0x2401` setter parser matrix produced two different responses to
the follow-up `0x2301` getter after independent fixture resets and Rekordbox
restarts. Both runs returned an immediate argument-free generic `0x0100` to the
setter and left the database pristine. In the first run, the new getter
connection received a later `0x4e02` response whose echoed request kind was
`0x2401`; in the repeat it received the expected `0x2301` response.

`discovery/record.json` and `discovery/repeat.json` are immutable copies of
those noncanonical observations. Their SHA-256 hashes are respectively
`ca665fde47730a3920451069ae6ddf6a127266e9d6f826c70a1377165435dd9c` and
`bdb95a3f2e3eefa0d4f06c5a3b7690a1a7d8c8ebf14884b695d5906713cd700f`.

The declared lifecycle matrix separates three socket topologies:

| Topology | Delay occurs | Question |
| --- | --- | --- |
| `same-connection` | after the setter response, before a read without a send | Does the late reply arrive on the setter socket? |
| `before-reconnect` | while the setter socket remains open, before replacing it | Does waiting allow the late reply to remain with the original socket? |
| `after-reconnect` | after replacing the setter socket, before a read without a send | Is a late reply routed to the newest connection for the player identity? |

Each suite observes the socket without transmitting bytes, then issues a type-1
getter on that connection and a final getter after another wait and fresh
connection. Every topology/delay cell has three independent fixture/process
replicates. These are observations rather than equality-promoted goldens because
nondeterminism is the behavior under investigation.

The three completed zero-delay `after-reconnect` observations demonstrate both
branches. Two setters first returned `0100 []`, after which the no-send read on
the replacement socket received `4e02 [2401, 50, 0, empty_blob, 0]`. One setter
received that status-50 response directly, after which the no-send read timed
out. Both getters in all three observations returned the pristine 124-byte
record. `summary.partial.json` records the per-cell counts while the remaining
observations run. The three zero-delay `same-connection` observations all
returned `0xfffffffe/0100`, then EOF on the no-send read and EOF on the getter
attempt. Their final fresh-connection getters returned the pristine record.

Static reconstruction explains why two messages can race. The `0x2401`
formatter declares number, number, number, number, blob, number. At
`PSvDBConnection::ReceiveCommand` `0x10143b8a8..0x10143b9bf`, the blob length is
taken from the preceding numeric argument and must be below `0x500000` and
nonzero. `UINT32_MAX` stops argument parsing but leaves the partially populated,
zero-initialized command eligible for dispatch. The setter therefore sees a
null blob and zero record count and schedules the correlated status-50 reply.
The separate `0xfffffffe/0100` frame is constructed by the connection Drop,
Listen, and destructor paths immediately before the EDB agent is dropped. It is
the close sentinel rather than a setter response. `RetNewCueToClient` later
routes the correlated reply through a shared queue keyed by player/device byte,
not by the originating socket. The matrix measures the resulting timing and
replacement-connection lifetime rather than assuming one from the static code.

Static evidence:

| Artifact | SHA-256 |
| --- | --- |
| `data/static-analysis/dbserver-command-parser.disasm.txt` | `f6066519e7fd9585f4790c655b03e6b162d128e30e143fe4eb0f94b072fb2c08` |
| `data/static-analysis/dbserver-connection-send.disasm.txt` | `83a760f7cd60ae954fe2d88888d118ad4a0ef7023f42de33c234806f6f006578` |
| `data/static-analysis/hot-cue-reply-routing.disasm.txt` | `df7bdcabc54d86823e098373084a1daba09c74c2faed4aef759130c69c236a7f` |

Run the matrix only against the isolated real-Rekordbox VM:

```bash
conformance/record_hot_cue_declared_length_ffffffff_lifecycle.sh
```

The recorder restores the `play-paths` fixture on exit. It does not launch or
compare any implementation backend.

## Recorder interruption

After 15 complete observations, an attempted systemd `After=` handoff started
the next parser recorder immediately because the lifecycle unit's start job had
already completed. The new recorder was stopped during fixture activation,
before it sent an oracle request or wrote a golden. Its EXIT trap restored
`play-paths`, invalidating the lifecycle recorder's in-progress 500 ms attempt.
That attempt reached only a port-query timeout and wrote no observation file.

The original lifecycle unit was then stopped cleanly and its EXIT trap restored
`play-paths`. Exactly 15 nonempty observation files remained and passed the
partial reducer. The resumed bounded unit
`codex-rekordbox-hot-cue-ffffffff-matrix-20261002b.service` skipped those files,
reinstalled the fingerprinted duplicate-slot fixture, and resumed at
`same-connection-0500ms-run-1`. No interrupted attempt is part of the evidence
set.

The replacement handoff is an explicit validation gate rather than a systemd
ordering dependency. Bounded unit
`codex-rekordbox-hot-cue-parser-handoff-20261002b.service` waits while the
resumed lifecycle unit is active, runs the strict reducer without
`--allow-partial`, and starts the resumable deterministic parser recorder only
when all 60 observations validate. An early lifecycle stop therefore leaves
the next recorder unstarted.
