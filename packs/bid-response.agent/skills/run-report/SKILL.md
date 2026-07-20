---
name: run-report
description: Summarize the full bid-response run — elapsed time, per-model token/cr cost, files generated, and remaining placeholder count — reusing existing cost/usage instrumentation.
---

# 런 리포트 (처리시간·토큰·cr 비용·placeholder 잔여)

## Purpose

전체 응찰 패키지 run의 요약 리포트를 만든다. 새 계측을 만들지 않고 기존
`server/store/llm_costs.py`/`usage_costs.py`/`server/billing/run_billing.py`
경로를 그대로 재사용한다(agent-hub의 `accounting-cost-of-pass` eval 선례와
동일한 계측 원칙).

## Inputs

- 각 단계(rfp-intake / requirement-scoring-map / company-memory-grounding /
  proposal-drafting / form-filling / hwpx-packaging)의 시작·종료 타임스탬프.
- `awp_operations.bid-response-proposal.text_model`이 실제로 호출한 모델별
  input/output 토큰 수(기존 usage 로깅이 이미 기록).
- `hwpx-packaging` 단계의 생성 파일 수 + kordoc validate 결과.
- `form-filling`/`proposal-drafting`이 남긴 placeholder 잔여 개수.

## Pipeline (단계)

1. **시간 집계** — 단계별 소요시간 + 전체 소요시간(PROOF.md의 "RFP 수령→
   패키징·검수 종료" 구간과 동일한 정의).
2. **비용 집계** — 모델별 input/output 토큰 × `tokenizer.py` 단가 = cr 비용.
   `text_model`이 디폴트(`openai/gpt-5.4-mini`)에서 교체됐으면 실제 사용된
   모델 기준으로 계산한다(하드코딩된 디폴트 가격을 그대로 쓰지 않는다).
3. **산출물 집계** — 생성 HWPX 개수, validate 통과/실패, 제출 대상(본문+서식)
   대 부속물(README 등 비제출물) 구분.
4. **placeholder 집계** — 본문/서식별 placeholder 잔여 개수 + 주요 항목
   나열(회사 등록정보·대표자·인력·금액·서명란 등).
5. **검수 게이트 요약** — `faithfulness-check`의 `GateResult`(passed 여부,
   위반 건수·카테고리별 분포, `[검증 필요]` 마킹 라인 목록), constraints
   위반 스캔 결과, compliance [확인필요 — 최우선] 항목을 최상단에 요약.

## Rules

- 비용 수치는 실제 사용량 로깅(`llm_costs.py`)에서 가져온다 — 추정치를 실측인
  것처럼 제시하지 않는다. 추정 단계(스캐폴딩 단계)에서는 반드시 "추정치, 실측
  아님"을 명시한다.
- placeholder 개수는 실제 렌더된 문서에서 정규식/카운트로 집계한다(수동 어림
  금지).

## 도구 경계

- 비용 조회는 `agent_hub.cost.log`/기존 usage 저장소를 그대로 쓴다. 신규 비용
  계측 테이블/컬럼을 만들지 않는다.
- 리포트 렌더링(html/markdown)은 이 스킬이 만들고, xlsx/pdf 변환이 필요하면
  document-helper에 위임한다.

## Output Contract

- `format`: html/markdown
- {id, title, bullets:[{claim, details[]}]} — 시간/비용/산출물/placeholder/
  검수게이트 5개 블록.
- 마지막 섹션은 항상 "제출 전 최종 검수(사람 확인)"으로 남긴다.
