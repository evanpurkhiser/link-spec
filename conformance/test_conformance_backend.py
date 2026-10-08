import unittest
from contextlib import nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

import conformance_backend


class FakeAdapter:
    name = "fake"
    reuse_server_across_suites = True

    def prepare(self) -> None:
        pass

    def source_provenance(self) -> dict[str, object]:
        return {"tree_sha256": "source", "lab_tree_sha256": "lab"}

    def version(self, provenance: dict[str, object]) -> str:
        return str(provenance["tree_sha256"])

    def server(self, fixture: str, second_column: str, sorts: str | None, result_root: Path):
        return nullcontext(12345)

    def summary_notes(self) -> tuple[str, ...]:
        return ("Fake backend.",)


class FailingAdapter(FakeAdapter):
    def server(
        self,
        fixture: str,
        second_column: str,
        sorts: str | None,
        result_root: Path,
    ):
        raise RuntimeError("unsupported fixture setting")


class IsolatedAdapter(FakeAdapter):
    reuse_server_across_suites = False

    def __init__(self) -> None:
        self.server_count = 0

    def server(
        self,
        fixture: str,
        second_column: str,
        sorts: str | None,
        result_root: Path,
    ):
        self.server_count += 1
        return nullcontext(12345)


class BackendAdapterTests(unittest.TestCase):
    def test_adapter_contract_is_backend_neutral(self) -> None:
        adapter: conformance_backend.BackendAdapter = FakeAdapter()

        self.assertEqual("fake", adapter.name)
        self.assertTrue(adapter.reuse_server_across_suites)
        self.assertEqual("source", adapter.version(adapter.source_provenance()))
        with adapter.server("full", "key", None, Path("results")) as port:
            self.assertEqual(12345, port)

    def test_aggregate_reports_exact_and_shape_rates(self) -> None:
        totals = conformance_backend.aggregate_suites(
            [
                {
                    "cases": 3,
                    "exact_cases": ["a"],
                    "same_outcome_total_row_count_cases": ["a", "b"],
                    "behavior_matches": False,
                    "run_error": None,
                },
                {
                    "cases": 1,
                    "exact_cases": ["c"],
                    "same_outcome_total_row_count_cases": ["c"],
                    "behavior_matches": True,
                    "run_error": "transport failed",
                },
            ]
        )

        self.assertEqual(4, totals["cases"])
        self.assertEqual(2, totals["exact_cases"])
        self.assertEqual(3, totals["same_outcome_total_row_count_cases"])
        self.assertEqual(0.5, totals["exact_case_rate"])
        self.assertEqual(0.75, totals["same_outcome_total_row_count_rate"])
        self.assertEqual(1, totals["completed_suites"])
        self.assertEqual(1, totals["errored_suites"])

    def test_server_startup_failure_is_reported_without_aborting(self) -> None:
        replay = SimpleNamespace(
            model="xdj-rx3",
            suite="example",
            fixture="full",
            second_column="key",
            sorts=None,
        )

        with TemporaryDirectory() as directory:
            destination = Path(directory)
            with mock.patch.object(conformance_backend, "summarize") as summarize:
                result = conformance_backend.run(
                    FailingAdapter(), (replay,), destination, no_build=True
                )

            self.assertEqual(destination.resolve(), result)
        errors = summarize.call_args.args[4]
        self.assertEqual(
            "RuntimeError: unsupported fixture setting",
            errors[("xdj-rx3", "example")],
        )

    def test_non_reusable_adapter_starts_one_server_per_suite(self) -> None:
        replays = tuple(
            SimpleNamespace(
                model="xdj-rx3",
                suite=suite,
                fixture="full",
                second_column="key",
                sorts=None,
            )
            for suite in ("first", "second")
        )
        adapter = IsolatedAdapter()

        with TemporaryDirectory() as directory:
            with (
                mock.patch.object(conformance_backend, "verify_replay", return_value=None),
                mock.patch.object(conformance_backend, "summarize"),
            ):
                conformance_backend.run(
                    adapter, replays, Path(directory), no_build=True
                )

        self.assertEqual(2, adapter.server_count)
