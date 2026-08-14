from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kit"))

import apm_kit
from apm_codec import ApmArchiveError, build_apm_bundle, read_apm_bundle


class ApmExtractionTests(unittest.TestCase):
    def _archive(self, members: list[tuple[str, bytes, bytes | None]]) -> bytes:
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w:gz") as tar:
            for name, content, kind in members:
                info = tarfile.TarInfo(name)
                info.type = kind if kind is not None else tarfile.REGTYPE
                info.size = len(content) if info.isfile() else 0
                tar.addfile(info, io.BytesIO(content) if info.isfile() else None)
        return raw.getvalue()

    def _artifact(self) -> tuple[bytes, str]:
        manifest = {
            "agent_id": "source-agent",
            "version": "1.2.3",
            "package_ref": "source-agent@1.2.3",
        }
        return build_apm_bundle(
            manifest,
            {
                "agent.md": b"# Source\n",
                "apm.yml": b"name: source-agent\nversion: 1.2.3\n",
                "pack.json": json.dumps(manifest).encode(),
            },
        )

    def test_reader_rejects_unsafe_and_ambiguous_archive_members(self) -> None:
        cases = {
            "traversal": [("manifest.json", b"{}", None), ("../escape", b"x", None)],
            "absolute": [("manifest.json", b"{}", None), ("/escape", b"x", None)],
            "noncanonical": [("manifest.json", b"{}", None), ("./agent.md", b"x", None)],
            "directory": [("manifest.json", b"{}", None), ("directory", b"", tarfile.DIRTYPE)],
            "duplicate": [("manifest.json", b"{}", None), ("agent.md", b"one", None), ("agent.md", b"two", None)],
            "manifest_collision": [("manifest.json", b"{}", None), ("manifest.json", b"{}", None)],
        }
        for label, members in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(ApmArchiveError):
                    read_apm_bundle(self._archive(members))

    def test_builder_rejects_reserved_manifest_source_file(self) -> None:
        with self.assertRaises(ApmArchiveError):
            build_apm_bundle({"agent_id": "example"}, {"manifest.json": b"collision"})

    def test_extract_refuses_nonempty_output_and_writes_editable_source(self) -> None:
        artifact, content_hash = self._artifact()
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            source = temp_path / "source.apm"
            source.write_bytes(artifact)
            output = temp_path / "editable.agent"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = apm_kit.cmd_extract(argparse.Namespace(artifact=str(source), output=str(output)))
            self.assertEqual(rc, 0)
            self.assertEqual((output / "agent.md").read_text(encoding="utf-8"), "# Source\n")
            self.assertIn(content_hash, stdout.getvalue())

            stderr = io.StringIO()
            with redirect_stderr(stderr):
                rc = apm_kit.cmd_extract(argparse.Namespace(artifact=str(source), output=str(output)))
            self.assertEqual(rc, 1)
            self.assertIn("absent or empty", stderr.getvalue())

    def test_fork_reidentifies_canonical_and_authoring_manifests(self) -> None:
        artifact, content_hash = self._artifact()
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            source = temp_path / "source.apm"
            source.write_bytes(artifact)
            output = temp_path / "fork.agent"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = apm_kit.cmd_fork(
                    argparse.Namespace(
                        artifact=str(source),
                        output=str(output),
                        agent_id="forked-agent",
                        version="2.0.0-rc.1",
                    )
                )
            self.assertEqual(rc, 0)
            pack = json.loads((output / "pack.json").read_text(encoding="utf-8"))
            self.assertEqual(pack["agent_id"], "forked-agent")
            self.assertEqual(pack["version"], "2.0.0-rc.1")
            self.assertEqual(pack["package_ref"], "forked-agent@2.0.0-rc.1")
            authoring = apm_kit._load_yaml(output / "apm.yml")
            self.assertEqual(authoring["name"], "forked-agent")
            self.assertEqual(authoring["version"], "2.0.0-rc.1")
            self.assertIn(content_hash, stdout.getvalue())
            self.assertIn("rebuild and re-sign", stdout.getvalue())

    def test_fork_rejects_non_semver_before_writing(self) -> None:
        artifact, _ = self._artifact()
        with tempfile.TemporaryDirectory() as temp:
            temp_path = Path(temp)
            source = temp_path / "source.apm"
            source.write_bytes(artifact)
            output = temp_path / "fork.agent"
            with redirect_stderr(io.StringIO()):
                rc = apm_kit.cmd_fork(
                    argparse.Namespace(
                        artifact=str(source), output=str(output), agent_id="forked-agent", version="v2"
                    )
                )
            self.assertEqual(rc, 1)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
