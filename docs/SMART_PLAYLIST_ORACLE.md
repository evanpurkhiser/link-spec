# Smart playlist Link Export oracle

This oracle separates three questions that are easy to conflate:

1. whether Link Export selects `SmartList` or `djmdSongPlaylist`;
2. how Rekordbox parses and evaluates the rule XML;
3. whether another backend connects its rule evaluator to the Link Export
   playlist path.

The `smart-playlists` fixture answers the first question. The independent
`smart-rule-matrix`, `smart-numeric-matrix`, `smart-property-matrix`,
`smart-date-matrix`, `smart-relative-date-matrix`,
`smart-date-format-matrix`, `smart-text-matrix`,
`smart-string-property-matrix`, `smart-mytag-matrix`, `smart-xml-matrix`, and
`smart-numeric-boundaries` fixtures answer the second with 716 exact cases.
The same suites replay unchanged against rbxport for the third.

## Evidence

The rule matrix uses Rekordbox 7.2.19 and the isolated XDJ-RX3 player-1
identity. It was recorded after the suite contained exact ordered expectations,
then immediately repeated against the resulting golden.

| Artifact | Identity |
| --- | --- |
| Fixture database | `9831df811963e76f87c7d014a49995cc9440c706cdb69edf3f814b574848f7d7` |
| Logical fixture fingerprint | `d3a6032e6d63b2dc1aaae6403fd9309bc7754b14605df35c91b739496e47a79f` |
| Suite | `conformance/suites/smart-rule-matrix.json` |
| Golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-rule-matrix.json` |
| Machine summary | `data/experiments/smart-rule-matrix/summary.json` |
| Validator | `tools/summarize_smart_rule_matrix.py` |
| Numeric fixture database | `d1e58253cec61f0ebf6528d5e86d2324d71b1951be2e137b2680d7b24430802f` |
| Numeric logical fingerprint | `bcfe45e698261d0c7fd248430620cead30e9897dd8e2c8b65f3277e182b17726` |
| Numeric suite | `conformance/suites/smart-numeric-matrix.json` |
| Numeric golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-numeric-matrix.json` |
| Numeric machine summary | `data/experiments/smart-numeric-matrix/summary.json` |
| Numeric-boundary fixture database | `e24f385099f67721702afa49fd57beaa35ff5fdc87a834480920bbe23f78b93e` |
| Numeric-boundary logical fingerprint | `49d85459ca4f01d7020eb3821b6d4fc0897f7d2dea6fe36706c90562f8ca5240` |
| Numeric-boundary suite | `conformance/suites/smart-numeric-boundaries.json` |
| Numeric-boundary golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-numeric-boundaries.json` |
| Numeric-boundary machine summary | `data/experiments/smart-numeric-boundaries/summary.json` |
| Property fixture database | `c6b23269484398eb859985a2ed5f09b1938d656e7108e72be8b0780325e825d8` |
| Property logical fingerprint | `cea390a8e45b8dea84a84aade2be494d8532d22117f9382bbaf27d0da5ea8855` |
| Property suite | `conformance/suites/smart-property-matrix.json` |
| Property golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-property-matrix.json` |
| Property machine summary | `data/experiments/smart-property-matrix/summary.json` |
| Date fixture database | `7ec2225562023db4df8e7cd35c418cbcb9db4b6ae7a447714bea82acc61d12ba` |
| Date logical fingerprint | `9328d718ad717eb154c696339334136037d2f1e52f6d1c8908e58d0c04ccdb87` |
| Date suite | `conformance/suites/smart-date-matrix.json` |
| Date golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-date-matrix.json` |
| Date machine summary | `data/experiments/smart-date-matrix/summary.json` |
| Relative-date fixture database | `ba7298d8fc7319419adf2da67f9518886facd8fd8ed2059351a951417fc6fe5d` |
| Relative-date logical fingerprint | `df53ac9a736108788aa8521c79f649cc425b1026324f143fd2a5149c792b33e9` |
| Relative-date suite | `conformance/suites/smart-relative-date-matrix.json` |
| Relative-date golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-relative-date-matrix.json` |
| Relative-date machine summary | `data/experiments/smart-relative-date-matrix/summary.json` |
| Controlled-clock evidence | `data/experiments/smart-relative-date-matrix/clock.log` |
| Evaluator disassembly | `data/static-analysis/smart-condition-evaluator.disasm.txt` |
| Date-format fixture database | `df0652fa94f811884823b99c954b25da508573aa0e382b79497b7786fa39d9cd` |
| Date-format logical fingerprint | `b323a8e384a2849f30ae1eefae8b7c3425fd67249bf90ea80380c2db1ed989a6` |
| Date-format suite | `conformance/suites/smart-date-format-matrix.json` |
| Date-format golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-date-format-matrix.json` |
| Date-format machine summary | `data/experiments/smart-date-format-matrix/summary.json` |
| Date-conversion disassembly | `data/static-analysis/smart-date-conversion.disasm.txt` |
| LINK/modal UI evidence | `data/experiments/ui-debug/link-{before-click,after-click,loop-live}.png` |
| Text fixture database | `83da4b6b95bf99ba18a94a37f8bb7fa848d06d8d6ccb86a70fe33d9ea4c851cd` |
| Text logical fingerprint | `2d1e0f01d762fb0de5805eb64f1d74a4ba04949aab52add2762f45877f94397f` |
| Text suite | `conformance/suites/smart-text-matrix.json` |
| Text golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-text-matrix.json` |
| Text machine summary | `data/experiments/smart-text-matrix/summary.json` |
| Collation disassembly | `data/static-analysis/smart-collation.disasm.txt` |
| String-property fixture database | `56f4ffa97e0c4001fbb2c35f1de8e27c10d9c332265c68501bfea189d9bf473f` |
| String-property logical fingerprint | `288ccca10167ae01f82ccfe4fcd6fac7e4b0c1e4de34074a38de0038aa541c5e` |
| String-property suite | `conformance/suites/smart-string-property-matrix.json` |
| String-property golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-string-property-matrix.json` |
| String-property machine summary | `data/experiments/smart-string-property-matrix/summary.json` |
| My Tag fixture database | `3a4a804f062488b0c5c1285cbbb1fef0cc96c1ff355bad0906c29d2064d42728` |
| My Tag logical fingerprint | `1bf993c2ad6ce52d30b454675f0ddecfdb7fc1ccf74cf4a674b6a276549a4861` |
| My Tag suite | `conformance/suites/smart-mytag-matrix.json` |
| My Tag golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-mytag-matrix.json` |
| My Tag machine summary | `data/experiments/smart-mytag-matrix/summary.json` |
| XML fixture database | `f5a1179c0f37b1616d2fc9e154ce67a6cce74ace5e4d3140675130cb527aeea1` |
| XML logical fingerprint | `07a3c5bd928fe7d10c17bc4c53ce44ce4475963ad1bf21cabf3c06c12ad3d0e8` |
| XML suite | `conformance/suites/smart-xml-matrix.json` |
| XML golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-xml-matrix.json` |
| XML machine summary | `data/experiments/smart-xml-matrix/summary.json` |
| XML parser disassembly | `data/static-analysis/smart-xml-parser.disasm.txt` |
| Serving-cross suite | `conformance/suites/smart-serving-crosses.json` |
| Serving-cross golden | `conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-serving-crosses.json` |
| Legacy serving suite/golden | `conformance/{suites,goldens/rekordbox-7.2.19/xdj-rx3}/smart-serving-legacy.json` |
| Serving-cross machine summary | `data/experiments/smart-serving-crosses/summary.json` |

The eight live tracks deliberately alternate Genre while BPM and Rating rise:

| Content IDs | Genre | BPM storage | Rating |
| --- | --- | ---: | ---: |
| 10001-10008 | House, Techno, repeated | 12000 through 12350 by 50 | 0, 1, 2, 3, 4, 5, 0, 1 |

No matrix playlist has a `djmdSongPlaylist` row. A nonempty response therefore
comes from rule evaluation.

## Operator results

For the Genre field, codes 1, 2, and 8-11 behave as the community names
predict. Codes 3-7 are inapplicable and return an empty playlist.

| Code | Input | Ordered result | Observed meaning |
| ---: | --- | --- | --- |
| 1 | `Fixture House` | 10001, 10003, 10005, 10007 | equal |
| 2 | `Fixture House` | 10002, 10004, 10006, 10008 | not equal |
| 3 | `Fixture House` | empty | inapplicable to text |
| 4 | `Fixture Techno` | empty | inapplicable to text |
| 5 | House through Techno | empty | inapplicable to text |
| 6 | 1 day | empty | inapplicable to text |
| 7 | 1 day | empty | inapplicable to text |
| 8 | `House` | 10001, 10003, 10005, 10007 | contains |
| 9 | `House` | 10002, 10004, 10006, 10008 | does not contain |
| 10 | `Fixture` | all eight | starts with |
| 11 | `Techno` | 10002, 10004, 10006, 10008 | ends with |

The BPM cases intentionally use display-scale decimal values such as `121.5`.
Rekordbox compares them against the integer BPM storage domain. With database
values 12000-12350, equality returns empty, inequality and greater-than return
all rows, and less-than/range return empty. Codes 6-11 also return empty for
this numeric property. This establishes the scale boundary directly: a Link
Export-compatible evaluator must not multiply the XML value by 100 merely
because the UI displays BPM with a decimal.

## Stored numeric semantics

The independent `smart-numeric-matrix` adds 60 rules over BPM, Rating, Play
Count, Duration, and Year. Each property's normal cases use a value present in
exactly one row and ascending range endpoints that bracket several rows.

| Code | Numeric meaning | Boundary behavior |
| ---: | --- | --- |
| 1 | equal | exact stored value |
| 2 | not equal | complement of code 1 |
| 3 | greater than | exclusive |
| 4 | less than | exclusive |
| 5 | range | inclusive lower and upper endpoints |

All five reversed ranges return empty. Rekordbox does not normalize or swap
their endpoints. Empty `ValueLeft` and `not-a-number` produce the same results:
they coerce to numeric zero. Rating therefore returns content 10001 and 10007,
Play Count and Year return 10001, while BPM and Duration return empty because
their controlled rows contain no zero. Not-equal returns each complement.

A BPM threshold of -1 remains negative: greater-than returns all eight positive
rows and less-than returns empty. `2147483648` remains above every ordinary
fixture BPM, so it does not wrap negative. The storage-boundary matrix below
shows that positive rule text at and above `INT32_MAX` clamps to `INT32_MAX`.
The range `-1..0` and the range `2147483648..4294967296` are both valid ordered
ranges that contain no ordinary fixture row.

### Database numeric conversion boundaries

The independent 100-case `smart-numeric-boundaries` fixture stores the same ten
values in `BPM`, `Rating`, `DJPlayCount`, `Length`, and `ReleaseYear`: SQL
`NULL`, integer zero, REAL `0.5`, REAL `1.5`, REAL `-0.5`, integer `-1`,
`INT32_MAX`, `INT32_MAX + 1`, `UINT32_MAX`, and `UINT32_MAX + 1`. SQLite
`typeof()` was checked in the encrypted fixture before recording, so the REAL
and null cases are genuine storage classes **[DB]**.

The live equality, inequality, and ordered comparisons partition those rows as
follows **[OBS]**:

| Property path | Effective zero class | Positive class | Negative class | Excluded from every measured comparison |
| --- | --- | --- | --- | --- |
| BPM | null, 0, 0.5, -0.5, `UINT32_MAX + 1` | 1.5, `INT32_MAX` | none | -1, `INT32_MAX + 1`, `UINT32_MAX` |
| Rating | null, 0, 0.5, -0.5, `INT32_MAX + 1`, `UINT32_MAX + 1` | 1.5 | -1, `INT32_MAX`, `UINT32_MAX` | none |
| Play Count, Duration, Year | null, 0, 0.5, -0.5, `INT32_MAX + 1`, `UINT32_MAX + 1` | 1.5, -1, `INT32_MAX`, `UINT32_MAX` | none | none |

These partitions are consistent with three distinct field-conversion domains:
BPM applies a signed integer conversion and rejects negative converted rows;
Rating exhibits signed low-byte behavior; Play Count, Duration, and Year share
an unsigned-like path. The table is the normative result; the C++ type labels
are an inference from that result **[OBS, INF]**.

Fractional rule text `0.5` truncates to zero for all five properties. An absent
`ValueLeft` has the same result as explicit zero, and absent range endpoints
also become zero. Equality rule text at `2147483647`, `2147483648`,
`4294967295`, and `4294967296` selects the stored BPM `INT32_MAX` row, proving
positive saturation at the XML-to-condition boundary. The exact exploratory
result repeated, and the promoted 100-case golden repeated independently.
Rbxport is exact on 29 empty-result controls and differs on 71 populated cases.
`data/experiments/smart-numeric-boundaries/summary.json` retains every ordered
partition and provenance hash.

## Property vocabulary and storage mapping

The 33-case property matrix exercises all 23 property names documented by the
Pyrekordbox SmartList model, plus aliases and deliberately conflicting source
columns. Every populated case was selected so its row set identifies the
underlying database field rather than merely proving that the spelling parses.

| SmartList property | Controlled source | Ordered result |
| --- | --- | --- |
| `artist` | artist lookup | 10001-10005 |
| `album` | album lookup | 10001, 10003, 10004 |
| `albumArtist` | album-artist lookup | 10001-10005 |
| `originalArtist` | original-artist lookup | all eight |
| `bpm` | `BPM` | 10004 |
| `grouping` | color/grouping ID | 10004 |
| `comments` | `Commnt` | 10004 |
| `producer` | composer/producer lookup | 10001, 10003, 10005, 10007 |
| `stockDate` | `StockDate` | 10004 |
| `dateCreated` | `DateCreated` | 10004 |
| `counter` | `DJPlayCount` | 10004 |
| `fileName` | `FileNameL` | 10004 |
| `genre` | genre lookup | 10001, 10003, 10005, 10007 |
| `key` | key lookup | 10001, 10003, 10005, 10007 |
| `label` | label lookup | 10001, 10003, 10005, 10007 |
| `mixName` | `Subtitle` | 10004 |
| `myTag` | tag membership | controlled below |
| `rating` | `Rating` | 10004 |
| `dateReleased` | `ReleaseDate` | 10004 |
| `remixedBy` | remixer lookup | all eight |
| `duration` | `Length` | 10004 |
| `name` | track title | 10004 |
| `year` | `ReleaseYear` | 10004 |

`dateCreated` selects the track's `DateCreated` value. A deliberately
conflicting `created_at` audit timestamp returns empty. `mixName` selects
`Subtitle`. These controls make both mappings unambiguous.

For custom My Tags 8502 and 8504, rule values containing the raw positive IDs
return their exact membership sets: 10001/10002 and 10001/10003 respectively.
Values transformed to signed 32-bit form by subtracting 2^32 return empty.
This is live Link Export behavior for the controlled encrypted database and is
therefore the required representation at this boundary.

`filename` also selects `FileNameL`, so this spelling is accepted alongside
`fileName`. The plausible aliases `title`, `color`, `playCount`, `remixer`, and
`composer` all return normal empty menus. Their empty controls do not prove
that Rekordbox rejects the name independently of the value; they establish the
observable result for these exact rules.

## Fixed-date semantics

The 30-case date matrix applies operators 1-5 independently to `stockDate`,
`dateCreated`, and `dateReleased`. Each field contains the same controlled
sequence: 2024-02-28, leap day, 2024-03-01, 2025-01-31, 2025-02-28,
2025-03-01, blank, and `not-a-date`.

All three properties produce the same ordered sets:

| Code | Condition | Ordered result | Meaning |
| ---: | --- | --- | --- |
| 1 | equal 2025-01-31 | 10004 | date equality |
| 2 | not equal 2025-01-31 | 10001, 10002, 10003, 10005, 10006 | valid-date complement |
| 3 | greater than 2025-01-31 | 10005, 10006 | strict later-than |
| 4 | less than 2025-01-31 | 10001, 10002, 10003 | strict earlier-than |
| 5 | 2024-02-29 through 2025-02-28 | 10002, 10003, 10004, 10005 | inclusive ordered range |

Reversing the range returns empty. Blank and malformed track values are
excluded from both equal and not-equal results. A blank or malformed rule
value returns empty for equality; inequality returns the six parseable track
dates rather than admitting the blank and malformed rows. Date operators
therefore have a validity gate before comparison, unlike the numeric zero
coercion described above.

## Relative-date semantics

The 56-case relative matrix fixes the guest clock at
`2032-03-31T12:00:00-04:00` and applies operators 6 and 7 to `stockDate`,
`dateCreated`, and `dateReleased`. The ten rows include today, yesterday,
seven days earlier, the 2032 leap-day boundary, the day before it, one year
earlier, the preceding day, tomorrow, blank, and malformed values.

All three properties agree. For count 1, only case-insensitive singular
`month` uses calendar-month arithmetic. Units `day`, `week`, `year`, their
plural spellings, an empty unit, and an unknown unit all use the day helper.

| Rule | Operator 6 result | Operator 7 result |
| --- | --- | --- |
| count 1, non-`month` unit | 10001, 10008 | 10002-10007 |
| count 1, `month` or `MONTH` | 10001-10004, 10008 | 10005-10007 |
| count 2, day helper | 10001, 10002, 10008 | 10003-10007 |
| count 31, day helper | 10001-10003, 10008 | 10004-10007 |
| count 2, month helper | 10001-10005, 10008 | 10006, 10007 |

Operator 6 is a lower-bound test rather than a closed "past only" window:
tomorrow's row 10008 is included. Operator 7 is the complementary older-than
side for parseable rows. Blank and malformed track dates match neither side.
Zero, negative, blank, malformed, and fractional counts all behave like a
zero integer count. `ValueRight` is ignored by both operators.

The live results are independently repeated. Static evidence explains the
dispatch: `getSmartlistCondition` compares `ValueUnit` to `month`
case-insensitively, calls `pastMonthToDay` only for that spelling, calls
`pastDayToDay` otherwise, and rejects nonpositive `dateToDay` track values
before selecting the comparison operator.

## Fixed-date input grammar

The 117-case `smart-date-format-matrix` applies equality to 38 rule strings
for each of `stockDate`, `dateCreated`, and `dateReleased`, then applies a
canonical inequality control to each property. Forty track rows add embedded
NUL and SQL `NULL` values that cannot be represented safely as XML attribute
values. No playlist has materialized membership. All three properties produce
identical ordered results.

`dateToDay` accepts a nonempty JUCE string only when `length()` is exactly 10.
It reads year positions 0-3, month positions 5-6, and day positions 8-9.
Positions 4 and 7 are never read. The live oracle consequently treats all of
these as the same date:

| Stored/rule text | Equality result |
| --- | --- |
| `2025-01-31` | the seven equivalent rows |
| `2025/01/31` | the seven equivalent rows |
| `2025.01.31` | the seven equivalent rows |
| `2025 01 31` | the seven equivalent rows |
| `2025x01y31` | the seven equivalent rows |
| `2025Ω01Ω31` | the seven equivalent rows |
| `2025\n01\n31` | the seven equivalent rows |

The consumed positions are converted by arithmetic on their character code
points; there is no digit predicate. The function fills a C time structure,
invokes the runtime calendar conversion, rejects a nonpositive conversion,
then reduces the result to a day number. Live equality proves that each of the
following inputs survives as a parseable value: `2024-02-29`, `2025-02-29`,
`2024-02-30`, `2025-02-30`, `2025-02-31`, `2025-04-31`, `2025-00-15`,
`2025-13-01`, `2025-01-00`, `2025-01-32`, `2025-99-01`, `2025-01-99`, and
`202A-01-31`. Calendar overflow is therefore normalized rather than rejected.
Each fixture value was chosen to yield a distinct normalized day except for
the seven deliberate January 31 equivalents.

The following values match no equality rule: the epoch and pre-epoch controls,
year zero, year 9999, every string whose length is not 10, leading/trailing
spaces, arbitrary letters, all-zero digits, signed years, fullwidth digits,
and the empty string. Embedded NUL and SQL `NULL` track values also appear in
neither canonical equality nor canonical inequality. Canonical inequality
returns exactly the 13 other parseable values; it excludes the seven rows that
normalize to January 31 and every conversion failure.

This is a parser contract, not an endorsement of those strings as valid
calendar notation. A compatible backend must reproduce the conversion and
normalization results rather than validate ISO 8601.

## Text collation and string operators

The 55-case `smart-text-matrix` exercises operators 1, 2, and 8-11 against
`comments` over 43 controlled track values. It covers ASCII case, composed and
decomposed accents, combining-mark order, width, Turkish I, Greek sigma,
hiragana/katakana, German sharp S, AE ligatures, supplementary characters,
punctuation, spaces/tabs/newlines, cross-script confusables, XML entities,
empty, SQL `NULL`, and embedded NUL. No playlist has materialized membership.

The applicable operators are:

| Code | Meaning | Empty rule |
| ---: | --- | --- |
| 1 | collation equality | matches empty and SQL `NULL` candidates |
| 2 | collation inequality | matches every nonempty candidate |
| 8 | contains | matches nothing |
| 9 | does not contain | matches nothing |
| 10 | starts with | matches nothing |
| 11 | ends with | matches nothing |

The nonempty matcher is case-insensitive and ignores precomposed accents,
fullwidth versus ASCII forms, hiragana versus katakana, and Greek sigma versus
final sigma. ASCII `I` and dotted capital `İ` agree under the US locale;
dotless `ı` remains distinct. Cyrillic and Greek capital-alpha confusables do
not match Latin `A`.

Canonical composition is directional. A precomposed `Álpha` rule matches plain,
precomposed, and decomposed Alpha candidates, while a decomposed
`A` + combining-acute rule matches no row, including the byte-identical
decomposed candidate. A trailing-combining-mark rule and both two-mark-order
rules likewise return empty. Candidate-side decomposed forms still enter the
plain/precomposed Alpha equivalence set.

Collation expansions are also directional. A `straße` rule matches both
`straße` and `STRASSE`, while a `STRASSE` rule matches only `STRASSE`; a rule
containing `ss` does not find the sharp-S candidate. `Æther` matches both
`Æther` and `AETHER`, while `AETHER` matches only the expanded spelling.

Punctuation and whitespace remain significant at equality: `AlphaBeta`,
`Alpha-Beta`, `Alpha Beta`, `Alpha\tBeta`, and `Alpha\nBeta` each match only
their own fixture row. Contains/prefix/suffix searches still locate `Beta`
at their respective boundaries. Contains crosses hyphen, no separator, tab,
newline, ampersand, quote, and apostrophe forms. Supplementary-plane
characters work at code-point boundaries for exact, contains, prefix, and
suffix operations.

The candidate `Alpha\0Tail` compares exactly equal to `Alpha`, while
`Before\0Alpha` behaves as `Before`; conversion to ICU therefore truncates at
the first embedded NUL. XML `&amp;`, `&quot;`, and `&apos;` rule values decode and
match their database characters.

Static evidence explains the broad equivalences and the directional edge
cases. `CollationRule` constructs ICU 51 `StringSearch` with the US locale,
sets collator strength to primary, shares the search object behind a critical
section, and implements four custom loops that advance over Unicode
code-point boundaries. The 55 exact ordered sets remain the authority where
the custom loops differ from generic ICU expectations.

## Cross-property string semantics

The 104-case `smart-string-property-matrix` crosses the six applicable string
operators and the empty equality/inequality pair over all 13 written string
properties:

- lookup-backed: `artist`, `album`, `albumArtist`, `originalArtist`,
  `producer`, `genre`, `key`, `label`, and `remixedBy`;
- direct: `comments`, `fileName`, `mixName`, and `name`.

Ten tracks assign the same controlled value sequence to every path: `Alpha`,
`alpha`, precomposed `Álpha`, decomposed `A` plus combining acute, fullwidth
`Ａｌｐｈａ`, `Alpha Beta`, `Beta Alpha`, `Beta`, empty, and missing/null. Each
lookup track points to a distinct lookup row, including an empty-name row;
the missing track uses relation ID zero. The four direct fields use an empty
string and SQL `NULL` for the same two tracks.

Every property returns the same ordered sets:

| Rule | Content IDs |
| --- | --- |
| equals `Alpha` | 13001-13005 |
| not equal `Alpha` | 13006-13010 |
| contains `Alpha` | 13001-13007 |
| does not contain `Alpha` | 13008 |
| starts with `Alpha` | 13001-13006 |
| ends with `Alpha` | 13001-13005, 13007 |
| equals empty | 13009, 13010 |
| not equal empty | 13001-13008 |

The shared result proves that the observed ICU collation/search behavior is
not specific to Comments. An empty lookup name behaves like a direct empty
string, and a missing lookup relation behaves like SQL `NULL`, including for
nonempty inequality and empty equality. The exploratory capture repeated all
104 cases. The exact promoted golden then passed an independent immediate
repeat. `tools/summarize_smart_string_property_matrix.py` validates every row
set and binds the suite, fixture, golden, and replay hashes.

## My Tag condition semantics

The 49-case `smart-mytag-matrix` uses eight tracks and five tag IDs spanning
zero, one, `INT32_MAX`, the high bit, and `UINT32_MAX`. Operators 8 and 9 are
membership and non-membership. Every other operator code from 1 through 11
returns an empty playlist for this property. An untagged track participates
normally: it is excluded by membership and included by non-membership.

The XML value is parsed through JUCE's signed integer attribute conversion.
Positive values above `INT32_MAX`, including raw `2147483648`, raw
`4294967295`, and `4294967296`, saturate to `INT32_MAX`. `-2147483648`
preserves the high-bit tag ID, while `-1` preserves the `UINT32_MAX` bit
pattern. Negative underflow saturates to `INT32_MIN`. Leading zeroes, a plus
sign, and surrounding spaces parse as decimal; `0x1` becomes zero;
`1,2147483648` consumes the leading decimal one. Malformed text becomes zero,
but a blank attribute is a distinct case that returns empty for both
operators. `ValueRight` and `ValueUnit` do not affect membership.

All/any grouping applies per condition rather than merging tag operands.
Because raw positive `2147483648` saturates to `INT32_MAX`, an all-group
requiring tag 1 and that value is empty, while an any-group selects the union
of tag 1 and `INT32_MAX` memberships. Mixed contains/not-contains groups obey
the same normal Boolean composition. Every ordered set is preserved in
`data/experiments/smart-mytag-matrix/summary.json`.

Static evidence agrees with the oracle. `db::operate` at `0x1023354a0`
dispatches property type `0x40`, accepts only operators 8 and 9, and scans the
track tag array at offset `0x440` with count at `0x44c`. The parser branch at
`0x102336623` recognizes `myTag`, calls `XmlElement::getIntAttribute`, and
assigns type `0x40` **[OBS, DB, DEC]**.

## Group and parser behavior

| Case | Ordered result | Consequence |
| --- | --- | --- |
| root all: House and BPM > 121.5 | House IDs | all-of is active; the BPM predicate admits every stored BPM |
| root any: House or BPM > 121.5 | all eight | any-of is active |
| all containing nested any, then Rating > 2 | 10004, 10005, 10006 | nested `NODE` is ignored; only the direct Rating condition remains |
| any containing nested all, then BPM > 121.5 | all eight | nested `NODE` is ignored; only the direct BPM condition remains |
| empty all or empty any | empty | empty groups do not use Boolean identity semantics |
| unknown operator or property | empty | an invalid single condition rejects every row |
| condition before an empty root | empty | conditions outside the selected root are ignored |
| two consecutive roots | House IDs | the first root wins; the second is ignored |
| missing logic, logic 0, or logic 3 | House IDs | missing/unknown root logic defaults to all-of |
| AutomaticUpdate 0, 1, or absent | House IDs | this attribute does not alter serving |
| matching, mismatched, or absent root Id | House IDs | root Id does not select or gate serving |

Malformed XML from the precedence fixture and unknown semantic elements from
this matrix both produce a normal empty menu. They do not cause a protocol
error, timeout, or connection close.

### XML document and node parser

The dedicated 73-case XML matrix separates document parsing from condition
evaluation. `db::getSmartlistContentData` at `0x102334b00` calls JUCE
`XmlDocument::parse`, rejects a null document element, and passes the first
element to `db::getSmartlistNode` at `0x102335130`. The node parser requires a
case-insensitive `NODE` element, reads the case-sensitive `LogicalOperator`
attribute as an integer, iterates direct children, and calls
`getSmartlistCondition` only for case-insensitive `CONDITION` elements. It has
no recursive `NODE` call. A root with no valid direct conditions returns false;
after at least one condition, logic values outside 1 and 2 become 1 (all-of)
**[OBS, DB, DEC]**.

Element names and property values are case-insensitive; attribute names are
case-sensitive. Attribute order and quoting style do not matter. Duplicate
attributes use their first value. Integer attributes accept a plus sign,
surrounding whitespace, and leading zeroes. XML declarations, leading
comments, leading processing instructions, trailing comments, decimal/hex
character references, and trailing text are accepted. The first of two roots
wins. A trailing NUL is tolerated, while a leading NUL, BOM, or ordinary text
before the root yields an empty result. Unknown entities, invalid numeric
entities, namespaces, wrappers, unknown direct children, and wrapped or nested
conditions yield no usable condition. Rekordbox's JUCE parser surprisingly
accepts the measured mismatched root close **[OBS, DB]**.

All parser failures and zero-condition forms return an ordinary zero-row menu;
none produces a protocol error or closes the connection. The canonical run
recorded all 73 cases and immediately repeated them exactly. Rbxport matches
the 40 empty controls and returns empty for all 33 populated Rekordbox cases.
`tools/summarize_smart_xml_matrix.py` asserts the ordered sets, parser
partitions, disassembly addresses, fingerprints, and replay result.

### Downstream serving crosses

The 65-case `smart-serving-crosses` suite opens the rule-only `logic_any`
playlist, whose two direct conditions select all eight controlled tracks. It
then applies the same sort, render, pagination, and packed-context matrices as
an ordinary collection request. A separate one-case suite uses legacy setup.
Both canonical recordings passed an immediate independent repeat **[OBS, DB]**.

All sort IDs 0-17 return the same eight-member rule result. Their exact Content
ID orders are:

| Sort IDs | Ordered Content IDs |
| --- | --- |
| 0, 2, 4, 7, 9, 11, 15 | 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008 |
| 1, 14 | 10001, 10002, 10003, 10004, 10005, 10008, 10006, 10007 |
| 3 | 10001, 10003, 10004, 10006, 10008, 10002, 10005, 10007 |
| 5 | 10006, 10005, 10004, 10003, 10002, 10008, 10001, 10007 |
| 6, 10, 12 | 10001, 10003, 10005, 10007, 10002, 10004, 10006, 10008 |
| 8, 13, 16 | 10008, 10007, 10006, 10005, 10004, 10003, 10002, 10001 |
| 17 | 10004, 10008, 10003, 10007, 10002, 10006, 10001, 10005 |

The render gate and selectors 2-17 preserve membership and order. Their row
item types are the same complete map documented in `SECONDARY_COLUMNS.md`:
Artist `0x0704`, Album `0x0204`, BPM `0x0d04`, Rating `0x0a04`, Genre
`0x0604`, Comments `0x2304`, Time `0x0b04`, Remixer `0x2904`, Label
`0x0e04`, Original Artist `0x2804`, Key `0x0f04`, Bitrate `0x1004`, the
reserved selector `0x0004`, Color `0x1404`, Play Count `0x2a04`, and Date
Added `0x2e04`. A zero gate retains the database-selected Key column even when
the override argument is nonzero **[OBS, DB]**.

Pagination is also shared exactly. Count zero returns the first row; offsets at
or beyond total clamp to the last row; an overrun from the last offset wraps to
the complete eight-row result; overlapping windows repeat the overlap; and
offset `UINT32_MAX` reaches `render_timeout`. Requester 1 succeeds, requester
bytes 2-6 time out, menu locations 1-8 succeed, and slots 0-4 succeed. Extended
setup emits 16 row arguments and legacy setup emits 12 **[OBS]**.

Search cannot be scoped to an intelligent playlist on this Link Export request
surface. Both `0x1300` and `0x1500` carry context, sort, and query data but no
playlist ID; `0x1105` carries the playlist ID but no search term. A “search
inside this SmartList” cross therefore has no server request to declare. The
global Search behavior is covered independently in `SEARCH_ORACLE.md`.

## Link Export integration

`djmdPlaylist.Attribute = 4` is the serving switch. Rekordbox evaluates the
rule at request time and ignores contradictory materialized membership. It
does not rewrite the fixture database on startup.

Rbxport has a separate smart-rule parser, but its Link Export playlist path
still reads materialized membership. In the property matrix every rule
playlist has no membership, so its eight empty Rekordbox controls are
field-exact and all 25 nonempty cases diverge. Across the rule and numeric
matrices, the same mechanism makes empty controls exact and populated rules
diverge. This is an integration boundary, not evidence that the empty rule
interpretations agree.

The date matrix adds nine exact empty controls and 21 populated divergences at
the same integration boundary. Its equality, ordering, range, and invalid-date
semantics remain untested inside rbxport until Link Export invokes the evaluator.

The relative-date matrix adds 56 populated divergences and no exact or
same-shape cases. Rbxport's Link Export path therefore exercises none of the
recorded unit dispatch, boundary, count-coercion, or invalid-date behavior.

The date-format matrix adds 54 exact empty controls and 63 populated
divergences. Rbxport returns an empty menu for every declaration, so the exact
cases prove only shared emptiness. Its Link Export path does not exercise the
recorded fixed-length parser, ignored separators, character arithmetic, or
calendar normalization.

The text matrix adds eight exact empty controls and 47 populated divergences.
Rbxport again returns an empty menu for every declaration. The exact controls
therefore do not validate its equality classes, substring boundaries,
expansions, Unicode handling, or empty/null semantics.

The cross-property matrix adds 104 divergences and no exact or same-shape
cases. Unlike the Comments-only empty substring controls, every rule here has
a nonempty Rekordbox result: empty equality returns the empty/missing pair,
empty inequality returns all nonempty rows, and the nonempty string rules each
select at least one track. Rbxport's empty menus therefore disagree for every
lookup-backed and direct string path.

The My Tag matrix adds 12 exact empty controls and 37 populated divergences.
Rbxport returns empty for all 49 declarations, so its exact cases do not
exercise tag parsing, signed conversion, membership, or Boolean composition.

The downstream serving suites add 66 populated divergences and no exact or
same-shape cases. Rbxport returns zero rows before any recorded sort, secondary
selector, pagination, context, or width behavior can operate. Once its Link
Export catalog evaluates `SmartList`, these cases become the direct regression
surface for the shared serving stages.

After rule evaluation, Rekordbox applies the ordinary Link Export visibility
predicate to each Smart result. The separate `link-visibility` fixture proves
that Smart and ordinary playlists return the same ten visible IDs from fourteen
candidate rows, filtering active streaming-protocol `FolderPath` values. See
`LINK_EXPORT_VISIBILITY_ORACLE.md`.

## Reproduction

From `/home/evan/workspace/rx3-research`:

```sh
PY=rekordbox-windows/.venv/bin/python
LAB=rekordbox-link-export-research

