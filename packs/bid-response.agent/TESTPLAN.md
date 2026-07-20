# bid-response.agent — E2E 런 하네스 (TESTPLAN)

**이 문서는 하네스 준비만 한다. 라이브 호출은 하지 않았다.** SCAFFOLD.md의
GO 없이는 실제 등록·배포·활성화도 하지 않는다. 아래는 Test 단계(스모크,
SCAFFOLD.md #5)에서 그대로 실행 가능하도록 절차·커맨드·SQL을 정리한 것.

## 0. 결론 먼저 — 이 팩은 아직 "실행 불가"다

`services/agent-hub/src/agent_hub/agent_packs.py` 전체를 grep했지만
`bid-response`/`bid_response` 참조가 **0건**이다. 이 서비스의 팩 레지스트리는
`apm.yml` 같은 선언 파일을 스캔하는 제너릭 로더가 아니라, `bizplan`/`deck`/
`cardnews`/`accounting` 등 각 팩을 `AgentPack(...)` dataclass 인스턴스로
**Python에 하드코딩**하는 구조다 (agent.md 콘텐츠, skill manifest, variant
keyword, non-runnable id 전부 모듈 상수로 선언 후 `agent_packs.py`에서 조립).

즉 SCAFFOLD.md가 "GO 필요"라고 명시한 항목 중:
- **#2 (`install_pack_seeds()` 배선)** — 사실이고, 그 이상이다. 단순
  seed 훅 하나가 아니라 **agent_packs.py에 새 AgentPack 인스턴스를 추가하는
  코드 변경**이 없으면 `/v1/agents/bid-response/config`도, bootstrap도 전부
  404/"unknown agent"로 실패한다.
- **#4 (`.apm` 레지스트리 등록)** — `schift-api/server/routes/apm_registry.py`는
  R2 content-addressed ref 시스템(배포 파이프라인 전용, `SCHIFT_ADMIN_KEY`
  필요)이다. 로컬 dev 등록 경로가 별도로 없다 — 이건 prod 배포 reconcile이
  쓰는 것이지 로컬 스모크용이 아니다. 로컬 스모크는 agent-hub 안에
  AgentPack을 하드코딩하는 것으로 충분하고, 그게 유일한 로컬 실행 경로다.

따라서 이 문서의 §2~§5는 **"코드 배선이 끝났다고 가정했을 때"의 절차**다.
실행하려면 먼저 SCAFFOLD.md #2(agent_packs.py에 bid-response AgentPack 추가)가
선행되어야 한다. 이 임무(C)는 그 코드를 작성하지 않는다 — 하네스만 준비한다.

## 1. 로컬 실행 경로 — agent-hub 스택 기동

정본: `services/agent-hub/README.md`, `services/agent-hub/docker-compose.local.yml`.

```bash
docker compose -f services/agent-hub/docker-compose.local.yml up --build -d
curl http://127.0.0.1:8087/health
```

- 로컬 compose는 `mock-ocr`(8080), `mock-rtx`(8080), `mock-rag-worker`(8088)를
  같이 띄운다. 실제 LLM 호출 없이 배선만 검증하는 용도 — bid-response 팩의
  `text_model` 스위칭(§3)을 검증하려면 이 mock 스택으로는 부족하다(모델 호출이
  mock으로 흡수됨).
- 실 모델 호출까지 검증하려면 `docker-compose.real.yml`(공개/서버 라우트는
  `docker-compose.server.yml`)을 써야 한다. README의 "For a public/server
  proof" 절 커맨드가 `DEEPSEEK_API_KEY`/`GLM_API_KEY`/`KIMI_API_KEY` 등을
  요구하는데, `openai/gpt-5.4-mini`·`google/gemini-3.5-flash` 스위칭 검증에는
  이 서버 compose가 아니라 **schift-api의 `/v1/chat` 경로(§3)**를 쓰는 편이
  맞다 — agent-hub 자체는 인메모리 컨트롤 플레인이고 실제 텍스트 생성은
  `text_model` 파라미터를 통해 schift-api LLM 라우터로 위임되는 구조이기
  때문(`apm.yml`의 `provider_catalog_ref`가 `schift-api/server/llm/router.py`).

### 알려진 로컬 env 함정 (README/기존 사고 이력에서 확인)

1. **`ROOM821_AGENT_HUB_SHARED_SECRET`이 설정돼 있으면** 모든 non-health
   요청에 `X-Room821-Agent-Hub-Secret` 헤더가 필요하다. 로컬 compose 기본값은
   unset이라 이 프로젝트 로컬 스모크에서는 보통 문제 없음 — 하지만 `.env.local`에
   값이 있다면 curl에 헤더를 추가해야 함.
2. **`AGENT_HUB_RAG_HOOK_REQUIRED=1`**이 로컬 compose 기본값이다. `mock-rag-worker`가
   안 뜨면 모든 세션 요청이 hook 실패로 막힌다 — `docker compose ps`로 3개 mock이
   모두 healthy인지 먼저 확인.
3. **`tenant=room821`은 room821 API 키가 아니면 spoof 차단된다**
   (`project_agent_hub_api_key_runs.md` 메모 확인). bid-response는 Room821
   전용 팩(`access_scope: org`, `owner_org_id=org_room821`)이므로 이 스모크는
   **반드시 Room821 org의 SCHIFT_API_KEY**로 실행해야 한다 — 중립 tenant로
   바꾸면 안 됨(공개 모델 라우팅으로 잘못 새서 org 전용 memory 그라운딩이
   깨짐).
4. **`docker-compose.real.yml`은 legacy `agent_hub.real_inference` adapter를
   `legacy-adapters` profile 뒤에 숨겨둔다** — 기본 profile로 up하면 그
   adapter 없이 뜨므로, 필요 시 `--profile legacy-adapters` 명시.

## 2. 팩 로컬 등록 절차 (선행 코드 배선 이후)

**커맨드 한 줄로 되는 등록 절차는 없다.** 이 서비스의 등록은 코드다:

1. `services/agent-hub/src/agent_hub/agent_packs.py`에 다른 팩(예:
   `DECK_*`, `ACCOUNTING_*`)과 동일한 패턴으로 `BID_RESPONSE_AGENTS_MD_CONTENT`,
   `BID_RESPONSE_SKILL_MANIFESTS`, `BID_RESPONSE_NON_RUNNABLE_AGENT_IDS` 등을
   선언하고, `agent_id="bid-response"`인 `AgentPack(...)` 인스턴스를 등록해야
   한다. 이 작업은 SCAFFOLD.md #2 그 자체이며 이 임무(C)의 소유 범위 밖이다
   (다른 세션 소유 파일 수정 금지 규칙).
2. 배선이 끝나면 로컬 확인은 다음으로:
   ```bash
   curl http://127.0.0.1:8087/v1/agents | python3 -m json.tool | grep -A2 bid-response
   curl http://127.0.0.1:8087/v1/agents/bid-response/config
   ```
3. **prod `.apm` R2 레지스트리(`/v1/apm/registry`) 등록은 이 스모크에 필요
   없다.** 그건 배포 reconcile 전용 표면이고, 로컬 agent-hub는 §2-1 코드
   배선만으로 팩을 인식한다. SCAFFOLD.md #4는 prod 배포 게이트이지 로컬
   스모크 전제조건이 아니다 — 순서를 착각하지 말 것.

## 3. 런 인보크 경로 — API 키 기반 (콘솔 아님)

정본: `memory/project_agent_hub_api_key_runs.md`, `schift-api/server/routes/agent_hub_facade.py`.

- facade가 API 키를 허용하려면 scope `agents:documents:run`이 필요하고,
  allowlist 경로만 통과한다: `/v1/agents`, `/v1/agents/{id}/config`,
  `/v1/sessions/{s}/bootstrap`, `memory:append`, `intake:question|answer`,
  `agentic-runs`, `artifacts`, `images`, `images:search`, `export-*`.
- 헤더: `Authorization: Bearer $SCHIFT_API_KEY` + `X-Org-Id: $SCHIFT_ORG_ID`.
- **Room821 전용 키를 써야 한다** (§1 함정 #3). `.env.local`의 일반
  `SCHIFT_API_KEY`/`SCHIFT_ORG_ID`가 아니라 `SCHIFT_API_KEY_SCHIFT`/
  `SCHIFT_ORG_ID_SCHIFT`(Room821/Schift 분리 — `project_org_model_room821_schift_split.md`)
  중 Room821에 해당하는 값인지 먼저 확인. **값은 여기 출력하지 않음.**

흐름 (다른 검증된 팩과 동일 패턴):

```bash
export API_BASE="${SCHIFT_API_URL:-http://127.0.0.1:8000}"
export ORG_ID="$SCHIFT_ORG_ID"          # Room821 org id로 교체 확인 후 실행
export SESSION_ID="room821:bid-response:testuser:conv1"

# 1) bootstrap
curl -sS -X POST "$API_BASE/v1/sessions/$SESSION_ID/bootstrap" \
  -H "Authorization: Bearer $SCHIFT_API_KEY" -H "X-Org-Id: $ORG_ID" \
  -H "Content-Type: application/json" -d '{"agent_id":"bid-response"}'

# 2) intake:question (있으면) → intake:answer
curl -sS -X POST "$API_BASE/v1/sessions/$SESSION_ID/intake:question" \
  -H "Authorization: Bearer $SCHIFT_API_KEY" -H "X-Org-Id: $ORG_ID"

# 3) agentic-runs (본 실행)
curl -sS -X POST "$API_BASE/v1/sessions/$SESSION_ID/agentic-runs" \
  -H "Authorization: Bearer $SCHIFT_API_KEY" -H "X-Org-Id: $ORG_ID" \
  -H "Content-Type: application/json" \
  -d '{"message": "<RFP 텍스트 또는 첨부 참조>"}'

# 4) artifacts 조회
curl -sS "$API_BASE/v1/sessions/$SESSION_ID/artifacts" \
  -H "Authorization: Bearer $SCHIFT_API_KEY" -H "X-Org-Id: $ORG_ID"
```

### 모델 오버라이드 (openai/gpt-5.4-mini ↔ google/gemini-*)

`apm.yml`의 `awp_operations[0].text_model.model_env = BID_RESPONSE_TEXT_MODEL`.
런타임 실행 전에 이 env로 오버라이드:

```bash
BID_RESPONSE_TEXT_MODEL=openai/gpt-5.4-mini        # 디폴트
BID_RESPONSE_TEXT_MODEL=google/gemini-3.5-flash    # 대안 A
```

**중요 — 카탈로그 확인 결과: `google/gemini-3-flash`는 등록돼 있지 않다.**
`schift-api/server/llm/router.py`의 `PROVIDER_MODELS["google"]`에는
`gemini-3.5-flash`, `gemini-3.1-pro/flash/flash-lite`, `gemini-2.5-*`만
있고 `gemini-3-flash`는 없다. 반면 `schift-api/server/tokenizer.py`의 가격표
(`_get_encoding` 아래 pricing 딕셔너리)에는 `("chat_input", "google/gemini-3-flash")`
`0.50/M`, `("chat_output", ...)` `3.00/M`이 **존재한다** — 즉 가격은 정의돼
있지만 실제로 호출 가능한 모델 리스트에는 없는 상태(가격표 선반영, 라우터
등록 누락 또는 아직 출시 전 placeholder로 추정, 확인 안 됨). `apm.yml`의
`cheapest_alt: google/gemini-3-flash`를 그대로 쓰면 라우터가 모델을 못 찾아
실패할 가능성이 높다.

→ **A/B 테스트는 지시대로 `openai/gpt-5.4-mini` ↔ `google/gemini-3.5-flash`로
진행한다** (`gemini-3-flash`는 카탈로그 미등록이라 스킵). `apm.yml`의
`cheapest_alt` 필드는 이 감사 결과를 반영해 스모크 전에 정정이 필요하다
(이 임무 범위 밖 — main에 보고).

## 4. cr 실측 쿼리 — llm_cost_log

테이블: `llm_cost_log` (모델 `schift-api/server/models/ops.py:LLMCostLog`,
기록 함수 `server/store/llm_costs.py:record_llm_cost`). 컬럼: `org_id`,
`request_id`, `source`, `model`, `provider`, `input_tokens`, `output_tokens`,
`cached_input_tokens`, `provider_cost_usd`, `credits_charged`,
`billing_status`, `created_at`.

### 로컬 스택에서 실제로 쌓이는지

- 로컬 Postgres는 root `docker-compose.yml`(`db` 서비스, host port **5433**,
  db `schift`, user `schift`)로 뜬다. `schift-api/.env.local`의
  `DATABASE_URL`은 host `db`(compose 네트워크 내부 이름)를 가리키므로, API를
  호스트에서 직접 uvicorn으로 돌릴 때는 `DATABASE_URL`을
  `postgresql://schift:schift_dev@127.0.0.1:5433/schift`로 바꿔 접속하거나,
  `scripts/dev/api-local.sh`(SQLite 임시 DB, `SCHIFT_LOCAL_USE_DATABASE_URL`
  미설정 시 기본)를 쓴다. **SQLite 로컬 모드로 스모크하면 `llm_cost_log`
  테이블 자체는 생기지만(SQLModel `create_all`), Postgres 전용 인덱스/제약이
  빠질 수 있어 prod 스키마와 완전히 동일하진 않다** — cr 실측은
  `SCHIFT_LOCAL_USE_DATABASE_URL=1` + 로컬 Postgres(5433) 조합으로 하는 게
  더 신뢰도 높음.
- `record_llm_cost`는 챗 완료 경로에서 호출되므로, agent-hub → schift-api
  `/v1/chat`(또는 agentic-run 내부에서 위임하는 완료 호출) 경로가 실제로
  타면 로컬 DB에도 쌓인다. **로컬 mock 스택(`docker-compose.local.yml`)만
  쓰면 mock-rtx가 진짜 LLM 호출을 흡수하므로 `llm_cost_log`에 아무 것도
  안 쌓인다** — cr 실측을 원하면 §1에서 언급한 대로 schift-api의 실제
  `/v1/chat` 호출 경로(진짜 provider 키 필요)까지 타야 한다.

### SQL — 특정 run의 소모 조회

`request_id`를 run 단위로 채번해서 넘기는 게 이상적이지만, agentic-run이
`request_id`를 채우지 않는 경우 `source`(예: `"agent_hub:bid-response"`류로
넘겨야 함, 현재 코드에 그런 source 태깅이 없음 — 배선 필요 항목으로 별도
기록) + `created_at` 시간 범위 + `org_id`로 근사 조회한다.

```sql
-- 방법 1: request_id를 채번해 넘긴 경우 (권장, 배선 확인 필요)
SELECT id, model, provider, input_tokens, output_tokens,
       cached_input_tokens, provider_cost_usd, credits_charged,
       billing_status, created_at
FROM llm_cost_log
WHERE org_id = :org_id
  AND request_id = :run_id
ORDER BY created_at;

-- 방법 2: source + 시간창으로 근사 (request_id 배선 전 임시 방편)
SELECT id, model, provider, input_tokens, output_tokens,
       cached_input_tokens, provider_cost_usd, credits_charged, created_at
FROM llm_cost_log
WHERE org_id = :org_id
  AND created_at BETWEEN :run_started_at AND :run_finished_at
ORDER BY created_at;

-- 런 합산 (§3 A/B 비교용 — 모델별 합)
SELECT model, provider,
       SUM(input_tokens)  AS total_input_tokens,
       SUM(output_tokens) AS total_output_tokens,
       SUM(cached_input_tokens) AS total_cached_input_tokens,
       SUM(provider_cost_usd)  AS total_provider_cost_usd,
       SUM(credits_charged)    AS total_credits_charged,
       COUNT(*) AS call_count
FROM llm_cost_log
WHERE org_id = :org_id
  AND created_at BETWEEN :run_started_at AND :run_finished_at
GROUP BY model, provider
ORDER BY total_provider_cost_usd DESC;
```

접속 예:

```bash
docker compose up -d db   # root docker-compose.yml
PGPASSWORD=schift_dev psql -h 127.0.0.1 -p 5433 -U schift -d schift -c \
  "SELECT model, provider, SUM(input_tokens), SUM(output_tokens), SUM(provider_cost_usd) \
   FROM llm_cost_log WHERE org_id='<room821-org-id>' \
   AND created_at BETWEEN '<start-iso>' AND '<end-iso>' GROUP BY model, provider;"
```

Non-LLM overage(§4 밖, 참고용): `usage_cost_log`(`server/store/usage_costs.py`)는
search/ingest/execution/storage/web_search 축이라 이 팩의 텍스트 생성 cr에는
직접 안 걸림 — bid-response 런이 RAG bucket 조회(`company-memory-grounding`
skill)를 하면 그쪽도 같이 확인 필요.

## 5. A/B 프로토콜

**고정 변수**: 동일 RFP 입력 파일(나라장터 공고 1건, PROOF.md 실측에 쓰인 것과
동급 난이도), 동일 memory-pack(company core memory — 아직 `.cclg` 어댑터
미착수라 SCAFFOLD.md #1도 선행 필요. 이 조건이 안 되면 A/B는 회사 컨텍스트
없이 진행되어 PROOF.md의 12분 실측과 비교 불가하다는 점을 리포트에 명시할 것).

**가변 변수**: `BID_RESPONSE_TEXT_MODEL` 하나만 스위칭.
- A: `openai/gpt-5.4-mini` (디폴트)
- B: `google/gemini-3.5-flash` (품질 상향 대안 — `gemini-3-flash`는 §3 사유로 스킵)

**측정 항목** (각 run마다 기록):
| 항목 | 출처 |
|---|---|
| 벽시계 시간 | `agentic-runs` 호출 전후 타임스탬프 (클라이언트 측정) |
| 입력/출력 토큰 | §4 SQL `SUM(input_tokens)`/`SUM(output_tokens)` |
| $ (provider raw cost) | §4 SQL `SUM(provider_cost_usd)` |
| cr (플랫폼 과금) | §4 SQL `SUM(credits_charged)` — `schift-api/server/billing/pricing.py` 환산율 적용 후 |
| placeholder 잔여 | 산출 HWPX/markdown 본문에서 `{{...}}` 또는 미채움 필드 grep (hwpx-packaging/run-report skill 산출 스펙 참조) |
| 섹션 완성도 | run-report skill 산출 요약의 섹션 카운트 vs `per_run_section_count_estimate: 12`(apm.yml) 대비 |

**진행 순서**: 1) SCAFFOLD.md #1(memory-pack `.cclg` 어댑터), #2(agent_packs.py
배선) 완료 확인 → 2) §1 로컬 스택 기동 → 3) §3 흐름으로 A 실행, 결과·§4 SQL
기록 → 4) `BID_RESPONSE_TEXT_MODEL` 스위칭 후 B 실행, 동일 세션 재사용
금지(새 `SESSION_ID`로 격리, memory 오염 방지) → 5) 두 결과를 표로 비교.

