# 차트·아키타입 확장 카탈로그 (연구 재료)

> 2026-07-15 수집. 출처: Financial Times **Visual Vocabulary**(9범주 40+ 차트), Gene Zelazny **Say It With Charts**(McKinsey, 5비교), Andrew Abela **Chart Chooser**.
> 목적: `deck_render.py`의 `TEMPLATE_RENDERERS`를 IR 한 덱 역설계 편향에서 빼고, **목적별 차트/다이어그램**을 확장하기 위한 후보 backlog.
> **이 문서는 데이터(팩 참조)일 뿐 렌더러가 아니다.** 실제 함수 추가는 건별 GO. 각 후보는 bullets{claim,details} 계약 + 인라인 SVG 난이도로 평가.

## 0. 선택 규칙 — 메시지 → 비교유형 → 차트 (Zelazny + FT)

장표에 차트를 넣기 전, **메시지가 함축하는 비교 유형**을 먼저 정한다. 차트는 그 다음이다.

| 메시지가 말하는 것 | 비교유형(Zelazny) | FT 범주 | 기본 차트 |
|---|---|---|---|
| "A가 B보다 크다/많다" | Item / Magnitude | Magnitude·Ranking | **막대(bar/column)**, lollipop |
| "X의 구성은 …" | Component | Part-to-Whole | pie/donut, **stacked bar**, **waterfall**, treemap |
| "시간에 따라 변한다" | Time series | Change over Time | line, **area**(보유), slope, **fan** |
| "값의 분포/편차" | Frequency / Deviation | Distribution·Deviation | histogram, **diverging bar**, boxplot |
| "두 변수의 관계" | Correlation | Correlation | **scatter**(보유=positioning), bubble, connected scatter |
| "순위" | — | Ranking | ordered bar, **slope**, dot strip |
| "흐름/전환" | — | Flow | **sankey**, waterfall, chord |
| "위치/지역" | — | Spatial | choropleth, 심볼맵 |

> 규칙: **차트는 시리즈 ≤ 3, accent 1색**(SKILL §3). 인라인 SVG로 못 그리면(외부 라이브러리 금지) 후보에서 제외하거나 단순화.

## 1. 신규 차트 아키타입 후보 (보유 13종 제외)

보유: cover/stat(donut)/redefine/architecture/flow/positioning(scatter)/before_after/metric_cards/market_nested/funnel/pricing/area_chart(line)/team_timeline.

