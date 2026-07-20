---
name: deck-designer
description: IR·사업발표·정부지원사업 발표용 장표(HTML 슬라이드)를 생성·교정할 때 사용. Schift IR 발표자료의 17장 구성을 표준 프레임으로 쓰고, 유저 문서에 평가기준(Criteria)이 있으면 그것을 그대로 판단 기준으로 삼는다. "장표", "IR 덱", "발표자료", "피치덱", "슬라이드" 요청에 사용.
---

# 장표 생성 (Deck Designer)

> 핵심 명제: **장표는 "읽는 문서"가 아니라 "3초 안에 결론이 보이는 화면"이다.**
> 슬라이드 1장 = 메시지 1개. 제목이 결론을 말한다 (Action Title).

## 0. Criteria 우선 규칙 (절대)

- 유저가 제공한 문서(공고문, 평가표, 심사 기준, RFP)에 **평가기준/배점이 있으면 그것을 그대로 판단 기준으로 삼는다.** 임의 기준을 발명하지 않는다.
- 평가기준이 없으면 이 스킬의 표준 IR 프레임(아래 2절)을 기본값으로 쓴다.
- 평가기준 → 슬라이드 매핑표를 먼저 만들고, 배점 큰 항목에 슬라이드 수를 비례 배분한다.

## 1. 어투 규칙

`submission-writer` 스킬의 슬랍 블랙리스트를 그대로 적용한다 — 혁신적/압도적/독보적/최첨단/완벽한/극대화/"뿐만 아니라" 금지, 보고체(`~를 검증함/확보함/제시함`) 금지.

장표 특화 규칙:
- **Action Title**: 슬라이드 제목은 토픽("시장 분석")이 아니라 결론("국내 제조 AX SOM 약 260억")으로 쓴다. 단 Cover/TEAM/Closing 등 구조 슬라이드는 예외.
- 헤드라인 2줄 이내, 강조 키워드만 accent 색.
- 본문은 명사형 종결. 발표 멘트가 아닌 화면 텍스트에는 "합니다/입니다"를 쓰지 않는다 (Closing 메시지 1장은 예외 허용).
- 모든 수치에 출처. 슬라이드 하단에 출처 캡션 (예: "중소벤처기업부 2025 스마트제조혁신실태조사").

## 1.5 카피 길이 규칙 (지저분함 방지 — 절대)

- **Action Title ≤ 28자.** 두 줄로 넘어가면 메시지가 두 개라는 뜻 — 하나를 버린다.
- **claim(포인트 헤드라인) ≤ 30자**, 명사구로 끝낸다. 문장형 서술 금지.
- **detail(보조설명) ≤ 45자, 슬라이드당 ≤ 4개.** "라벨 — 짧은 설명" 형태 권장 (예: "사내 맥락의 부재 — 회사·고객·프로젝트 맥락 모름").
- **슬라이드당 포인트 블록 ≤ 3개.** 더 쓰고 싶으면 슬라이드를 나누지, 글자를 줄이지 않는다.
- 같은 단어를 한 슬라이드에서 3회 이상 반복하면 카피를 다시 쓴다.
- 정본 카피 예시: `references/exemplar-sections.json` — 실제 Schift IR 발표자료의 카피 밀도가 기준선이다. 이보다 길면 깎는다.

## 2. 표준 IR 구성 (Schift 발표자료 17장 역설계)

