# Runtime Adapter Guide

`AgentPackage`는 실행 서비스가 아니다. `.agent` source package를 `.apm`으로
빌드한 뒤, Runtime adapter가 capability를 실제 서비스에 연결한다.

## Model

```text
.agent source
  → apm-kit validate/build
.apm artifact
  → Runtime adapter
  → capability providers
  → operation results and artifacts
```

This is intentionally similar to a Node module lifecycle:

- `.agent/` is the editable package source in Git.
- `.apm` is the packed, versioned distribution artifact.
- The Runtime is the host process that installs and executes the artifact.

## Adapter responsibilities

An adapter must:

1. read and validate the bundle manifest;
2. expose the capabilities it actually provides;
3. reject missing required capabilities before execution;
4. map operation inputs and outputs without changing their declared meaning;
5. record artifact and execution provenance;
6. keep secrets, tenant credentials, billing, and provider configuration outside
   the package source;
7. make unsupported optional capabilities visible instead of silently pretending
   they worked.

An adapter must not:

- execute an unvalidated `.agent` directory as if it were a built artifact;
- grant arbitrary network, filesystem, or code execution because a package asks
  for it;
- treat `visibility: public` as permission to access private data;
- replace a required capability with a silent fallback that changes the result;
- put Runtime-specific secrets into `apm.yml`, `agent.md`, or `pack.json`.

## Capability mapping

The package declares requirements, not vendors:

```yaml
capabilities:
  required:
    - llm.generate
    - artifact.write
  optional:
    - source.search
    - image.generate
    - image.reference
```

Example mappings:

| Capability | Schift | Cloudflare | Local/custom |
|---|---|---|---|
| `llm.generate` | Agent Hub inference adapter | Workers AI binding | Ollama, OpenAI-compatible API |
| `artifact.write` | Schift artifact store | R2 binding | filesystem, S3-compatible store |
| `state.durable` | Agent Hub persistence | Durable Objects / D1 | SQLite, Postgres |
| `queue.enqueue` | Schift worker queue | Queues binding | Redis, SQS, local queue |
| `image.generate` | Schift image service | Worker service or external provider | ComfyUI or custom API |
| `source.search` | Schift web search | Worker/API integration | user-provided connector |

Cloudflare bindings are deployment details of the adapter, not fields in the
portable package. See the official [Workers AI bindings](https://developers.cloudflare.com/workers-ai/configuration/bindings/),
[R2 Workers API](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/),
and [Durable Objects](https://developers.cloudflare.com/durable-objects/).

## Reference adapter interface

An implementation may use any language, but it should provide the equivalent of:

```text
adapter.capabilities() -> CapabilitySet
adapter.install(bundle) -> InstalledPackage
adapter.run(installed, operation_id, input) -> OperationResult
adapter.artifacts(result) -> ArtifactRefs
```

The reference Python kit does not prescribe an HTTP protocol or a database. Those
belong to the Runtime adapter. The portable boundary is the manifest, capability
set, operation contract, and artifact/provenance result.

## Compatibility

Adapters should report both:

- the AgentPackage protocol version they understand; and
- the capabilities they provide.

The protocol version answers “can I parse this package?” The capability set answers
“can I execute this package here?” They are deliberately separate.
