---
name: ad-qc
description: Gate ad creative before render and before ship. Run the 17-point creative scorecard and a vision-based consistency scorer (product 50 / character 30 / environment 20), then regenerate only the failing panels.
---

# Ad QC (스코어카드 + vision 일관성 게이트)

## Goal

광고를 **렌더 전**과 **출시 전** 두 번 채점한다. 부실한 컷은 전체 재생성이 아니라 **해당 컷만**
앵커를 보정해 다시 뽑는다.

17점 스코어카드 상세는 `references/scorecard-17.md`.

## 두 게이트

### 1. 크리에이티브 스코어카드 (17점, 전략·카피)
`references/scorecard-17.md`의 11개 항목 채점. 임계값:
- **15~17 ship** / 12~14 solid(보완 권장) / 9~11 rework / <9 근본 재작업.
- 6요소 커버리지(Hook/Pain/Value/Proof/Offer/Urgency/CTA)가 비면 자동 rework.

### 2. Vision 일관성 스코어러 (0.0~1.0, 이미지)
grid 초안/최종 프레임을 vision 모델에 base64로 던져 채점. **광고용 가중치**:
- **제품 충실도 50% + 캐릭터 30% + 환경 20%** (표준 스토리보드의 캐릭터60/환경40을 광고용으로 재조정).
- 루브릭: 1.0 동일 · 0.8~0.9 경미 · 0.5~0.7 눈에 띔 · 0.1~0.4 큰 drift · 0.0 식별 불가.
- **임계값 0.7 게이트**: 미달 컷은 `consistency_issues`를 앵커 텍스트/레퍼런스에 반영해 그 컷만 재생성.

## Output Contract

```jsonc
{
  "scorecard": { "total": 16, "breakdown": { "hook": 2, "pain": 2, "value": 2, "proof": 2, "offer": 1, "urgency": 1, "cta": 2, "differentiation": 1, "emotion": 1, "platform_fit": 1, "culture_fit": 1 }, "verdict": "ship" },
  "consistency": { "overall": 0.82, "per_panel": [ { "n": 1, "score": 0.9 }, { "n": 4, "score": 0.55, "issues": ["의상 색 drift"], "action": "regenerate" } ], "weights": { "product": 0.5, "character": 0.3, "environment": 0.2 } },
  "regenerate_panels": [4]
}
```

## Rules

- 두 게이트를 **모두** 통과해야 승인 화면으로 넘긴다.
- 재생성은 **미달 컷만**. 통과 컷은 건드리지 않는다(비용·drift 방지).
- vision 스코어러 실패(에러)는 run을 죽이지 말고 `overall: null`로 두고 사람 확인으로 에스컬레이트.
- 스코어러가 지적한 이슈는 반드시 앵커에 반영 후 재생성(같은 프롬프트 반복 금지 — 무한 루프).
- 재생성 상한(예: 컷당 2회) 두고, 초과하면 사용자에게 앵커/레퍼런스 교체를 제안한다.
