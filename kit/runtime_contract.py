from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


RUNTIME_CONTRACT_VERSION = "apm.runtime.services.v1"
AGENT_PLUGINS_VERSION = "1.0.0"
AGENT_PLUGINS_SCHEMA = (
    "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
)
AGENT_PLUGINS_MCP_SCHEMA = (
    "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
)
A2A_VERSION = "1.0"
_RUNTIME_REF_PATTERN = re.compile(
    r"^apm://runtime/[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?@"
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def declared_host_capabilities(manifest: dict[str, Any]) -> set[str]:
    boundary = manifest.get("runtime_boundary") or {}
    if not isinstance(boundary, dict):
        return set()
    declared = boundary.get("host_services_only") or []
    if isinstance(declared, str):
        declared = [declared]
    if not isinstance(declared, (list, tuple, set)):
        return set()
    return {str(capability).strip() for capability in declared if str(capability).strip()}


def runtime_required_capabilities(manifest: dict[str, Any]) -> set[str]:
    contract = manifest.get("runtime_contract")
    if not isinstance(contract, dict):
        return set()

    required: set[str] = set()
    if "model" in contract:
        required.add("model_inference_adapter")
    if "interaction" in contract:
        required.add("human_input_channel")

    memory = contract.get("memory")
    if isinstance(memory, dict):
        if memory.get("read") not in (None, "none"):
            required.add("cclg_memory_read")
        if memory.get("write") not in (None, "none"):
            required.add("cclg_memory_candidate_write")

    data = contract.get("data")
    if isinstance(data, dict):
        if data.get("web_search") not in (None, "none"):
            required.add("web_search_connector")
        connected = data.get("connected_sources")
        if isinstance(connected, dict):
            if connected.get("search") not in (None, "none"):
                required.add("connected_source_search_connector")
            if connected.get("fetch") not in (None, "none"):
                required.add("connected_source_fetch_connector")

    mcp = contract.get("mcp")
    if isinstance(mcp, dict) and mcp.get("bindings"):
        required.add("scoped_mcp_binding")

    sandbox = contract.get("sandbox")
    if isinstance(sandbox, dict):
        if sandbox.get("mode") not in (None, "local"):
            required.add("isolated_sandbox")
        if sandbox.get("model_egress") == "provider-proxy":
            required.add("provider_egress_proxy")

    interoperability = contract.get("interoperability")
    if isinstance(interoperability, dict):
        if interoperability.get("agent_plugins") is not None:
            required.add("agent_plugins_runtime")
        a2a = interoperability.get("a2a")
        if isinstance(a2a, dict):
            role = a2a.get("role")
            if role == "client":
                required.add("a2a_task_client")
            elif role == "server":
                required.add("a2a_task_server")
    return required


def validate_runtime_contract(
    manifest: dict[str, Any],
    *,
    pack_root: Path | None = None,
    package_files: Mapping[str, bytes] | None = None,
) -> list[str]:
    problems: list[str] = []
    if "runtime_ref" in manifest:
        _validate_runtime_ref(manifest.get("runtime_ref"), problems)
    if "runtime_contract" not in manifest:
        return problems
    contract = manifest["runtime_contract"]
    if not isinstance(contract, dict):
        problems.append("runtime_contract must be an object")
        return problems

    allowed = {
        "version",
        "model",
        "interaction",
        "memory",
        "data",
        "mcp",
        "sandbox",
        "interoperability",
    }
    unknown = sorted(set(contract) - allowed)
    if unknown:
        problems.append(f"runtime_contract has unknown fields {unknown}")
    if contract.get("version") != RUNTIME_CONTRACT_VERSION:
        problems.append(
            f"runtime_contract.version must be {RUNTIME_CONTRACT_VERSION!r}"
        )

    _validate_model(contract.get("model"), problems)
    _validate_interaction(contract.get("interaction"), problems)
    _validate_memory(contract.get("memory"), problems)
    _validate_data(contract.get("data"), problems)
    _validate_mcp(contract.get("mcp"), problems)
    _validate_sandbox(contract.get("sandbox"), problems)
    _validate_interoperability(
        contract.get("interoperability"), pack_root, package_files, problems
    )

    required = runtime_required_capabilities(manifest)
    undeclared = sorted(required - declared_host_capabilities(manifest))
    if undeclared:
        problems.append(
            "runtime_contract requires runtime_boundary.host_services_only entries "
            f"{undeclared}"
        )
    return problems


def _validate_runtime_ref(value: Any, problems: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        problems.append("runtime_ref must be a non-empty logical APM runtime URI")
        return
    if not _RUNTIME_REF_PATTERN.fullmatch(value):
        problems.append(
            "runtime_ref must match 'apm://runtime/<name>@<semver>' and must not "
            "contain a provider URL"
        )


def _validate_model(value: Any, problems: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.model must be an object")
        return
    _unknown_fields(value, {"interface", "selection", "input_modes", "output_modes"}, "runtime_contract.model", problems)
    if value.get("interface") != "chat.v1":
        problems.append("runtime_contract.model.interface must be 'chat.v1'")
    if value.get("selection") != "host":
        problems.append("runtime_contract.model.selection must be 'host'")
    _string_list(value.get("input_modes"), "runtime_contract.model.input_modes", problems)
    _string_list(value.get("output_modes"), "runtime_contract.model.output_modes", problems)


def _validate_interaction(value: Any, problems: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.interaction must be an object")
        return
    _unknown_fields(value, {"channel", "resume"}, "runtime_contract.interaction", problems)
    if value.get("channel") != "host-mediated":
        problems.append("runtime_contract.interaction.channel must be 'host-mediated'")
    if value.get("resume") != "task-turn":
        problems.append("runtime_contract.interaction.resume must be 'task-turn'")


def _validate_memory(value: Any, problems: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.memory must be an object")
        return
    _unknown_fields(value, {"format", "read", "write"}, "runtime_contract.memory", problems)
    if value.get("format") != "cclg/0.1":
        problems.append("runtime_contract.memory.format must be 'cclg/0.1'")
    if value.get("read") not in {"none", "scoped-active-pack"}:
        problems.append("runtime_contract.memory.read must be 'none' or 'scoped-active-pack'")
    if value.get("write") not in {"none", "candidate-only"}:
        problems.append("runtime_contract.memory.write must be 'none' or 'candidate-only'")


def _validate_data(value: Any, problems: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.data must be an object")
        return
    _unknown_fields(value, {"web_search", "connected_sources"}, "runtime_contract.data", problems)
    if value.get("web_search") not in {"none", "host-mediated"}:
        problems.append("runtime_contract.data.web_search must be 'none' or 'host-mediated'")
    connected = value.get("connected_sources")
    if not isinstance(connected, dict):
        problems.append("runtime_contract.data.connected_sources must be an object")
        return
    _unknown_fields(connected, {"search", "fetch"}, "runtime_contract.data.connected_sources", problems)
    for key in ("search", "fetch"):
        if connected.get(key) not in {"none", "host-mediated"}:
            problems.append(
                f"runtime_contract.data.connected_sources.{key} must be 'none' or 'host-mediated'"
            )


def _validate_mcp(value: Any, problems: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.mcp must be an object")
        return
    _unknown_fields(value, {"bindings"}, "runtime_contract.mcp", problems)
    bindings = value.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        problems.append("runtime_contract.mcp.bindings must be a non-empty list")
        return
    seen: set[str] = set()
    for index, binding in enumerate(bindings):
        prefix = f"runtime_contract.mcp.bindings[{index}]"
        if not isinstance(binding, dict):
            problems.append(f"{prefix} must be an object")
            continue
        _unknown_fields(binding, {"id", "scopes", "tools"}, prefix, problems)
        identifier = binding.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            problems.append(f"{prefix}.id must be a non-empty string")
        elif identifier in seen:
            problems.append(f"{prefix}.id duplicates {identifier!r}")
        else:
            seen.add(identifier)
        _nonempty_string_list(binding.get("scopes"), f"{prefix}.scopes", problems)
        _nonempty_string_list(binding.get("tools"), f"{prefix}.tools", problems)


def _validate_sandbox(value: Any, problems: list[str]) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.sandbox must be an object")
        return
    _unknown_fields(value, {"mode", "package_network", "model_egress"}, "runtime_contract.sandbox", problems)
    if value.get("mode") != "isolated":
        problems.append("runtime_contract.sandbox.mode must be 'isolated'")
    if value.get("package_network") != "none":
        problems.append("runtime_contract.sandbox.package_network must be 'none'")
    if value.get("model_egress") not in {"none", "provider-proxy"}:
        problems.append("runtime_contract.sandbox.model_egress must be 'none' or 'provider-proxy'")


def _validate_interoperability(
    value: Any,
    pack_root: Path | None,
    package_files: Mapping[str, bytes] | None,
    problems: list[str],
) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        problems.append("runtime_contract.interoperability must be an object")
        return
    _unknown_fields(value, {"agent_plugins", "a2a"}, "runtime_contract.interoperability", problems)

    plugin = value.get("agent_plugins")
    if plugin is not None:
        if not isinstance(plugin, dict):
            problems.append("runtime_contract.interoperability.agent_plugins must be an object")
        else:
            _unknown_fields(plugin, {"version", "plugin_manifest"}, "runtime_contract.interoperability.agent_plugins", problems)
            if plugin.get("version") != AGENT_PLUGINS_VERSION:
                problems.append(
                    "runtime_contract.interoperability.agent_plugins.version must be '1.0.0'"
                )
            label = "runtime_contract.interoperability.agent_plugins.plugin_manifest"
            if pack_root is not None:
                plugin_path = _package_json_path(
                    pack_root, plugin.get("plugin_manifest"), label, problems
                )
                if plugin_path is not None:
                    _validate_agent_plugin_manifest(plugin_path, problems)
                    _validate_agent_plugin_mcp(plugin_path.parent / "mcp.json", problems)
            elif package_files is not None:
                plugin_path = _package_json_file_path(
                    package_files, plugin.get("plugin_manifest"), label, problems
                )
                if plugin_path is not None:
                    _validate_agent_plugin_manifest_document(
                        _read_package_json(
                            package_files, plugin_path, "Agent Plugins plugin.json", problems
                        ),
                        problems,
                    )
                    mcp_path = str(PurePosixPath(plugin_path).parent / "mcp.json")
                    if mcp_path in package_files:
                        _validate_agent_plugin_mcp_document(
                            _read_package_json(
                                package_files,
                                mcp_path,
                                "Agent Plugins mcp.json",
                                problems,
                            ),
                            problems,
                        )

    a2a = value.get("a2a")
    if a2a is not None:
        if not isinstance(a2a, dict):
            problems.append("runtime_contract.interoperability.a2a must be an object")
        else:
            _unknown_fields(a2a, {"version", "role", "agent_card_template"}, "runtime_contract.interoperability.a2a", problems)
            if a2a.get("version") != A2A_VERSION:
                problems.append("runtime_contract.interoperability.a2a.version must be '1.0'")
            role = a2a.get("role")
            if role not in {"client", "server"}:
                problems.append("runtime_contract.interoperability.a2a.role must be 'client' or 'server'")
            if role == "server":
                label = "runtime_contract.interoperability.a2a.agent_card_template"
                if pack_root is not None:
                    card_path = _package_json_path(
                        pack_root, a2a.get("agent_card_template"), label, problems
                    )
                    if card_path is not None:
                        _validate_a2a_card_template(card_path, problems)
                elif package_files is not None:
                    card_path = _package_json_file_path(
                        package_files, a2a.get("agent_card_template"), label, problems
                    )
                    if card_path is not None:
                        _validate_a2a_card_template_document(
                            _read_package_json(
                                package_files,
                                card_path,
                                "A2A Agent Card template",
                                problems,
                            ),
                            problems,
                        )
            elif "agent_card_template" in a2a:
                problems.append(
                    "runtime_contract.interoperability.a2a.agent_card_template is only valid for role 'server'"
                )


def _unknown_fields(value: dict[str, Any], allowed: set[str], label: str, problems: list[str]) -> None:
    unknown = sorted(set(value) - allowed)
    if unknown:
        problems.append(f"{label} has unknown fields {unknown}")


def _string_list(value: Any, label: str, problems: list[str]) -> None:
    if value is not None and (
        not isinstance(value, list) or not all(isinstance(item, str) and item for item in value)
    ):
        problems.append(f"{label} must be a list of non-empty strings when present")


def _nonempty_string_list(value: Any, label: str, problems: list[str]) -> None:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
        problems.append(f"{label} must be a non-empty list of strings")


def _package_json_path(
    pack_root: Path | None, value: Any, label: str, problems: list[str]
) -> Path | None:
    if not isinstance(value, str) or not value.startswith("./"):
        problems.append(f"{label} must be a package-relative './' JSON path")
        return None
    if pack_root is None:
        return None
    root = pack_root.resolve()
    path = (root / value[2:]).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        problems.append(f"{label} escapes the package root")
        return None
    if not path.is_file():
        problems.append(f"{label} does not exist: {value}")
        return None
    return path


def _package_json_file_path(
    package_files: Mapping[str, bytes], value: Any, label: str, problems: list[str]
) -> str | None:
    if not isinstance(value, str) or not value.startswith("./"):
        problems.append(f"{label} must be a package-relative './' JSON path")
        return None
    path = PurePosixPath(value[2:])
    if path.is_absolute() or not path.parts or any(part in {".", ".."} for part in path.parts):
        problems.append(f"{label} escapes the package root")
        return None
    relative = str(path)
    if relative not in package_files:
        problems.append(f"{label} does not exist: {value}")
        return None
    return relative


def _read_json(path: Path, label: str, problems: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        problems.append(f"{label} is not valid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        problems.append(f"{label} must contain a JSON object")
        return None
    return value


def _read_package_json(
    package_files: Mapping[str, bytes], path: str, label: str, problems: list[str]
) -> dict[str, Any] | None:
    try:
        value = json.loads(package_files[path].decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        problems.append(f"{label} is not valid JSON: {exc}")
        return None
    if not isinstance(value, dict):
        problems.append(f"{label} must contain a JSON object")
        return None
    return value


def _validate_agent_plugin_manifest(path: Path, problems: list[str]) -> None:
    _validate_agent_plugin_manifest_document(
        _read_json(path, "Agent Plugins plugin.json", problems), problems
    )


def _validate_agent_plugin_manifest_document(
    plugin: dict[str, Any] | None, problems: list[str]
) -> None:
    if plugin is None:
        return
    if plugin.get("$schema") != AGENT_PLUGINS_SCHEMA:
        problems.append("Agent Plugins plugin.json must declare the 1.0.0 plugin schema")
    if not isinstance(plugin.get("name"), str) or not plugin["name"].strip():
        problems.append("Agent Plugins plugin.json must declare a non-empty name")


def _validate_agent_plugin_mcp(path: Path, problems: list[str]) -> None:
    if not path.exists():
        return
    _validate_agent_plugin_mcp_document(
        _read_json(path, "Agent Plugins mcp.json", problems), problems
    )


def _validate_agent_plugin_mcp_document(
    mcp: dict[str, Any] | None, problems: list[str]
) -> None:
    if mcp is None:
        return
    if mcp.get("$schema") != AGENT_PLUGINS_MCP_SCHEMA:
        problems.append("Agent Plugins mcp.json must declare the 1.0.0 MCP schema")
    if not isinstance(mcp.get("mcpServers"), dict):
        problems.append("Agent Plugins mcp.json must declare an mcpServers object")


def _validate_a2a_card_template(path: Path, problems: list[str]) -> None:
    _validate_a2a_card_template_document(
        _read_json(path, "A2A Agent Card template", problems), problems
    )


def _validate_a2a_card_template_document(
    card: dict[str, Any] | None, problems: list[str]
) -> None:
    if card is None:
        return
    for key in ("name", "description", "version"):
        if not isinstance(card.get(key), str) or not card[key].strip():
            problems.append(f"A2A Agent Card template must declare a non-empty {key!r}")
    if not isinstance(card.get("capabilities"), dict):
        problems.append("A2A Agent Card template capabilities must be an object")
    for key in ("defaultInputModes", "defaultOutputModes"):
        _nonempty_string_list(
            card.get(key), f"A2A Agent Card template {key}", problems
        )

    skills = card.get("skills")
    if not isinstance(skills, list) or not skills:
        problems.append("A2A Agent Card template skills must be a non-empty list")
        return
    seen: set[str] = set()
    for index, skill in enumerate(skills):
        label = f"A2A Agent Card template skills[{index}]"
        if not isinstance(skill, dict):
            problems.append(f"{label} must be an object")
            continue
        identifier = skill.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            problems.append(f"{label}.id must be a non-empty string")
        elif identifier in seen:
            problems.append(f"{label}.id duplicates {identifier!r}")
        else:
            seen.add(identifier)
        for key in ("name", "description"):
            if not isinstance(skill.get(key), str) or not skill[key].strip():
                problems.append(f"{label}.{key} must be a non-empty string")
        _nonempty_string_list(skill.get("tags"), f"{label}.tags", problems)
        for key in ("examples", "inputModes", "outputModes"):
            _string_list(skill.get(key), f"{label}.{key}", problems)
