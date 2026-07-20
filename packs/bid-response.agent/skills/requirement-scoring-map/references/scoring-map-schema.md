# 평가표 구조화 스키마

이 스키마는 `agent_hub.bid_response_contracts.ScoringMap`(단일 정본, JSON↔dataclass
왕복은 `services/agent-hub/tests/test_bid_response_contracts.py`)의 JSON 표현이다.
실 인스턴스: `services/agent-hub/tests/fixtures/ipnavi_scoring_map.json`.

```json
{
  "notice_id": "한국지식재산보호원-2026-37",
  "total_weight": 90,
  "items": [
    {
      "id": "tech_rag_reference_accuracy",
      "title": "RAG 레퍼런스·정확도",
      "weight": 10,
      "sub_criteria": ["정확도 수치 포함"],
      "s_grade_keywords": ["MRR", "nDCG", "Hit@k", "Recall@k"],
      "capability_keys": ["cap.rag_pipeline", "cap.eval", "cap.public_bench"],
      "reference_keys": ["ref.public_bench"]
    }
  ],
  "annex_forms": [
    {
      "id": "annex_01_biparticipation_application",
      "title": "별지 제1호 입찰참가신청서",
      "cardinality": "single",
      "fields": ["상호/법인명칭", "주소", "전화번호", "대표자 성명", "대표자 생년월일", "법인등록번호"]
    }
  ]
}
```

## 필드 규칙

- `items[].title`은 RFP 원문 평가항목명 그대로(임의 재명명 금지) — 이후 제안서
  목차·섹션 제목과 1:1 대응시키기 위함.
- `items[].weight`는 그 leaf 항목 자체 배점. `sum(items[].weight)`가
  `total_weight`(RFP 명시 총점)와 일치하는지 검산한다. 불일치 시 [확인 필요].
- `items[].sub_criteria`는 S등급 커트라인 조건(괄호 조건 문구) — 채점자가 S를
  주려고 찾는 키워드의 근거. `items[].s_grade_keywords`는 그 조건을 충족했음을
  본문에서 리터럴로 검출 가능하게 하는 키워드 목록(`faithfulness-check`/품질
  체크가 grep 대상으로 쓴다).
- `items[].capability_keys`/`reference_keys`는 이 스킬 단계에서는 빈 배열로
  둔다 — `company-memory-grounding`이 tenant core memory의 `usage_map` 섹션
  (`company-memory-grounding/references/memory-pack-usage-map.md`)에서
  fuzzy 매칭으로 채운다. 이 스킬이 값을 추측하지 않는다.
- `annex_forms[].cardinality`는 `single`/`per_team_member`/`per_reference`
  중 하나(`agent_hub.bid_response_contracts.AnnexCardinality`). **파일 단위
  확장이 실제로 필요한 경우에만** single이 아닌 값을 쓴다 — 참여인력이
  여럿이라도 서식 안의 표 행이 반복되는 패턴(IP-NAVI 골드 별첨2/별첨3 실측)은
  `single` + `fields`에 반복 행 컬럼을 그대로 나열한다.
- `annex_forms[].fields`는 그 서식의 placeholder 필드명 목록(회사 등록정보·
  대표자·인력 이력 등) — 신원/날인/서명 필드도 이름은 여기 나열하되 실제 값
  채움은 항상 placeholder(`form-filling`/`bid_response_annex_fill` 스킬 규칙).

## 이 계약에 없는 것 (스킬이 참고용으로 부가 생산 가능, 파이프라인 입력 아님)

`mandatory_requirements`(필수 보유서류), `schedule`(제출기한·발표시간)은
사람 확인/문서 검토에 유용하지만 `ScoringMap` dataclass의 필드가 아니다 —
`bid_response_operation.py` 오케스트레이터는 이 두 정보를 입력으로 소비하지
않는다. 스킬이 참고 자료로 별도 블록에 남기는 것은 허용되나, `items`/
`annex_forms`/`notice_id`/`total_weight` 밖의 키를 오케스트레이터가 읽게
만들지 않는다(계약 오염 방지).
