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

## Provider mapping

| Deployment | Typical `resource` identity | Invocation authority | Adapter status |
|---|---|---|---|
| Google Cloud Run | `projects/<project>/locations/<region>/services/<service>` | `gcp-oidc` + `roles/run.invoker` | Reference binding validator and Schift CLI resolver |
| AWS Lambda | Lambda ARN or function URL identity | SigV4/role chosen by the adapter | Same binding shape; invocation adapter is provider-owned |
| Cloudflare Workers | Worker/service identity | Worker service binding or service token | Same binding shape; invocation adapter is provider-owned |
| Vercel Functions | Project/function deployment identity | deployment-scoped credential chosen by the adapter | Same binding shape; invocation adapter is provider-owned |
| Supabase Edge | project/function identity | project-scoped credential chosen by the adapter | Same binding shape; invocation adapter is provider-owned |
| local host | no external binding; capability-selected host profile | local process/keychain | `runwith`/local adapter selects by capability |
| custom remote Runtime | adapter-defined resource identity | adapter-defined credential | Same binding shape; invocation adapter is provider-owned |

“Same binding shape” does not mean every provider adapter is already implemented.
An adapter must reject an unresolved or unsupported binding rather than silently
fall back to a different provider.

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

[`../examples/runtime-bindings/cloud-run.json`](../examples/runtime-bindings/cloud-run.json)
is a non-deployable placeholder template. Copy it into deployment configuration;
do not replace its placeholders in a public package repository.
