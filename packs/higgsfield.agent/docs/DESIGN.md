# Higgsfield Directing Pack — 설계안 (v0.1)

> [txt2img]: storyboard + movement → [imgs2vid]
> 오픈 연출 RAG 버킷을 근거로, Gemini 계열 가장 싼 이미지 모델로 스토리보드 grid 초안을 뽑고,
> 승인된 패널만 image-to-video로 짧은 클립화해 이어 붙이는 연출 전용 APM 팩.

## 1. 목표와 비목표

**목표**
- "연출 워딩 + 그 모든 요소(광원·카메라워크·분위기·무브먼트·앵커)"를 **오픈 RAG 버킷**에 적재하고, 스토리라인을 짤 때 그 지식을 근거로 쓴다.
- Unity로 만들어 전달하듯, 연출을 **프롬프트 + 시각화(grid)** 로 표현해 사람이 승인한다.
- 비용: 초안은 **grid 1장**(단일 forward pass = 일관성 + 최저비용), 클립화는 **승인 패널만**.
- 파이프라인: `[txt2img] storyboard+movement → [imgs2vid] clip → stitch`.

**비목표**
- 광고 5부 구조(Hook→CTA) 강제하지 않는다(그건 `ad-creative` 팩).
- Remotion 템플릿 합성(`reels` 팩)을 대체하지 않는다. higgsfield는 **생성형 i2v**다.
- 회사/브랜드 고유 사실을 담지 않는다(그건 `SCHIFT_COMPANY_RAG_BUCKET`).

## 2. 핵심 결정 (요약)

| 항목 | 결정 | 근거 |
|---|---|---|
| 팩 id | `higgsfield` | 사용자 지정 명명 |
| 버킷 | **전용 레퍼런스 버킷** `higgsfield-directing` (`bucket_role: directing_reference`, Schift-org 소유) | 회사 `default`도, 세션 메모리도 아님. `kr-labor-law-reference`·`accounting-kr-tax-reference`와 같은 계층. AGENTS.md "Agent Hub RAG Bucket Rule" 준수. |
| txt2img | `gemini-3.1-flash-lite-image` | 사용자 요구 "Gemini 쪽 제일 싼 이미지 생성기". grid draft 1장. 문서 단가는 계획치이며 생성 전 견적을 재확인한다. |
| imgs2vid | 기본 `seedance_2_0`, 기본 길이 5초 | Higgsfield 공식 CLI ID. Schift는 2~6초를 편집 가드레일로 적용하며 공급자 한계로 표현하지 않는다. |
| i2v 대안 | `kling3_0`, `minimax_hailuo`, `veo3_1` | 공식 CLI ID만 미리 알고, 실제 도구·모델 필드·허용값은 인증된 `tools/list.inputSchema`를 따른다. |
| Higgsfield MCP | OAuth Streamable HTTP (`https://mcp.higgsfield.ai/mcp`) | 런타임이 인증 후 동적으로 도구를 조회한다. 정적 도구명·인자 계약을 만들지 않는다. |
| pipeline | `react` | 에디터 루프 + 툴(RAG·txt2img·i2v), `sub_agent_plan=[]`. ad-creative와 동일. |
| owner | 공용 (`owner_org_id=""`) + `feature_flag="higgsfield"` | 범용 연출 지식, org-specific 데이터 없음. reels와 동일 게이팅. |
| 승인 | 3단: pre-spend → post-grid 패널 선택 → pre-ship | spend 전 결정적 NO-spend proposal. 고정 단가가 아니라 호출 직전 provider cost preflight 견적이 정본. |

## 3. RAG 버킷 콘텐츠 온톨로지

원칙: **enum 우선·free-text 최소화**. 모든 청크는 패널/클립 프롬프트에 **그대로 붙여넣을 수 있는 형태**(그라운딩이 쿼리당 top_k=4·4000자만 주입하므로 청크가 곧 페이로드).