| # | 섹션 라벨 | 슬라이드 | 필수 요소 |
|---|---|---|---|
| 1 | — | Cover | 브랜드명(accent) + 카테고리 한 줄 정의 + 서브카피 + 회사/연락처 |
| 2 | PROBLEM | 시장 긴장 | "수요 폭증 vs 실패 폭증" 대비 + 핵심 수치 1개(파이/도넛) + 실패 원인 카드 4개 |
| 3 | PROBLEM | 원인 재정의 | "문제는 X가 아니라 Y" 구조 + 기존 도구 단편화 다이어그램 |
| 4 | SOLUTION | 아키텍처 | INPUT → 엔진(6모듈 그리드) → OUTPUT 1장 다이어그램 |
| 5 | SOLUTION | 파이프라인 | 5단계 가로 플로우 + 각 단계 하단 효익 캡션(dark pill) |
| 6 | COMPETITIVE | 포지셔닝 맵 | 2축 산점도, 자사는 우상단 accent 배지 |
| 7-9 | USE CASE 1-3 | BEFORE/AFTER | 좌 BEFORE(점선 박스·흑백) / 우 AFTER(accent 테두리) + 결과 배너 |
| 10 | SOLUTION | 기대효과 | 측정 가능한 지표 카드 6개 (아이콘 + 지표명 + 측정 방식) |
| 11 | SCALE UP | TAM/SAM/SOM | 중첩 박스 + 각 시장 정의·금액·산출근거 |
| 12 | SCALE UP | 초기 타겟 | 깔때기 3단 카드(전체→조건1→조건2) + 출처 캡션 |
| 13 | SCALE UP | BM | 가격 티어 4카드 (주력 티어 accent 테두리) + 파트너십/패키지 |
| 14 | GTM | 시장 진입 | 고객 증거(MOU/PoC 진행 배지) + 전환 퍼널 5단계 |
| 15 | SCALE UP | 매출 성장 | stacked area 차트 + 연도별 계정 수 + 마진율 |
| 16 | TEAM | 팀 | 3인 사진/역할 + 연도별 트랙레코드 타임라인 |
| 17 | — | Closing | 철학 1~3문장 (핵심 구절만 accent) + 연락처 |

- 슬라이드 좌상단에 섹션 라벨(PROBLEM/SOLUTION/COMPETITIVE/SCALE UP/GTM/TEAM)을 accent 소문자 캡으로 단다.
- 배경 리듬: cream 기본, 강조 슬라이드(시장/퍼널)는 dark 패널 반전으로 페이스 전환.

## 2.5 아키타입별 bullets 계약 — 렌더 트리거 (절대)

> 표준 17장(아래 표)의 렌더러 12종(stat/redefine/architecture/flow/positioning/before_after/
> metric_cards/market_nested/funnel/pricing/area_chart/team_timeline)은 `deck_templates_ir_a.py` +
> `deck_templates_ir_b.py`가 Figma 실덱(ir-deck/slide-*.html) 레이아웃으로 구조 업그레이드해
> `deck_render.py` 기본 렌더러를 오버라이드한 것이다 — bullets 계약(아래 표)은 그대로다.

각 섹션은 sub-agent가 만든 `bullets: [{claim, details:[…]}]`로만 렌더된다. 렌더러(`deck_render.py`)는
슬라이드 id로 템플릿을 고르고, **아래 트리거 토큰/최소개수를 만족해야 다이어그램을 그린다. 못 채우면
조용히 밋밋한 point 리스트로 폴백**한다(에러 안 남 → 그래서 더 위험). 새 덱을 쓸 때 반드시 이 계약대로
bullets를 뽑아라. 카피 밀도·길이는 §1.5, 실제 shape는 `references/exemplar-sections.json`(17장 정본)을 그대로 본뜬다.

