---
name: faithfulness-check
description: Gate the drafted proposal body against [RFP text ∪ tenant memory-pack] before HWPX packaging — deterministic numeric-claim cross-check plus an LLM-judge second opinion on flagged sentences, so fabricated figures/facts never reach the submission package.
---

# Faithfulness 게이트 (수락 게이트)

## Purpose

`proposal-drafting`이 만든 본문 markdown을 `hwpx-packaging`으로 넘기기 전에
검증한다. A/B 실측(`~/Desktop/Room 821/2026/조달청/IPNAVI/server-run/AB_REPORT.md`,
2026-07-11)에서 gemini-3.5-flash가 memory-pack에 없는 정확도 수치(95% 등)와
실존하지 않는 법률 사실(USPTO Declaration 기한, CNIPA 관납료 감면 비율)을
창조했다 — grep 금지어 스캔으로는 못 잡히고(내부 코드네임이 아니라 "그럴듯한
수치·사실"이라서) 의미 대조로만 발견됐다. 이 스킬이 그 대조를 매 런마다
결정적으로 자동 수행한다(`telegram-agent-router-orchestrator.md` §0f "증명
인프라(수락 게이트)"의 실물).

## Inputs

- `proposal-drafting` 산출 본문 markdown.
- `[RFP 원문 ∪ tenant core memory(company-memory-pack)]` — 이 두 소스의
  합집합만 "실존"으로 인정한다. 어느 쪽에도 없는 숫자·사실은 창조로 간주.

## Pipeline (단계)

1. **결정적 검사** (`scripts/faithfulness_check.py::find_violations`) — 본문의
   모든 %·임계치(이상/이하/미만/초과)·금액·속도(µs/ms/초/분)·연도를 정규식으로
   추출해 소스 텍스트에 그 숫자가 실존하는지 문자열 대조. 없으면 위반 후보.
2. **LLM 판정(보조)** (`judge_violations`) — 위반 후보 문장만 싼 모델
   (`google/gemini-3-flash` 급 저가가 아니라 `openai/gpt-5.4-nano`,
   $0.20/M in · $1.25/M out)로 "이 주장이 두 소스에서 도출 가능한가"를
   재확인한다. 결정적 검사가 오탐(예: 소스와 표현만 다른 동일 사실, "5트랙" vs
   "5개 트랙")을 낼 수 있어 이 단계가 필요하다.
3. **마킹/재생성 요청** (`apply_gate`) — 최종 위반으로 남은 문장은
   `[검증 필요]` 접두로 치환한다. 게이트 통과(`passed=True`)해야
   `hwpx-packaging` 진행. 실패 시 `[검증 필요]` 목록을 사람에게 올리거나
   `proposal-drafting`에 해당 섹션만 재생성 요청한다.

## 현재 상태 (결정적 게이트 배선 완료, LLM 판정은 여전히 블로커)

- 결정적 검사(1단계)는 **순수 함수로 완성**됐고 픽스처(A/B 실측 gpt/gemini
  산출물)로 단위 테스트 통과함(`services/agent-hub/tests/test_faithfulness_check.py`,
  정본은 `src/agent_hub/faithfulness_gate.py` — 이 스크립트는 그 정본의 shim).
- **post-react-run 핸들러로 bid-response 런에 배선됨**
  (`src/agent_hub/bid_response_faithfulness.py` →
  `tool_runtime.apply_post_react_run_hooks`, apm.yml `runtime: faithfulness-check`
  선언 기반 디스패치 — 다른 팩 런에는 발동하지 않는다). 단위 테스트:
  `services/agent-hub/tests/test_bid_response_faithfulness.py`(위반 검출/무위반
  통과/타 팩 무발동 3케이스).
- 근거 소스는 현재 **tenant core/agent 메모리 본문**(`list_runtime_memory`
  경유)만 쓴다. RFP 원문을 소스에 합치는 배선은 아직 없다 — `rfp-intake`/
  `requirement-scoring-map` 산출물(구조화된 RFP 텍스트)을 그대로 `sources`
  리스트에 추가하면 되지만, 이 스킬은 소스 텍스트 리스트를 받기만 하고 RFP
  파싱은 하지 않는다(별도 배선 필요).
- LLM 판정(2단계)은 `judge_fn` 콜러블을 주입받는 인터페이스만 선언한다 —
  실제 `openai/gpt-5.4-nano` 호출은 `apm.yml`의 `host_services_only.
  text_generation_connector` 배선 이후에 연결한다(이 팩의 스캐폴딩 범위 밖).
  **`judge_fn`이 없으면 결정적 위반을 그대로 최종 판정으로 채택한다
  (fail-closed)** — 판정 커넥터가 없다고 창조 의심 수치를 통과시키지 않는다.

## Rules

- **결정적 검사가 1차 게이트다.** LLM 판정은 결정적 검사가 "위반 후보"로 낸
  것만 좁혀서 보는 보조 단계이지, 전체 본문을 LLM에 다시 통째로 채점시키는
  방식이 아니다(비용/토큰 낭비 방지 + 재현성).
- 구조적 숫자(목차 번호 III-2, WBS 주차 W1-W2, 12주 등)는 **의도적으로
  매칭하지 않는다** — 실제 창조 벡터는 성능 %·임계치·법률 절차 수치였다
  (`_PATTERNS`가 percent/threshold/speed/money/year 카테고리로 한정).
- 위반 문장을 임의로 "안전한 문장"으로 재작성하지 않는다 — `[검증 필요]`
  마킹만 하거나 재생성을 요청한다(proposal-drafting의 MISSING-ask 가드와
  동일 톤 — 창조 대신 정직한 미확인 표시).

## 도구 경계

- 결정적 검사·마킹 로직은 이 스킬(`scripts/faithfulness_check.py`, pure
  Python, 외부 의존성 없음)이 전부 소유한다.
- LLM 판정 커넥터(`text_generation_connector`)와 RFP 원문 소스 조달은 이
  스킬 밖(`host_services_only`/`rfp-intake` 소관) — 이 스킬은 `judge_fn`/
  `sources: list[str]` 파라미터로만 받는다.

## Output Contract

- `GateResult(passed: bool, annotated_text: str, violations: list[Violation])`.
- `run-report` 스킬의 "검수 게이트 요약" 블록이 이 결과(`passed` 여부,
  위반 건수·카테고리별 분포)를 그대로 상단에 요약한다.
