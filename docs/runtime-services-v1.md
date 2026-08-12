# APM Runtime Services v1 (normative)

`runtime_contract` is an additive canonical-manifest field for a package that
needs more than a static instruction and artifact workspace. Its version is
`apm.runtime.services.v1`.

It describes required host services. It is not a provider configuration,
credential container, network policy escape hatch, or a replacement for a
runtime's authorization model. A package that declares the block MUST also
declare every derived capability in
`runtime_boundary.host_services_only`; `apm-kit lint` rejects a mismatch.

Existing packages may omit `runtime_contract` and remain valid.

## Contract shape

```yaml
runtime_boundary:
  host_services_only:
    - model_inference_adapter
    - human_input_channel
    - cclg_memory_read
    - cclg_memory_candidate_write
    - web_search_connector
    - connected_source_search_connector
    - connected_source_fetch_connector
    - scoped_mcp_binding
    - isolated_sandbox
    - provider_egress_proxy
    - agent_plugins_runtime
    - a2a_task_server

runtime_contract:
  version: apm.runtime.services.v1
  model:
    interface: chat.v1
    selection: host
    input_modes: [text/plain]
    output_modes: [text/plain]
  interaction:
    channel: host-mediated
    resume: task-turn
  memory:
    format: cclg/0.1
    read: scoped-active-pack
    write: candidate-only
  data:
    web_search: host-mediated
    connected_sources:
      search: host-mediated
      fetch: host-mediated
  mcp:
    bindings:
      - id: schift-memory
        scopes: [memory:read]
        tools: [memory.search, memory.cite]
  sandbox:
    mode: isolated
    package_network: none
    model_egress: provider-proxy
  interoperability:
    agent_plugins:
      version: 1.0.0
      plugin_manifest: ./plugin.json
    a2a:
      version: "1.0"
      role: server
      agent_card_template: ./a2a/agent-card.template.json
```

Every omitted sub-block asks for no service. A host MUST reject the package
before execution when a declared capability is missing; it MUST NOT turn a
required service into a best-effort local fallback.

## Model dependency injection

`model` has exactly one portable interface in v1: `chat.v1`, selected by the
host. A package MUST NOT declare a vendor, model identifier, base URL, API key,
OAuth token, or provider-specific environment variable in this block.

`model` requires `model_inference_adapter`. The runtime chooses the model and
records the actual runner/provider policy in execution provenance. This lets a
Schift service, a Cloudflare adapter, or a local Codex adapter provide the same
package interface without making any provider part of the `.apm` format.

## Human input and task resumption

`interaction.channel: host-mediated` requires `human_input_channel`.
The host owns the waiting state, authorization of the responder, validation of
the submitted payload, and re-entry of the task. The package can describe the
question in its instructions, but it does not open a socket, create a browser
form, or define a user identity.

`apm.run.result.v1` uses `input_required` while waiting. A host SHOULD emit a
`run.input_required` event containing a stable request ID, a human-readable
prompt, and a JSON-schema-compatible input description. A later
`run.input_submitted` event MUST name that request ID and MUST be attributed to
the host-authenticated responder. The host resumes as a new task turn; it MUST
not splice untrusted input into an earlier hidden prompt or fabricate a
response.

## CCLG memory transfer

`memory.format` is `cclg/0.1`. `read: scoped-active-pack` requires
`cclg_memory_read` and permits the host to supply only the effective,
scope-filtered active-memory view for this run. The package receives no broad
tenant dump and no authority to choose a different scope.

`write: candidate-only` requires `cclg_memory_candidate_write`. A candidate is
not effective memory and MUST NOT automatically promote into session, agent,
or company memory. The host records provenance and routes candidate review and
promotion through its own governance policy. A package cannot request direct
memory mutation in this v1 contract.

The `.cclg` container remains the transferable memory artifact. It is supplied
or accepted only through a host-scoped capability; packages do not embed an
organization memory export, access token, or remote memory URL.

## Search and connected data

`data.web_search: host-mediated` requires `web_search_connector`.
`data.connected_sources.search` and `.fetch` independently require
`connected_source_search_connector` and `connected_source_fetch_connector`.

These are host-mediated operations. A package never receives a general network
allowlist, a connector credential, or a source URL that bypasses the host's
authorization and provenance path. Search/fetch results should carry source
identity and citation metadata supplied by the host. A host may deny a request
because a caller lacks a connector grant even when it supports the capability
in general.

## Governed MCP bindings

`mcp.bindings` requires `scoped_mcp_binding`. Each entry has only an identifier,
the required scopes, and allowed tool names. It MUST NOT contain an endpoint,
headers, bearer token, client secret, or arbitrary tool configuration.

The host resolves a binding after package, caller, and run authorization are
known. It may mint a lease-scoped endpoint or use a local transport, but it
MUST expose only the declared tools and no broader scope. A failure to create
or authorize a binding rejects the run; a runtime cannot silently substitute a
different MCP server.

## Sandbox and egress

`sandbox.mode` is `isolated` in v1 and requires `isolated_sandbox`.
`package_network` MUST be `none`: package-controlled commands have no direct
Internet, host-network, Docker-socket, cloud credential, or arbitrary proxy
access.

`model_egress` is either `none` or `provider-proxy`. `provider-proxy` requires
`provider_egress_proxy` and is a separate host-owned path: the worker can reach
only a policy-enforcing proxy on a private network, and that proxy may connect
only to approved model-provider authorities. It is not a general network grant.

A runtime MUST record the enforced mode, whether direct egress was possible,
and the credential posture. Mounting a user's raw Codex/Claude profile is a
compatibility mode, not credential isolation; production adapters SHOULD use a
short-lived brokered provider credential instead. No runtime may describe a
plain Docker bridge or host network as this contract's `provider-proxy` mode.

## Derived capabilities

| Contract declaration | Required capability |
| --- | --- |
| `model` | `model_inference_adapter` |
| `interaction` | `human_input_channel` |
| `memory.read != none` | `cclg_memory_read` |
| `memory.write != none` | `cclg_memory_candidate_write` |
| `data.web_search != none` | `web_search_connector` |
| `data.connected_sources.search != none` | `connected_source_search_connector` |
| `data.connected_sources.fetch != none` | `connected_source_fetch_connector` |
| non-empty `mcp.bindings` | `scoped_mcp_binding` |
| `sandbox.mode: isolated` | `isolated_sandbox` |
| `sandbox.model_egress: provider-proxy` | `provider_egress_proxy` |
| Agent Plugins declaration | `agent_plugins_runtime` |
| A2A `role: client` | `a2a_task_client` |
| A2A `role: server` | `a2a_task_server` |

The canonical vocabulary and host profiles live in
[`kit/capabilities.json`](../kit/capabilities.json). A profile must list its
provided capabilities explicitly. It MUST NOT claim every future vocabulary
entry merely because it supports older packages.
