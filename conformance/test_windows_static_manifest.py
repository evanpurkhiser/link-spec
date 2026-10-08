import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WINDOWS = ROOT / "data/static-analysis/windows"
MANIFEST = WINDOWS / "manifest.json"
GENERATOR = ROOT / "tools/generate_windows_static_manifest.py"


class WindowsStaticManifestTests(unittest.TestCase):
    def test_manifest_regenerates_byte_identically(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "manifest.json"
            subprocess.run(
                ["python3", GENERATOR, "--output", output],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertEqual(MANIFEST.read_bytes(), output.read_bytes())

    def test_manifest_covers_every_retained_extract(self) -> None:
        manifest = json.loads(MANIFEST.read_text())
        expected = {
            str(path.relative_to(ROOT))
            for path in WINDOWS.iterdir()
            if path.is_file() and path != MANIFEST
        }
        actual = {artifact["path"] for artifact in manifest["artifacts"]}

        self.assertEqual(expected, actual)
        self.assertEqual(20, len(actual))
        for artifact in manifest["artifacts"]:
            path = ROOT / artifact["path"]
            self.assertEqual(
                artifact["sha256"],
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )

    def test_function_extracts_bind_their_start_addresses(self) -> None:
        manifest = json.loads(MANIFEST.read_text())
        for artifact in manifest["artifacts"]:
            arguments = artifact["producer_arguments"]
            if artifact["producer"] != "tools/analyze_windows_pe.py":
                continue
            if arguments[0] != "function":
                continue

            first_line = (ROOT / artifact["path"]).read_text().splitlines()[0]
            self.assertTrue(first_line.startswith(f"address={arguments[1]} "))

    def test_cleanup_and_documentation_keep_the_pe_boundary(self) -> None:
        manifest = json.loads(MANIFEST.read_text())
        static = (ROOT / "docs/STATIC_ANALYSIS.md").read_text()
        cleanup = (ROOT / "docs/CLEANUP.md").read_text()

        self.assertFalse(manifest["cleanup"]["temporary_host_copy_retained"])
        self.assertEqual(3, manifest["format"])
        self.assertEqual(
            "290bfaa2bbab6d4b650d9e8982b5a8eeaaa86ad168eb8dc3f3d506c11310f862",
            manifest["source"]["installer_sha256"],
        )
        self.assertEqual("rekordbox.exe", manifest["source"]["installer_member"])
        self.assertIn("Windows PE evidence boundary", static)
        self.assertIn("host executable", cleanup)
        self.assertIn("are disposable", cleanup)


if __name__ == "__main__":
    unittest.main()
