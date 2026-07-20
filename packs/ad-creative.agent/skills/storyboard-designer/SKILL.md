---
name: storyboard-designer
description: Design an ad storyboard as a single hand-off object using the MEGA-ANCHOR prompt recipe, an enum shot grammar, and a grid-first draft (8-12 panels in one generation) with per-panel upscale only after approval.
---

# Storyboard Designer

## Goal

선택된 세그먼트의 광고 스토리보드를 만든다. 캐릭터/제품/환경 앵커를 매 컷 프롬프트 앞에
고정 concat하고, 초안은 **grid 1장**으로 뽑아 일관성과 비용을 동시에 잡는다.

샷 문법은 `references/shot-grammar.md`, AI티 제거 규칙은 `references/anti-slop-prompt-rules.md`.

## Output Contract

세그먼트당 스토리보드 객체 1개(단일 핸드오프):

```jsonc
{
  "segment": "20대 첫 직장인",
  "anchors": { "character": "…", "attire": "…", "product": "…", "environment": "…" }, // 시트에서
  "timing": "hook 0-3 / pain 3-10 / value 10-25 / offer 25-45 / cta 45-60",
  "panels": [
    {
      "n": 1,
      "beat": "HOOK",                 // HOOK|AGITATE|REVEAL|PROOF|OFFER|CTA
      "story": "이 컷의 동작/표정/상황",
      "camera_angle": "close-up",     // enum: wide|medium|close-up|extreme-close-up|bird-eye|worm-eye
      "composition": "인물 우측 1/3, 하단 여백(카피)",
      "lighting": "자연광, 부드러운 측광",
      "mood": "궁금·긴장",
      "on_screen_text": "≤6 단어",
      "image_prompt": ""              // MEGA-ANCHOR 레시피로 조립(아래)
    }
  ],
  "draft_mode": "grid",               // 초안은 grid. 승인 컷만 개별 업스케일.
  "grid_layout": "2x4"                // 패널 수에 맞춰
}
```

## MEGA-ANCHOR 프롬프트 레시피 (일관성의 핵심)

각 컷 `image_prompt`는 반드시 이 순서로 조립한다(앵커는 **매 컷 동일 텍스트**):

```
[Environment Anchor] [Character Anchor] wearing [Attire Anchor], [Product Anchor if visible].
[이 컷의 동작·표정·mood]. [camera_angle, shot type, composition, lighting].
[anti-slop realism block + negative prompt]
```

- **항상** 환경 앵커로 시작 → 캐릭터+의상 앵커 → (제품 노출 시) 제품 앵커 → 그다음에야 이 컷 고유 내용.
- 앵커는 컷마다 바꾸지 않는다(스크립트가 의상 변경을 명시할 때만 예외).

## Rules (grid-first)

- **초안은 grid 1장**: 8~12 패널을 하나의 생성으로 뽑는다. 단일 forward pass라 캐릭터가 물리적으로
  동일하고 비용도 1장분(예: ~28원)이다. 개별 12장 생성(~340원) 금지.
- 승인 후 **선택된 컷만** 개별 고해상 재생성/업스케일(레퍼런스+seed 유지).
- 샷 필드는 free-text 금지, `shot-grammar.md`의 enum만 사용(필터·재생성 가능하게).
- 컷은 짧고 이산적으로. 한 프롬프트에 긴 서사 몰아넣기 금지(identity drift).
- `on_screen_text`는 ≤6 단어. 텍스트 레이어는 이미지 생성이 아니라 후속 오버레이로 얹는다.
- timing/beat는 5부 구조 고정: Hook 0-3 → Pain 3-10 → Value 10-25 → Offer 25-45 → CTA 45-60.
- 매 컷 anti-slop 블록을 붙인다(8K/cinematic/masterpiece 금지, 폰카 룩+그레인, negative prompt).