## 6. 필요 API 키 목록 (이름만 — 값 미출력)

| env var | 용도 | 로컬(.env.local) 존재 확인 |
|---|---|---|
| `SCHIFT_API_KEY` | facade API 키 인증 (Bearer) | **SET** — 단, Room821 org 소속인지 별도 확인 필요 |
| `SCHIFT_ORG_ID` | `X-Org-Id` 헤더 | **SET** |
| `SCHIFT_API_KEY_SCHIFT` / `SCHIFT_ORG_ID_SCHIFT` | Room821/Schift org 분리 시 대안 키 세트 | **SET** |
| `SCHIFT_API_URL` | facade base URL | **SET** |
| `SCHIFT_ADMIN_KEY` | `.apm` 레지스트리(prod reconcile) — 이 스모크에는 불필요(§2-3) | 확인 안 함(불필요 판단) |
| `OPENAI_API_KEY` 또는 provider-side 키 (라우터가 platform-managed 키를 쓰는지 org BYOK인지 확인 필요) | `openai/gpt-5.4-mini` 실호출 | **미확인** — `schift-api/server/llm/router.py` provider_source(platform/byok) 분기 확인 필요, 이 임무에서 grep만 하고 존재 여부 미검증 |
| `GOOGLE_API_KEY` / Gemini 키 | `google/gemini-3.5-flash` 실호출 | **미확인**, 상동 |
| `SCHIFT_LLM_API_KEY` | Room821 RTX 라우팅용(이 팩은 안 씀 — public router 경로라 참고용) | 로컬 `.env.local`엔 없음(README 예시가 `/tmp/schift-llm-router-api-key` 파일에서 읽음) |

