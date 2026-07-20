---
name: reels-storyboard-writer
description: Create approval-ready Korean Reels/Shorts storyboard packets with 9:16 safe areas, captions, media source choices, TTS, BGM, render constraints, and usage metering.
---

# Reels Storyboard Writer

## Goal

사용자가 준 자료를 릴스/쇼츠용 세로 템플릿 영상으로 바꾼다. 결과는 바로 렌더하지 않고, 승인 가능한 계획으로 낸다.

## Output Contract

반드시 아래 섹션을 만든다.

1. `hook_and_goal`
   - 첫 2초 훅
   - 영상에서 끝까지 남길 메시지
   - 금지할 과장 표현
2. `scene_storyboard`
   - 9:16, 1080x1920 기준
   - 장면별 duration, background_media, black_zone, caption, motion
   - 상단/하단 플랫폼 UI safe area를 침범하지 않는 caption_y
3. `media_and_caption_plan`
   - 기본 media_source는 `image_search`
   - 대체 선택지는 `upload`, `image_generation`
   - 검색 결과는 image_db에 저장할 수 있게 query, source_url, thumbnail_url, license_hint를 남긴다
   - 중앙 캡션 텍스트는 줄바꿈 가능한 길이로 제한한다
4. `audio_and_render_packet`
   - TTS voice, speech_rate, BGM mood, bgm_volume
   - render format: mp4, 1080x1920, 30fps
   - usage_metering events: llm_tokens, image_search_query, image_generation, tts_seconds, bgm_asset, render_seconds

## Rules

- 카드뉴스 4:5/1:1 레이아웃을 재사용하지 않는다.
- 텍스트는 중앙 캡션으로 두되 플랫폼 UI safe area에는 넣지 않는다.
- 이미지 생성은 기본값이 아니다. 검색 또는 업로드로 충분하면 생성하지 않는다.
- 흑백/검은 오버레이는 영상 가독성 조절 값으로만 쓰고, 배경을 가리는 장식으로 남발하지 않는다.
- 사용량은 실행 후가 아니라 각 connector 호출 시 라이브로 빠지는 것으로 기록한다.