| 슬라이드 | 템플릿 | 최소 | bullets 구조 | ★렌더 트리거(없으면 폴백) |
|---|---|---|---|---|
| 1 | cover | 2 | b0.claim=서브카피, b1.claim=회사·연락처 (details 비움) | 없음(항상 렌더) |
| 2 | stat | 1 | b0.claim=헤드라인(도넛 라벨), details=실패카드 ≤4(✕) | **claim 또는 details 어딘가에 `NN%` 리터럴**(0<값<100). 예 "…데이터 7%" |
| 3 | redefine | 2 | b0={claim=상단 명제, details=근거}, b1={claim=다크밴드 제목, details=칩 ≤6} | bullets ≥2 |
| 4 | architecture | 3 | 순서 고정 INPUT/ENGINE/OUTPUT. 각 claim=열 제목, details=셀(ENGINE=모듈들, 2열 그리드) | bullets ≥3 |
| 5 | flow | 3 | 단계당 1 bullet. claim=단계 제목, details[0]=하단 캡션 | 유효 단계 ≥3(≤5). 단계당 details 1개 권장(여러 개면 각각 별 셀로 쪼개짐) |
| 6 | positioning | 1 | b0.claim=하단 캡션, details=경쟁사명 나열 | **details를 `, / ·`로 쪼갠 토큰이 경쟁사(각 2~18자)**. 자사=Schift 배지 고정 |
| 7–9 | before_after | 2 | b0=BEFORE{claim,details}, b1=AFTER{claim,details}, b2(opt).claim=하단 배너 | bullets ≥2 |
| 10 | metric_cards | 4 | 지표당 1 bullet. claim=지표명, details[0]=측정방식 | 유효 카드 ≥4(≤6) |
| 11 | market_nested | 3 | 레벨당 1 bullet. claim="TAM … 약 37조 원", details=[산출근거] | **각 레벨 텍스트에 `TAM`/`SAM`/`SOM` 리터럴 + `조`/`억` 금액**. 3레벨 모두 |
| 12 | funnel | 3 | 단계당 1 bullet. claim=단계, details[0]=캡션(수치·출처) | 유효 단계 ≥3(≤5). 마지막 2단계 자동 강조 |
| 13 | pricing | 3 | 티어를 claim/details 항목으로. "이름 가격 — 설명" 형태 | **각 티어 head에 `무료`/`만원`/`Free`/`Starter`/`Business`/`Enterprise` 중 하나**. 3~4티어 |
| 14 | funnel | 3 | (12와 동일 템플릿) GTM 전환 단계 | funnel과 동일 |
| 15 | area_chart | 1 | b0.claim=하단 캡션, details=연도별 매출 서술 | **`20XX년 … N억` 패턴 ≥2개**. 예 "2026년 2.3억 → 2028년 33.9억" |
| 16 | team_timeline | 1 | 인물 bullet(claim=핵심 N인, details=역할) + 연혁 bullet(details=연도별) | **인물 details에 `CEO/CTO/CMO/대표/Developer/Designer` 토큰**(≤3), 연혁은 `20XX` 포함(≤7) |
| 17 | closing | 2 | b0.claim=철학(accent), b1.claim=연락처 | 없음(항상 렌더) |

### 확장 아키타입 (섹션 `template` 명시로 사용 — IR 17-맵 밖)

표준 17장 외의 차트/다이어그램이 필요하면 섹션 JSON에 `"template": "<id>"`를 넣어 아래 렌더러를 직접 지정한다
(id를 SLIDE_TEMPLATES에 매핑하지 않아도 됨). 색은 자동으로 테넌트 accent 상속. 라이브 21종
(Tier 1 8 + Tier 2 9 + Tier 3 4) 전부 `deck_templates_ext_{a,b,c}.py`에 구현되어 있다 —
`merged_template_renderers()` 실제 키와 아래 표는 1:1 대응한다.

**Tier 1 (8종, `deck_templates_ext_a.py`)**