"$PY" "$LAB/conformance/build_fixture.py" smart-rule-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-rule-matrix"

"$LAB/conformance/activate_fixture.sh" \
  "$LAB/conformance/fixtures/generated/smart-rule-matrix"
"$LAB/conformance/start_oracle_ui.sh"
"$LAB/conformance/oracle_record.sh" \
  "$LAB/conformance/suites/smart-rule-matrix.json" \
  "$LAB/conformance/fixtures/generated/smart-rule-matrix/manifest.json" \
  "$LAB/conformance/runs/xdj-rx3-player-1.json" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-rule-matrix.json"

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$PY" "$LAB/tools/summarize_smart_rule_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-numeric-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-numeric-matrix"

"$LAB/conformance/activate_fixture.sh" \
  "$LAB/conformance/fixtures/generated/smart-numeric-matrix"
"$LAB/conformance/start_oracle_ui.sh"
"$LAB/conformance/oracle_record.sh" \
  "$LAB/conformance/suites/smart-numeric-matrix.json" \
  "$LAB/conformance/fixtures/generated/smart-numeric-matrix/manifest.json" \
  "$LAB/conformance/runs/xdj-rx3-player-1.json" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-numeric-matrix.json"

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$PY" "$LAB/tools/summarize_smart_numeric_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-property-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-property-matrix"

