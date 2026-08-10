# MEGA-ANCHOR Variants & Anti-Slop Blocks

프롬프트 일관성의 핵심. **조립 순서는 load-bearing**이다 — 순서를 바꾸면 identity가 풀린다.

## 조립 순서 (load-bearing)

```
1) [Environment Anchor]            # 공간·배경·광원 환경 (항상 먼저)
2) [Subject Anchor] wearing [Attire Anchor]   # 인물/피사체 + 의상 (2번째, 붙여서)
3) [Mood Anchor]                   # 분위기·색감 한 줄
4) [이 컷 고유 동작·mood]          # 이 컷만의 액션/표정
5) [camera_angle, shot_size, lighting preset, camera_movement + motion_intensity]
6) [REALISM_BLOCK] [NEGATIVE_PROMPT]  (+ 비디오: [VIDEO_NEGATIVE_ADD])
```

- 1→2→3은 **매 컷 동일 텍스트**(identity lock). 4→5만 컷마다 바뀐다. 6은 항상.
- 앵커는 짧고 구체적으로(예: "작은 카페 코너, 창측광" / "20대 여성 지민, 짧은 단발" / "베이지 니트").

## 변형

### 일반 연출용 (scene_beat)
- 앵커 1→3 동일. 4번 슬롯에 `scene_beat` 의도(ESTABLISH/REVEAL/ESCALATE …)에 맞는 동작을 넣는다.
- 5번에 `camera_movement`·`motion_intensity`를 반드시 포함(연출 팩 핵심 차이).

### 광고용 (channel=ad, ad_beat 하위 보존)
- 5부 비트(HOOK→CTA)는 `ad_beat` 하위 필드로만 보존하고, 프롬프트 앵커 구조는 동일.
- 제품 노출 컷에만 `[Product Anchor]`를 2번 뒤에 추가(보이는 컷에서만).

## Anti-slop 블록 (항상 첨부)

### REALISM_BLOCK
```
phone-camera look, natural light, subtle grain, real-time pace, one motivated light source, slight human imperfection
```

### NEGATIVE_PROMPT (이미지)
```
no morphing, no warping, no melting, no jelly, no extra fingers, no distorted hands,
no slow-mo blur, no plastic skin, no waxy face, no watermark, no logo, no UI text,
no 8K, no cinematic, no studio, no hyperreal, no masterpiece, no ultra-detailed
```

### VIDEO_NEGATIVE_ADD (비디오 클립 프롬프트에 추가)
```
no camera teleport, no identity drift between panels
```

## 금지어 (절대 프롬프트에 넣지 않음)
`8K` · `cinematic` · `studio` · `hyperreal` · `masterpiece` · `ultra-detailed` — 왁스·플라스틱 룩 유발.

## Grid 프롬프트 템플릿 (단일 forward pass)

```
[ANCHOR 1·2·3 한 번만].
A contact-sheet storyboard grid, {grid_layout} panels, consistent character identity and same light across all panels:
panel1 {scene_beat}, {camera_angle} {shot_size}, {동작};
panel2 … ; … panel{N}.
panel dividers thin, no text inside panels, no captions.
[REALISM_BLOCK] [NEGATIVE_PROMPT]
```

- 그리드는 **1장**만 생성. 패널 안에 텍스트/캡션 금지(오버레이로 후처리).
- 그리드 전체에 동일 앵커·동일 광원을 명시해 컷 간 일관성을 확보한다.
