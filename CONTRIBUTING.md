# Contributing to Agent Package

Thank you for your interest in APM.

## What we accept

- **Bug reports** — open an issue with reproduction steps
- **Format spec clarifications** — if SPEC.md is ambiguous, file an issue
- **Example packages** — new examples in `examples/` are welcome
- **Documentation fixes** — typos, broken links, unclear wording
- **Kit improvements** — bug fixes and performance improvements to `kit/`

## What we don't accept

- **Runtime/adapter implementations** — the runtime contract is documented
  in `docs/runtime-adapter.md`. Build your own adapter against the spec;
  don't PR it here. Schift's managed runtime is proprietary.
- **Changes to the container format or hash algorithm** — these are frozen
  in SPEC.md. Breaking changes require a new spec version.
- **Features that require proprietary Schift services** — this repo must
  work standalone without a Schift account.

## How to contribute

1. Fork the repo
2. Create a branch (`git checkout -b fix/my-fix`)
3. Make your changes
4. Run validation: `python3 kit/apm_kit.py lint --packs-dir examples`
5. Open a PR with a clear description of what and why

## PR rules

- One concern per PR. Don't mix a bug fix with a feature.
- All PRs must pass `apm-kit lint` on all examples.
- New examples must include `apm.yml`, `agent.md`, and `pack.json`.
- Don't add dependencies. The kit has one dependency (pyyaml).
- English for code and commit messages. Docs can be bilingual.

## Code of Conduct

Be respectful. We don't have a formal CoC document — just don't be a jerk.

## Security

See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions will be licensed under
the Schift Agent Package License v1.0 (see [LICENSE](LICENSE)).
