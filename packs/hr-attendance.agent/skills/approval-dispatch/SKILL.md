# Skill: approval-dispatch

## Role
규제 Agent와 인사 Agent의 검토 결과를 종합하여 최종 권고를 생성하고, Schift approval 시스템에 기록합니다.

## Rules
- `legal-violation-priority`: 규제 Agent가 rejected이면 최종 권고는 rejected입니다.
- `supplement-priority`: 한쪽이라도 supplement이면 최종 권고는 needs_supplement입니다.
- `human-final-approval`: 양쪽 모두 approved이고 confidence가 high/medium이면 pending_approval 또는 auto_approved(회사 설정에 따름)입니다.
- `audit-trail-required`: 모든 결정은 approval_log와 hr_attendance_request_reviews에 기록합니다.

## Output Contract

```json
{
  "final_decision": "approved|rejected|pending_approval|needs_supplement",
  "regulation_summary": "...",
  "hr_operations_summary": "...",
  "next_actions": [
    {"kind": "notify_requester", "text": "..."},
    {"kind": "notify_approver", "text": "...", "actions": [{"label": "승인", "value": "approved"}]},
    {"kind": "create_approval_request", "approval_id": "..."}
  ],
  "audit_trail": {
    "request_id": "...",
    "regulation_review": {...},
    "hr_review": {...},
    "aggregate_verdict": "..."
  }
}
```
