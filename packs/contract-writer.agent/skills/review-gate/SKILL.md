---
name: review-gate
description: Deterministically check the drafted clauses before HWPX packaging — required-clause coverage, party name consistency, term/consideration gaps, legal-advice language guard, and unsourced numeric-claim detection. fail-closed.
---

# Review Gate (검토 게이트 — 수락 게이트)

## Purpose

`contract-drafting`이 만든 조항 markdown을 `hwpx-packaging`으로 넘기기 전에
검증한다. bid-response `faithfulness-check`의 결정적 게이트 패턴을 계약
문서 도메인에 재구현한다(임포트 공유가 아니라 재구현 — 소스 shape가 다름:
여기는 RFP/memory가 아니라 intake 구조 필드 대조).

## Inputs

- `contract-drafting` 산출 `list[ClauseInstance]`.
- `contract-intake` 산출 `ContractIntake`(소스 대조 기준).

## Pipeline (단계, 전부 결정적 — LLM 호출 없음)

1. **필수 조항 누락 검사** — 계약 유형의 `required=True` 조항이 전부
   렌더링됐는지 확인(`missing_required_clause`, blocking).
2. **당사자 불일치 검사** — 갑/을 회사명이 동일하면 blocking
   (`party_name_collision`).
3. **기간/대가 공백 검사** — 시작·종료일 미확정은 advisory, 용역계약/
   공동사업협약의 대가·수익배분 미확정도 advisory(제출 차단은 아니지만
   run report 상단에 강조).
4. **법률자문 가드** — "이 조항이 유리합니다", "법적으로 문제없습니다" 류
   문구를 정규식으로 스캔한다. 발견 즉시 blocking(`legal_advice_language`)
   — 이 팩의 절대 경계.
5. **창조 수치 차단** — 조항 markdown의 금액·비율이 intake 소스
   (`source_notes` + 구조 필드)에 없으면 blocking(`unsourced_numeric_claim`).
   기간(30일/14일 등 절차 조항의 고정 문구)은 대상에서 제외한다 —
   bid-response가 "구조적 숫자는 의도적으로 매칭하지 않는다"고 정한 것과
   같은 이유.

## Rules

- **blocking finding이 하나라도 있으면 `passed=False`** — HWPX 변환을
  보류한다(fail-closed). advisory는 통과를 막지 않지만 run report에 강조
  표시된다.
- 위반 조항을 임의로 "안전한 문장"으로 재작성하지 않는다 — 위반 목록만
  사람에게 올리거나 intake를 보강해 재실행을 요청한다.
- P1 MVP는 LLM 판정(2차 보조) 없이 결정적 검사만 수행한다(bid-response의
  `judge_fn`처럼 향후 보조 판정을 붙일 자리는 열어두되 배선하지 않는다).

## 도구 경계

- 검사 로직 전부 `contract_writer_review_gate.py`(pure Python, 외부
  의존성 없음)가 소유한다.

## Output Contract

- `ReviewGateResult(passed: bool, findings: list[ReviewFinding])`.
- `run-report` 스킬이 이 결과를 상단 "검수 게이트 요약" 블록으로 그대로
  요약한다.
