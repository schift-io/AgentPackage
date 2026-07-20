# bid-response.agent — SCAFFOLD 상태 (등록/배포 없음)

이 팩은 **파일 스캐폴딩까지만** 완료됨. 아래 GO 없이는 등록·배포·활성화하지 않는다.

## 배경

노트북 지그 실측(`~/Desktop/Room 821/2026/조달청/IPNAVI/draft/PROOF.md`):
RFP 수령 → 응찰 패키지 HWPX 13개(제출 대상 12개) — **12분, 사람 개입 0**.
이 팩은 그 워크플로를 나라장터 공고 일반에 대해 반복 가능한 서버 제품으로
포팅하는 스캐폴딩이다.

## 생성 파일

```
services/agent-hub/apm/bid-response.agent/
  agent.md
  apm.yml                                  # pipeline:react, awp_operations.text_model 파라미터화(gpt-5.4-mini 디폴트)
  seeds/README.md                          # memory-pack IMPORT 블로커 설명(의도적으로 .cclg 없음)
  skills/rfp-intake/{SKILL.md,references/rfp-attachment-categories.md}
  skills/requirement-scoring-map/{SKILL.md,references/scoring-map-schema.md}
  skills/company-memory-grounding/{SKILL.md,references/memory-pack-usage-map.md}
  skills/proposal-drafting/SKILL.md
  skills/faithfulness-check/SKILL.md       # 수락 게이트 — post-react-run으로 bid-response 런에 배선 완료
  skills/form-filling/{SKILL.md,references/common-annex-forms.md}
  skills/hwpx-packaging/SKILL.md           # /hwpx/generate·/hwpx/package 라우트 실재 확인 완료
  skills/run-report/SKILL.md
  scripts/faithfulness_check.py            # shim — 정본은 src/agent_hub/faithfulness_gate.py
services/agent-hub/src/agent_hub/faithfulness_gate.py       # 결정적 numeric-claim 대조 순수 함수(단일 정본)
services/agent-hub/src/agent_hub/bid_response_faithfulness.py  # post-react-run 핸들러(self-register, agent_id 가드)
schift-api/awp_packs/first_party/bid-response/package-hwpx.awp.yaml   # render_body/merge_package direct 호출, .apm 등록만 pending
```

## 다음 단계 (각 GO 필요 — 순서대로)

| # | 단계 | 상태 | GO 필요 이유 |
|---|---|---|---|
| 1 | company-memory-pack md/json → `.cclg` 빌더 작성 | 미착수 | 신규 코드, cclg 스키마 설계 결정 필요 |
| 2 | `apm_memory_seed.install_pack_seeds()` 배선(팩 설치/등록 경로 훅) | 미착수 | 다른 세션 소유 파일(`agent_packs.py`/`pack_manifest.py`) 수정 필요 |
| 3 | document-helper에 `markdownToHwpx`(kordoc) 신규 생성 라우트 추가 | **완료** | `/v1/document-helper/hwpx/generate`(신규 생성)·`/v1/document-helper/hwpx/package`(병합) 실재(`services/document-helper/src/main.py`). `package-hwpx.awp.yaml`이 두 라우트를 direct 호출하도록 갱신됨 |
| 4 | `.apm` 레지스트리 등록(`apm_registry.py`) | 미착수 | prod 등록 — 배포 게이트 |
| 5 | 로컬 스모크(실제 나라장터 공고 1건으로 end-to-end) | 미착수 | 1·2가 끝나야 의미 있는 스모크 가능(3은 해소됨) |
| 6 | prod 배포(`./deploy.sh api`/`agent-hub` 해당 경로) | 미착수 | CLAUDE.md "No deploy without GO" |

## 런당 예상 cr 비용 (추정 — 실측 아님)

가정: RFP 구조화 1회 + 제안서 본문 1개 + 별지서식 11개(PROOF.md 실측 산출물 수
기준) = 섹션 12개. 디폴트 모델 `openai/gpt-5.4-mini`($0.75/M in, $4.50/M out —
`tokenizer.py` 실측 가격). 토큰 수는 **추정치**(실제 RFP 길이·회사 메모리 크기에
따라 크게 달라짐 — 스모크 후 재계산 필요).

