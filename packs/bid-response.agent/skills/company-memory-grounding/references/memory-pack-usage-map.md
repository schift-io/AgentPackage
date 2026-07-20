# company-memory-pack usage_map 재사용 규칙

`company-memory-pack/0.1` 스키마는 `usage_map` 섹션에 이미 "평가항목 →
capabilities/references/constraints" 매핑 표를 갖고 있다(예시):

| 평가항목 | capabilities | references | constraints |
|---|---|---|---|
| RAG 레퍼런스·정확도 | cap.rag_pipeline, cap.eval, cap.public_bench | ref.public_bench | 1,2,6 |
| 멀티도메인·로드맵 | cap.multidomain, cap.own_engine | — | 3,8 |
| ... | ... | ... | ... |

- 이 스킬은 위 표를 **재발명하지 않는다.** core memory에서 조회된 `usage_map`
  엔트리를 RFP의 평가항목명과 fuzzy 매칭(동의어 정도만 허용, 의미 확장 금지)해
  그대로 가져온다.
- RFP 평가항목이 memory-pack의 `usage_map`에 없는 새로운 항목이면, capability
  자체를 추측하지 않고 [확인 필요]로 남긴다 — usage_map 확장은 사람이 memory-pack
  을 갱신한 뒤에만 이뤄진다(이 팩이 memory-pack을 직접 수정하지 않는다).
