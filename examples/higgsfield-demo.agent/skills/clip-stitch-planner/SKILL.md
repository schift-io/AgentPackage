---
name: clip-stitch-planner
description: Plan one imgs2vid clip per approved panel via the OAuth Higgsfield MCP (source panel, motion, Schift 2-6s edit guardrail, model) plus stitch order/transitions/fps/output. Default model seedance_2_0 at 5 seconds; live tools/list inputSchema and cost preflight remain authoritative. Clips stay disabled until panels are approved.
---

# Clip-Stitch Planner

## Goal

**승인된 패널별** imgs2vid 클립 계획(소스 패널·모션·길이·모델)을 세우고, 스티치 순서/전환/fps/출력 스펙을 정한다.

실행은 **Higgsfield 공식 MCP**(`https://mcp.higgsfield.ai/mcp`)로 통합한다. 이 엔드포인트는
OAuth 인증이 필요한 Streamable HTTP이며, 런타임은 인증된 `tools/list`에서 현재 도구 이름과
`inputSchema`를 읽은 뒤 그 계약에 맞는 인자만 보낸다.

- 기본 모델: `seedance_2_0`, 기본 길이 5초.
- 공식 CLI에서 확인된 대안 ID: `kling3_0`, `minimax_hailuo`, `veo3_1`. 이 ID가 MCP의 모든
  생성 도구에서 같은 필드로 전달된다고 가정하지 않고, 실행 시 서버 스키마를 따른다.
- 클립 길이: Schift 편집 가드레일은 **2~6초**다. 이는 공급자 최대 길이가 아니며, 모든 클립은
  패널 승인 전까지 `enabled=false`다.
- 인물 일관성이 필요하면 Soul에서 얻은 `reference_id`를 Soul-aware 이미지 생성에 사용한다.
  승인된 결과 패널 URL은 먼저 `media_import_url`로 import하고, 반환된 `media_id`를
  `generate_video.params.medias[]`의 `{value, role: "start_image"}`로 전달한다. 일반 비디오용 캐릭터 학습 도구 또는
  캐릭터 참조 필드 계약은 만들지 않는다.
- 고정 USD/초 값은 계획 비교용이다. 유료 호출 직전 서버 비용 preflight 견적을 보여주고 승인받는다.

모델별 제약·리트라이 가드레일은 `references/imgs2vid-constraints.md`.

## Output Contract

```jsonc
{
  "clip_plan": [
    {
      "shot_n": 1,
      "source_panel_ref": "panel:1",        // 승인된 txt2img 패널 참조(첫 프레임)
      "motion": "slow dolly-in toward subject, subtle parallax, locked horizon",  // movement_plan.i2v_prompt_snippet
      "duration_sec": 5,                    // 기본 5, Schift 제품 가드레일 2~6
      "model": "seedance_2_0",              // 공식 CLI ID. 실행 인자는 live inputSchema로 확정
      "aspect_ratio": "9:16",
      "image_continuity": {
        "soul_reference_id": "soul-ref:char_1", // Soul-aware 패널 생성에만 사용(없으면 null)
        "approved_panel_ref": "panel:1"          // 비디오 start_image가 될 승인 결과물
      },
      "enabled": false                      // 패널 승인 전까지 false — 승인 후에만 true
    }
  ],
  "stitch_plan": {
    "order": [1, 2, 3, 4, 5],
    "transitions": ["cut", "cut", "match-cut", "cut", "dissolve"],  // order[i]→order[i+1]
    "fps": 24,
    "output": { "width": 1080, "height": 1920, "fps": 24, "format": "mp4/h264" }
  }
}
```

### 출력 해상도 기본값 (aspect별)
| aspect | width×height |
|--------|--------------|
| `9:16` | 1080×1920 |
| `1:1`  | 1080×1080 |
| `4:5`  | 1080×1350 |
| `16:9` | 1920×1080 |

`fps` 기본 24(시네마틱), 소셜은 30. `format` 기본 `mp4/h264`.

## Rules

- **approval-gate**: `enabled`는 패널 승인 전까지 `false`. 승인 전 생성·모델 호출 0(NO-spend).
- **duration-2-6**: Seedance 계획 기본은 5초다. 2~6초 제한은 Schift 편집 가드레일이며,
  공급자 제한으로 표현하지 않는다. 6초를 넘는 샷은 계획 단계에서 분할한다.
- **model-route**: 기본 `seedance_2_0`, 대안은 `kling3_0`/`minimax_hailuo`/`veo3_1`이다.
  실제 모델 필드·허용값·도구 이름은 인증된 `tools/list.inputSchema`를 따른다.
- **continuity-carry**: `image_continuity`는 이미지 생성 단계의 로컬 계획 정보다. Soul의
  `reference_id`는 Soul-aware 이미지 생성에만 쓰고, 승인된 패널만 비디오 `start_image`로 넘긴다.
- **no-invented-character-field**: 서버 스키마에 없는 캐릭터 학습·참조·연속성 필드를
  비디오 호출에 추가하지 않는다.
- **cost-preflight**: 문서 단가는 계획치다. 유료 생성 전에 공급자 preflight 견적을 정본으로
  보여주고 승인받으며, 승인 전에는 유료 호출을 하지 않는다.
- **motion-from-plan**: `motion`은 `movement_plan[].i2v_prompt_snippet`을 그대로 사용(재작성 금지).
- **retry-guard**: 실패 시 최대 2회 리트라이, 동일 파라미터 반복 실패면 루프 멈추고 질문(상세는 constraints).
