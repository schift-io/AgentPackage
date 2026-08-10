---
name: director-brief
description: Collect directing intent, tone, format/aspect and length (homage/style references are optional) into a structured brief state; never invent unknown values — mark required gaps "MISSING — ask" and raise at most 3 questions.
---

# Director Brief

## Goal

연출 의도·톤·레퍼런스·포맷/길이를 **구조화 state**로 수집한다. 모르는 값은 절대 지어내지
않고 해당 필드에 `"MISSING — ask"`를 쓰고, 질문은 `questions[]`에 **최대 3개**만 모은다.

샷 설계(`shot-list-designer`)로 넘어가기 전의 관문. 포맷·길이가 없으면 진행하지 않는다.

## Output Contract

브리프 객체 1개(JSON):

```jsonc
{
  "intent": "한 줄 연출 의도(무엇을 보여주고 어떤 감정을 남길지)",
  "tone": "톤/분위기 (예: 다큐·차분, 시네마틱·긴장)",
  // ★ OPTIONAL — 오마쥬·분위기·스타일·구도 참조. 없어도 진행한다(질문하지 않음).
  // 캐릭터 identity용 히어로 이미지는 여기가 아니라 characters[].reference에 넣는다.
  "references": [
    { "title": "…", "kind": "homage|style|mood|composition", "ref": "url|파일|메모", "note": "왜/어떻게 참고하는가" }
  ],
  "format": { "aspect_ratio": "9:16" },          // 9:16|1:1|4:5|16:9 (필수)
  "duration_sec": 24,                            // 총 길이(초) (필수) — 몇 초짜리 영상인지
  "per_clip_sec": 5,                             // 클립 1개 길이(초) (Seedance 계획 기본 5, Schift 가드레일 2~6)
  "channel": "ad",                               // ad|narrative|doc|music … (ad이면 ad_beat 하위 보존)
  // ★ 등장인물/캐릭터시트 슬롯 — 나와야 하는 사람/캐릭터는 반드시 여기에 넣는다.
  // 레퍼런스가 없으면 지어내지 말고 "MISSING — ask". prompt-composer의 MEGA-ANCHOR가 여기서 읽는다.
  "characters": [
    {
      "id": "char_1",
      "name": "주인공(20대 직장인)",
      "role": "hero|support|background|product",
      "identity": "외형 고정(얼굴·헤어·체형) 한 줄",          // 또는 "MISSING — ask"
      "attire": "의상 고정 한 줄",                            // 또는 "MISSING — ask"
      "reference": "히어로 레퍼런스 이미지 url|파일|메모",     // Soul-aware 이미지 생성 입력. 없으면 "MISSING — ask"
      "appears_in_shots": "all"                              // "all" 또는 [1,3,5]
    }
  ],
  "must_keep": [ "제품 로고 각도", "실제 촬영 톤" ],
  "must_avoid": [ "왁스 피부", "과장된 슬로모" ],
  // ★ 예상 비용은 brief에서 추정하지 않는다. build_higgsfield_proposal의 계획치를
  // 승인 화면에 표면화하되, 유료 생성 직전 Higgsfield cost preflight 견적을 정본으로 다시 확인한다.
  "questions": [ "MISSING — ask 항목에 대한 질문, ≤3개" ]
}
```

## Rules

- **missing-ask-guard**: 확인 불가한 값은 추측해 채우지 말고 `"MISSING — ask"`로 두고
  `questions[]`에 ≤3개로 묶는다. 질문은 진행을 막는 최소만.
- **no-invented-facts**: 레퍼런스 내용·브랜드 사실·수치·인물/제품 고유 정보를 지어내지 않는다.
  근거 없으면 MISSING.
- **format-required-before-shot**: `format.aspect_ratio`와 `duration_sec` 둘 중 하나라도 없으면
  샷 설계로 진행하지 않고 우선 질문한다(그리드 비율·컷 수가 여기서 결정됨).
- **reference-optional**: `references`(오마쥬·분위기·스타일·구도 참조)는 **완전 선택**이다.
  0개여도 질문하지 않고 `intent`만으로 진행한다. 참조가 주어지면 `kind`(homage/style/mood/
  composition)와 `note`(왜/어떻게 참고하는가)를 붙여 prompt-composer가 분위기·구도에만
  반영한다. 참조 작품의 고유 요소(로고·캐릭터 얼굴·대사·상표)는 그대로 복제하지 않는다
  (오마쥬 ≠ 복제). 캐릭터 identity용 히어로 이미지는 `references`가 아니라
  `characters[].reference`로 받는다(그쪽만 없으면 MISSING — ask).
- **enum-only-format**: `aspect_ratio`는 `{9:16, 1:1, 4:5, 16:9}` 중 하나만. 자유 비율 금지.
- **character-sheet-slot**: 화면에 등장하는 사람/캐릭터/제품이 하나라도 있으면 반드시
  `characters[]`에 `identity`·`attire`·`reference`를 채운다. `reference`(히어로 이미지)가 없으면
  지어내지 말고 `"MISSING — ask"`로 두고 `questions[]`에 "등장인물 레퍼런스 이미지가 있나요?"를
  추가한다. 이 이미지는 Soul이 `reference_id`를 만들어 일관된 패널을 생성할 때만 쓰며,
  승인된 패널 결과가 비디오 `start_image`가 된다. 이 슬롯이 비어 있으면(완전 무대/풍경만)
  그 사실을 `intent`에 명시한다.
- **no-video-character-contract**: Soul의 `reference_id`를 일반 비디오 인자로 넘기거나, 서버
  `tools/list.inputSchema`에 없는 공통 캐릭터 참조 필드를 만들지 않는다.
- **duration-drives-shot-count**: `duration_sec`(필수)와 `per_clip_sec`(기본 5, Schift 가드레일 2~6)으로
  `shot_count` 하한을 잡는다(`ceil(duration_sec / per_clip_sec)`). 사용자가 `shot_count`를 직접
  정하면 그 값을 우선한다. 2~6초는 공급자 제한이 아니라 제품 편집 가드레일이다. 길이가 없으면
  진행하지 않고 질문한다.
- **cost-not-in-brief**: 예상 비용은 brief에 쓰지 않는다. 비용 계산·표시는 승인 전
  `build_higgsfield_proposal`의 `cost_estimate`가 담당한다. 고정 단가는 계획치이며, 유료 호출 직전
  Higgsfield cost preflight 견적을 보여주고 승인받는다.
