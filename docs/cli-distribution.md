# CLI distribution contract

This document defines the public command and registry boundary for an
AgentPackage distribution client. It describes the contract a CLI may consume;
it does not implement a registry server.

## Source to artifact

The portable distribution unit is always a validated `.apm` artifact. A source
directory is an authoring input only:

```text
<name>.agent/ --lint/check--> <name>-<version>.apm --push--> registry
```

The reference kit in this repository is the compatibility oracle for the
format:

```bash
python3 kit/apm_kit.py lint portable.agent --packs-dir examples
python3 kit/apm_kit.py check portable.agent --host local-byo --packs-dir examples
python3 kit/apm_kit.py build portable.agent --packs-dir examples --out /tmp/apm-dist
```

The `check` step is runtime-neutral: `local-byo` is only one host profile. A
different adapter may provide the same capabilities and consume the same
artifact. A CLI must not add provider endpoints, secrets, tenant bindings, or
database identifiers to the package while building or pushing it.

`pack.json`, when present, is the canonical manifest used inside the bundle;
`apm.yml` remains the authoring manifest. The two files must describe the same
public package identity and version. See [SPEC.md](../SPEC.md) §5 and §8.

## Public CLI command contract

A distribution CLI may expose the following commands. The names and options
are the public UX contract; an implementation may add equivalent aliases but
must preserve the artifact and metadata semantics.

```text
schift pack validate <path> [--host <profile>]
schift pack build <path> --output <file>
schift pack push <path> [--registry <url>] [--dry-run]
```

Expected behavior:

| Command | Required behavior |
|---|---|
| `pack validate` | Validate the source manifest, required `agent.md`, capability vocabulary, and (when present) the canonical `pack.json`. With `--host`, fail closed if a required capability is missing. |
| `pack build` | Validate first, then emit a deterministic `.apm`; print the package ref, byte size, and full SHA-256 content hash. Do not mutate the source directory. |
| `pack push` | Build once, upload/deduplicate the artifact by content hash, then register the immutable package reference. A registry conflict for an existing version with a different hash is an error requiring a version bump. |
| `--dry-run` | Run validation, build, hash, and metadata calculation without uploading or registering anything. |

The source path may be any directory ending in `.agent`; the CLI must not
require the package to live under an internal `packs/` directory. A failed
validation must prevent both artifact upload and registry registration.

## Registry metadata

The registry registration request is an HTTP `POST` to the configured registry
endpoint's `/v1/apm/registry` resource. The artifact is addressed separately
by the content hash. The minimum JSON body is:

```json
{
  "agent_id": "portable-hello",
  "version": "0.1.0",
  "content_hash": "<64 lowercase hexadecimal SHA-256 characters>",
  "r2_key": "apm/objects/<content_hash>.apm",
  "size_bytes": 1234
}
```

The fields mean:

- `agent_id`: public package identifier, normally from the canonical manifest.
- `version`: the immutable registry version. If `package_ref` contains `@`,
  its suffix is authoritative; top-level `version` is the fallback.
- `content_hash`: the full AgentPackage content hash defined in SPEC §4.
- `r2_key`: an object-store key or equivalent opaque artifact reference. It is
  not a Runtime endpoint and must not be put into the package manifest.
- `size_bytes`: the exact byte length of the `.apm` artifact.

Optional registry ACL fields are additive and default to private when absent:

```json
{
  "visibility": "public",
  "allowed_orgs": ["<public-consumer-org>"]
}
```

`owner_org`/`owner_org_id` are intentionally absent from the portable fixture
and should only be supplied by an authenticated registry owner when the
registry contract requires them. They are registration metadata, not package
content. Do not copy internal organization identifiers into this public
repository.

The request uses the registry's authentication mechanism (the reference
publisher uses `Authorization: Bearer <credential>`). Credentials are read
from the environment or the CLI credential store and never from `apm.yml`,
`pack.json`, fixtures, logs, or command examples.

## Immutability and failure rules

1. Uploading the same content hash is idempotent; a client may skip the upload
   after a successful existence check.
2. Registering the same `agent_id@version` with the same hash is idempotent.
3. Registering the same version with a different hash is a conflict (HTTP 409).
   The client must report that the package version needs to be bumped; it must
   not overwrite the registry entry.
4. A successful local build is not proof of publication. `pack push` must report
   upload and registration separately, including the final registry response.
5. `visibility: public` controls registry visibility only. It does not grant
   access to private data and does not make a Runtime adapter or provider
   endpoint portable.

The complete wire-shaped example is
[`examples/registry-metadata.json`](../examples/registry-metadata.json). Its
zero hash and size are deliberate placeholders for documentation and must be
replaced by values calculated from the actual `.apm` before a real push.
