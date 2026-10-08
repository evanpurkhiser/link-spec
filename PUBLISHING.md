# Publication checklist

The Git repository should contain the research narrative, tooling, suite
declarations, compact evidence, and canonical golden responses. Generated and
machine-local state is excluded by `.gitignore`, including:

- virtual environments and build products;
- generated fixture databases;
- backend replay results and runtime processes;
- historical accepted runner binaries retained for capture provenance;
- copied Rekordbox databases, WAL files, and shared-memory files;
- guest-control runtime state.

The ignored database copies remain local source evidence. `data/SHA256SUMS`
covers both publishable artifacts and this larger retained archive; a public
checkout verifies the available subset with `sha256sum --ignore-missing
--check data/SHA256SUMS`. The checked-in JSON, CSV, packet captures,
screenshots, declarations, and goldens should be reviewed as the publishable
evidence set. Large raw campaigns can be distributed separately if independent
reproduction needs them; they do not belong in ordinary Git history.

Before publishing the initial revision:

1. Review captured packets, screenshots, static-analysis extracts, and fixture
   payloads for personal data and third-party redistribution constraints.
2. Verify `data/SHA256SUMS` against the retained local evidence archive.
3. Confirm each published backend adapter documents its external executable
   contract and does not bundle implementation-specific build artifacts.
4. Run `make test`, `mise exec -- prek run --all-files`, and one backend smoke
   replay.
5. Inspect the complete initial staged diff and confirm no ignored artifact was
   force-added.