"$LAB/conformance/activate_fixture.sh" \
  "$LAB/conformance/fixtures/generated/smart-property-matrix"
"$LAB/conformance/start_oracle_ui.sh"
"$LAB/conformance/oracle_record.sh" \
  "$LAB/conformance/suites/smart-property-matrix.json" \
  "$LAB/conformance/fixtures/generated/smart-property-matrix/manifest.json" \
  "$LAB/conformance/runs/xdj-rx3-player-1.json" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-property-matrix.json"

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$PY" "$LAB/tools/summarize_smart_property_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-date-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-date-matrix"

"$LAB/conformance/activate_fixture.sh" \
  "$LAB/conformance/fixtures/generated/smart-date-matrix"
"$LAB/conformance/start_oracle_ui.sh"
"$LAB/conformance/oracle_record.sh" \
  "$LAB/conformance/suites/smart-date-matrix.json" \
  "$LAB/conformance/fixtures/generated/smart-date-matrix/manifest.json" \
  "$LAB/conformance/runs/xdj-rx3-player-1.json" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-date-matrix.json"

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$PY" "$LAB/tools/summarize_smart_date_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-relative-date-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-relative-date-matrix"

"$LAB/conformance/record_smart_relative_date.sh" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-relative-date-matrix.json" \
  auto

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$PY" "$LAB/tools/summarize_smart_relative_date_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-date-format-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-date-format-matrix"

