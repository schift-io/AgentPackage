---
name: cardnews-style-hub
description: 마케터가 생성한 카드뉴스/포스터 HTML을 카드뉴스 스타일 허브로 열어 브랜드 키트와 레이어를 시각적으로 편집할 수 있게 한다. 카드뉴스/포스터 산출물 완료 후 사용.
---

# 카드뉴스 스타일 허브 연결 (Cardnews Style Hub)

> 핵심: **카드뉴스/포스터는 생성이 끝나면 스타일 허브에서 브랜드 키트와 개별 레이어를 다듬는다.**
> 텍스트, 색상, 폰트, 위치를 1080×1080(또는 1080×1350) 캔버스 위에서 직접 조정하고, PNG/JPG로 낼 수 있다.

## 언제 사용하는가

- 마케터 에이전트가 **카드뉴스** 또는 **포스터** variant를 생성한 뒤, HTML 산출물을 사용자에게 보여줄 때.
- 사용자가 "디자인 수정", "색상 바꿔줘", "글자 위치 조정", "브랜드 키트 반영" 등 시각 편집을 요청했을 때.
- 브랜드 키트 변경(주조색, 보조색, 폰트, 로고 텍스트) 후 카드뉴스/포스터를 다시 렌더링해야 할 때.

> 블로그, 스레드, 링크드인 글은 이 스킬을 사용하지 않는다.

## 라우팅 방법

생성된 카드뉴스/포스터 HTML을 `/v1/cardnews/style-hub/session`에 POST로 별도 세션을 만든다.

### 요청

```http
POST /v1/cardnews/style-hub/session
Content-Type: application/json
```

```json
{
  "variant_id": "cardnews",
  "brand_kit": {
    "brand_name": "Room821",
    "key_color": "#315C8A",
    "colors": {
      "secondary": "#C8FF1A",
      "accent": "#FF4D00"
    },
    "fonts": {
      "heading": "Pretendard",
      "body": "Pretendard"
    }
  },
  "section_results": [
    {
      "agent_id": "cardnews-writer-agent",
      "sections": [
        {"id": "1", "title": "훅", "bullets": [{"claim": "...", "details": ["..."]}]}
      ]
    }
  ],
  "html": "<!doctype html>...",
  "source": "marketer/cardnews"
}
```

### 필드 우선순위

- `html`이 있으면 HTML을 파싱해 에디터 레이어로 변환한다.
- `section_results`가 있으면 섹션 구조를 에디터 레이어로 변환한다.
- `brand_kit`이 있으면 에디터 브랜드 팔레트를 채운다. 없으면 기본값으로 열린다.
- `variant_id`는 `"cardnews"` 또는 `"poster"`를 권장한다.

### 응답

```json
{
  "kind": "cardnews_style_hub_session",
  "brand": {
    "name": "Room821",
    "logoText": "Room821",
    "primary": "#315C8A",
    "secondary": "#C8FF1A",
    "accent": "#FF4D00",
    "headingFont": "Pretendard",
    "bodyFont": "Pretendard"
  },
  "layers": [
    {
      "id": "layer-1",
      "name": "헤드라인",
      "type": "text",
      "role": "headline",
      "x": 80,
      "y": 120,
      "w": 920,
      "h": 160,
      "opacity": 1,
      "hidden": false,
      "locked": false,
      "text": "...",
      "fontSize": 72,
      "weight": 800,
      "color": "#FFFFFF",
      "background": "transparent"
    }
  ],
  "variant_id": "cardnews",
  "style_contract": {},
  "card_size": "1080x1080"
}
```

## 사용자 안내

- 스타일 허브에서는 **브랜드 키트 패널**에서 색상/폰트를 바꾸면 전체 카드에 일괄 적용된다.
- **레이어 패널**에서 개별 텍스트 박스를 선택해 직접 이동·크기 조정·텍스트 수정할 수 있다.
- 캔버스는 1080×1080(포스터/정방형 카드뉴스) 또는 1080×1350(세로 카드뉴스) 픽셀 기준. 안전 여백(safe margin)을 확인하며 편집한다.
- 낼 때는 클라이언트 PNG/JPG 익스포트를 먼저 시도하고, 브라우저 환경이 제한적이면 `/v1/cardnews/style-hub/render`로 서버 렌더링을 fallback으로 사용한다.

## 서버 렌더 fallback

브라우저 익스포트가 불가능할 때 `POST /v1/cardnews/style-hub/render`를 호출한다.

```json
{
  "brand": { ... },
  "layers": [ ... ],
  "format": "png"
}
```

응답:

```json
{
  "format": "png",
  "data_url": "data:image/png;base64,..."
}
```

## 규칙

- 카드뉴스/포스터 산출물이 완성된 다음에만 스타일 허브로 연결한다. 중간 초안 단계에서는 링크만 안내하지 않는다.
- `brand_kit`는 세션에 제공된 값을 그대로 전달한다. 제공되지 않은 로고·색상·폰트는 지어내지 않는다.
- HTML이 없고 `section_results`만 있어도 세션을 만들 수 있다. 이 경우 에디터가 구조를 먼저 보여주고 사용자가 내용을 채운다.
- `source` 필드는 `"marketer/cardnews"` 또는 `"marketer/poster"`로 남겨 추적한다.
