# Consistency Scorecard

컷별 일관성·안전 채점 기준. `pre-render`는 정적 축만, `pre-ship`은 모션 축까지 채점한다.

## 채점 축 + 가중치

| axis | weight | 채점 대상 | gate |
|------|--------|-----------|------|
| `identity` | 0.25 | 피사체/인물이 컷 간 동일한가(얼굴·의상·체형) | 둘 다 |
| `environment` | 0.15 | 배경·공간·소품이 같은 환경인가 | 둘 다 |
| `lighting` | 0.15 | 동기 있는 단일 광원이 일관되는가 | 둘 다 |
| `mood` | 0.10 | 분위기·색감이 의도와 맞는가 | 둘 다 |
| `motion_natural` | 0.15 | 모션이 자연스럽고 물리적으로 가능한가 | pre-ship만 |
| `safety` | 0.20 | 금지어·워터마크·로고·과장·identity drift 없음 | 둘 다(하드 게이트) |

`pre-render`에서 `motion_natural`은 채점하지 않고, 해당 가중치(0.15)를 나머지 정적 축에 비례 재배분한다.

## Threshold / 판정

- **pass**: `weighted ≥ 0.80` **그리고** `safety == 1.0` **그리고** 각 축 최소 `≥ 0.60`.
- **regen**: 통과 컷 외 미달 컷만 앵커 보정 재생성.
- **block**: `safety < 1.0`(금지어/워터마크/로고/identity drift) 또는 `regen_cap` 초과에도 미달.

## 미달 시 앵커 보정 규칙 (전체 프롬프트 재작성 금지)

| 미달 축 | 보정 조치 |
|---------|-----------|
| `identity` | `[Subject Anchor] wearing [Attire Anchor]` 문구를 통과 컷과 **동일 텍스트**로 통일. 캐릭터 시트 L2/L3·face-ref 고정. |
| `environment` | `[Environment Anchor]`를 통과 컷과 동일하게 맞추고 소품/배경 변경 지시 제거. |
| `lighting` | 광원 preset을 통과 컷과 동일하게 단일화. 다중 소스/색 spill 제거. |
| `mood` | `[Mood Anchor]` 한 줄을 의도에 맞게 구체화(과포화 지시 제거). |
| `motion_natural` | `motion_intensity`를 한 단계 낮추고(dynamic→moderate→subtle) `i2v_prompt_snippet`을 단순화. |
| `safety` | 즉시 `block`. 금지어/워터마크/로고 제거, drift면 앵커+continuity_ref 재설정 후에만 재검토. |

## 반복 상한
- 컷당 재생성 기본 `regen_cap = 2`. 상한 초과 미달은 `block` 처리하고 사용자에게 질문한다(루프 금지).
- 재생성은 통과 컷을 바꾸지 않고, 미달 컷의 앵커/continuity만 보정한다.
