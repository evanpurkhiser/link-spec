#!/usr/bin/env python3
import hashlib
import json
from collections import Counter
from pathlib import Path

try:
    from .rekordbox_health import validate_health_pair
except ImportError:
    from rekordbox_health import validate_health_pair


ROOT = Path(__file__).resolve().parent.parent
CONFORMANCE = ROOT / "conformance"
MATRIX = CONFORMANCE / "data/track-compatibility-exhaustive-matrix.json"
MANIFEST = CONFORMANCE / "fixtures/generated/compatibility-exhaustive/manifest.json"
GOLDEN_ROOT = CONFORMANCE / "goldens/rekordbox-7.2.19/xdj-rx3"
OUTPUT = ROOT / "data/experiments/track-compatibility-exhaustive/summary.json"
EVIDENCE_ROOT = ROOT / "data/experiments/track-compatibility-exhaustive/setups"
IDENTITY = CONFORMANCE / "runs/xdj-rx3-player-11.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(argument: dict) -> int:
    if argument.get("type") != "number":
        raise AssertionError(f"expected number argument, got {argument}")

    return int(argument["value"])


def summarize_golden(path: Path, setup: str, expected: dict[int, dict]) -> dict:
    golden = load(path)
    behavior = golden["behavior"]
    provenance = golden["provenance"]
    case = behavior["cases"][0]
    suite = (
        CONFORMANCE
        / "suites/generated/track-compatibility-exhaustive"
        / f"track-compatibility-exhaustive-{setup}.json"
    )
    evidence = EVIDENCE_ROOT / setup
    receipt_path = evidence / "receipt.json"
    receipt = load(receipt_path)

    assert golden["format"] == 2
    assert provenance["backend"] == "rekordbox"
    assert provenance["backend_version"] == "7.2.19"
    assert provenance["suite_sha256"] == sha256(suite)
    assert provenance["fixture_database_sha256"] == load(MANIFEST)["database_sha256"]
    assert provenance["fixture_fingerprint"] == load(MANIFEST)["fixture_fingerprint"]
    assert provenance["identity"]["model"] == "XDJ-RX3"
    assert provenance["identity"]["player"] == 11
    assert provenance["identity"]["packet_sha256"] == load(IDENTITY)["packet_sha256"]
    assert receipt == {
        **receipt,
        "format": 1,
        "scope": "real Rekordbox 7.2.19 exhaustive track compatibility",
        "setup": setup,
        "suite_sha256": sha256(suite),
        "fixture_manifest_sha256": sha256(MANIFEST),
        "identity_sha256": sha256(IDENTITY),
        "golden_sha256": sha256(path),
        "independently_repeated": True,
    }
    health = validate_health_pair(
        evidence,
        receipt,
        f"track-compatibility-exhaustive-{setup}",
        sha256,
    )
    assert case["outcome"] == "menu"
    assert case["total"] == len(expected)
    assert len(case["rows"]) == len(expected)

    argument_count = 16 if setup == "extended" else 12
    observed = {}
    partitions = Counter()
    for row in case["rows"]:
        arguments = row["arguments"]
        assert len(arguments) == argument_count
        content_id = number(arguments[1])
        compatibility = number(arguments[10])
        declaration = expected.pop(content_id)
        expected_word = 0x100 if declaration["supported"] else 0x101
        assert compatibility == expected_word, (content_id, compatibility, expected_word)
        partitions[f"{declaration['axis']}:{'supported' if declaration['supported'] else 'unsupported'}"] += 1
        observed[content_id] = arguments[:12]

    assert not expected
    return {
        "setup": setup,
        "golden_sha256": sha256(path),
        "argument_count": argument_count,
        "row_count": len(observed),
        "partitions": dict(sorted(partitions.items())),
        "receipt_sha256": sha256(receipt_path),
        "post_request_health": health,
        "rows": observed,
    }


def main() -> None:
    matrix = load(MATRIX)
    declared = {int(row["id"]): row for row in matrix["rows"]}
    results = []
    for setup in ("extended", "legacy"):
        path = GOLDEN_ROOT / f"track-compatibility-exhaustive-{setup}.json"
        results.append(summarize_golden(path, setup, dict(declared)))

    assert results[0]["rows"] == results[1]["rows"]
    for result in results:
        result.pop("rows")

    summary = {
        "format": 1,
        "experiment": "track-compatibility-exhaustive",
        "matrix_sha256": sha256(MATRIX),
        "fixture_database_sha256": load(MANIFEST)["database_sha256"],
        "fixture_fingerprint": load(MANIFEST)["fixture_fingerprint"],
        "declared_rows": matrix["row_count"],
        "extended_legacy_prefix_equal": True,
        "results": results,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
