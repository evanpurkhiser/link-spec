# link-spec

`link-spec` is a research corpus and conformance suite for rekordbox Link
Export. It documents the protocol used by rekordbox to expose a music library
to Pioneer and AlphaTheta players, then turns the observed behavior into
replayable golden tests.

## Repository layout

- `conformance/` contains suite declarations, Rekordbox goldens, the protocol
  client, and backend adapters.
- `docs/` contains the protocol reference, research findings, experiment logs,
  and coverage records. Start with the [documentation index](docs/README.md).
- `data/` contains retained captures, derived datasets, and the checksum ledger.
- `tools/` contains the scripts that regenerate derived references and reports.

## Rekordbox oracle

Rekordbox 7.2.19 is the behavioral oracle. Its canonical results are under
`conformance/goldens/rekordbox-7.2.19/` and cover library navigation, row
rendering, configuration, Smart Playlists, Song Info, Hot Cue Banks, malformed
requests, and lifecycle behavior.

The recordings run in an isolated Windows guest with no default route. The
active backend-neutral catalog contains 287 safe replay suites; another 149
mutation and lifecycle suites remain deferred. See the
[research summary](docs/RESEARCH_SUMMARY.md),
[coverage ledger](docs/CONFORMANCE_COVERAGE.md), and
[source inventory](docs/SOURCES.md) for the detailed evidence and remaining
gaps.

## Running the suite

Install the pinned development tools and Git hooks:

```sh
mise install
mise exec -- prek install
```

Run the local unit and protocol-client tests:

```sh
make test
```

The full research-integrity suite also uses retained local evidence and the
pinned Rekordbox executable:

```sh
make test-research
```

Backend adapters implement the interface in
`conformance/conformance_backend.py`. Their commands and result format are
documented in [conformance/BACKENDS.md](conformance/BACKENDS.md).

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions and golden
update rules.

## License

This repository is licensed under the [MIT License](LICENSE).
