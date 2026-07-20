---
name: requirement-scoring-map
description: Structure the ingested RFP into a requirement/scoring/schedule table that downstream drafting and form-filling skills consume as their single source of truth for what to write and how to weight it.
---

# 요구사항·평가표·일정 구조화

## Purpose

`rfp-intake`가 세션 버킷에 넣은 RFP를 검색해 **평가항목·배점·필수요건·제출기한·
필요 서식 목록**을 구조화 테이블로 뽑는다. 이 테이블이 이후 `proposal-drafting`과
`form-filling`의 입력이자 근거다.

## Inputs

- 세션 버킷에 ingest된 RFP(제안요청서·과업지시서·공고서).
- (선택) 사용자가 이미 알고 있는 평가위원 구성·정성/정량 배점 비중.

## Pipeline (단계)

1. **평가표 추출** — RFP 본문에서 정성평가/정량평가 배점표를 찾아 항목별 배점·
   세부 기준을 표로 뽑는다. 배점 합계가 RFP 명시 총점과 맞는지 검산한다. 불일치 시
   [확인 필요].
2. **필수요건 추출** — 입찰 참가자격, 직접생산확인증명서 등 보유 서류 요건,
   인력 자격요건(경력·학위)을 별도 리스트로 뽑는다.
3. **일정·제출 요건 추출** — 제출 마감일시, 제출 방법(전자입찰/서면), 발표 평가
   여부·발표 시간 배분, 필요 서식 목록(별지 몇 호까지)을 추출한다.
4. **평가항목 → 회사 컨텍스트 매핑 골격 작성** — 각 평가항목에 대해 어떤
   capability/reference로 답할지 매핑 키만 미리 세팅한다(값 채우기는
   `company-memory-grounding` + `proposal-drafting`의 몫).

세부 스키마는 references/scoring-map-schema.md.

## Rules

- RFP 원문에서 확인되는 사실만 적는다. 배점·기준·기한이 불명확하면 [확인 필요]로
  표시하고 지어내지 않는다.
- 배점표 합계 검산이 어긋나면 자동 확정하지 않고 검토 필요로 남긴다.
- 평가항목명은 RFP 원문 표현을 그대로 쓴다(임의 재명명 금지) — 이후 제안서 목차와
  1:1 대응시키기 위함.

## 도구 경계

- RFP 검색은 `schift-rag`(세션 버킷)로 한다.
- 회사가 어떤 capability로 각 평가항목에 답할지는 이 스킬이 정하지 않는다 —
  `company-memory-grounding`이 tenant core memory에서 조회한 뒤,
  `proposal-drafting`이 실제 문장을 만든다. 이 스킬은 **매핑 키(빈 골격)**까지만.

## Output Contract

산출물은 `agent_hub.bid_response_contracts.ScoringMap`(설계 정본
`docs/2026-07-11-bid-response-full-package-design.md` §2)이 정의하는 JSON
스키마를 따른다 — 아래 두 배열이 이후 `bid_response_section_plan`/
`bid_response_annex_fill`의 유일한 입력이다.

- `items[]`: RFP 평가표의 **leaf 평가항목** 1개당 1엔트리
  (`{id, title, weight, sub_criteria[], s_grade_keywords[], capability_keys[],
  reference_keys[]}`). `title`은 RFP 원문 표현 그대로. `weight`는 그 항목
  자체 배점(상위 대분류 합이 아님). `sub_criteria`는 S등급을 가르는 괄호
  조건 문구. `capability_keys`/`reference_keys`는 이 스킬 단계에서는 빈
  배열로 두고 `company-memory-grounding`이 tenant core memory의
  `usage_map`에서 채운다.
- `annex_forms[]`: RFP 붙임 별지서식 1종당 1엔트리
  (`{id, title, cardinality, fields[]}`). `cardinality`는
  `single`/`per_team_member`/`per_reference` 중 하나 — 서식이 사업 전체
  1부인지, 참여인력·레퍼런스 건별로 반복 생성해야 하는지를 표시한다.
  실측 근거(IP-NAVI 골드 hwpx 13개 대조): 참여인력이 여러 명이어도
  **서식 파일 자체가 늘어나지 않고 한 서식 안의 표 행이 반복**되는
  패턴이면 `cardinality=single`을 쓰고 반복 행은 `fields`에 그대로 나열한다
  (예: 별지 제7호 별첨2/별첨3). 공고가 인력·레퍼런스별로 **별도 서식 파일**을
  요구할 때만 `per_team_member`/`per_reference`로 표시한다.
- 배점표 검산(`sum(items[].weight) == RFP 명시 총점`)이 어긋나면 [확인 필요]로
  남기고 자동 확정하지 않는다.
- 세부 JSON 예시는 references/scoring-map-schema.md, 실 인스턴스는
  `services/agent-hub/tests/fixtures/ipnavi_scoring_map.json`.
