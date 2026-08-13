# Runtime binding contract

`runtime_ref` connects a sealed `.apm` package to a Runtime deployment without
putting a vendor endpoint, cloud identity, or credential inside the package.

```text
.agent / .apm                         deployment-owned configuration
──────────────────────────────        ──────────────────────────────────────
runtime_ref: apm://runtime/...   ───▶  apm.runtime.binding.v1
                                        logical ref → provider resource + URL
```

The package continues to declare what it needs through
`runtime_boundary.host_services_only` and `runtime_contract`. A binding declares
what a particular deployment actually provides. Resolution is fail-closed: the
binding must exist and its declared capabilities must cover the package's required
capabilities before any provider invocation begins.

## Package field

`runtime_ref` is optional and has this exact shape:

```yaml
runtime_ref: apm://runtime/human-input-runner@0.1.0
```

It is a logical APM URI, not an HTTPS URL, ARN, Worker name, queue ID, tenant ID,
or secret. The required `@<semver>` makes a runtime protocol change explicit.
Packages without `runtime_ref` remain portable and let a host select any compatible
adapter by capability.

## Binding document

The binding document is deployment configuration. JSON is the canonical wire
shape; a CLI may accept an equivalent YAML authoring file.

```json
{
  "version": "apm.runtime.binding.v1",
  "bindings": {
    "apm://runtime/human-input-runner@0.1.0": {
      "provider": "gcp-cloud-run",
      "resource": "projects/example/locations/asia-northeast3/services/apm-human-input-runner",
      "invoke_url": "https://apm-human-input-runner-example.run.app",
      "auth": {
        "type": "gcp-oidc",
        "audience": "https://apm-human-input-runner-example.run.app",
        "invoker_service_account": "agent-host@example.iam.gserviceaccount.com"
      },
      "capabilities": [
        "human_input_channel",
        "isolated_sandbox",
        "model_inference_adapter"
      ]
    }
  }
}
```

The top-level document has only `version` and `bindings`. A binding has only:

| Field | Meaning |
|---|---|
| `provider` | Lowercase adapter/provider identifier, such as `gcp-cloud-run` |
| `resource` | Provider resource identity. It is the Cloud Run-style counterpart of an AWS ARN, not a package field |
| `invoke_url` | HTTPS base URL for the adapter; no path, query, fragment, or credentials |
| `auth` | Non-secret invocation descriptor. `credential_ref`, when needed, points to host-local credential configuration rather than containing a credential |
| `capabilities` | Exact capabilities supplied by this deployment; resolution rejects a missing requirement |

For `gcp-cloud-run`, `resource` must be
`projects/<project>/locations/<region>/services/<service>`. `auth.type` is
`gcp-oidc`, `auth.audience` equals `invoke_url`, and
`auth.invoker_service_account` is the Google service account granted
`roles/run.invoker`.

The contract deliberately does not standardize an AWS access key, Cloudflare API
token, Vercel token, Supabase secret, or any provider SDK call. Those are host
credentials and adapter implementation details. A provider can use `auth.type`,
`auth.principal`, `auth.credential_ref`, and `auth.parameters` as non-secret
descriptors while keeping the actual value in its secret manager or local keychain.

`auth.parameters.application_secret_header` is a Runtime-owned, safe header
name; the actual value is resolved from the host-only `credential_ref`. When a
provider mounts a function beneath its HTTPS origin, its binding may also use
`auth.parameters.invoke_path_prefix`. It is a strict absolute path prefix with
normal path segments only, such as `/api/apm` or `/apm-task-turn`; it is never
package input and never a caller-selected URL.

## Provider mapping

| Deployment | `resource` identity | Invocation authority | Invocation/profile |
|---|---|---|---|
| Google Cloud Run | `projects/<project>/locations/<region>/services/<service>` | `gcp-oidc` + `roles/run.invoker` | Full task-turn HTTP invocation adapter |
| AWS Lambda | `arn:aws:lambda:<region>:<account>:function:<name>` | caller AWS workload identity / profile | Full task-turn invocation through `aws lambda invoke`; `auth.type: aws-lambda-invoke` |
| Cloudflare Workers | `accounts/<account>/workers/services/<worker>` | Runtime application secret | Edge task-turn transport canary; `auth.type: http-header-secret`; not a package executor |
| Vercel Edge | `projects/<project>/functions/<route>` | Runtime application secret | Edge task-turn transport canary; `http-header-secret` plus `/api/apm`-style `invoke_path_prefix`; not a package executor |
| Supabase Edge | `projects/<project-ref>/functions/<function>` | Runtime application secret | Edge task-turn transport canary; `http-header-secret` plus function `invoke_path_prefix`; not a package executor |
| local host | no external binding; capability-selected host profile | local process/keychain | `runwith`/local adapter selects by capability |
| custom remote Runtime | adapter-defined resource identity | adapter-defined credential | Same binding shape; invocation adapter is provider-owned |

The edge rows intentionally prove transport semantics rather than computational
isolation. Their capability response must say that package execution and model
calls are disabled. A full package run belongs on a container Runtime such as
Cloud Run or Lambda. Every adapter rejects an unresolved or unsupported binding
rather than silently falling back to a different provider.

## CLI resolution contract

The Schift CLI resolves but does not invoke a provider with:

```bash
schift apm runtime resolve ./approval.agent --binding ./runtime-bindings.yaml
```

The command reads the sealed/source package, validates its logical ref, checks the
binding document, and prints a credential-free `apm.runtime.resolution.v1` plan.
It never fetches an OAuth token, reads a secret value, or executes an agent. A
runtime adapter consumes that plan only after its own caller authorization and
provider-specific credential checks pass.

The Schift CLI installs the Cloud Run, Lambda, Cloudflare Worker, Vercel Edge,
and Supabase Edge transports defined above. Cloud Run sends an OIDC token from
an explicit local token file (or `APM_RUNTIME_ID_TOKEN`); Lambda uses the
caller's AWS CLI/workload identity and needs no OIDC token file; the three edge
transports send only the binding-selected application-secret header. All resolve
the secret only from `auth.credential_ref` or an explicit local secret file and
never serialize or print it.

[`../examples/runtime-bindings/cloud-run.json`](../examples/runtime-bindings/cloud-run.json)
and the sibling `aws-lambda.json`, `cloudflare-worker.json`, `vercel-edge.json`,
and `supabase-edge.json` are syntactically valid fictional examples. Copy one
into private deployment configuration and replace every provider identity; do
not put live project, account, endpoint, or secret values in a public package
repository.
