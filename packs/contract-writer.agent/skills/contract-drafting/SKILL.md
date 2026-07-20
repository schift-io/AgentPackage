---
name: contract-drafting
description: Render the selected contract type's standard clause template with the structured intake into numbered markdown clauses (제N조), leaving unresolved facts as [확인 필요] placeholders — never inventing legal effect or advantageous phrasing.
---

# Contract Drafting (템플릿 + intake → 조항 markdown)

## Purpose

`contract-intake`가 만든 `ContractIntake`와 선택된 계약 유형의 표준 조항
템플릿(`contract_writer_templates.py`)으로 `제N조(제목)` 형식의 조항
markdown을 렌더링한다. **표준 문구의 빈칸을 채우는 것이지 조항을 새로
창작하거나 유불리를 판단하지 않는다.**

## Inputs

- `contract-intake` 산출 `ContractIntake`.
- 회사 컨텍스트(필요 시) — tenant core memory에서 `schift.memory.query`로
  조회(bid-response company-memory-grounding 패턴). 지식 버킷이 아니다.

## Pipeline (단계)

1. **템플릿 로드** — `contract_writer_templates.get_template(contract_type)`
   로 이 유형의 조항 목록(order 오름차순)을 가져온다.
2. **조항 렌더링** — `contract_writer_draft.render_clauses(intake)`가 각
   조항의 `{placeholder}`를 intake 값으로 채운다. intake에 없는 값은
   `[확인 필요]`로 남는다(str.format이 자연히 보장 — 창조 없음).
3. **본문 조립** — `render_contract_markdown(intake, clauses)`가 법적 검토
   고지 + `제N조(제목)` 번호를 붙여 전체 markdown을 만든다.

## Rules

- **법률 자문 아님.** 조항 문구를 당사자에게 유리하게 재작성하지 않는다.
  "이 조항이 유리합니다" 류 서술은 절대 생성하지 않는다 — 발견 시
  `review-gate`가 차단한다.
- intake에 없는 실적·수치·법률 사실을 창조하지 않는다. 특약(`special_terms`)
  도 사용자가 명시한 문구만 그대로 삽입한다.
- 회사 등록정보(사업자등록번호 등)는 intake에 실값이 없으면 항상
  `[확인 필요]`.
- 서명란은 항상 placeholder("(인)")만 — 실제 서명/인감 이미지는 사람이
  나중에 삽입한다.

## 도구 경계

- 렌더링 로직은 `contract_writer_draft.py`(pure Python, LLM 미사용)가 전부
  소유한다. P1 MVP는 표준 템플릿 치환만 하므로 LLM 자유생성 경로가 없다 —
  향후 특약 서술 보강에 LLM을 붙이더라도 이 스킬의 결정적 뼈대(조항 구조·
  번호 매기기)는 그대로 유지한다.

## Output Contract

- `list[ClauseInstance]` + 조립된 markdown 본문(법적 검토 고지 포함).
