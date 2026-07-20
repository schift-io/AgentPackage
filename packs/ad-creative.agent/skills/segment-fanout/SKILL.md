---
name: segment-fanout
description: Deterministically fan a single Ogilvy brief into N audience segments along one of five orthogonal axes, then hydrate each segment with a persona whose emotional drivers and real quotes differentiate the creative.
---

# Segment Fan-out (세그먼트 팬아웃)

## Goal

한 브리프를 여러 세그먼트(연령대/생애주기/역할 등)로 **결정적으로** 나눈다. 즉흥이 아니라
5개 직교 축 중 하나를 골라 테이블로 떨군다. 세그먼트마다 `must_feel`/`why_care`가 갈리며
연출·프롬프트·전문성·캐릭터가 분기된다.

축 정의는 `references/segment-axes.md`.

## Output Contract

`segments[]` 배열. 각 세그먼트:

```jsonc
{
  "name": "20대 첫 직장인",
  "criteria": "이 세그먼트를 식별하는 기준(관측 가능한 특성)",
  "purpose": "이 세그먼트에 대한 마케팅/메시징 목표",
  "persona": {
    "emotional_drivers": ["창피함 회피", "또래 인정"],   // ← 연출을 가르는 핵심
    "real_quotes": ["이거 나만 모르는 거 아니지?"],        // ← 타깃의 실제 어투(카피 소스)
    "motivators": ["빠른 결과", "간편함"],
    "barriers": ["가격 부담", "실패 경험"],
    "comm_prefs": { "channel": ["instagram_reels"], "tone": "구어체·짧게" }
  },
  "angles": ["identity", "social_proof"],                 // 6요소를 채울 앵글(앵글 뱅크에서)
  "must_feel_override": "세그먼트 전용 감정(브리프 must_feel을 이 세그먼트에 맞게 특화)"
}
```

## Rules

- **축은 하나만 고른다**(브리프 `segment_axis`). 여러 축을 섞으면 세그먼트가 폭발한다.
- 세그먼트 수는 기본 2~4개. 5개 초과 금지(제작·검증 비용 폭증).
- **차별화는 인구통계가 아니라 감정 드라이버·실제 어투·동기·장벽에서 온다.** 나이만 다르고
  메시지가 같으면 세그먼트를 나눈 의미가 없다.
- `real_quotes`는 타깃이 실제로 쓸 법한 말 그대로. 카피와 훅의 1차 소스다.
- 브랜드 버킷/원본 자료에 없는 행동·후기를 지어내지 않는다("현실적이지 않은 행동 금지").
- 각 세그먼트는 6요소 앵글 매핑을 따로 가진다(같은 제품, 다른 진입점).
