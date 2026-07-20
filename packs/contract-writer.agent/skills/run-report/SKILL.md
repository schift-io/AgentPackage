---
name: run-report
description: Summarize the contract-writer run — clause count, remaining placeholder count, review-gate result, HWPX artifact status, elapsed time — pure deterministic instrumentation, no LLM narrative text.
---

# 런 리포트 (조항 수·placeholder 잔여·게이트 결과·처리시간)

## Purpose

계약서 초안 런의 결정적 요약을 만든다. bid-response `run-report` 스킬과
동일 원칙 — 새 계측을 만들지 않고 이미 계산된 값을 모은다.

## Inputs

- `contract-drafting` 산출 `list[ClauseInstance]`(각 `placeholder_count`).
- `review-gate` 산출 `ReviewGateResult`(passed, findings).
- `hwpx-packaging` 산출물 수(0 또는 1) + 처리시간.

## Pipeline (단계)

1. **조항 집계** — 렌더링된 조항 수, placeholder 잔여 총합
   (`ClauseInstance.placeholder_count` 합).
2. **검수 게이트 요약** — `passed` 여부, blocking/advisory finding 개수 —
   최상단에 표시.
3. **산출물 집계** — HWPX 생성 성공 여부(1) 또는 보류(0, 사유 포함).
4. **시간 집계** — intake→draft→gate→HWPX 전체 소요시간(ms).

## Rules

- LLM 서술 텍스트를 담지 않는다 — 순수 계측 JSON/구조만.
- placeholder 개수는 실제 렌더된 텍스트에서 카운트한다(수동 어림 금지).
- 검수 게이트가 `passed=False`면 리포트 최상단에 "제출 불가 — 검토 필요"를
  명시한다.

## 도구 경계

- 집계 로직은 `contract_writer_run_report.py`(pure Python)가 전부 소유한다.
  신규 비용/사용량 계측 테이블을 만들지 않는다.

## Output Contract

- `ContractRunReport(contract_type, clause_count, placeholder_remaining,
  review_passed, review_finding_count, hwpx_artifact_count, elapsed_ms,
  artifact_refs)`.
- 리포트 마지막 섹션은 항상 "제출·서명 전 검수 체크(사람 확인) —
  placeholder 치환·법률 검토·서명/날인 확인 필요"로 남긴다.
