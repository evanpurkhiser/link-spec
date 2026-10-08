# Delivery row-order state experiment

Seventeen generated suites isolate request position, render controls, preceding
request family. Each was recorded twice from a separately activated `full`
fixture and a fresh Rekordbox process. The paired `.behavior` objects are
byte-identical. The first three suites establish the Delivery-only sequence:

| Suite | Cases | Behavior SHA-256 |
| --- | ---: | --- |
| repeated identical request | 16 | `a640b7472b8e2fa9e694ece1f82bc069e1480e1b598ca6d99f91a407b162d97a` |
| controls forward | 21 | `3ad97d44b1ffda4ccefd84a0c6edac051e3e968ba19c472a041fa09811aa7039` |
| controls reversed | 21 | `e1c83e5c589e6502cdd9a9caa7902ba6c9f5ec59332a58e720ec87d56361be71` |

For populated Delivery Info requests with identical render arguments, a cold
process produces order A for requests 1-3, B for request 4, C for request 5,
D for request 6, then A/B/C/D repeatedly:

```text
A 0036 000d 0023 000f 0012 0006 000e 0007 0037 004f 0f04 0002 000b
B 0036 000d 0023 000f 0012 0f04 000e 0006 0037 0007 0002 004f 000b
C 004f 000f 0007 0002 0023 0037 000b 000e 0f04 0012 000d 0036 0006
D 0036 0006 004f 0f04 0002 000e 0023 0012 0037 000f 000b 000d 0007
```

The forward and reversed suites inherit the same pattern by case position when
the selector-specific composite type is normalized to `0x0f04`. Reversing the
controls changes which pattern accompanies a selector without changing the
selector's composite value or type. The selector controls the composite Title
row; it does not select the heterogeneous row permutation.

The rejected same-process boundary repeat in the sibling experiment is the
same sequence continuing across suite passes: its second pass begins at C/D/A/B
after the first eight requests. Restarting Rekordbox resets the cold prefix.
Fresh TCP connections do not reset it because every case in these suites opens
a fresh connection.

Six additional suites alternate one precursor with one populated Delivery
probe for eight iterations. Their results are:

| Precursor | Precursor result | Delivery probe patterns | Behavior SHA-256 |
| --- | --- | --- | --- |
| Delivery missing | zero-row menu | `AAABCDAB` | `3bdc47acdbb4756ad22fabf1fa7c456fa0ff0e1182e95c0c53f84a52ad01f843` |
| Display missing | zero-row menu | `AAAAAAAA` | `4f626091a7aca252070eed959ca14807a7e7210dfa7c84cd62f0550fce67df83` |
| Display populated | 16-row menu | `AAEAEAEA` | `062b94163e9ea6bce31fabb53d45b109286406262ff25504f692c197ab5feea9` |
| Play missing | zero-row menu | `AAAAAAAA` | `348d61ffe23ea82117cb2ab02a9390e5db92e96fb41b3ad55db1a49fc29aa777` |
| Play populated | 7-row menu | `AAAAAAAA` | `e584d9bd1148d53b2eb38cce34565583cc386b22e74590c709e6d0fba5b43f86` |
| recognized `0x2202` | `4003` error | `AAABCDAB` | `70253144e918e5bcaf830a802c1ad172821eb5f81677886054e8cb543c483dae` |

Pattern E is:

```text
E 0002 0f04 0023 000f 004f 0037 0007 000e 0006 0012 000d 0036 000b
```

Delivery-missing requests and no-builder errors leave the populated Delivery
sequence untouched: the eight probes are exactly the first eight standalone
populated positions. Missing Display, missing Play, and populated Play make
every following Delivery probe use baseline A. Populated Display gives two
initial A results, then alternates E/A. The evidence therefore describes
shared list-buffer state rather than a single request counter **[OBS]**.

Run `tools/summarize_delivery_order.py` to verify paired behavior equality,
recompute hashes, recover the precursor results, and print every normalized
pattern directly from the retained recordings.

Six matched suites repeat the family matrix on one TCP connection from setup
through the final probe. Every complete 16-case response array is exactly equal
to its per-case reconnect counterpart:

| Precursor | Same-socket probe patterns | Same-socket behavior SHA-256 |
| --- | --- | --- |
| Delivery missing | `AAABCDAB` | `a3a6f3e71b535b522dac1c5a4c0dec51a47c4f9be75290f2ec9b1eed1cdbd19f` |
| Display missing | `AAAAAAAA` | `0de939cac60f443e19ee889cb61f530e02618b76073fa033c8d0bf95bae0ec68` |
| Display populated | `AAEAEAEA` | `d125c922e8e804cd4b3c843a51570b9da1c0573c0cd7129b6a92b25061689a67` |
| Play missing | `AAAAAAAA` | `5804661c090b3d6039c5fbb70f868e5ee6bff0ba59fb56b25a83ff79512aef9d` |
| Play populated | `AAAAAAAA` | `e17325a89875cd0cc0c4577b2c9c0d2cd8c11dc3ce57fc69e8f71cbc1635c5b3` |
| recognized `0x2202` | `AAABCDAB` | `831d355074903c285a3f06acf7f8c7a05d4d14c07f22f115055495950b630ab4` |

TCP connection reuse and replacement therefore have no observable effect on
the tested ordering state **[OBS]**. The remaining lifecycle matrix is removal
and reintroduction of the discovery identity without restarting Rekordbox.

That lifecycle was tested in two modes, each repeated from a separate cold
process. Six populated Delivery calls warm the process through `AAABCD`. The
identity then stops for 40 seconds. The first port query after renewed emission
times out in every automated run; a further 30-second wait and renewed identity
emission reopens Link Export without restarting Rekordbox. Run 1 of the
same-identity case was recovered manually against the still-running process,
which accounts for its 108-second recording gap versus 98 seconds in the three
automated retry paths.

| Lifecycle | Warm-up | Post-rejoin | Warm-up behavior SHA-256 | Post behavior SHA-256 |
| --- | --- | --- | --- | --- |
| same XDJ-RX3 identity | `AAABCD` | `ABCDABCD` | `3b27099d46537d61fe3d9a2f2d4dc530d372ce36cfe7392468b24ba65867861e` | `56132f1cea4b5f002555a5158e6da8a608f3f4ee4f402d7d4b37666140f9ba11` |
| XDJ-RX3 -> CDJ-3000 | `AAABCD` | `ABCDABCD` | `3b27099d46537d61fe3d9a2f2d4dc530d372ce36cfe7392468b24ba65867861e` | `56132f1cea4b5f002555a5158e6da8a608f3f4ee4f402d7d4b37666140f9ba11` |

Both phases are byte-identical across repeats and across lifecycle modes. The
post sequence is the exact continuation after warm-up call six, not the cold
`AAABCDAB` prefix. Discovery expiry, rejoin, and replacement across XDJ/CDJ
model and keepalive classes preserve Delivery builder state **[OBS]**.

The remaining ordering work is sequences longer or less regular than strict
precursor/probe alternation and status-backed sibling identities.
