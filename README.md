# Agent Package (.apm)

[한국어](README.ko.md)

> **Docker sealed apps. APM seals agents.**

You build an AI agent on your laptop — a prompt, some skills, maybe a
memory hook. But the model lives on a server. The search engine is an API.
The tools need credentials you don't want in your repo.

APM draws a clean line. **You ship the `.apm`. The runner provides the
infrastructure.** Same file runs the same way everywhere — your laptop,
your company's server, a hosted platform. If the runner can't provide
what the package needs, it says so before anything executes.

```
my-agent/                  ← your folder (any name)
  → schift pack build
my-agent-0.1.0.apm         ← share this
```

## Think Docker, but for agents

| Docker | APM |
|---|---|
| App source → image | Your folder → `.apm` |
| Container runtime | Runner (local / server / custom) |
| Ports, env, volumes | Capability declarations |
| Network isolation | Sandbox + egress policy |
| Image digest | Content hash (deterministic) |

Docker seals what an **app** does. APM seals what an **agent** does — its
instructions, skills, tools it's allowed to call, what memory it can
access, and what it's *not* allowed to do. The model? Injected by the
runner. Same way Docker injects environment variables.

## Install

```bash
npx @schift-io/mcp pack init my-agent    # zero install
```

or with the Python CLI:

```bash
pip install schift-cli
schift pack init my-agent
```

No account needed. No server. No API key.

## Create an agent

```bash
schift pack init my-agent \
  --display-name "Weekly Report Writer" \
  --description "Turns meeting notes into a team report"
```

You get a folder:

```
my-agent/
├── agent.md     ← your agent's instructions (edit this)
├── apm.yml      ← name, version, description
└── pack.json    ← runtime config, skills, tools
```

## Build a `.apm`

```bash
schift pack build my-agent/
# → my-agent-0.1.0.apm ✓
```

That's your package. Share it, upload it, run it anywhere.

## Already have an agent? Convert it

Got a `SKILL.md`, `.claude/`, or `.cursorrules`?

```bash
schift pack import ./my-skill
# → my-skill-0.1.0.apm ✓
```

| You have | What happens |
|---|---|
| `SKILL.md` | Frontmatter → metadata, body → instructions |
| `CLAUDE.md` / `.claude/` | Instructions + commands → skills |
| `.cursorrules` | Rules → instructions |
| Any markdown | Content → instructions |

## Validate

```bash
schift pack lint my-agent/                       # structure + fields
schift pack check my-agent/ --host local-byo     # can my machine run it?
```

## What's in a `.apm`

Deterministic tar.gz. Same input = same bytes = same hash.

```
apm.yml          name, version, visibility
agent.md         the prompt — what the agent does
pack.json        skills, tools, pipeline config
skills/          skill definitions (optional)
scripts/         executable code (optional)
references/      static data (optional)
```

**Never in a package:** API keys, tokens, model endpoints, cloud IDs,
secrets. The runner provides these. Your package stays portable.

## Capability negotiation

Before running anything, the runner checks if it can deliver what the
package needs.

```yaml
runtime_boundary:
  host_services_only:
    - model_inference_adapter      # "I need a model"
    - human_input_channel          # "I need to ask a human"
    - cclg_memory_read             # "I need to read memory"
```

Can't provide it? Rejected **before execution**. Not silently. The worst
thing an agent can do isn't crash — it's quietly do the wrong thing.

## Where it runs

```
.apm
 ├── Local                  your model, your files, free
 ├── Schift Agent Runtime   one command, fully managed
 └── Self-hosted            your cloud, your rules
```

**[Schift Agent Runtime](https://schift.io/agent-runtime/)** — the fastest
path. `pack push` and it runs. Memory, search, governance, billing included.

**Self-hosted** — run the `.apm` on your own infrastructure.

| Cloud | How |
|---|---|
| **AWS / Azure / GCP** | [Contact us](mailto:hello@schift.io) for deployment support |
| **NCloud / On-premises** | [Contact us](mailto:hello@schift.io) for dedicated instance |
| **Your own runner** | Implement the [runtime contract](docs/runtime-adapter.md) yourself |

Want to build your own runner? Everything you need is in [`docs/`](docs/) —
runtime services, capability negotiation, execution modes, artifact results,
release provenance. The spec is open.

## CLI

| Command | Description |
|---|---|
| `schift pack init <name>` | Create new agent |
| `schift pack import <path>` | Convert existing skill/agent |
| `schift pack lint <dir>` | Validate |
| `schift pack check <dir> --host <profile>` | Runner compatibility |
| `schift pack build <dir>` | Seal into `.apm` |
| `schift pack extract <apm>` | Unpack for editing |
| `schift pack fork <apm> --agent-id <id>` | New identity |

## Publish to [Schift Agent Runtime](https://schift.io/agent-runtime/)

```bash
npm install -g schift-cli    # or: pip install schift-cli

schift pack push my-agent-0.1.0.apm
schift pack push my-agent-0.1.0.apm --private-with org_mycompany
```

Signed receipt (Ed25519) binds content hash + version + access list.

## Package vs skill

A skill is what an agent *reads*. A package is what an agent *runs on*.

| | Skill | Package |
|---|---|---|
| Missing file | Answer gets worse | Agent does the wrong thing |
| Contract | None | Declared + enforced |
| Integrity | None | Content hash |

## Interoperability

| Standard | APM adds |
|---|---|
| MCP | Which servers/tools are allowed |
| Agent Plugins | Sealed manifest in the package |
| A2A | Agent card template |

## Spec

[`SPEC.md`](SPEC.md) — the normative contract. This README explains why.

## License

**Schift Agent Package License v1.0** ([`LICENSE`](LICENSE))

| Use | |
|---|---|
| Create, build, share, run packages | **Free** |
| Build `.apm`-compatible tools | **Free** (open spec) |
| Offer APM execution as a managed service | [Commercial](mailto:licensing@schift.io) |

---

[Spec](SPEC.md) · [Docs](docs/) · [Examples](examples/) · [한국어](README.ko.md)
