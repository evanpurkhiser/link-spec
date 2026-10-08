# Contributing

This repository separates test intent, generated fixture databases, oracle
responses, and backend replay output. Keep changes in the layer that owns the
behavior:

- `conformance/suites/` describes requests and expected case structure;
- `conformance/goldens/` contains immutable responses recorded from the named
  Rekordbox version;
- `replay_catalog.py` owns the backend-neutral active and deferred suite sets;
- `conformance_backend.py` owns backend-neutral orchestration and reporting;
- each `replay_*.py` module owns one backend's executable discovery, fixture translation, and
  server lifecycle;
- `tools/` regenerates derived research indexes and summaries.

Do not edit a golden to make an implementation pass. Change a golden only when
a reproducible Rekordbox recording establishes a different oracle result, and
retain the recording provenance described in `docs/CONFORMANCE.md`.

Install the pinned development tools and Git hooks with:

```sh
mise install
mise exec -- prek install
```

## Local checks

Run the unit and protocol-client tests from the repository root:

```sh
make test
```

Run the repository hooks with `mise exec -- prek run --all-files`.

The larger research-integrity suite also regenerates evidence from the pinned
Rekordbox executable. Prepare its Python environment with:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

Restore the binary at the path recorded in `docs/SOURCES.md`, then run
`make test-research`.

The rbxport adapter consumes a backend-provided executable. Its path can be
overridden with the adapter command-line options.

See `conformance/BACKENDS.md` for the adapter contract, full-corpus command,
result schema, and safety boundary.
