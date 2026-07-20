---
name: allergy-check
description: 겐츠 품목 알레르기를 식약처 C002 품목제조보고(원재료)로 결정적 조회한다. LLM 추론 금지.
license: proprietary
metadata:
  agent: gentz
  visibility: corporate
  runtime: gentz-allergy
---

# 겐츠 알레르기 결정적 조회

192품목 식약처 원재료 인덱스(`data/allergen_index.json`)를 **결정적으로 룩업**한다.
전성분 텍스트를 LLM이 읽고 추론하면 안 된다 — 안전 이슈.

## 툴
- `allergy_check(품목, 사용자알레르기[])` → verdict: 위험 / 주의(불확실) / 표기상 안전 / 확인불가
- `list_safe_products(사용자알레르기[])` → 표기상 안전 품목 목록 (복합원료 품목은 보수적 제외)

## 복합원료 마스킹 (핵심 가드레일)
192품목 중 다수가 "당류가공품·빵류·유함유가공품" 등 복합원료로 표기 → 하위 알레르기가
식약처 1차 전성분에 안 드러난다. 이 경우 `복합원료마스킹=true` →
**"표기엔 없지만 제조사 확인 필요"**로 답한다. 절대 "안전"이라 단정하지 않는다.

## 출력 시 반드시
- verdict와 경고를 그대로 전달.
- 근거: "식약처 OpenAPI C002 품목제조보고(원재료)".
- 최종 판단은 제조사/의료진 확인 권고.
