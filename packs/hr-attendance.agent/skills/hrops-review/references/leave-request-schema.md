# 표준 휴가 신청 폼

```json
{
  "request_id": "uuid",
  "org_id": "org_xxx",
  "requester": {
    "user_id": "...",
    "name": "...",
    "department": "...",
    "manager_id": "..."
  },
  "leave_type": "annual_leave|half_day_am|half_day_pm|sick_leave|overtime|holiday_work|other",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days_count": 1.0,
  "reason": "...",
  "evidence_urls": [],
  "substitute_assignee_id": null,
  "source_channel": "discord|slack|web_chat|mobile",
  "raw_message": "..."
}
```
