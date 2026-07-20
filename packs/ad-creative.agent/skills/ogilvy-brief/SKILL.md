---
name: ogilvy-brief
description: Fill the Ogilvy DO BRIEF as a structured state object that drives all downstream ad creative. Enforce the MISSING-ask anti-hallucination guard and the 6-element coverage gate before any generation.
---

# Ogilvy DO BRIEF (구조화 intake)

## Goal

광고 제작의 **single source of truth**를 만든다. 브리프는 "문서"가 아니라 downstream
(세그먼트·캐릭터·스토리보드·프롬프트 조합)을 결정적으로 구동하는 **state 객체**다.
상단 11개 오길비 필드를 채우면, 하단 4개 실행 필드(coverage_check / segment_axis / anchors)는
브리프·브랜드 버킷에서 자동 파생한다.

정식 스키마는 `references/ogilvy-brief-schema.json`. 6요소 온톨로지는
`references/six-element-ontology.md`.

## Output Contract

`references/ogilvy-brief-schema.json`을 그대로 채운 JSON 1개. 상단 11필드:

- `brand`, `product`, `job_no`, `date`
- `why_brief` — 이 브리프가 왜 필요한가(비즈니스 목표 / 어떻게 더 팔 것인가)
- `target_raw` — 누구에게 영향을 줄 것인가(현재 구매행동 포함, 생생하게)
- `the_do` — 그들이 실제로 해야 할 **행동 변화**("더 많이 산다" 금지, 구체 행동)
- `how` — 커뮤니케이션 방식: `촉구 | 알고싶게 | 결심강화 | 인식전환` 중
- `core_thought` — 핵심 생각 한 줄
- `must_know` / `must_feel` / `why_care` — 알아야/느껴야("친근·신뢰" 진부표현 금지)/관심가져야
- `success_metric` — 구매↑ / 빈도↑ / 전환 / 객단가↑ 등 측정 기준
- `mandatories` — 반드시/절대 + 채널

파생 4필드:

- `coverage_check` — Hook·Pain·Value·Offer·Urgency·CTA 6요소가 각각 어느 앵글로 커버되는지.
  **생성 전 필수 검증**(빈 요소가 있으면 진행하지 않는다).
- `segment_axis` — 팬아웃 축 택1(`lifecycle|engagement|value_fit|role|industry`).
- `anchors` — `{ character_json, product, environment }` 앵커 초기값(캐릭터 스킬이 채움).

## Rules

- **MISSING-ask 가드**: 값을 모르면 임의로 채우지 말고 해당 필드에 `"MISSING — ask"`를 넣고
  사용자에게 ≤3개 질문으로 묶어 묻는다. 브랜드 버킷(RAG)에 있으면 retrieve해서 채운다.
- `must_feel`은 "친근한/신뢰할 수 있는" 같은 진부한 표현을 금지한다. 구체적 감정 반응으로.
- `the_do`는 반드시 실제 행동. "인지도 상승" 같은 추상 목표는 `success_metric`으로 분리한다.
- 회사가 준 평가 기준·배점·필수요소가 있으면 그대로 `mandatories`에 반영한다(임의 변경 금지).
- 6요소 커버리지가 비면 스토리보드로 넘어가지 않는다 — 먼저 브리프를 보강한다.
- 숫자·실적은 버킷 근거가 있을 때만. 없으면 `측정 예정` 가드를 남긴다.