| 단계 | 가정 input 토큰 | 가정 output 토큰 | 비용(gpt-5.4-mini) |
|---|---|---|---|
| requirement-scoring-map (RFP 전체 구조화 1회) | 30,000 | 3,000 | $0.0225 + $0.0135 = $0.036 |
| company-memory-grounding (core memory 조회, 평가항목 12개 합산) | 8,000 | 2,000 | $0.006 + $0.009 = $0.015 |
| proposal-drafting (본문 1개, 섹션 다회 호출 합산) | 20,000 | 8,000 | $0.015 + $0.036 = $0.051 |
| form-filling (별지서식 11개 합산) | 15,000 | 6,000 | $0.011 + $0.027 = $0.038 |
| run-report (요약 1회) | 5,000 | 1,500 | $0.004 + $0.007 = $0.011 |
| **합계 (1런)** | **78,000** | **20,500** | **≈ $0.151 (약 151 cr, 1cr=$0.001 가정)** |

- 모델을 `google/gemini-3-flash`(가장 저렴, $0.50/$3.00 per M)로 바꾸면 대략
  같은 토큰 가정에서 ≈ $0.100로 낮아진다. `google/gemini-3.5-flash`(품질 상향,
  $1.50/$9.00 per M)로 바꾸면 ≈ $0.300로 올라간다.
- **이 표는 스캐폴딩 단계의 추정치다.** 실제 cr 환산 단가·마진은
  `schift-api/server/billing/pricing.py`가 정본이며, 실측은 로컬 스모크(단계 5)
  이후 `llm_costs.py` 로그로 재계산해야 한다.

## 과장 금지 — 정직한 현황

- **만든 것**: 팩 구조(agent.md/apm.yml/9개 skill), 모델 파라미터화
  (`text_model` 블록, gpt-5.4-mini 디폴트 + gemini 계열 교체 가능), 메모리
  그라운딩 인터페이스 선언, document-helper `hwpx/generate`+`hwpx/package`
  실라우트(값 치환 `hwpx_mutate`까지 3라우트 전부 실재) + `package-hwpx.awp.yaml`
  direct 호출 배선, cr 비용 추정표, **faithfulness-check 게이트**(결정적 검사
  완성 + 단위 테스트 11건 통과 — A/B 실측 gemini 산출물에서 numeric-claim 위반
  22건 검출, gpt 산출물은 0건) — **post-react-run 핸들러로 bid-response 런에
  배선 완료**(`bid_response_faithfulness.py`, `tool_runtime.apply_post_react_run_hooks`,
  단위 테스트: 위반 검출/무위반 통과/타 팩 무발동 3케이스, `test_bid_response_faithfulness.py`).
- **안 만든 것 / 미검증**:
  - memory-pack → `.cclg` 어댑터, `install_pack_seeds` 배선 (blocker #1, #2)
  - faithfulness-check의 LLM 판정 단계(`judge_fn` 실연결, gpt-5.4-nano) —
    `text_generation_connector` 배선 이후 블로커. 결정적 검사만으로도
    fail-closed 게이트는 이미 동작(judge_fn 없으면 위반을 그대로 최종 판정)하며,
    이 결정적 검사가 이제 실제 bid-response 런에 배선돼 있다
  - faithfulness-check의 근거 소스는 현재 tenant core/agent 메모리만이다 —
    RFP 원문(session bucket ingest)을 sources에 합치는 배선은 아직 없다
    (`faithfulness-check/SKILL.md` "현재 상태" 참조, rfp-intake 산출물 연결 필요)
  - `.apm` 레지스트리 등록·배포·활성화 (전부 미실행, GO 대기)
  - 로컬 스모크 실행 (0회 — 이 스캐폴딩은 코드 리뷰·단위 테스트만 됐고 실행된 적 없음)
  - cr 비용 표의 토큰 가정치 (실측 아님, 스모크 후 재계산 필요)
