---
name: director-qc
description: Score per-cut consistency (subject identity, environment, light source) and safety (banned words, watermark, exaggeration); regenerate only failing cuts with anchor correction, capped. Runs twice — pre-render and pre-ship.
---

# Director QC

## Goal

컷 **일관성**(피사체 identity·환경·광원·분위기·모션 자연스러움)과 **안전**(금지어·워터마크·과장)을 채점하고,
**미달 컷만** 앵커 보정으로 재생성한다(반복 상한). 게이트는 **두 번**: `pre-render`(i2v 전) / `pre-ship`(stitch 후).

채점 축·가중치·threshold·보정 규칙은 `references/consistency-scorecard.md`.

## Output Contract

```jsonc
{
  "qc_report": {
    "gate": "pre-render",                 // pre-render | pre-ship
    "shot_scores": [
      {
        "shot_n": 1,
        "identity": 0.9,                  // 0.0~1.0
        "environment": 0.85,
        "lighting": 0.8,
        "mood": 0.9,
        "motion_natural": null,           // pre-ship에서만 채점(pre-render는 null)
        "safety": 1.0,                    // 하드 게이트(1.0 아니면 block)
        "weighted": 0.86,
        "pass": true
      }
    ],
    "failed_shots": [3],
    "anchor_fixes": [
      { "shot_n": 3, "fix": "[Attire Anchor] 문구를 다른 컷과 동일하게 통일", "reason": "identity 0.55 < 0.6" }
    ],
    "regen_count": 1,
    "regen_cap": 2,
    "decision": "regen"                   // pass | regen | block
  }
}
```

## Rules

- **two-gates**: `pre-render`(i2v 전, 정적 일관성·안전)과 `pre-ship`(stitch 후, 모션 자연스러움 포함) 둘 다 실행.
- **regen-only-failed**: threshold 미달 컷만 재생성. 통과 컷은 건드리지 않는다(비용·드리프트 최소화).
- **anchor-correction**: 전체 프롬프트를 다시 쓰지 말고 **앵커/continuity_ref를 보정**해 고친다(identity lock 우선).
- **regen-cap**: 컷당 재생성 기본 상한 2회. 상한 초과에도 미달이면 `decision: block` + 사용자에게 질문.
- **safety-hard-block**: 금지어·워터마크·로고·identity drift가 발견되면 가중 점수와 무관하게 `block`.
- **no-spend-before-approval**: pre-render 이전엔 모델 호출 0. 재생성도 승인 범위 내에서만.
