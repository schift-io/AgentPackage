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
    - scoped_connector_proxy
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
The host owns the waiting state, responder authorization, response validation,
and task re-entry. The package can describe a question in its instructions, but
it does not open a socket, create a browser form, select a responder, or define
a user identity.

### Sealed package input and workspace boundary

Before the first task turn, the host MUST verify the sealed package content hash
and freeze the execution input: the complete package files, canonical manifest,
`package_ref`, verified `content_hash`, requested operation, initial task input,
and accepted runtime contract. Every task turn MUST receive that complete,
unchanged sealed package input. A host MUST NOT resume from only a generated
prompt, a partial package directory, or an unverified replacement package.

The host MUST expose the sealed package input read-only and provide a separate
writable workspace for task output and host-mediated request/response material.
The package MUST NOT modify its sealed input. The workspace belongs to the run,
not the package: a host chooses its location, retention, and isolation policy,
and MUST prevent a resumed turn from reading another run's workspace.

### Request and response records

During a task turn, a package may ask the host for one or more human answers by
creating a request record. The portable record is:

```json
{
  "protocol": "apm.input.request.v1",
  "id": "input_approval",
  "questions": [
    {
      "id": "approve",
      "label": "Continue with this action?",
      "type": "approval",
      "required": true
    }
  ]
}
```

`id` and every question `id` MUST be stable, non-empty identifiers within the
run. `type` is `text`, `select`, or `approval`. A `select` question MUST declare
non-empty, distinct string `options`; `approval` accepts a boolean response;
and `required` is a boolean. Hosts MAY render an equivalent native UI, but MUST
validate the submitted answer against this record before resuming.

The response is host-mediated, not package-authenticated. Its logical shape is
`{"protocol":"apm.input.response.v1","answers":{...}}`; the host binds it to
the run and request ID from the command path, API route, or persisted task
state. A response MUST contain only declared question IDs, satisfy required
questions, and match the requested types/options. A host MAY deliver the
validated response to the next task turn through a workspace response record or
another isolated local mechanism. It MUST NOT expose responder credentials,
provider credentials, MCP secrets, or authorization headers to the package.

### Run and task-turn state machine

`apm.run.result.v1` uses `input_required` while waiting. Its associated
`task_turn.state` is `paused`: the current turn has stopped, the request record
is immutable, and no new package execution occurs until the host accepts a
response or cancellation.

After accepting one valid, authorized response, the host records the task as
`resuming` and starts a new task turn with the same sealed package input,
separate workspace, prior run artifacts, and the validated response. It MUST
NOT splice untrusted answer bytes into an earlier hidden prompt, alter the
sealed package, or fabricate a response. `resuming` is a host task state, not a
new `apm.run.result.v1` status. The new turn either emits another
`input_required` result with `task_turn.state: paused` or reaches a terminal
`succeeded`, `failed`, or `cancelled` result.

An authorized responder or host policy MAY cancel a paused request. A declined
required approval MUST produce terminal `cancelled`; its result error has a
stable cancellation code such as `human_input_declined`. A cancelled request
MUST NOT be resumed. Repeating an already accepted identical response MAY be
idempotent, but a host MUST reject a different response after a terminal result.

### Events and host interfaces

The host SHOULD emit the following metadata-only events:

```json
{"type":"run.input_required","run_id":"run_01...","input_request_id":"input_approval","task_turn":1,"question_ids":["approve"]}
{"type":"run.input_submitted","run_id":"run_01...","input_request_id":"input_approval","task_turn":2,"answer_keys":["approve"]}
```

Events MUST NOT contain answer values, responder credentials or identity
credentials, provider credentials, MCP secrets, authorization headers, or a
secret-bearing URL. Hosts may record an answer digest for idempotency, but MUST
NOT treat that digest as an answer or credential.

A conforming CLI MAY expose the flow as:

```text
schift apm runwith <sealed-package> --codex --docker --output <run-directory>
schift apm resume <run-id> --output <run-directory> --input <request-id> --answer <answers.json>
schift apm cancel <run-id> --output <run-directory> --input <request-id>
```

These are an adapter-specific reference command shape, not required command
names. An equivalent host API MAY expose:

```text
GET  /v1/runs/{run_id}
POST /v1/runs/{run_id}/input-requests/{request_id}/responses
POST /v1/runs/{run_id}/input-requests/{request_id}/cancel
```

The response endpoint accepts a validated `apm.input.response.v1` body; the
host authenticates the caller outside that body. These are interface shapes,
not required paths, command names, transport, provider, or runtime choices.

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

Any non-`none` data operation also requires `scoped_connector_proxy`. This is
the host-owned operation boundary, not an HTTPS CONNECT tunnel: it exposes only
the declared operation through a local typed API and never accepts an arbitrary
upstream URL, hostname, request headers, credential, or provider base URL from
the package. A Docker development adapter may implement public web search with
this bridge, but connected-source search and fetch remain unavailable until the
host supplies tenant-scoped connector authorization and opaque source IDs.

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
| any non-`none` `data` operation | `scoped_connector_proxy` |
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
