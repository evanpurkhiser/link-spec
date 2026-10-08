# Captured probe sources

These are exact snapshots of the Rust probes used to create the source menu
evidence:

- `menu-probe-source.txt`: bounded tree traversal and pagination.
- `legacy-menu-probe-source.txt`: one-argument setup and 12-field rows.
- `search-probe-source.txt`: search encoding and length behavior.

They were copied from
`/home/evan/workspace/rbxport/crates/rbl-fakecdj/examples/` at rbxport commit
`c144f19`. They depend on that workspace's crates to compile; the source needed
to audit capture behavior is retained here even if the external checkout moves.
