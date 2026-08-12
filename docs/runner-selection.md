# Runner selection (normative)

This document defines how a host chooses an executor for an AgentPackage run.
It is part of the AgentPackage protocol version 0.1.0.

Before starting a run, a host MUST resolve the verified package content hash,
canonical manifest, requested operation, required capabilities, declared
permissions, caller permissions, and available execution profiles.

Candidate runners MUST be gated in this order:

1. protocol support for 0.1.0;
2. package integrity and content-hash verification;
3. required capability satisfaction;
4. permission satisfaction;
5. requested local or isolated execution-mode guarantees; and
6. resource policy, quotas, and availability.

The first candidate in the host's explicit priority order that passes every
gate MUST be selected. A host MUST NOT silently downgrade isolation,
permissions, capabilities, or result semantics. If no candidate passes, the
run MUST be rejected before package code executes.

The selection decision MUST be recorded as runner.id, runner.mode, and
runner.selection_reason in the result envelope. The reason MUST NOT contain
secrets. A runner MUST advertise the mode it actually provides; a separate
thread, working directory, or virtual environment alone is not isolated
execution.