| 후보 id | 목적/언제 | bullets 계약 | 렌더 트리거(안) | SVG 난이도 | Tier | 상태 |
|---|---|---|---|---|---|---|
| **bar_compare** | 항목 크기/순위 비교(가장 흔한 메시지, 지금 없음!) | 항목당 1 bullet: claim=라벨, details[0]에 수치 | details/claim에 숫자 리터럴 ≥3항목 | 쉬움 | **1** | 구현됨 → `bar_compare` (deck_templates_ext_a.py) |
| **quadrant_2x2** | BCG식 2×2 매트릭스(전략 포지셔닝, positioning scatter와 별개) | 4 bullet=4사분면, claim=사분면명, details=항목 | 정확히 4 bullet | 쉬움 | **1** | 구현됨 → `quadrant_2x2` (deck_templates_ext_a.py) |
| **kpi_hero** | 단일 핵심 지표를 크게(스탯 도넛과 다른 "빅넘버") | 1 bullet: claim=숫자+단위, details=맥락/델타 | claim에 큰 수치 | 쉬움 | **1** | 구현됨 → `kpi_hero` (deck_templates_ext_a.py) |
| **bullet_target** | 실적 vs 목표(게이지/진척) | 지표당 1 bullet: claim=지표, details=[현재, 목표] | details에 현재/목표 2값 | 쉬움 | **1** | 구현됨 → `bullet_target` (deck_templates_ext_a.py) |
| **roadmap_timeline** | 로드맵/일정(기간 있는 가로 간트, Priestley) | 단계당 1 bullet: claim=단계, details=[시작~기간] | 날짜/분기 토큰 | 중 | **1** | 구현됨 → `roadmap_timeline` (deck_templates_ext_a.py) |
| **waterfall** | 매출/비용 브리지, 증감 누적(Part-to-Whole +/-) | 단계당 1 bullet: claim=항목, details=[+/− 값] | +/− 숫자 시퀀스 | 중 | **1** | 구현됨 → `waterfall` (deck_templates_ext_a.py) |
| **comparison_matrix** | 기능 비교표(우리 vs 대안, 체크/X) | 행=bullet, claim=기능, details=열별 O/X | 열 헤더 + O/X | 쉬움 | **1** | 구현됨 → `comparison_matrix` (deck_templates_ext_a.py) |
| **grouped_bar** | 2 시리즈 비교(전/후, us/them) | 카테고리당 bullet, details=[값A, 값B] | 2값 쌍 | 쉬움 | 2 | 구현됨 → `grouped_bar` (deck_templates_ext_b.py) |
| **stacked_100** | 구성비(합=100%) | 카테고리당 bullet, details=구성요소 | 비율 합 | 중 | 2 | 구현됨 → `stacked_100` (deck_templates_ext_b.py) |
| **slope** | 2시점 순위/값 변화 | 항목당 bullet, details=[값1, 값2] | 2시점 2값 | 쉬움 | 2 | 구현됨 → `slope` (deck_templates_ext_b.py) |
| **lollipop** | 값 강조(막대보다 집중) | 항목당 bullet: claim=라벨, details=값 | 숫자 | 쉬움 | 2 | 구현됨 → `lollipop` (deck_templates_ext_b.py) |
| **gridplot_isotype** | "100 중 7" 유닛 스퀘어(stat 도넛 대체) | 1 bullet: claim에 `NN%` | `NN%` | 쉬움 | 2 | 구현됨 → `gridplot_isotype` (deck_templates_ext_b.py) |
| **radar** | 다변량 역량 비교(우리 vs 경쟁, 축 3~6) | 축당 bullet 또는 series, details=값 | 축 ≥3 | 중 | 2 | 구현됨 → `radar` (deck_templates_ext_b.py) |
| **fan_chart** | 미래 불확실성 밴드(전망) | 연도 bullet, details=[중앙, 하한, 상한] | 3값/연도 | 중 | 3 | 구현됨 → `fan_chart` (deck_templates_ext_c.py) |
| **sankey_flow** | 단계 간 흐름/전환(퍼널의 흐름 버전) | 흐름당 bullet: claim="A→B", details=[값] | `A→B` + 값 | 어려움 | 3 | 구현됨 → `sankey_flow` (deck_templates_ext_c.py) |
| **treemap** | 계층적 구성비(작은 조각 다수) | 항목 bullet, details=값 | 다수 값 | 어려움 | 3 | 구현됨 → `treemap` (deck_templates_ext_c.py) |
| **choropleth** | 지역별 분포(지도) | 지역 bullet, details=값 | 지역명+값 | 어려움(지도 필요) | 3 | 스킵 — 지역 경계 SVG path 등 지도 geometry 에셋이 필요한데 인라인 SVG만 허용(외부 에셋/이미지 라이브러리 금지)이라 정확한 지도 표현 불가. 에셋 계약 확정 후 전용 슬라이스로 재검토 |

## 2. 신규 레이아웃 아키타입 후보 (비-차트)

