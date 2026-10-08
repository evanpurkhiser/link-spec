# Delivery boundary same-process ordering experiment

The first eight-case Delivery-boundary recording and its immediate verification
used one Rekordbox process. The verifier rejected the candidate because the
first two cases changed row order. Cases three through eight were exact.

`first-process-record.json` begins with order patterns `A A A B C D A B`.
`immediate-same-process-repeat.json` uses `C D A B C D A B`, where each letter
represents a distinct permutation of the same thirteen item types. Every case
used the identical render arguments. This isolates warmed process/list-buffer
state as a response-order dimension; it does not support attributing those
permutations solely to render selectors.

The canonical boundary suite uses `fixture-reset-and-restart` repetition so
field-boundary equality is tested from the same cold fixture/process state.
Follow-up order experiments must vary request order and process reset as
independent dimensions.