| `kind` | 무엇을 | 형태 | 왜 |
|---|---|---|---|
| `shot_grammar` | 샷 사이즈·앵글·구도 enum + 용도 | enum 표 + 1줄 용도 (`ad-creative` shot-grammar 확장) | 필터·재생성·QC 가능 |
| `camera_movement` | 무브먼트를 **1급 시민**으로: `static/pan/tilt/dolly-in/out/truck/push-in/pull-out/orbit/crane/handheld/rack-focus/whip/dolly-zoom/tracking/steadicam/fpv` + `motion_intensity(subtle/moderate/dynamic)` | enum + "i2v에서 어떤 모션으로 번역되는가" 1줄 | i2v 품질은 명시적·제약된 모션 워딩에 좌우 (ad-creative에 없는 핵심 차이) |
| `lighting_preset` | 동기 있는 단일 광원 프리셋(창측광/자연광/제품 스포트/골든아워/네온 실용광) | `prompt_snippet` + `negative` 쌍 | "studio 3-point" 남발(AI티) 방지, 컷 간 조명 일관성 |
| `mood_grade` | 분위기·색감(`teal-orange low-key`, `warm tungsten`, `desaturated documentary`) | 이름 + 1줄 + 주의(과포화 금지) | 감정 드라이버와 정렬 |
| `lens_focus` | 초점거리·피사계심도·랙포커스(`35mm, f/2.0 shallow DoF`) | 짧은 사양 문자열 + 용도 | 시네마틱/다큐 톤 결정 |
| `anchor_template` | 캐릭터·의상·환경 **MEGA-ANCHOR 재사용 조각** | `[Env] [Character] wearing [Attire]` 슬롯 + 채우기 규칙 | 매 컷 동일 텍스트 concat → identity lock |
| `edit_rhythm` | 전환: `cut/match-cut/dissolve/whip-pan/motion-blur/smash-cut`, 비트→`duration_sec` 매핑 | enum + "언제 쓰는가" | 클립 체인 시 전환 일관·드리프트 억제 |
| `negative_anti_slop` | 금지어 + 이미지/비디오 negative + realism 블록 | 항상 첨부 문자열 블록 | 비디오 전용(`no camera teleport, no identity drift between panels`) 추가 |
| `composition_recipe` | 1/3 배치·여백(카피 자리)·시선·전/배경 | 자유서술이되 명시적 슬롯 | 채널별 세이프 영역·오버레이 공간 |
| `channel_aspect` | `9:16/4:5/1:1/16:9` + 채널 매핑 + grid 배치 규칙 | enum + 매핑 표 | 그리드 패널 안 각 컷 비율 유지 |

### 청크 스키마 (검색 최적화 단일 청크)

```jsonc
{
  "chunk_id": "hf-mv-dolly-in-001",
  "title": "Dolly-in push-in — 접근하며 긴장 고조",
  "kind": "camera_movement",
  "summary": "피사체를 향해 천천히 밀고 들어가 긴장·집중. hook/reveal/escalate에 강함.",
  "prompt_snippet": "slow dolly-in push-in toward subject, subtle parallax, locked horizon, 24fps cinematic motion, gentle speed ramp",
  "negative": "no camera teleport, no whip unless specified, no morphing, no melting, no identity drift, no warping, no extra fingers, no plastic skin, no watermark, no logo, no UI text",
  "tags": {
    "camera_angle": ["medium", "close-up"],
    "movement": ["dolly-in", "push-in"],
    "motion_intensity": "moderate",
    "lighting": ["motivated single source", "natural side light"],
    "mood": ["tension", "focus", "anticipation"],
    "lens": ["35mm", "shallow-dof"],
    "beat": ["HOOK", "REVEAL", "ESCALATE"],
    "aspect_ratio": ["9:16", "16:9"]
  },
  "use_when": "인물 접근·제품 공개·긴장 고조. 정적 컷 다음에 배치해 대비.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "phone-camera look, natural light, subtle grain, real-time pace",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://movement/dolly-in-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```

`summary`+`tags`로 임베딩 매칭, `prompt_snippet`+`negative`가 주입 페이로드, `metadata.source_id/chunk_id`로 S5 3-tier 메모리(`memory_context.conclusion_boost`)가 useful/noisy 재정렬할 때 안정 식별자. Schift 예약/정책 메타데이터 키와 충돌시키지 않는다.

### retrieval_queries 전략

- flat 8개 고정은 비용/노이즈(cheongchangsa 선례: "flat은 두지 않는다"). **코어 ≤6 flat + 핸들러가 씬의 `beat`/`scene_type`/`channel`로 2~4개 고르는 동적 선택**(총 ≤ 8, `MAX_QUERIES=8` 상한).
- 코어 예시: `higgsfield 샷 문법 enum`, `higgsfield anti-slop 금지어 negative`, `higgsfield MEGA-ANCHOR 앵커 템플릿`.
- 비트별 예시: `HOOK hook close-up push-in`, `REVEAL product rack-focus orbit spot`, `ESCALATE tension dolly-in handheld dynamic low-key`, `transition match-cut whip-pan continuity identity lock`.

