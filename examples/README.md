# `higgsfield-demo.agent` — spec example, not a live pack

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
cd core-dependencies/AgentPackage

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
