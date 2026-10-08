# Conformance backends

The Link Export golden corpus is backend-neutral. `replay_catalog.py` owns the
shared suite inventory, while `conformance_backend.py` owns fixture grouping,
execution, and report generation. A backend adapter supplies the following
operations:

- build or locate the backend launcher;
- record source provenance;
- derive a reproducible backend version;
- start one isolated server for a fixture/configuration group and yield its
  discovery port;
- describe backend-specific configuration limits in the report.

The adapter also declares whether a server can be reused across suites with an
equivalent configuration. rbxport can reuse a server for equivalent
configurations.

`replay_rbxport.py` implements this interface against the shared `REPLAYS`
catalog. It runs the 287 active suites and produces `summary.json`,
`SUMMARY.md`, actual-response, diff, and log files. The 149 mutation and
lifecycle suites in `DEFERRED_REPLAYS` remain outside the safe automated phase.

## rbxport

The rbxport adapter accepts an implementation-owned server through
`--server-binary`. The executable must implement the readiness and command-line
contract used by `replay_rbxport.py`; link-spec does not import or compile
rbxport crates.