## 4. ad-creative `shot-grammar.md` 재사용/확장

**재사용(그대로):** enum·free-text 금지, `camera_angle/lighting/mood/composition/aspect`, MEGA-ANCHOR concat 순서, realism+negative 상시 첨부, 이미지 내 텍스트 금지(오버레이), **grid-first 초안**(8~12 패널 1회 → 승인 컷만).

**확장(차이):**
- 광고 5부 → **일반 연출 이중축**: 기존 `beat`은 `channel=ad`일 때 `ad_beat`로 하위 보존, 상위에 내러티브 `scene_beat`(`ESTABLISH/INCITE/REVEAL/ESCALATE/CLIMAX/RESOLVE/TRANSITION`) 추가.
- 고정 타이밍(`0-3/…/45-60`) 제거 → 패널별 `duration_sec` + `edit_rhythm`.
- **`movement` 1급 승격**: `camera_movement/subject_motion/motion_intensity/transition`을 필수 enum 필드로, 패널 프롬프트 `[camera…]` 슬롯에 movement 강제. 비디오 전용 anti-slop 상시 추가.
- **연속성 블록**: 인물 일관성이 필요하면 Soul `reference_id`를 Soul-aware 이미지 생성에만 써서
  패널을 만든다. 사람이 승인한 패널 결과를 비디오 `start_image`로 넘기며, 일반 비디오용
  캐릭터 참조 필드는 가정하지 않는다.
- 출력 객체는 `storyboard-designer` 단일 핸드오프를 상속하되 `panels[]`에
  `camera_movement/subject_motion/motion_intensity/duration_sec/transition/image_continuity`를 추가한다.
  `image_continuity`는 이미지 단계의 로컬 계획 정보이며 MCP 비디오 인자로 그대로 전달하지 않는다.

## 5. 버킷 위치 결정 — 전용 레퍼런스 버킷

- **세션 메모리 불가**: 장수명·크로스세션 정규 레퍼런스. 규칙 "canonical company facts를 세션 메모리에 쓰지 말 것". 그라운딩은 검색 결과를 `source_document:reference:` 세션 메모리로 *복사*해 쓰되 원본은 세션 버킷 아님.
- **회사 `default` 불가**: role `company_knowledge`(회사 소개·제품 SoT·재무) 전용. higgsfield 지식은 조직 불문 **연출 공예(craft) 레퍼런스**라, `default`에 섞으면 회사 프로필 히트와 샷-문법 히트가 검색에서 경쟁. `hr-attendance README §6` "일반 원칙=이름 있는 레퍼런스 버킷 / 회사 내규=company 버킷" 분리가 정확히 이 경우.
- **정답 = `kr-labor-law-reference`·`accounting-kr-tax-reference`와 동일 계층의 전용 이름 버킷.** `rag_grounding.py`는 `bucket_id`만 있으면 role 무관하게 읽고 `bucket_role`은 계약상 허용 → 코드 변경 없이 `directing_reference` 선언 가능.

3-way 분리(운영):
- 회사/브랜드 고유 사실·캐릭터/제품 앵커 → company `default` (`company_knowledge`)
- 연출 공예 온톨로지 → 전용 레퍼런스 버킷 (`directing_reference`)
- 런별 grid/패널/클립/QC·압축 요약 → 세션 메모리 (`session_memory`, `session:<uuid>`)

## 6. 팩 구조

```
apm/higgsfield.agent/
├── apm.yml
├── agent.md
├── docs/DESIGN.md            # 이 문서
└── skills/
    ├── director-brief/                 # 의도·톤·레퍼런스·포맷/길이 수집, MISSING-ask
    ├── shot-list-designer/             # 샷 나열 + enum 샷문법 + 광원 + 분위기
    ├── movement-composer/              # 컷 단위 모션/전환 배치 (1급)
    ├── prompt-composer/                # MEGA-ANCHOR 변형 + anti-slop
    ├── clip-stitch-planner/            # 승인 패널별 i2v 클립 계획 + 스티치
    └── director-qc/                    # 일관성/안전 채점, 미달 컷만 재생성
```

