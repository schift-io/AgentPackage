---
name: character-sheet
description: Build a per-segment character sheet as a 3-layer identity lock (JSON character sheet + hero reference image + native face-reference) plus a fixed product anchor, so the same character stays on-model across every storyboard frame.
---

# Character Sheet (3중 identity lock)

## Goal

스토리보드 컷마다 인물이 딴사람이 되는 걸 막는다. 세그먼트당 캐릭터를 **한 번** 정의하고,
그 정의를 모든 프레임에 고정한다. "JSON은 *무엇인지*를, 레퍼런스는 *어떻게 보이는지*를
말한다 — 둘 다 쓴다."

## Output Contract

세그먼트당 `character_sheet` 1개(+ 제품 노출 시 `product_anchor`):

```jsonc
{
  "segment": "20대 첫 직장인",
  "identity_json": {                    // L1: 툴 사이를 넘어다녀도 안 깨지는 구조화 시트
    "age_range": "25-29", "gender": "female",
    "ethnicity": "Korean",
    "face": { "shape": "", "eyes": "", "eyebrows": "", "nose": "", "lips": "", "skin_tone": "" },
    "hair": { "color": "", "length": "", "style": "" },
    "distinctive_marks": [],
    "persona_note": "또래 같은 사람. 모델처럼 완벽하지 않게."
  },
  "attire_anchor": "오버사이즈 니트, 데님, 흰 스니커 (색·소재·상태 고정)",
  "hero_reference": {                   // L2: 매 프레임 image-conditioning으로 주입
    "image_url": "", "note": "정면·깨끗한 1장. 이후 모든 생성의 레퍼런스."
  },
  "face_reference_feature": "native",   // L3: 모델의 face-ref 기능(Grok/Nano Banana ref 등)
  "environment_anchor": "자연광의 깨끗한 한국 오피스/카페 (건축·소품·색·조명 고정)"
}
```

제품 앵커:

```jsonc
{ "product_anchor": { "logo": "", "packaging": "", "color": "", "note": "제품 노출 컷은 실제 제품 픽셀에서 시작. text-to-image로 제품을 '그리지' 말 것." } }
```

## Rules (3중 lock)

- **L1 identity_json** = 얼굴/피부/헤어/특징을 구조화 JSON으로. 프레임 프롬프트의 캐릭터 앵커
  텍스트는 이 JSON에서 파생한다. identity + attire를 분리해 둔다(의상은 스크립트가 명시할
  때만 바꾼다).
- **L2 hero_reference** = 정면 깨끗한 1장을 만들어 이후 **모든** 생성에 레퍼런스로 재주입한다.
- **L3 face-reference** = 모델 네이티브 기능(레퍼런스 이미지/고정 seed)을 켠다. 텍스트 반복만으로
  버티지 않는다 — 레퍼런스+seed가 프롬프트 반복을 이긴다.
- **세그먼트당 캐릭터가 다르면** 시트를 세그먼트 수만큼 만든다(20대 인물 ≠ 40대 인물). 캐릭터를
  공유하는 캠페인이면 시트 1개를 모든 세그먼트가 공유한다.
- **제품 일관성**은 캐릭터 일관성과 같은 원리: 제품이 선명히 보이는 컷은 실제 제품 픽셀을 담는다.
- 캐릭터는 "모델"이 아니라 세그먼트 페르소나의 **또래**로. 감정 드라이버에 맞춘다.
- 앵커 텍스트/레퍼런스는 브랜드 버킷의 톤·연출 워딩을 반영한다.
