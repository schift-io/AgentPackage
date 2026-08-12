# AgentPackage protocol 0.1.0 (normative)

Version 0.1.0 is the initial public execution-contract version. It includes
runner selection, apm.run.result.v1, artifact result layout, local/isolated
execution modes, and permission gates.

The package container remains the apm-v1 format in SPEC.md. The execution
protocol version and container hash prefix are separate values; changing one
does not silently change the other.

An implementation claiming 0.1.0 support MUST validate before execution,
perform fail-closed capability and permission checks, report the actual runner
mode, return a conforming apm.run.result.v1 envelope, and apply artifact path,
size, and digest rules.

Version 0.1.0 is additive-compatible. Readers MUST ignore unknown additive
fields and writers MUST preserve required fields and meanings. Breaking changes
require a new protocol version and compatibility document.

This version does not standardize registry APIs, transport, authentication,
billing, schedulers, or provider implementations.
