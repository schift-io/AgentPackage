---
name: proposal-drafting
description: Draft the proposal body sections that map 1:1 to the RFP's scoring items, using only capabilities/references grounded in tenant core memory, with a MISSING-ask guard against fabrication.
---

# 제안서 섹션 생성 (평가항목 매핑 초안)

## Purpose

`requirement-scoring-map`의 평가항목 목록과 `company-memory-grounding`이 채운
capability/reference/constraint를 받아 제안서 본문 섹션 초안을 쓴다. 지그의
골격 로직("평가항목 → 근거 3종 순서로 조립")을 프롬프트로 이식하고, 나라장터
공고 일반에 대해 파라미터화한다(특정 사업명·발주기관에 종속되지 않는다).

## Inputs

- `scoring_to_capability_map`(완전히 채워진 상태 — company-memory-grounding
  산출물).
- RFP 요구사항·필수요건·일정(requirement-scoring-map 산출물).
- `awp_operations.bid-response-proposal.text_model` 파라미터(디폴트
  `openai/gpt-5.4-mini`, 카탈로그 내 교체 가능).

## 문체·형식 (owner 지시 2026-07-11 — bizplan.agent 제출체 규칙 준수)

모든 섹션은 [`references/submission-style.md`](references/submission-style.md)
(정본: `apm/bizplan.agent/skills/submission-writer/SKILL.md`)의 규칙을 따른다.
핵심만 요약:
- **보고체 금지** — "~를 검증함/확보함/설계함" 류 행위 서술 대신 평가자가 점수 매길
  사실·수치·방법 그 자체. 자가 점검: 불릿 읽고 "그래서 뭐?"가 나오면 실패.
- **AI slop 블랙리스트** — 혁신적/압도적/독보적/"단순한 ~가 아니라" 등 과장어,
  공허한 요약 라벨, 메타 안내문, 합니다체 전부 금지. 개조식 `~함/~음` 종결.
- **구조** — 계층 2단(h2/h3)까지, 개조식 2층 불릿(상위 ○ 40자 이내 → 하위 -),
  120자+ 문단 금지, 비교/수치는 표로.
- **수치 환각 금지** — memory-pack에 없는 수치는 쓰지 않는다
  (faithfulness-check 게이트가 이중 차단하지만, 생성 단계에서부터 지킨다 —
  startup-support.agent 플레이북의 동일 원칙).

## Pipeline (단계)

1. **목차 확정** — 평가항목 순서를 그대로 제안서 목차로 쓴다(RFP 원문 표현
   유지, 임의 재명명 금지).
2. **섹션별 작성** — 각 평가항목에 대해 `capabilities → references →
   constraints` 순으로 조립:
   - capability 문장: "이 회사가 보유한 것"을 결과 사실로 서술(내부 구현 상세는
     constraints가 차단).
   - reference 문장: 실적으로 뒷받침("이 수치/이 로그/이 로드맵"), 고객명은
     항상 익명화(`[고객A]` 등 — memory-pack이 이미 익명화했으면 그대로 유지).
   - constraint 적용: 해당 constraint 번호에 걸리는 표현은 자동 차단하고
     "확장 로드맵"·"결과 사실"까지만 서술하는 완곡 표현으로 대체.
3. **MISSING-ask 가드** — capability/reference가 비어 있는 평가항목은 절대
   창조하지 않는다. `[확인 필요]`로 표시하고 사람에게 회사 실적/수치를 물어야
   함을 남긴다.
4. **표지·개요·결론** 등 RFP가 요구하는 공통 섹션(회사 개요, 수행 조직, 일정
   등)은 `company-memory-pack`의 `company`/`team` 섹션에서 채우되, 인력·수치는
   placeholder(예: `[성명]`, `[설립연도]`)로 남긴다 — 사람이 실인력으로 치환.

## Rules

- **할루시네이션 0 원칙**: 본문의 모든 실적·역량 주장은 tenant core memory에
  1:1 대응해야 한다. 대응하는 근거가 없으면 절대 만들지 않는다(PROOF.md 실측
  기준: memory pack에 없는 실적/수치 창조 0건이 통과 기준).
  구체 수치는 "공개 벤치 기준"으로만 서술하고 내부 프로덕션 수치는 인용하지 않는다.
- constraints 위반 표현(LPDM 특허 방법론, 임베딩 모델명, 엔진 내부, 3-tier
  메모리 구현, 비용/마진, 사고 이력, CSAP 자사 취득 약속, 회사 등록정보 실값)은
  섹션 생성 전에 반드시 필터링한다.
- 평가항목별 배점이 클수록 더 구체적인 근거(reference)를 우선 배치한다.
- 발주기관·사업명이 바뀌어도 이 스킬은 그대로 재사용 가능해야 한다(하드코딩
  금지) — 사업 고유명사는 requirement-scoring-map 산출물에서만 가져온다.

## 도구 경계

- 텍스트 생성 모델은 `apm.yml`의 `awp_operations[].text_model`로 파라미터화한다
  (하드코딩 금지). 이 스킬 자체는 어떤 모델을 쓸지 결정하지 않는다.
- markdown → HWPX 변환·별지서식 값 병합은 `hwpx-packaging` 스킬/document-helper가
  처리한다. 이 스킬은 본문 markdown과 채울 값의 구조만 만든다.
- 이 스킬의 산출물은 `hwpx-packaging`으로 바로 넘어가지 않는다 —
  **`faithfulness-check` 게이트를 통과해야 한다.** "할루시네이션 0 원칙"은
  프롬프트 규칙(위 Rules)만으로는 실측상 지켜지지 않았다(A/B 실측,
  `AB_REPORT.md` 2026-07-11 — gemini가 memory-pack에 없는 수치·법률 사실을
  창조). `faithfulness-check`가 그 프롬프트 규칙의 결정적 수락 게이트다.

## Output Contract

- `format`: markdown (document-helper가 이후 HWPX로 변환)
- {id, title, bullets:[{claim, details[]}]} — 목차 순서의 섹션들 + 섹션별
  [확인 필요] 목록.
