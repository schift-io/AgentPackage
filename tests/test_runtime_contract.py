from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kit"))

import apm_kit
from runtime_contract import runtime_required_capabilities, validate_runtime_contract


class RuntimeContractTests(unittest.TestCase):
    def test_interoperability_fixture_is_valid_and_declares_all_authority(self) -> None:
        pack = ROOT / "examples" / "interoperability.agent"
        manifest = json.loads((pack / "pack.json").read_text(encoding="utf-8"))

        self.assertEqual(validate_runtime_contract(manifest, pack_root=pack), [])
        self.assertEqual(
            runtime_required_capabilities(manifest),
            {
                "a2a_task_server",
                "agent_plugins_runtime",
                "cclg_memory_candidate_write",
                "cclg_memory_read",
                "connected_source_fetch_connector",
                "connected_source_search_connector",
                "human_input_channel",
                "isolated_sandbox",
                "model_inference_adapter",
                "provider_egress_proxy",
                "scoped_mcp_binding",
                "web_search_connector",
            },
        )

    def test_runtime_contract_cannot_hide_required_capability(self) -> None:
        manifest = {
            "runtime_boundary": {"host_services_only": []},
            "runtime_contract": {
                "version": "apm.runtime.services.v1",
                "model": {"interface": "chat.v1", "selection": "host"},
            },
        }

        problems = validate_runtime_contract(manifest)

        self.assertTrue(any("model_inference_adapter" in problem for problem in problems))

    def test_plugin_path_cannot_escape_package_root(self) -> None:
        pack = ROOT / "examples" / "interoperability.agent"
        manifest = json.loads((pack / "pack.json").read_text(encoding="utf-8"))
        manifest["runtime_contract"]["interoperability"]["agent_plugins"]["plugin_manifest"] = "../plugin.json"

        problems = validate_runtime_contract(manifest, pack_root=pack)

        self.assertTrue(any("plugin_manifest" in problem for problem in problems))

    def test_check_uses_canonical_manifest_runtime_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = root / "canonical.agent"
            pack.mkdir()
            (pack / "apm.yml").write_text("name: canonical\nversion: 0.1.0\n", encoding="utf-8")
            (pack / "pack.json").write_text(
                json.dumps(
                    {
                        "agent_id": "canonical",
                        "name": "canonical",
                        "version": "0.1.0",
                        "runtime_boundary": {
                            "host_services_only": ["model_inference_adapter"]
                        },
                        "runtime_contract": {
                            "version": "apm.runtime.services.v1",
                            "model": {"interface": "chat.v1", "selection": "host"},
                        },
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(apm_kit._required_caps(pack), {"model_inference_adapter"})


if __name__ == "__main__":
    unittest.main()
