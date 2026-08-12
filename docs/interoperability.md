# APM interoperability profiles (normative)

AgentPackage does not replace Agent Plugins, A2A, or MCP. The three formats
have different ownership and are used together:

| Standard | Owns | APM adds |
| --- | --- | --- |
| [Agent Plugins 1.0](https://github.com/agentplugins/agent-plugins-spec) | reusable plugin package, `plugin.json`, Skills discovery, and `mcp.json` discovery | sealed bundle integrity, capability negotiation, runtime authorization, and sandbox policy |
| [A2A 1.0](https://a2a-protocol.org/latest/specification/) | Agent Card discovery, messages, tasks, artifacts, streaming, and multi-turn remote-agent interaction | which packaged instruction is authorized to serve or call that agent, and the local execution boundary |
| [MCP](https://modelcontextprotocol.io/specification) | tool/resource wire behavior and lifecycle | a lease-scoped binding decision; package-declared minimum scopes and tools |

The APM compatibility profile is optional for old packages and supported by
default for new runtime-services v1 packages. “Supported” means a host can
parse and fail closed on the profile; it does not mean every runtime claims to
implement every remote transport or plugin component.

## Agent Plugins 1.0 profile

```yaml
runtime_contract:
  interoperability:
    agent_plugins:
      version: 1.0.0
      plugin_manifest: ./plugin.json
```

The referenced file MUST remain inside the package, be valid JSON, use the
Agent Plugins 1.0 schema identifier, and declare a non-empty plugin name.
If a root `mcp.json` exists it MUST use the corresponding Agent Plugins MCP
schema and declare an `mcpServers` object.

The profile intentionally uses the upstream fixed locations:

```text
<package>.agent/
├── apm.yml / pack.json
├── agent.md
├── plugin.json
├── skills/<skill>/SKILL.md
└── mcp.json
```

`plugin.json` remains the Agent Plugins manifest. APM data MUST NOT be added as
new top-level plugin fields; Agent Plugins has a closed core manifest. APM's
own runtime data stays in `pack.json` / `apm.yml` under `runtime_contract`.

Package-owned stdio MCP commands are not automatically trusted by an APM
runtime. A host that implements this profile decides whether it can launch a
plugin component under its sandbox and what `PLUGIN_DATA` boundary it grants.
Hosted or governed MCP uses `runtime_contract.mcp.bindings` instead; that block
contains no endpoint or secret.

## A2A 1.0 profile

```yaml
runtime_contract:
  interoperability:
    a2a:
      version: "1.0"
      role: server
      agent_card_template: ./a2a/agent-card.template.json
```

`role` is exactly `client` or `server`:

- An A2A client calls a remote agent through the host's authorized transport.
- An A2A server causes the host to materialize and publish a final Agent Card
  and task endpoint for the verified package.

For a server, `agent_card_template` must be package-relative and contain the
public Agent Card identity fields (`name`, `description`, `version`,
`capabilities`, `skills`, `defaultInputModes`, and `defaultOutputModes`). The
host supplies its verified endpoint, authentication schemes, signatures, and
deployment-specific interface details. A package MUST NOT carry a bearer token,
private callback, customer-specific URL, or raw runtime credential in the
template.

The A2A task lifecycle remains authoritative. APM result states map as follows:

| APM run state | A2A task meaning |
| --- | --- |
| `accepted`, `running` | working/non-terminal task |
| `input_required` | A2A input-required interruption; a later task message resumes a new turn |
| `succeeded` | completed |
| `failed` | failed |
| `cancelled` | canceled |
| `rejected` | rejected |

An APM host MUST preserve A2A task IDs and caller authorization boundaries in
its own task store. It MUST NOT use an A2A Agent Card as proof that the caller
may execute a package or access the package's MCP/data grants.

## Conformance boundary

A package can contain both profiles. It then requires
`agent_plugins_runtime` and either `a2a_task_client` or `a2a_task_server`.
Runtimes must advertise only capabilities they actually implement. For example,
the Docker Codex development adapter may provide model inference and a restricted
provider proxy while rejecting Agent Plugins component execution, A2A, CCLG,
search, and governed MCP until those adapters exist.
