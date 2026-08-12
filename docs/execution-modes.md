# Local versus isolated execution (normative)

AgentPackage defines local and isolated execution. The host MUST report the
mode used in apm.run.result.v1.

Local execution runs in the caller-controlled environment. Before execution the
host MUST make its working-directory, filesystem, network, environment-variable,
child-process, and resource policies visible. Local mode is not a security
boundary.

An isolated runner MUST execute outside the caller's ordinary process and
credential context, with a dedicated workspace, enforced resource limits, and
an enforced network policy. Caller secrets MUST NOT be inherited unless the
permission policy explicitly grants them. The boundary MUST cover package code,
child processes, filesystem writes, and network access.

A separate process without resource enforcement is not sufficient. If the host
cannot prove the advertised guarantee, it MUST select local or reject the
request; it MUST NOT label best-effort execution isolated.

Both modes MUST validate the .apm and permissions before execution, write
results through the artifact layout, and preserve operation/result semantics.
