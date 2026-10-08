# RX3 status menu-location-2 state matrix

This directory isolates matched player-11 menu location 2 under the genuine
XDJ-RX3 status identity. Every header-only suite was recorded twice from a
fresh Rekordbox 7.2.19 process and deterministic `full` fixture. Each case uses
either a fresh TCP connection or one socket shared by the complete suite. All
paired behavior objects are byte-identical.

## Results

Seven families run eight iterations per cold process. A location-2 Delivery
probe follows each precursor; the Delivery-only control has no precursor.

| Precursor | Precursor result | Eight Delivery probe totals |
| --- | --- | --- |
| none | - | `13 13 13 13 13 13 13 13` |
| zero-context Play | timeout | `13 13 13 13 13 13 13 13` |
| primary-location Play | 7 rows | `13 13 13 13 13 13 13 13` |
| location-2 Play | 7 rows | `13 13 13 13 13 13 13 13` |
| primary-location Display | 16 rows | `13 13 13 13 13 13 13 13` |
| location-2 Display | 16 rows | `13 13 13 13 13 13 13 13` |
| primary-location Delivery | 13 rows | `13 13 13 13 13 13 13 13` |

The seven header-only families were also recorded twice with all cases sharing
one dbserver connection. Their 208 case results, fixture identity, setup, and
setup exchange exactly equal the per-case reconnect controls. This includes
all sixteen zero-context Play timeouts: each following Delivery probe succeeds
on the same socket with 13 rows.

The 16-precursor malformed bisection gives one direct exception. A blob-valued
content ID sent to either Play or Delivery makes the immediately following
location-2 Delivery menu empty. Every other tested malformed precursor leaves
the Delivery total at 13. Both 32-case cold recordings are exact.

The malformed suite cannot finish on one connection. In both cold attempts,
the no-argument, missing-content, and extra-argument Play pairs complete. The
wrong-typed string context is then followed by Rekordbox closing dbserver
before the paired Delivery probe can complete. The two retained `.log` files
are expected-failure evidence; a completed JSON envelope would misrepresent
the connection termination.

The older broad malformed sequence remains a wider-state caveat: its identical
final blob-content/Delivery pair produced 13 in one cold run and 0 in another,
correlated with zero-context Play timing out versus returning empty earlier in
the sequence. The direct-prefix result is deterministic; a longer malformed
history can alter whether that immediate effect is applied.

`delivery-only-run-{1,2}.json` are intentional render-location controls. Their
menu requests at location 2 advertise total 13, then their default-location-1
render requests time out. The corrected header-only control is
`delivery-only-header-run-{1,2}.json`.

Run `tools/summarize_status_location2.py` from the project root to validate
every suite hash, paired behavior object, reconnect/shared-socket equality,
malformed connection cutoff, precursor outcome, probe total, and render control
directly from these retained artifacts. The directory contains seventeen
generated declarations, thirty-two successful real recordings totaling 496
completed case executions, and two expected-failure transcripts.