| template | 언제 | bullets 구조 | ★트리거 |
|---|---|---|---|
| `bar_compare` | 항목 크기/순위 비교 | 항목당 bullet: claim=라벨, details[0]=값 | 값에 숫자, ≥2항목. index 0 강조 |
| `quadrant_2x2` | 2×2 전략 매트릭스 | 정확히 4 bullet=사분면(tl/tr/bl/br), claim=제목, details=항목 | **4 bullet**. 승자 칸 claim에 `★` |
| `kpi_hero` | 빅넘버 지표 ≤3 | bullet: claim=숫자+단위, details[0]=라벨, details[1]=맥락 | claim에 숫자 |
| `bullet_target` | 실적 vs 목표 게이지 | bullet: claim=지표, details=[현재, 목표] | 숫자 2개 |
| `waterfall` | 매출/비용 브리지 | 첫=시작, 중간=증감(+/−), 마지막=순액. claim=라벨, details[0]=값 | ≥3, 값에 부호 |
| `roadmap_timeline` | 로드맵/간트(4분기) | 단계당 bullet: claim=단계, details[0]=`Q1~Q2` | `Qn` 토큰 |
| `comparison_matrix` | 기능 비교표 | bullet[0]={claim=행제목, details=열이름들(0=자사)}, 이후 행={claim=기능, details=열별 O/X} | 헤더 열≥2 + 행≥1 |
| `quote_card` | 고객 인용 | bullet[0]: claim=인용, details[0]=출처 | claim 존재 |

**Tier 2 (9종, `deck_templates_ext_b.py`)**

| template | 언제 | bullets 구조 | ★트리거 |
|---|---|---|---|
| `grouped_bar` | 2 시리즈 비교(전/후, us/them) | b0={claim=범례 제목, details=[시리즈A명, 시리즈B명]}, 이후 카테고리당 {claim=카테고리, details=[값A, 값B]} | legend details 2개 + 카테고리≥2, 값A/값B 숫자 |
| `stacked_100` | 구성비(합=100%로 정규화) | 카테고리당 {claim=카테고리, details=["세그먼트명 값", ...]} | 카테고리≥1, 세그먼트≥2/카테고리(각 detail에 숫자) |
| `slope` | 2시점 값/순위 변화 | 항목당 {claim=항목, details=[값1, 값2]} | 항목≥2, 값1/값2 숫자 |
| `lollipop` | 값 강조(막대보다 집중) | 항목당 {claim=라벨, details[0]=값} | 항목≥2, 값에 숫자 |
| `gridplot_isotype` | "100 중 N" 유닛 스퀘어(도넛 대체, 작은 %에 유리) | b0={claim에 `NN%` 리터럴, details=캡션 ≤3} | b0.claim(또는 그 details)에 `NN%`(0<값<100) |
| `radar` | 다변량 역량 비교(우리 vs 경쟁, 축 3~6) | 축당 {claim=축명, details=[우리값, 비교값?]} | 축≥3(≤6), 각 축 우리값 숫자 필수 |
| `logo_wall` | 고객·파트너 이름 그리드(social proof, 이미지 없음) | bullet당 claim=이름(또는 details=이름 목록) | 이름≥3(≤12) |
| `pyramid_layers` | 계층/전략 피라미드(3~4단) | bullets[0]=최상층(꼭짓점, accent) … bullets[-1]=최하층(기반, 최대폭). 층당 {claim=층명, details[0]=설명} | 층≥3(≤4), claim 존재 |
| `big_statement` | 전면 한 문장 강조(챕터 전환) | b0={claim=한 문장, details[0]=서브카피}, 마지막 bullet.claim(옵션)=accent 하이라이트 줄 | b0.claim 존재 |

**Tier 3 (4종, `deck_templates_ext_c.py`)**

| template | 언제 | bullets 구조 | ★트리거 |
|---|---|---|---|
| `fan_chart` | 전망 불확실성 밴드(연도별 중앙값+하한/상한) | 연도 bullet(claim에 `20XX`): details=[중앙, 하한, 상한] | 연도 토큰 + 숫자 3개, 유효 연도≥3(≤6) |
| `sankey_flow` | 2컬럼 단순화 흐름/전환 | 흐름당 bullet: claim=`A→B`(또는 `->`), details[0]=값 | `→`/`->` 구분 + 값>0, 흐름≥2 |
| `treemap` | slice-and-dice 계층 구성비 | 항목당 bullet: claim=이름, details[0]=값(또는 claim 자체가 숫자) | 항목≥4, 값>0 |
| `image_full_overlay` | 풀블리드 이미지+오버레이 텍스트 | b0={claim=문구, details=[이미지URL, 캡션?]} | b0.claim 존재(URL 없으면 회색 폴백 패널) |

