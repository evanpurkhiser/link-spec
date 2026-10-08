# Captured status packet templates

These files preserve UDP payloads from real devices for isolated Rekordbox
identity experiments. `identity_adapter.py` validates the packet length,
player-status header, model, and both player-number fields before transmitting
one. It sends them only after the calling recorder passes the VM isolation
gate.

## CDJ-2000nexus player 1

`cdj-2000nexus-player-1.hex` is the unmodified 284-byte payload sent at
14:06:18.211725 in Dysentery capture
`doc/assets/captures/S05-link-browse/run.pcapng`:

- source: `169.254.103.172:9676`;
- destination: `169.254.202.84:50002`;
- model: `CDJ-2000nexus`;
- player fields: 1 and 1;
- payload SHA-256:
  `8e9c36049a85be2f31c989bfbff415d989bdb0f395987135eb35f53f1d8fb70b`;
- source capture SHA-256:
  `4ae48d19172c10c07180a80e6d488ae8c0d7f437149d8428cf17ad060adc8852`.

The paired genuine keepalive identifies generation 2, class CDJ, player 1,
presence 1, model code 0, and peer count 2. Its 54-byte payload SHA-256 is
`5f4e3e86ee4fac8146ba22b519505292092c65dfd6fcc6e3fa59c142c44ef4dc`.
The lab recreates that field shape with its isolated address and project MAC;
the status payload itself remains byte-for-byte captured evidence.
