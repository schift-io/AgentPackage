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
or cancelled. `input_required` is non-terminal: the host has paused the current
task turn for an authorized human response and MUST retain the run/task identity
needed to resume a new turn. It MUST NOT be represented as succeeded, failed,
or an implicit empty answer. `paused` and `resuming` are task-turn states, not
additional result statuses; a host MAY publish them in an additive
`metadata.task_turn` object.

An `input_required` envelope for a package declaring
`runtime_contract.interaction` SHOULD include these additive fields:

```json
{
  "input_request": {
    "protocol": "apm.input.request.v1",
    "id": "input_approval",
    "questions": [
      {"id": "approve", "label": "Continue?", "type": "approval", "required": true}
    ]
  },
  "metadata": {
    "task_turn": {
      "state": "paused",
      "number": 1,
      "input_request_id": "input_approval"
    }
  }
}
```

`input_request` is the request record for the current pause, not a response.
The host validates and binds a response to its `run.id` and request ID before it
starts a new task turn. Response values and responder authorization material are
not result-envelope fields.

`cancelled` is terminal. A human-declined required approval or an authorized
host cancellation MUST return `status: "cancelled"` with a stable error code and
human-readable message. A cancelled request cannot be resumed.
A final succeeded result MUST have error null. A terminal non-success result MUST
include an error object with stable code and human-readable message.

The artifacts array contains only complete, addressable artifacts. Its entries
and path rules are defined in artifact-results.md. Unknown additive fields MUST
be ignored by readers; writers MUST preserve required field meanings.

When a package requires `runtime_contract.interaction`, the event stream SHOULD
include `run.input_required` with a stable request ID, task-turn number, and
non-secret request metadata, followed by `run.input_submitted` carrying the
same request ID after host-side authorization and validation. Events MUST NOT
contain answer values, responder credentials, provider credentials, MCP secrets,
or authorization headers. See runtime-services-v1.md for the request/response,
workspace, state-transition, and host-interface contract.