**choropleth는 미구현이다** — 지역 경계 SVG path 같은 지도 geometry 에셋이 필요한데, 이 모듈은
인라인 SVG만 허용하고 외부 에셋/이미지 라이브러리 반입을 금지(§3 규칙 5)해 정확한 지도 표현이 불가능하다.
필요해지면 에셋 계약을 먼저 정하고 전용 슬라이스로 승격한다(`chart-archetype-catalog.md` Tier 3 참조).
choropleth를 지정하면 폴백된다 — 그 외 위 21종 + 표준 14종은 전부 렌더 가능.

원칙: **트리거는 "화면에 그 토큰을 노출하라"가 아니라 "claim/details 텍스트가 그 리터럴을 포함해야 파서가
인식한다"**는 뜻이다. 수치·시장명·연도·가격 키워드를 카피 안에 자연스럽게 넣어라(§1.5 길이 안에서).
평가기준(Criteria) 덱이라 슬라이드 구성이 표준 17장과 다르면, 각 섹션 id에 위 템플릿 중 의미가 맞는 것을
매핑하고 그 트리거를 따른다.

> **차트 선택 규칙**: 차트를 넣기 전 메시지의 **비교유형**(항목/구성/시계열/분포/관계/순위/흐름)을 먼저 정한 뒤
> 거기 맞는 차트를 고른다. 비교유형↔차트 매핑 원리와 각 아키타입의 유래(FT Visual Vocabulary + Zelazny)는
> `references/chart-archetype-catalog.md` 참조. 렌더 가능한 템플릿은 표준 14종 + 확장 21종(choropleth
> 제외) 총 35종이니, 그중 메시지에 가장 가까운 걸 고른다.

## 3. 디자인 규칙 (diagram-design + McKinsey 컨벤션)

1. **절제**: 최고의 수정은 삭제다. 슬라이드 밀도 목표 4/10. 요소마다 "없애면 메시지가 무너지는가"를 묻는다.
2. **accent 1색**: 강조색은 팔레트의 accent 1개. 두 번째 강조색 금지.
3. **색은 `references/color-palettes.md`에서만** 선택한다. IR 기본은 0번 Schift 브랜드 조합.
4. **4px 그리드**: 좌표·폭·간격은 4의 배수. 1px hairline 테두리, 그림자 금지, radius는 카드 16px 이하 / pill 999px.
5. **차트는 inline SVG**로 직접 그린다. 외부 차트 라이브러리 금지. 데이터 ≤ 시리즈 3개.
6. **아이콘**: outline 스타일 SVG 통일. 입체감이 필요하면 3dicons.co (CC0, 출처표기 불요)에서 소싱.
7. **대비**: 텍스트/배경 WCAG AA(4.5:1) 검증.
8. **표보다 다이어그램**: 흐름은 화살표 플로우, 비교는 BEFORE/AFTER, 시장은 중첩 박스. 표는 가격표·트랙레코드만.

## 4. 출력 계약

- self-contained HTML 1파일. 슬라이드는 `<section class="slide">` 1280×720 (16:9).
- 시스템 폰트 스택 (Pretendard/Apple SD Gothic Neo 우선). 외부 폰트/JS/이미지 의존 금지 (사진 placeholder는 회색 박스 + 라벨).
- `@media print` 페이지 나눔 지원 → PDF 변환 가능.
- 내부 메모/TODO/placeholder 문구를 최종본에 남기지 않는다.

## 5. QC 핸드오프

- 초안 완성 후 `deck-qc` 스킬(devadv 방식)로 넘긴다. Fatal/Serious가 0이 되기 전에는 최종본이라고 부르지 않는다.
- 근거 없는 수치는 QC에 가기 전에 제거하거나 "측정 예정"으로 바꾼다.
