---
name: movement-composer
description: Assign per-shot camera movement, subject motion, motion intensity and the cut-to-cut transition as first-class fields; every shot must carry camera_movement, subject_motion, motion_intensity and transition.
---

# Movement Composer

## Goal

컷 간 **모션**(`slow_push/subtle_pan/handheld/dolly-in/push-in/orbit/rack-focus/whip` …)과
**전환**(`cut/match-cut/dissolve/whip-pan/motion-blur/smash-cut`)을 **컷 단위**로 배치한다.

`movement`는 **1급 시민**이다 — 모든 샷이 `camera_movement`·`subject_motion`·`motion_intensity`·`transition`
네 필드를 반드시 갖는다. i2v 품질은 이 명시적·제약된 모션 워딩에 좌우된다.

전환별 사용 시점·i2v 번역·드리프트 주의는 `references/transition-library.md`.

## Output Contract

`movement_plan[]` 배열(샷마다 1 객체, `shot-list-designer`의 `shots[].n`과 1:1 정렬):

```jsonc
{
  "movement_plan": [
    {
      "shot_n": 1,
      "camera_movement": "dolly-in",        // enum (아래)
      "subject_motion": "인물이 천천히 고개를 든다",  // 피사체 자체 동작(짧게)
      "motion_intensity": "moderate",       // subtle|moderate|dynamic
      "transition": "cut",                  // cut|match-cut|jump-cut|dissolve|whip-pan|motion-blur|smash-cut|fade|invisible-cut
      "i2v_prompt_snippet": "slow dolly-in toward subject, subtle parallax, locked horizon, gentle speed ramp", // ≤12단어
      "duration_sec": 4
    }
  ]
}
```

### camera_movement enum
`static` · `slow_push` · `push-in` · `pull-out` · `dolly-in` · `dolly-out` ·
`truck-left` · `truck-right` · `pan` · `subtle_pan` · `tilt` · `orbit` · `arc` ·
`crane-up` · `crane-down` · `handheld` · `steadicam` · `tracking` · `rack-focus` ·
`whip` · `dolly-zoom` · `fpv`

### motion_intensity enum
`subtle`(미세·정적에 가까움) · `moderate`(명확한 이동) · `dynamic`(빠르고 큰 이동)

## Rules

- **movement-required**: 네 필드(`camera_movement/subject_motion/motion_intensity/transition`)는
  모든 샷 필수. 누락 금지. 정적 컷도 `camera_movement: static`으로 명시.
- **intensity-budget**: `dynamic`은 전체의 약 1/3 이하. dynamic 남발은 혼란·드리프트. 정적/대비 컷을 사이에 둔다.
- **i2v-snippet ≤12 words**: 각 샷의 모션을 짧은 i2v 프롬프트 조각으로 번역해 둔다(clip-stitch가 그대로 사용).
- **transition-continuity**: `match-cut`/`whip-pan`/`invisible-cut`은 직전 샷과의 `continuity_ref`가 필요하다(드리프트 위험).
- **no-teleport**: 카메라는 물리적으로 이동 가능해야 한다. 순간이동·불연속 점프는 전환 enum으로만 표현.
- **beat-aligned**: `ESCALATE/CLIMAX`에 강한 모션, `ESTABLISH/RESOLVE`에 정적·subtle을 둬 리듬을 만든다.
