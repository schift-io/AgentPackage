from __future__ import annotations

import argparse
import copy
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "kit"))

import apm_kit
from runtime_contract import runtime_required_capabilities, validate_runtime_contract


class RuntimeContractTests(unittest.TestCase):
    def _interoperability_fixture(self) -> tuple[Path, dict]:
        pack = ROOT / "examples" / "interoperability.agent"
        manifest = json.loads((pack / "pack.json").read_text(encoding="utf-8"))
        return pack, manifest

    def test_interoperability_fixture_is_valid_and_declares_all_authority(self) -> None:
        pack, manifest = self._interoperability_fixture()

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
        pack, manifest = self._interoperability_fixture()
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

    def test_each_runtime_service_rejects_an_unauthorized_or_invalid_value(self) -> None:
        pack, baseline = self._interoperability_fixture()
        cases = (
            (
                "model interface",
                lambda manifest: manifest["runtime_contract"]["model"].__setitem__(
                    "interface", "chat.v2"
                ),
                "runtime_contract.model.interface",
            ),
            (
                "model selection",
                lambda manifest: manifest["runtime_contract"]["model"].__setitem__(
                    "selection", "package"
                ),
                "runtime_contract.model.selection",
            ),
            (
                "interaction channel",
                lambda manifest: manifest["runtime_contract"]["interaction"].__setitem__(
                    "channel", "direct"
                ),
                "runtime_contract.interaction.channel",
            ),
            (
                "interaction resume",
                lambda manifest: manifest["runtime_contract"]["interaction"].__setitem__(
                    "resume", "stream"
                ),
                "runtime_contract.interaction.resume",
            ),
            (
                "memory format",
                lambda manifest: manifest["runtime_contract"]["memory"].__setitem__(
                    "format", "cclg/1.0"
                ),
                "runtime_contract.memory.format",
            ),
            (
                "memory read scope",
                lambda manifest: manifest["runtime_contract"]["memory"].__setitem__(
                    "read", "global"
                ),
                "runtime_contract.memory.read",
            ),
            (
                "memory write policy",
                lambda manifest: manifest["runtime_contract"]["memory"].__setitem__(
                    "write", "authoritative"
                ),
                "runtime_contract.memory.write",
            ),
            (
                "web search mediation",
                lambda manifest: manifest["runtime_contract"]["data"].__setitem__(
                    "web_search", "direct"
                ),
                "runtime_contract.data.web_search",
            ),
            (
                "connected source search mediation",
                lambda manifest: manifest["runtime_contract"]["data"][
                    "connected_sources"
                ].__setitem__("search", "direct"),
                "runtime_contract.data.connected_sources.search",
            ),
            (
                "connected source fetch mediation",
                lambda manifest: manifest["runtime_contract"]["data"][
                    "connected_sources"
                ].__setitem__("fetch", "direct"),
                "runtime_contract.data.connected_sources.fetch",
            ),
            (
                "MCP direct endpoint",
                lambda manifest: manifest["runtime_contract"]["mcp"]["bindings"][
                    0
                ].__setitem__("url", "https://mcp.example.invalid/mcp"),
                "runtime_contract.mcp.bindings[0] has unknown fields",
            ),
            (
                "MCP empty scopes",
                lambda manifest: manifest["runtime_contract"]["mcp"]["bindings"][
                    0
                ].__setitem__("scopes", []),
                "runtime_contract.mcp.bindings[0].scopes",
            ),
            (
                "MCP empty tools",
                lambda manifest: manifest["runtime_contract"]["mcp"]["bindings"][
                    0
                ].__setitem__("tools", []),
                "runtime_contract.mcp.bindings[0].tools",
            ),
            (
                "sandbox mode",
                lambda manifest: manifest["runtime_contract"]["sandbox"].__setitem__(
                    "mode", "host"
                ),
                "runtime_contract.sandbox.mode",
            ),
            (
                "sandbox package network",
                lambda manifest: manifest["runtime_contract"]["sandbox"].__setitem__(
                    "package_network", "internet"
                ),
                "runtime_contract.sandbox.package_network",
            ),
            (
                "sandbox model egress",
                lambda manifest: manifest["runtime_contract"]["sandbox"].__setitem__(
                    "model_egress", "direct"
                ),
                "runtime_contract.sandbox.model_egress",
            ),
            (
                "Agent Plugins version",
                lambda manifest: manifest["runtime_contract"]["interoperability"][
                    "agent_plugins"
                ].__setitem__("version", "2.0.0"),
                "runtime_contract.interoperability.agent_plugins.version",
            ),
            (
                "A2A version",
                lambda manifest: manifest["runtime_contract"]["interoperability"]["a2a"].__setitem__(
                    "version", "2.0"
                ),
                "runtime_contract.interoperability.a2a.version",
            ),
            (
                "A2A role",
                lambda manifest: manifest["runtime_contract"]["interoperability"]["a2a"].__setitem__(
                    "role", "peer"
                ),
                "runtime_contract.interoperability.a2a.role",
            ),
        )

        for label, mutate, expected in cases:
            with self.subTest(label=label):
                manifest = copy.deepcopy(baseline)
                mutate(manifest)
                problems = validate_runtime_contract(manifest, pack_root=pack)
                self.assertTrue(
                    any(expected in problem for problem in problems),
                    f"{label}: expected {expected!r}, got {problems!r}",
                )

    def test_interoperability_component_files_are_validated_at_the_package_root(self) -> None:
        pack, _ = self._interoperability_fixture()
        cases = (
            (
                "plugin schema",
                Path("plugin.json"),
                lambda component: component.__setitem__("$schema", "https://example.invalid/plugin"),
                "Agent Plugins plugin.json must declare the 1.0.0 plugin schema",
            ),
            (
                "plugin name",
                Path("plugin.json"),
                lambda component: component.__setitem__("name", ""),
                "Agent Plugins plugin.json must declare a non-empty name",
            ),
            (
                "MCP component schema",
                Path("mcp.json"),
                lambda component: component.__setitem__("$schema", "https://example.invalid/mcp"),
                "Agent Plugins mcp.json must declare the 1.0.0 MCP schema",
            ),
            (
                "MCP component server map",
                Path("mcp.json"),
                lambda component: component.__setitem__("mcpServers", []),
                "Agent Plugins mcp.json must declare an mcpServers object",
            ),
            (
                "A2A card required skill list",
                Path("a2a/agent-card.template.json"),
                lambda component: component.pop("skills"),
                "A2A Agent Card template must declare 'skills'",
            ),
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for label, relative_path, mutate, expected in cases:
                with self.subTest(label=label):
                    candidate = root / label.replace(" ", "-")
                    shutil.copytree(pack, candidate)
                    path = candidate / relative_path
                    component = json.loads(path.read_text(encoding="utf-8"))
                    mutate(component)
                    path.write_text(json.dumps(component), encoding="utf-8")
                    manifest = json.loads((candidate / "pack.json").read_text(encoding="utf-8"))
                    problems = validate_runtime_contract(manifest, pack_root=candidate)
                    self.assertTrue(
                        any(expected in problem for problem in problems),
                        f"{label}: expected {expected!r}, got {problems!r}",
                    )

    def test_interoperability_component_files_are_validated_from_bundle_files(self) -> None:
        pack, manifest = self._interoperability_fixture()
        files = {
            str(path.relative_to(pack)): path.read_bytes()
            for path in pack.rglob("*")
            if path.is_file()
        }

        self.assertEqual(
            validate_runtime_contract(manifest, package_files=files), []
        )

        card = json.loads(files["a2a/agent-card.template.json"].decode("utf-8"))
        card.pop("defaultOutputModes")
        files["a2a/agent-card.template.json"] = json.dumps(card).encode("utf-8")

        problems = validate_runtime_contract(manifest, package_files=files)

        self.assertIn(
            "A2A Agent Card template must declare 'defaultOutputModes'", problems
        )

    def test_host_capability_check_is_positive_for_docker_subset_and_fail_closed_for_full_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = root / "docker-subset.agent"
            pack.mkdir()
            (pack / "pack.json").write_text(
                json.dumps(
                    {
                        "agent_id": "docker-subset",
                        "runtime_boundary": {
                            "host_services_only": [
                                "model_inference_adapter",
                                "isolated_sandbox",
                                "provider_egress_proxy",
                            ]
                        },
                        "runtime_contract": {
                            "version": "apm.runtime.services.v1",
                            "model": {"interface": "chat.v1", "selection": "host"},
                            "sandbox": {
                                "mode": "isolated",
                                "package_network": "none",
                                "model_egress": "provider-proxy",
                            },
                        },
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            with redirect_stdout(output):
                result = apm_kit.cmd_check(
                    argparse.Namespace(
                        host="docker-codex-isolated",
                        pack="docker-subset.agent",
                        packs_dir=str(root),
                    )
                )
            self.assertEqual(result, 0, output.getvalue())

        output = io.StringIO()
        with redirect_stdout(output):
            result = apm_kit.cmd_check(
                argparse.Namespace(
                    host="docker-codex-isolated",
                    pack="interoperability.agent",
                    packs_dir=str(ROOT / "examples"),
                )
            )
        self.assertEqual(result, 1, output.getvalue())
        self.assertIn("scoped_mcp_binding", output.getvalue())
        self.assertIn("a2a_task_server", output.getvalue())


if __name__ == "__main__":
    unittest.main()