"$LAB/conformance/record_smart_date_format.sh" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-date-format-matrix.json" \
  auto

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$LAB/.venv/bin/python" \
  "$LAB/tools/summarize_smart_date_format_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-text-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-text-matrix"

"$LAB/conformance/record_smart_text.sh" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-text-matrix.json" \
  auto

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$LAB/.venv/bin/python" "$LAB/tools/summarize_smart_text_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-string-property-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-string-property-matrix"

"$LAB/conformance/record_smart_string_property.sh" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-string-property-matrix.json" \
  auto

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$LAB/.venv/bin/python" \
  "$LAB/tools/summarize_smart_string_property_matrix.py"

"$PY" "$LAB/conformance/build_fixture.py" smart-mytag-matrix \
  rekordbox-windows/shared/library/master.db \
  /mnt/documents/multimedia/djing/rekordbox/options.json \
  "$LAB/conformance/fixtures/generated/smart-mytag-matrix"

"$LAB/conformance/record_smart_mytag.sh" \
  "$LAB/conformance/goldens/rekordbox-7.2.19/xdj-rx3/smart-mytag-matrix.json" \
  auto

"$PY" "$LAB/conformance/replay_rbxport.py" --no-build
"$LAB/.venv/bin/python" "$LAB/tools/summarize_smart_mytag_matrix.py"
```

The isolation check inside `oracle_record.sh` is mandatory. Restore the guest
to `play-paths` after recording, stop the temporary synthetic identity, and
retain the fixture, golden, replay, and machine summary as evidence.

## Ordinary device-identity cross

The two-case `smart-device-cross.json` suite requests the rule-only
`logic_any` playlist and the zero-condition `empty_all` playlist. The same
fixture and request envelopes were recorded under XDJ-RX3, CDJ-3000,
CDJ-2000NXS2, XDJ-XZ, XDJ-AZ, XDJ-1000MK2, unknown mixer, and unknown DJM
discovery identities. Each golden was checked by an immediate independent
repeat before promotion **[OBS]**.

Every identity returns Content IDs `10001` through `10008` for the populated
playlist and a zero-row menu for the empty playlist. The complete canonical
`.behavior` object is byte-identical after sorted JSON normalization under all
eight identities, with SHA-256
`8a38e105670fb5942da59cbb2bbb9754d36dccc45ab1bdb53db0392b67b3f002`.
This closes the ordinary discovery model, device class, generation, and player
number cross for SmartList membership and track-row construction **[OBS]**.
It does not replace genuine player-status testing for the separately proven
Display Song Info AIO branch.

Rbxport is exact for the eight empty controls and differs for all eight
populated controls because its Link Export path reads materialized membership
instead of evaluating `SmartList`. The reproducible evidence and per-identity
packet, golden, and behavior hashes are in
`data/experiments/smart-device-cross/summary.json`.

## Persisted secondary-column cross

The 17-suite `smart-secondary-*` matrix crosses every valid persisted
secondary selection plus the no-selection and multiple-selection database
states with a populated eight-track intelligent playlist. Every suite was
recorded from real rekordbox and immediately repeated against its golden
**[OBS, DB]**.

The first `Alpha One` row is:

| State | Argument 0 | Argument 5 | Argument 6 |
| --- | ---: | --- | ---: |
| None | `0` | empty | `0x0004` |
| Album | `2001` | `Album One` | `0x0204` |
| Artist | `1001` | `Alpha Artist` | `0x0704` |
| Bitrate | `0` | empty | `0x1004` |
| BPM | `12000` | `120.0 bpm - Am` | `0x0d04` |
| Color | `1` | `Pink` | `0x1404` |
| Comment | `10001` | `comment-1` | `0x2304` |
| Date Added | `10001` | `2021-02-02` | `0x2e04` |
| Genre | `3001` | `Fixture House` | `0x0604` |
| Key | `5001` | `Am - 120.0 bpm` | `0x0f04` |
| Label | `4001` | `Fixture Label One` | `0x0e04` |
| Original Artist | `1004` | `Fixture Original` | `0x2804` |
| DJ Play Count | `0` | empty | `0x2a04` |
| Rating | `0` | empty | `0x0a04` |
| Remixer | `1003` | `Fixture Remixer` | `0x2904` |
| Time | `59` | empty | `0x0b04` |
| Comment + Key selected | `10001` | `comment-1` | `0x2304` |

This table records the Classic local CDJ style. The repeat-verified
Alphanumeric BPM control changes the first BPM row to `120.0 bpm - 8A` and
tertiary Key to `8A`; numeric BPM, KeyID, membership, and order remain fixed.
`KEY_NOTATION_ORACLE.md` contains the complete style cross.

For a given ContentID, every other field matches the corresponding ordinary
collection row. Smart rows differ in argument 9: they retain the persisted
SmartList membership sequence `1..8`, while the ordinary ALL-albums collection
rows carry zero. The Smart response follows membership order; the ordinary
default title order places the final three fixture tracks differently. This
proves that evaluation selects the candidate set while the playlist membership
sequence remains row metadata **[OBS]**.

Rbxport returns zero populated rows for all 17 cases, so none is exact or
same-shape. `tools/summarize_smart_secondary_columns.py` checks every row,
preference-specific value, item type, membership sequence, fixture and suite
hash, repeat claim, and replay result. Its machine-readable output is
`data/experiments/smart-secondary-columns/summary.json`.

The canonical batch used resumable promotion after three UI obstructions were
identified: the Mobile Library Sync dialog, the expanded Sync Manager layout,
and an elevated terminal left by Rekordbox Agent when Windows 11 lacks
`wmic.exe`. Direct noVNC RFB coordinates dismiss those overlays and activate
LINK. Every failed or successful exit restored `play-paths`; screenshots and
the recovery ledger are retained in `data/experiments/ui-debug/`.
