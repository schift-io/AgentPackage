---
name: contract-intake
description: Structure freeform/structured user input (parties, purpose, scope, term, consideration, special terms) into a ContractIntake for the selected contract type, asking [확인 필요] questions for anything missing instead of inventing values.
---

# Contract Intake (자연어/구조 입력 → 구조화)

## Purpose

사용자가 자연어 또는 부분 구조로 준 계약 정보(당사자 A·B, 목적, 범위, 기간,
대가, 특약)를 `ContractIntake`로 정규화한다. 누락된 필수 필드는 절대
창조하지 않고 `[확인 필요]` 질문으로 되묻는다(bid-response MISSING-ask
가드와 동일 톤).

## Inputs

- 계약 유형(사용자 선택 또는 목적 서술 기반 제안 — 자동 확정 금지, 확인
  필요).
- 자연어 설명 또는 이미 구조화된 필드(당사자명/주소/대표자, 목적, 범위,
  시작·종료일, 대가/지급방법, 비밀유지기간, 특약).

## Pipeline (단계)

1. **계약 유형 확정** — 사용자가 명시하지 않았으면 목적 서술에서 가장
   적합한 유형(MOU/NDA/용역계약/공동사업협약)을 제안하고 확인받는다.
2. **구조화** — `contract_writer_intake.build_contract_intake(contract_type,
   raw)`로 `ContractIntake` + 누락 질문 목록을 얻는다.
3. **누락 질문 제시** — `missing_questions`가 비어 있지 않으면 그 질문들을
   사용자에게 그대로 올린다. 답변을 받으면 1~3을 재귀적으로 반복한다.
4. **소스 노트 보존** — 사용자가 준 자유서술 원문을 `source_notes`에 그대로
   보존한다 — `review-gate` 스킬이 이후 조항의 수치가 이 소스에서 나온
   것인지 대조하는 유일한 근거가 된다.

## Rules

- 회사 등록정보(사업자등록번호 등)는 사용자가 명시적으로 준 값만 받는다 —
  추정/검색으로 채우지 않는다.
- 계약 유형에 따라 대가 질문 여부가 다르다(MOU/NDA는 대가가 없는 게 정상 —
  묻지 않는다. 용역계약/공동사업협약만 대가/수익배분을 묻는다).
- 사용자가 "일단 초안만 보고 싶다"고 하면 누락 필드를 `[확인 필요]`
  placeholder로 남긴 채 draft로 넘어갈 수 있다 — 다만 그 사실을 draft
  결과에 명시한다.

## 도구 경계

- 순수 정규화 로직은 `contract_writer_intake.py`(pure Python)가 전부
  소유한다. 자연어 파싱(문장에서 구조 추출)은 이 스킬을 호출하는 상위
  ReAct 턴의 책임 — 이 모듈은 이미 구조화된 dict만 받는다.

## Output Contract

- `IntakeResult(intake: ContractIntake, missing_questions: list[str])`.
