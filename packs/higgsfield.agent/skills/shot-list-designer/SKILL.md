---
name: shot-list-designer
description: Lay out shots with an enum-only shot grammar (camera angle + shot size), one motivated light source per shot, mood and lens focus; use narrative scene_beat and keep ad_beat only as a sub-field when channel=ad. No free-text for enum fields.
---

# Shot-List Designer

## Goal

샷을 나열하고 각 샷에 **enum 샷 문법**(카메라 앵글·사이즈), **한 개의 motivated 광원**,
분위기, 렌즈/초점을 지정한다. enum 필드는 자유텍스트 금지(필터·재생성·QC 가능하게).

내러티브 축은 `scene_beat`를 쓴다. `channel=ad`일 때만 광고 비트를 `ad_beat` **하위 필드**로 보존한다(광고 5부 강제 아님).

샷 문법 enum은 `references/shot-grammar-extended.md`, 광원/카메라워크 분류는 `references/lighting-camera-taxonomy.md`.

## Output Contract

`shots[]` 배열(샷마다 1 객체):

```jsonc
{
  "shots": [
    {
      "n": 1,
      "scene_beat": "ESTABLISH",          // ESTABLISH|INCITE|REVEAL|ESCALATE|CLIMAX|RESOLVE|TRANSITION
      "ad_beat": null,                    // channel=ad일 때만 HOOK|AGITATE|REVEAL|PROOF|OFFER|CTA, 아니면 null
      "camera_angle": "eye-level",        // enum (references)
      "shot_size": "wide",                // enum (references)
      "composition": "인물 우측 1/3, 하단 카피 세이프, 시선 좌측",  // 명시 슬롯(자유서술 허용)
      "lighting": "window-side",          // enum/프리셋 — 광원 1개만
      "mood": "calm",                     // enum 1~2개
      "lens_focus": "35mm f/2.0 shallow DoF",
      "story": "이 컷의 동작/표정/상황(짧게)",
      "on_screen_text": "≤6 단어",        // 오버레이용, 이미지에 그리지 않음
      "duration_sec": 4
    }
  ],
  "shot_count": 8,
  "grid_layout": "2x4"                    // shot_count에 맞춰 (prompt-composer가 grid 1장 조립)
}
```

## Rules

- **enum-only**: `camera_angle`·`shot_size`·`lighting`·`mood`·`lens_focus`·`scene_beat`는
  `shot-grammar-extended.md` enum만. free-text 두면 QC/재생성 불가.
- **one-motivated-source**: 샷당 광원 1개. "studio 3-point" 남발 금지(AI티). 실용광/창측광 등 동기 있는 소스.
- **dual-axis-beat**: 상위는 항상 `scene_beat`. `ad_beat`는 `channel=ad`일 때만 채우고 그 외엔 `null`.
- **format-gate**: `director-brief`의 `aspect_ratio`·`duration_sec`가 없으면 시작하지 않는다.
- **short-discrete-shots**: 한 컷에 긴 서사 몰아넣기 금지(identity drift). 짧고 이산적으로.
- **on-screen-text ≤6 words**: 카피/로고/숫자는 이미지 생성이 아니라 후속 오버레이.
- **grid-first**: 컷 수는 grid 1장(8~12 패널)에 맞춘다. 개별 N장 생성 금지.