**skills (최소 세트, `room821/skills/higgsfield-*`)**

| id | 역할 |
|---|---|
| `higgsfield-director-brief` | 연출 의도·톤·레퍼런스·포맷/길이를 구조화 state로 수집, 모르는 값은 `MISSING — ask`로 ≤3개 질문 |
| `higgsfield-shot-list-designer` | 샷 나열 + enum 샷 문법(카메라 앵글/사이즈) + 광원(한 개의 motivated source) + 분위기, 자유텍스트 금지 |
| `higgsfield-movement-composer` | 컷 간 모션(`slow_push/subtle_pan/handheld/…`)과 전환(`cut/match/whip`)을 컷 단위로 배치 |
| `higgsfield-prompt-composer` | MEGA-ANCHOR 변형 레시피로 매 패널 프롬프트 앞에 `[환경][피사체][의상][분위기]` 앵커 concat + anti-slop |
| `higgsfield-clip-stitch-planner` | 승인 패널별 i2v 클립 계획(소스 패널·모션·길이·모델) + 스티치 순서/전환/fps/출력 스펙 |
| `higgsfield-director-qc` | 컷 일관성(피사체·환경·광원) + 안전(금지어/워터마크/과장) 채점, 미달 컷만 앵커 보정 재생성 |

## 7. AWP operation + 승인 흐름

- operation: `higgsfield-directed-video`, `contract_version: awp.higgsfield.directed_video.v1`, `approval_required: true`.
- **승인 전 proposal(NO-spend, 결정적 `build_higgsfield_proposal`)**: `brief`, `anchors`, `storyboard`(`shot_count`, `grid_layout`, `shots[]`{n, beat, camera, size, lighting, mood, story, on_screen_text, image_prompt}), `movement_plan`, `grid_draft`(mode=grid, model, images=1, prompt), `clip_plan`(per-panel i2v, enabled=false until approved), `stitch_plan`, `cost_estimate`(`source=planning_estimate_not_provider_quote`, `provider_quote_required=true`), `usage_metering`, `approval_checkpoints`, `knowledge`(bucket ref).
- **승인 후 실행**: grid 생성(txt2img 1장) → **패널 확정**(사람이 animate할 패널 선택) → i2v(승인 패널만 per-clip) → stitch(ffmpeg concat+encode) → QC(미달 컷만 앵커 보정 재생성, 반복 상한).
- **사람 확인 지점**: A. pre-spend(샷 구성·앵커·grid 1장·계획 비용) / B. post-grid(animate할 패널 + 클립 수 + provider cost preflight 최신 견적) / C. pre-ship(최종 스티치 컷·일관성·안전). 최신 견적 승인 전 유료 호출은 없다.
- **usage_metering 이벤트**: `llm_tokens`, `rag_query`(bucket=higgsfield-directing), `image_generation`(grid 1장), `imgs2vid_clip`(seconds, enabled=패널 승인 시), `stitch_render`(seconds), `image_regeneration`(QC 미달 컷만).

## 8. 실행 모듈 설계

### txt2img — 기존 재사용
- `image_service.generate_and_store` 경로 재사용, 모델은 `HIGGSFIELD_TXT2IMG_MODEL` env → `gemini-3.1-flash-lite-image` 폴백.
- `compose_panel_prompt` / `compose_grid_prompt`는 `ad_creative_image_tools.py` 동명 함수와 동형(앵커 순서 load-bearing, anti-slop strip).

### imgs2vid — Higgsfield 공식 MCP

- **transport/auth**: `https://mcp.higgsfield.ai/mcp`는 OAuth Streamable HTTP 엔드포인트다.
  런타임은 `HIGGSFIELD_MCP_BEARER_TOKEN`을 Authorization Bearer로 주입하고 MCP initialize를 수행한다.
- **도구 발견**: 인증된 `tools/list` 결과를 런타임 tool surface로 사용한다. 도구 이름·설명·
  `inputSchema`는 서버 정본이며, 정적 비디오 생성·캐릭터 학습 계약을 별도로 만들지 않는다.
- **모델 라우팅**: 계획 기본은 `seedance_2_0` 5초다. `kling3_0`, `minimax_hailuo`,
  `veo3_1`도 공식 CLI ID지만, MCP 도구의 실제 모델 필드·enum·duration/aspect 인자는 매번
  live `inputSchema`와 대조한다.