| 후보 id | 목적 | bullets 계약 | 난이도 | Tier | 상태 |
|---|---|---|---|---|---|
| **quote_card** | 고객 인용/추천(신뢰) | 1 bullet: claim=인용, details=[출처/직함] | 쉬움 | 1 | 구현됨 → `quote_card` (deck_templates_ext_a.py) |
| **logo_wall** | 고객·파트너 로고 그리드(social proof) | 로고 목록(에셋 필요) | 쉬움 | 2 | 구현됨 → `logo_wall` (deck_templates_ext_b.py) — 실제로는 이미지 에셋 없이 이름 텍스트 타일로 구현(로고 이미지 반입 금지 제약 회피) |
| **pyramid_layers** | 계층/전략 피라미드(3~4단) | 층당 bullet | 쉬움 | 2 | 구현됨 → `pyramid_layers` (deck_templates_ext_b.py) |
| **big_statement** | 전면 한 문장 강조(챕터 전환) | 1 bullet: claim | 쉬움 | 2 | 구현됨 → `big_statement` (deck_templates_ext_b.py) |
| **image_full_overlay** | 풀블리드 이미지+오버레이 텍스트 | claim + 이미지 에셋 | 쉬움(에셋) | 3 | 구현됨 → `image_full_overlay` (deck_templates_ext_c.py) — details[0]에 http(s)/data: URL 없으면 회색 폴백 패널로 렌더 |

## 3. 조판/컨벤션 보강 (SKILL에 아직 없는 것)

- **비교유형 우선 사고**(§0): 차트를 고르기 전에 메시지의 비교유형을 먼저 정한다 → 차트 오용 방지.
- **정렬로 순위 전달**: 순위 메시지는 정렬(ordered)만으로도 대부분 해결(별도 차트 불필요).
- **diverging(편차) 축**: 찬반/증감은 0 기준 양방향 막대가 파이보다 명확.
- **grid/isotype**: 작은 퍼센트(7% 등)는 도넛보다 100-유닛 그리드가 더 즉각적.
- **차트 정직성**(Zelazny): 축 절단·이중축 왜곡 금지. WCAG AA 대비.

## 4. 우선순위 (구현 시)

- **Tier 1 (즉시 후보, SVG 쉬움·계약 깔끔·IR/사업덱 수요 큼)**: bar_compare · quadrant_2x2 · kpi_hero · bullet_target · roadmap_timeline · waterfall · comparison_matrix · quote_card
- Tier 2: grouped_bar · stacked_100 · slope · lollipop · gridplot_isotype · radar · logo_wall · pyramid_layers
- Tier 3(복잡/에셋): fan_chart · sankey_flow · treemap · choropleth · image_full_overlay

각 후보를 실제 `render_*` 함수로 승격 = deck_render.py `TEMPLATE_RENDERERS` 등록 + 해당 CSS 블록을 DECK_CSS에 추가 + SLIDE_TEMPLATES/pack slide_specs 매핑 + SKILL §2.5 bullets 계약 1행 추가. **건별 GO.**

## 5. 구체 HTML 템플릿 (승격 스펙)

Tier 1 후보의 **실제 HTML 템플릿**(deck CSS 어휘 + `var(--accent)` 테마 + 인라인 SVG, 샘플 데이터 채움) =
`../../../../../../../[회사소개서]_20260715/archetype-templates/templates.html` (Room821 워크 폴더, 로컬 뷰어).
각 `<section class="slide">`가 곧 그 render_* 함수가 bullets로 만들어야 할 **목표 마크업**이다. 승격 시:
markup은 fragment 생성 함수로, 상단 `<style>`의 아키타입별 CSS 블록은 DECK_CSS에 이식.
포함: bar_compare · quadrant_2x2 · kpi_hero · bullet_target · waterfall(SVG) · roadmap_timeline · comparison_matrix · quote_card. (bar_compare/quadrant/waterfall 렌더 검증 완료.)

## 출처

- Financial Times — Visual Vocabulary: https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary
- Gene Zelazny — Say It With Charts (McKinsey): 5비교(Component/Item/Time-series/Frequency/Correlation) + Message(Action) title
- Andrew Abela — Chart Chooser (Extreme Presentation): Zelazny 5비교의 의사결정 트리 판
