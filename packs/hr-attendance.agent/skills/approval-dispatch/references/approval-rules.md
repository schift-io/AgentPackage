# 결정 합성 규칙

```python
def aggregate_verdict(regulation, hr):
    if regulation.verdict == "rejected" or hr.verdict == "rejected":
        return "rejected"
    if regulation.verdict == "supplement" or hr.verdict == "supplement":
        return "needs_supplement"
    if regulation.confidence == "high" and hr.confidence == "high":
        return "approved"  # or "auto_approved" based on org policy
    return "pending_approval"
```

## 다음 행동
- `approved` → 신청자 통보 + 잔여일 차감 + 캘린더 반영
- `rejected` → 신청자 통보 + 사유
- `needs_supplement` → 신청자에게 누락 항목 질문
- `pending_approval` → 결재자에게 승인/반려/보완 요청 버튼 전송