- **Schift 길이 가드레일**: 2~6초는 승인·편집 단위를 작게 유지하기 위한 제품 제한이다.
  공급자 최대 길이가 아니며, 서버 스키마가 허용하지 않는 조합은 호출하지 않는다.
- **캐릭터 연속성**: Soul이 만든 `reference_id`는 Soul-aware 이미지 생성에만 쓴다. 이 흐름으로
  만든 패널 중 사람이 승인한 결과를 비디오 생성의 `start_image`로 전달한다. 일반 비디오 도구에
  공통 캐릭터 참조 필드가 있다고 가정하지 않는다.
- **storyboard 연결**: 승인된 씬별 `{caption, motion, duration_sec}`와 패널 URL을 live 스키마에
  맞춰 매핑하고, 반환된 클립 URL을 스티치 순서대로 전달한다.
- **stitch**: ffmpeg concat+encode worker(`schift.higgsfield.ffmpeg-stitch.v1`) — reels의 Remotion과 분리. 초기에는 Remotion 합성을 재사용하는 폴백도 가능(영상=정적 패널+모션)하나, 생성형 i2v 클립 concat이 정본.

## 9. 비용 가드레일

- `build_higgsfield_proposal`의 grid·모델별 USD/초 값은 비교와 승인 범위를 위한 계획치다.
  이는 공급자 가격표나 빌링 계약이 아니다.
- 유료 생성 직전 Higgsfield cost preflight를 실행하고, 반환 견적을 정본으로 승인 화면에 보여준다.
  계획치와 다르면 새 견적을 다시 승인받는다.
- 승인 전 proposal은 유료 모델 호출 0이다. `tools/list`, 스키마 검증, 로컬 계획만 수행한다.
- 재시도·모델 변경으로 승인 비용 범위를 넘으면 자동 실행하지 않고 변경된 선택지와 견적을 먼저 보여준다.

## 10. `agent_packs.py` 등록 초안

```python
from agent_hub.higgsfield_assets import (
    HIGGSFIELD_AGENTS_MD_CONTENT, HIGGSFIELD_HIERARCHY,
    HIGGSFIELD_NON_RUNNABLE_AGENT_IDS, HIGGSFIELD_SKILL_MANIFESTS, HIGGSFIELD_TOOLS,
)

HIGGSFIELD_PACK = AgentPack(
    agent_id="higgsfield",
    name="Room821 Higgsfield Directing Agent",
    agents_md_ref="room821/higgsfield.agent/agent.md",
    agents_md_content=HIGGSFIELD_AGENTS_MD_CONTENT,
    skills=[
        "room821/skills/higgsfield-director-brief",
        "room821/skills/higgsfield-shot-list-designer",
        "room821/skills/higgsfield-movement-composer",
        "room821/skills/higgsfield-prompt-composer",
        "room821/skills/higgsfield-clip-stitch-planner",
        "room821/skills/higgsfield-director-qc",
        "room821/skills/schift-memory",
    ],
    skill_manifests=HIGGSFIELD_SKILL_MANIFESTS,
    sub_agent_plan=[],                 # react editor loop
    tools=HIGGSFIELD_TOOLS,            # txt2img builtin. RAG는 공통 기본 도구
    mcp_servers=[{
        "name": "higgsfield",
        "transport": "streamable_http",
        "url": "https://mcp.higgsfield.ai/mcp",
        "discover_tools": True,
        "auth": {
            "type": "oauth_bearer",
            "resource_metadata": "https://mcp.higgsfield.ai/.well-known/oauth-protected-resource/mcp",
            "token_env": "HIGGSFIELD_MCP_BEARER_TOKEN",
        },
        "tools": [],                  # 인증된 tools/list에서 동적 발견
    }],
    document_hierarchy=HIGGSFIELD_HIERARCHY,
    primary_skill_id="room821/skills/higgsfield-director-brief",
    non_runnable_agent_ids=frozenset(HIGGSFIELD_NON_RUNNABLE_AGENT_IDS),
    markdown_title="연출 스토리보드·클립 패킷",
    include_required_tables=False,
    markdown_artifact_title="연출 스토리보드·클립 패킷.md",
    html_artifact_title="연출 스토리보드·클립 패킷.html",
    visual_assets_enabled=True,
    html_renderer="submission",
    package_ref="room821-higgsfield-agent@0.1.1",
    pipeline="react",
    manifest_overrides={
        "name": "room821-higgsfield-agent",
        "version": "0.1.1",
        "manifest_path": "apm/higgsfield.agent/apm.yml",
        "agents": [{"id": "room821/higgsfield.agent/agent.md", "path": "apm/higgsfield.agent/agent.md"}],
        "skills": [ /* 6 skills + schift-memory */ ],
        "tools": HIGGSFIELD_TOOLS,
        "awp_operations": [{"id": "higgsfield-directed-video",
                            "contract_version": "awp.higgsfield.directed_video.v1",
                            "approval_required": True}],
        "knowledge": {"bucket_name": "higgsfield-directing",
                      "bucket_role": "directing_reference",
                      "retrieval_required": True},
    },
    hub_label="연출 스토리보드→클립",
    hub_role="오픈 연출 버킷(higgsfield-directing)에서 샷 문법·광원·카메라워크·무브먼트·앵커 템플릿을 끌어와, txt2img로 스토리보드 grid 초안을 만들고 승인된 패널만 imgs2vid로 짧게 클립화해 이어 붙입니다. 초안은 grid 1장(저비용), 승인 패널만 클립화합니다. (베타)",
    hub_inputs=["연출 의도 한 줄 — 분위기·톤·레퍼런스", "대상/포맷 — 9:16·1:1·16:9 중 택1, 길이(초)"],
    hub_output="연출 패킷 — 샷 리스트+무브먼트+MEGA-ANCHOR 변형 프롬프트, grid 초안 1장, 승인 패널 클립 계획, 최종 스티치 컷(mp4)",
    hub_review="grid 생성·패널 확정·imgs2vid·스티치 전 샷 구성·앵커·클립 수를 확인하고, 유료 생성 직전 최신 견적을 승인합니다.",
    qc_enabled=False,
    feature_flag="higgsfield",
    intake_question="이번 연출에서 먼저 할 일은 무엇인가요?",
    intake_options=["샷 리스트부터 설계", "레퍼런스·톤 먼저 잡기", "기존 샷에 무브먼트 추가"],
    owner_org_id="",                   # 공용
)
# AGENT_PACKS[higgsfield] = HIGGSFIELD_PACK
```

