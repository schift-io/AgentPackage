---
name: prompt-composer
description: Assemble each panel's image_prompt by concatenating a fixed MEGA-ANCHOR ([Environment][Subject][Attire][Mood]) in front of the shot-unique action, camera/lighting/movement and realism+negative blocks; anchor text is identical across cuts. Also builds the single grid prompt.
---

# Prompt Composer

## Goal

**MEGA-ANCHOR 변형 레시피**로 매 패널 프롬프트 앞에 `[환경][피사체][의상][분위기]` 앵커를 concat하고,
그 뒤에 `[이 컷 고유 동작·mood] [camera_angle, shot_size, lighting, movement] [realism + negative]`를 붙인다.

앵커 텍스트는 **매 컷 동일**하다(의상 변경을 스크립트가 명시할 때만 예외). grid 1장 프롬프트도 여기서 조립한다.

레시피 순서·변형·anti-slop 블록은 `references/mega-anchor-variants.md` (순서는 load-bearing).

## Output Contract

`shot-list-designer`의 `shots[]` 각 항목의 `image_prompt`를 채우고, `grid_prompt` 1개를 추가한다:

```jsonc
{
  "panels": [
    {
      "n": 1,
      "image_prompt": "[Env] [Subject] wearing [Attire], [Mood anchor]. [이 컷 동작·mood]. [camera_angle, shot_size, lighting, movement]. [REALISM_BLOCK] [NEGATIVE_PROMPT]"
    }
  ],
  "grid_prompt": "[ANCHOR once] A contact sheet storyboard grid 2x4, panels: [shot1 beat+camera] … [shot8 …]. consistent identity, same light across panels. [REALISM_BLOCK] [NEGATIVE_PROMPT]",
  "draft_mode": "grid",
  "clip_mode": "per_panel_i2v"
}
```

## 조립 순서 (load-bearing — 바꾸지 말 것)

```
[Environment Anchor] [Subject Anchor] wearing [Attire Anchor], [Mood Anchor].
[이 컷 고유 동작·mood].
[camera_angle, shot_size, lighting preset, camera_movement + motion_intensity].
[REALISM_BLOCK] [NEGATIVE_PROMPT]   (+ 비디오: [VIDEO_NEGATIVE_ADD])
```

## Rules

- **anchor-first-identical**: 항상 환경 → 피사체+의상 → 분위기 앵커로 시작하고, 앵커 문구는 컷마다 바꾸지 않는다(identity lock).
- **shot-unique-after**: 앵커 다음에야 이 컷 고유 동작·mood를, 그다음 카메라/라이팅/무브먼트 enum을 둔다.
- **realism-negative-always**: 모든 컷에 `REALISM_BLOCK` + `NEGATIVE_PROMPT`를 붙인다.
  비디오로 갈 패널에는 `VIDEO_NEGATIVE_ADD`("no camera teleport, no identity drift between panels")를 추가.
- **grid-single**: 8~12 패널을 **grid 1장** 프롬프트로 조립한다(단일 forward pass). 패널별 N개 프롬프트로 개별 생성 금지.
- **no-in-image-text**: 카피·로고·숫자를 이미지 안에 그리지 않는다(오버레이로 후처리). `on_screen_text`는 별도 필드.
- **anti-slop-words**: `8K/cinematic/studio/hyperreal/masterpiece/ultra-detailed` 금지어를 절대 넣지 않는다.
