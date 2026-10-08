# Song Info malformed-state experiments

These artifacts retain Play (`0x2102`) and Delivery (`0x2602`) malformed
request behavior that cannot honestly be represented by one context-free
golden. Every recording came from rekordbox 7.2.19 on the isolated VM with the
deterministic `full` fixture. The physical RX3 was unreachable.

## Ordinary identity

| Artifact | Purpose |
| --- | --- |
| `record.json`, `repeat-1.json` | First broad candidate and its non-identical immediate repeat |
| `audit-run-1.json` | Cold alternating zero-context audit |
| `sequence-run-1.json` | Valid-family requests interleaved with zero context |
| `prefix-run-{1,2}.json` | Repeat-identical precursor bisection |
| `zero-context-*-suite.json` | Declarations for the three focused experiments |

Only a blob-valued content ID immediately before zero context changes the cold
timeout into an empty menu. `prefix-run-1.json` and `prefix-run-2.json` are
behavior-identical and establish that result independently.

## Genuine status identities

The status experiments preserve all 17 malformed cases in a fixed order. The
canonical status goldens contain the 14 repeatable type/arity cases; zero
context and the two alternate-location requests remain here.

| Recordings | Identity/context | Observed zero / Play location 2 / Delivery location 2 |
| --- | --- | --- |
| `status-cdj-3000-run-{1,2}.json` | CDJ-3000 player 1; matched `0x01020301` | empty / 7 / 13 in both runs |
| `status-rx3-run-{1,2}.json` | RX3 player 11; inherited player-1 `0x01020301` | timeout then empty / timeout / empty |
| `status-rx3-matched-run-{1,2}.json` | RX3 player 11; matched `0x0b020301` | timeout then empty / 7 / 13 then 0 |

`status-xdj-rx3-immediate-repeat-actual.json` retains the rejected immediate
repeat that first demonstrated non-canonical status behavior. The `*-suite.json`
files preserve both the inherited-context and player-matched declarations.

Run `tools/summarize_status_siblings.py` from the project root to validate the
canonical status equality and every outcome above. Regenerate declarations
with `python3 conformance/generate_matrices.py`; do not regenerate or overwrite
the real recordings.