## 요약

- 로컬 스택(agent-hub mock compose)은 기동 가능하나, **bid-response 팩은
  agent_packs.py에 등록되어 있지 않아 지금 이 상태로는 bootstrap조차 실패한다.**
- API 키 기반 run 인보크 경로는 기존에 검증된 패턴(facade allowlist +
  Room821 전용 키)을 그대로 재사용 가능 — 키 이름은 모두 `.env.local`에
  존재.
- 모델 스위칭은 `BID_RESPONSE_TEXT_MODEL` env 하나로 가능하나 **카탈로그
  감사 결과 `google/gemini-3-flash`는 등록 안 됨** → 대안은
  `google/gemini-3.5-flash`.
- cr 실측은 `llm_cost_log`에서 가능하나 로컬 mock 스택으로는 안 쌓이고,
  실제 provider 호출 경로(schift-api `/v1/chat`)까지 타야 한다. 로컬 Postgres는
  root `docker-compose.yml`(port 5433)로 별도 기동 필요.
- provider 쪽 실제 API 키(OpenAI/Google)가 로컬에 있는지는 **미확인** — 이건
  `schift-api/server/llm/router.py`의 platform-managed 키 저장 위치를 확인해야
  하는데 이 임무 범위(agent-hub apm 문서+하네스) 밖이라 grep만 하고 결론 내지
  않음.