## 11. 미해결/확인 필요

- **전용 버킷 `bucket_id` 프로비전**: 시드 스크립트(`scripts/upload_higgsfield_rag.py`) + `knowledge/rag-sources/` 구조(hr-attendance 선례)와 `SCHIFT_KNOWLEDGE_API_KEY` 소유 org 일치.
- **MCP live 계약**: 배포 환경 OAuth 토큰으로 `tools/list`를 조회해 현재 tool name·`inputSchema`·
  모델별 duration/aspect 옵션을 확인한다. 정적 문서에 복제하지 않는다.
- **비용 preflight**: 승인 화면은 계획치를 먼저 보여줄 수 있지만, 유료 호출 직전 Higgsfield가
  반환한 최신 견적을 정본으로 재승인받는다.
- **i2v/stitch worker 바인딩**: ffmpeg stitch worker(`schift.higgsfield.ffmpeg-stitch.v1`)의 실제 엔드포인트. 초기엔 queued graceful(reels 패턴).
- **그라운딩**: 핸들러 동적 선택(소형 훅) vs 순수 선언형(코어 ≤6 flat). 1차는 코어 6 flat으로 시작.

## 12. 구현 순서(제안)

1. APM 골격: `apm/higgsfield.agent/`(apm.yml, agent.md, skills 6 + references) + `higgsfield_assets.py` + `agent_packs.py` 등록 → **허브에 팩 노출(feature flag)**.
2. txt2img 레그: `higgsfield_image_tools.py`(`compose_panel_prompt`/`compose_grid_prompt`/`generate_grid_draft` = ad-creative와 동형) + 승인 전 `build_higgsfield_proposal`.
3. imgs2vid 레그: OAuth Streamable HTTP initialize → 인증된 `tools/list` 동적 발견 → 승인 패널을
   live `inputSchema`에 맞춰 호출. 기본 계획은 `seedance_2_0` 5초이며 2~6초는 Schift 가드레일.
4. stitch worker 바인딩(ffmpeg) + 최종 mp4 산출.
5. 버킷 시드 스크립트 + `knowledge/rag-sources/` 초안(온톨로지 청크 샘플) + 테스트.
