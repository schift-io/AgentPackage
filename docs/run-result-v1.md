# apm.run.result.v1 (normative)

apm.run.result.v1 is the portable JSON result envelope for one accepted or
rejected AgentPackage operation. It is UTF-8 and has no vendor-specific fields
in its required core.

The required shape is:

    {
      "protocol": "apm.run.result.v1",
      "status": "succeeded",
      "run": {
        "id": "run_01...",
        "package_ref": "portable-hello@0.1.0",
        "content_hash": "<64 lowercase hex characters>",
        "operation": "run"
      },
      "runner": {
        "id": "local-reference",
        "mode": "local",
        "selection_reason": "capabilities-and-permissions-satisfied"
      },
      "artifacts": [],
      "error": null
    }

protocol, status, run, runner, artifacts, and error MUST be present.
run.id, run.package_ref, run.content_hash, run.operation, runner.id, and
runner.mode MUST be non-empty strings. content_hash MUST be the verified
AgentPackage content hash, not a hash of the result JSON.

status is one of accepted, running, input_required, succeeded, failed, rejected,
or cancelled. input_required is non-terminal: the host is waiting for an
authorized human input submission and MUST retain the run/task identity needed
to resume a new turn. It MUST NOT be represented as succeeded, failed, or an
implicit empty answer.
A final succeeded result MUST have error null. A terminal non-success result MUST
include an error object with stable code and human-readable message.

The artifacts array contains only complete, addressable artifacts. Its entries
and path rules are defined in artifact-results.md. Unknown additive fields MUST
be ignored by readers; writers MUST preserve required field meanings.

When a package requires `runtime_contract.interaction`, the event stream SHOULD
include `run.input_required` with a stable request ID, prompt, and input schema,
followed by `run.input_submitted` carrying the same request ID after host-side
authorization and validation. The event payload MUST NOT contain a responder's
credential or a provider/MCP secret. See runtime-services-v1.md for the
interaction and A2A state mapping.
