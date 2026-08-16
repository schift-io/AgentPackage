# Examples

## `portable.agent`

`portable.agent/` is the smallest fixture with both authoring and canonical
manifest forms. It is intentionally vendor-, tenant-, and runtime-neutral and
is the example used by the public CLI distribution contract:
[`docs/cli-distribution.md`](../docs/cli-distribution.md).

```bash
python3 kit/apm_kit.py lint portable.agent --packs-dir examples
python3 kit/apm_kit.py check portable.agent --host local-byo --packs-dir examples
python3 kit/apm_kit.py build portable.agent --packs-dir examples --out /tmp/apm-dist
```

The resulting `.apm` is the only artifact a registry or Runtime adapter should
consume. [`registry-metadata.json`](registry-metadata.json) shows the separate
registration payload shape; its zero hash and size are documentation
placeholders, not a publishable artifact.

## `hello.agent`

The smallest portable package. It has no Schift, Cloudflare, provider, or
billing dependency and is useful for checking that a Runtime can load the
format:

```bash
python3 kit/apm_kit.py lint hello.agent --packs-dir examples
python3 kit/apm_kit.py check hello.agent --host local-byo --packs-dir examples
python3 kit/apm_kit.py build hello.agent --packs-dir examples --out dist
```

The output is a versioned `.apm` artifact. A Runtime adapter may install that
artifact on Schift, Cloudflare Workers, a local process, or another host that
provides the package's declared capabilities.

## `interoperability.agent`

This fixture opts into the runtime-services v1 contract and demonstrates the
upstream Agent Plugins 1.0 layout plus an A2A 1.0 Agent Card template. It asks
for every governed runtime capability on purpose, so a partial runtime must
reject it before execution rather than providing direct network, memory, or MCP
access by accident.

```bash
python3 kit/apm_kit.py lint interoperability.agent --packs-dir examples
python3 kit/apm_kit.py check interoperability.agent --host docker-codex-isolated --packs-dir examples
```

The second command is expected to fail because the Docker Codex adapter only
provides model inference, isolation, and a provider-only egress proxy. It does
not claim CCLG, search/data, governed MCP, Agent Plugins component execution,
A2A transport, or host-mediated human input yet.

## `higgsfield-demo.agent` — spec example, not a live pack

`higgsfield-demo.agent/` is an **identity-scrubbed teaching copy** of the live
`packs/higgsfield.agent` pack. It exists to give `SPEC.md` one worked example
that is complex enough to show every major `.apm` mechanism in one place —
it is **not** shipped, published, or run in production. Do not edit it
expecting the change to reach any real deployment; the live pack is
`packs/higgsfield.agent` (and, downstream, the `services/agent-hub` runtime
copy in the main monorepo). Conversely, don't copy fixes made here back onto
the live pack blindly — this copy has placeholder org/bucket identifiers
that must not leak into real config.

## What it demonstrates

- **Capability negotiation (fail-closed hosts).** The pack declares
  `runtime_boundary.host_services_only` (`higgsfield_mcp`, `stitch_worker`,
  `usage_ledger`, …) as capabilities the *host* must supply. A host that
  can't supply them is rejected outright rather than falling back to a
  degraded mode — see the `local-byo` run below.
- **script-runtime.** `scripts/higgsfield_rag/*.py` and
  `scripts/upload_higgsfield_rag.py` are plain stdlib scripts invoked by
  the packaged runtime, not code the host `import`s.
- **Skills.** Six `skills/*/SKILL.md` files, each with its own rules and
  output contract, chained into one pipeline (brief → shot list → movement
  → prompt → clip/stitch plan → QC).
- **RAG knowledge binding.** `apm.yml: knowledge` + `knowledge/rag-sources/`
  show how a pack binds to a dedicated reference bucket instead of a
  tenant's general knowledge base.

## Try it

```bash
cd AgentPackage

# Host that has every declared capability — passes.
python3 kit/apm_kit.py check higgsfield-demo.agent --host agent-hub --packs-dir examples

# Minimal host without higgsfield_mcp/stitch_worker/usage_ledger — fails closed,
# on purpose. This is the behavior the spec calls out in the capability
# negotiation section: an unmet capability is a hard reject, not a silent
# downgrade.
python3 kit/apm_kit.py check higgsfield-demo.agent --host local-byo --packs-dir examples

# Vocabulary / required-field lint.
python3 kit/apm_kit.py lint higgsfield-demo.agent --packs-dir examples

# Pack dir -> .apm artifact.
python3 kit/apm_kit.py build higgsfield-demo.agent --packs-dir examples --out dist
```

## What was changed from the live pack

The internal tenant identity was replaced throughout with the fictional
org `acme` (owner org id, skill id namespace, display name, package name). The real knowledge-bucket UUID was replaced
with a placeholder `00000000000000000000000000000000`. The pack was
renamed `higgsfield-demo` at version `0.1.0` (`apm.yml: name`/`version`,
`pack.json: package_ref`, `pack.json: manifest_overrides.version` are kept
in sync — see `SPEC.md` §8 on why a mismatch here 409s on publish).
`docs/HANDOFF.md` (an internal deployment/ops log with a live OAuth client
id and internal callback URL) was dropped rather than scrubbed, since it
carries no spec-teaching value. `docs/DESIGN.md` was dropped for the same
reason: it is an internal design log that names sibling packs and internal
registration wiring, and it teaches nothing about the `.apm` format.
`marketplace.publish` is left undeclared,
so this pack is unpublishable by the kit's own fail-closed default — it
is meant to be read and run locally with `--packs-dir`, not marketplace-listed.
