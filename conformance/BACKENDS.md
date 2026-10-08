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
equivalent configuration. Vynull uses a fresh process per suite so a
protocol-triggered crash remains local to the case that caused it. rbxport can
reuse a server for equivalent configurations.

`replay_rbxport.py` and `replay_vynull.py` implement this interface against the
same `REPLAYS` catalog. Both therefore run the same 287 active suites and
produce the same `summary.json`, `SUMMARY.md`, actual-response, diff, and log
shapes. The 149 mutation and lifecycle suites in `DEFERRED_REPLAYS` remain
explicitly outside the safe automated phase for every backend.

## Vynull

The Vynull adapter decrypts each generated `master.db` fixture into an isolated
JSON transfer file, preserving the canonical Rekordbox IDs. Vynull's
`cmd/conformance-server` command maps that fixture into its library, playlist,
tag, cue, settings, and menu interfaces and starts only the database server on
`127.0.0.1`. It does not
start device announcements, NFS, the web application, or audio analysis.

Run the complete active corpus:

```bash
python3 conformance/replay_vynull.py --enable-vynull-replay
```

Run one or more suites while developing:

```bash
python3 conformance/replay_vynull.py \
  --enable-vynull-replay \
  --suite xdj-rx3/full \
  --suite xdj-rx3/empty
```

The default output is
`conformance/results/vynull/<commit>+tree.<digest>/`. Each suite reports exact
case equality and a coarser outcome/total/row-count match. Transport failures
remain visible as run errors rather than being counted as protocol mismatches.

The adapter obtains the fixture database key from the configured Rekordbox
`options.json` and passes it to Vynull's dump helper through the environment.
The key is not written to results or placed in the process argument list.
The adapter builds that command from the checkout selected by `--vynull`.
Vynull owns its Go version and dependencies; this repository's runner and
development toolchain remain Python-only.

## rbxport

The rbxport adapter accepts an implementation-owned server through
`--server-binary`. The executable must implement the readiness and command-line
contract used by `replay_rbxport.py`; link-spec does not import or compile
rbxport crates.
