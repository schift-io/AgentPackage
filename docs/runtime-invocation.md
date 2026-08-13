# Runtime invocation contract

This document defines the portable task-turn wire contract used after a host
has resolved a package `runtime_ref` through `apm.runtime.binding.v1`.

The sealed package remains provider-neutral. The binding selects the deployed
Runtime; the invocation adapter supplies the provider-specific transport and
caller credentials. A Runtime must reject missing package capabilities before
starting a task turn.

```text
sealed .apm + runtime_ref
  -> binding resolution
  -> provider invocation adapter
  -> one isolated Runtime task turn
  -> public result + caller-owned checkpoint
```

## Start a task turn

The HTTP-shaped adapter contract is `apm.runtime.start.v1`:

```text
POST /apm/runs
```

Its JSON body has exactly these fields:

```json
{
  "runtime_ref": "apm://runtime/human-input-runner@0.1.0",
  "run_id": "run_01",
  "scope": {
    "tenant_id": "tenant_821",
    "session_id": "tenant_821:agent_1:requester_456:session_123",
    "requester_id": "requester_456"
  },
  "package": {
    "encoding": "base64",
    "sha256": "raw-apm-byte-sha256",
    "size_bytes": 1234,
    "data": "base64-encoded-sealed-apm"
  },
  "execution": {
    "adapter": "runtime-owned-adapter-id",
    "prompt": "host-selected task prompt",
    "model": "host-selected-model-or-null"
  }
}
```

`package.sha256` is the transport digest of the sealed `.apm` bytes. It is not
the APM content hash; the content hash is calculated from the validated
manifest and package files. The Runtime validates both the transport envelope
and the sealed package before execution.

The Runtime response always has exactly two fields:

```json
{
  "result": {"protocol": "apm.human_input.runner.result.v1", "...": "public projection"},
  "checkpoint": {"protocol": "apm.run.checkpoint.v1", "...": "private successor state"}
}
```

`result` may contain only the task status, run identifier, task-turn state,
safe artifact names, selected adapter, safe error code, and an input request
when paused. It must not contain answers, package bytes, stdout, stderr,
events, output paths, or checkpoint archive data. `checkpoint` is private
caller-owned state and is never a public API receipt.

## Resume a paused task turn

```text
POST /apm/runs/{run_id}/resume
```

```json
{
  "request_id": "input_approval",
  "answers": {"approve": true},
  "checkpoint": {"protocol": "apm.run.checkpoint.v1", "...": "prior private state"}
}
```

The same two-field response shape applies. The Runtime validates that the
checkpoint scope, run ID, paused input ID, task-turn number, adapter, digest,
and archive boundary all match before it exposes answers to the package.
Answers are handed to one task turn only and are removed before the successor
checkpoint is returned.

## Binding and credential boundary

Bindings identify a target and non-secret authentication descriptor. They do
not carry access tokens or application secrets. A Cloud Run binding using the
human-input runner looks like this:

```yaml
version: apm.runtime.binding.v1
bindings:
  apm://runtime/human-input-runner@0.1.0:
    provider: gcp-cloud-run
    resource: projects/example/locations/asia-northeast3/services/runner
    invoke_url: https://runner-example.run.app
    auth:
      type: gcp-oidc
      audience: https://runner-example.run.app
      invoker_service_account: runner-invoker@example.iam.gserviceaccount.com
      credential_ref: env:APM_HUMAN_INPUT_RUNTIME_SECRET
      parameters:
        application_secret_header: x-apm-human-input-runtime-secret
    capabilities:
      - human_input_channel
```

The invocation adapter obtains the OIDC identity token from its caller context
and resolves `credential_ref` locally. It must never write either value into
the binding, `.apm`, public result, or checkpoint. `auth.parameters` is owned
by the selected Runtime adapter; the `application_secret_header` above is not
a global package field.

## Installed provider transports

The sealed package and HTTP-shaped task-turn body stay unchanged across these
transports. Only binding-owned routing and caller authority change.

| Provider | CLI action | Binding requirements | Runtime claim |
| --- | --- | --- | --- |
| `gcp-cloud-run` | HTTPS POST to `invoke_url` | `gcp-oidc`, audience equal to origin, caller OIDC token | Package-executing container Runtime when its capabilities advertise it |
| `aws-lambda` | `aws lambda invoke` with an API Gateway v2-shaped event | Lambda ARN resource, `aws-lambda-invoke`, application secret header | Package-executing Lambda container Runtime when its capabilities advertise it |
| `cloudflare-worker` | HTTPS POST to the Worker origin | `http-header-secret`, root-mounted endpoint | Edge transport conformance canary only, unless another Worker Runtime advertises package execution |
| `vercel-edge` | HTTPS POST to the deployment origin plus `invoke_path_prefix` | `http-header-secret`, safe prefix such as `/api/apm` | Edge transport conformance canary only |
| `supabase-edge` | HTTPS POST to the function origin plus `invoke_path_prefix` | `http-header-secret`, safe prefix such as `/apm-task-turn` | Edge transport conformance canary only |

The Lambda transport uses the AWS caller identity to invoke the function. It
does not put AWS keys in a package, binding, or client state. An edge
conformance adapter validates package bytes and checkpoint integrity but does
not execute the package or call a model. It must advertise that limitation,
rather than implying that a task-turn transport proof is a sandbox proof.

## Stateless Runtime and durable control plane

An invocation Runtime can be request-ephemeral and scale to zero. In that
shape, callers must treat unknown start or resume outcomes as non-retryable
until a durable control plane reconciles them. A governance/control-plane
implementation owns leases, idempotency receipts, approval state, quotas,
audit, and durable checkpoint storage. It may call a stateless Runtime for one
task turn, but it must not expose raw answers or checkpoints through its public
status and receipt endpoints.

Provider adapters for Lambda, Workers, Vercel, Supabase Edge, or local
execution may implement the same task-turn semantics with their native caller
authentication. They must preserve this package, result, checkpoint, and
capability boundary instead of putting provider URLs or credentials in the
sealed package.
