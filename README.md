# AgentPackage (APM)

> **Build from yours. Run with others. Same contract.**
>
> 내가 만든 에이전트를, 다른 사람이 가진 Runtime에서, 같은 계약으로 실행한다.

APM(Agent Package)은 에이전트를 Git에서 만들고, 검증된 배포 아티팩트로 봉인해
서로 다른 Runtime에서 실행하기 위한 **Apache-2.0 오픈소스 패키지 규약과 정본 키트**다.

APM이 해결하는 문제는 간단하다. 프롬프트와 스킬은 내 컴퓨터에 있는데 모델,
검색, MCP, 메모리, 이미지 생성, 샌드박스는 다른 사람의 서버에 있을 수 있다.
APM은 이 경계를 패키지와 실행 계약으로 고정한다.

```text
<name>.agent/             내가 편집하는 Git source package
  → apm-kit lint/check    구조·능력·호스트 계약 검증
  → apm-kit build         결정적 .apm artifact 생성
<name>-<version>.apm      설치·배포 가능한 sealed package
  → Runtime adapter       local, Schift, Cloudflare, Vercel, AWS, custom host
```

## Docker for Agents

APM은 Docker를 흉내 내는 제품이 아니다. 다만 사용자가 이해하기 쉬운 비유로는
**Docker for Agents**에 가깝다.

Docker가 애플리케이션을 이미지로 봉인해 여러 환경에서 같은 입력 경계를 가진 채
실행하게 했다면, APM은 에이전트의 instructions, skills, tools, memory,
artifacts, permissions를 `.apm`으로 봉인한다. 실제 모델·검색·스토리지·MCP와
샌드박스는 각 Runtime adapter가 제공하고, 패키지는 필요한 capability를 선언한다.

| Docker | APM |
|---|---|
| application source | `.agent` source package |
| image | `.apm` sealed artifact |
| container/runtime | Runtime adapter |
| ports, env, volumes | capability·permission·data contract |
| container isolation | sandbox·network egress policy |
| image digest | package content hash |

여기서 “same result”는 LLM의 문장이 항상 바이트 단위로 같다는 뜻이 아니다.
같은 package hash, 입력·데이터 snapshot, 모델/version, temperature, Runtime
contract를 고정하면 재현 가능한 실행을 목표로 한다. 조건이 달라지면 APM이
보장하는 것은 같은 **계약·권한·trace·artifact 의미**이며, 결과 텍스트의 동일성은
보장하지 않는다.

### Governance profile: 선언만으로 보안을 주장하지 않는다

`runtime_contract.governance`의 optional `apm.governance.v0.1` profile은 Docker AI
Governance류의 실행 경계를 **요구**할 수 있다. microVM isolation, deny-by-default
network와 mount, brokered-only credential, MCP server/tool allowlist, metadata-only
audit/SIEM export, digest·signature·SBOM으로 검증한 runtime image를 한 선언으로
묶는다.

이 profile을 쓴 팩은 Runtime이 `governance_policy_enforcer`, `credential_broker`,
`audit_siem_export`, `trusted_runtime_image`를 모두 명시적으로 제공할 때만 실행한다.
하나라도 없으면 실행 전에 fail-closed로 거절된다. 즉 APM 표준이 host에 microVM,
SIEM, credential broker가 이미 있다고 주장하는 것이 아니며, 현재 이를 구현하지 않은
local·Edge·host profile은 governance 팩을 정상 팩처럼 실행할 수 없다. 정확한
필드와 금지 값은 [`docs/runtime-services-v1.md`](docs/runtime-services-v1.md),
실행 가능한 fixture는 [`examples/governance.agent`](examples/governance.agent)에 있다.

## 60초 만에 패키지 만들기

```bash
# source package를 검증한다
python3 kit/apm_kit.py lint examples/portable.agent --packs-dir examples
python3 kit/apm_kit.py check examples/portable.agent --host local-byo --packs-dir examples

# Runtime에 넘길 sealed artifact를 만든다
python3 kit/apm_kit.py build examples/portable.agent --packs-dir examples --out dist

# 받은 artifact를 새 편집 소스로만 안전하게 푼다 (기존 파일 덮어쓰기 금지)
python3 kit/apm_kit.py extract dist/portable-hello-0.1.0.apm --output work/portable.agent

# identity/version을 바꾼 fork는 새 artifact를 다시 build하고 서명해야 한다
python3 kit/apm_kit.py fork dist/portable-hello-0.1.0.apm --output work/portable-fork.agent \
  --agent-id portable-fork --version 0.2.0
```

실제 예시는 [`gongnangi-chart.agent`](examples/gongnangi-chart.agent)다.
`0.1.0` 같은 SemVer 패키지로 만들고, 다른 Runtime에서는 `.apm`만 받아
검증·설치한다. 개발 중에는 `.agent`를 직접 지정할 수 있지만 Runtime은 먼저
동일한 검증을 수행해야 한다.

`.agent`는 Git에서 관리하는 원본이고 `.apm`은 그 원본에서 빌드한 배포물이다.
Runtime은 `.agent`의 내부 구현을 직접 알지 않고 `.apm`의 선언과 capability를
자기 서비스에 연결한다.

`extract`와 `fork`는 archive traversal·링크/디렉터리 같은 비파일 엔트리·중복 이름·
매니페스트 충돌을 거절하고, 출력 디렉터리가 없거나 비어 있을 때만 쓴다. `fork`는
원래 content hash를 출력한 뒤 `pack.json`과 존재하는 `apm.yml`의 identity/version을
바꾼다. 새 `.agent`는 원 artifact의 서명이나 신뢰를 물려받지 않으므로 반드시 다시
`build`하고, 서명을 쓰는 배포 경로에서는 재서명해야 한다.

Schift Registry의 private release는 `apm.release.v1` Ed25519 receipt를 함께 발행한다.
receipt는 `agent_id@version`, content hash, artifact object key, visibility, 허용 조직,
소유 조직, 발행자를 한 서명으로 묶는다. 같은 version에서 내용이나 ACL을 바꾸는 일은
거절되며, fork·수정본은 새 version으로 올려 새 receipt를 받아야 한다. Runtime은 private
팩을 실행하기 전에 registry authorization과 이 receipt를 모두 검증한다. 로컬 파일에서
직접 연 artifact에는 registry provenance가 없으므로, 그 신뢰 경계는 로컬 사용자에게만
있다. wire 형식은 [`docs/release-provenance-v1.md`](docs/release-provenance-v1.md)다.

```bash
# 수정 가능한 source로 fork한 뒤 정상 조직 API credential로 private release를 발행한다.
schift pack fork received.apm --output work/received-fork.agent \
  --agent-id room821-bizplan-private --version 0.3.0
schift pack build work/received-fork.agent --output dist/room821-bizplan-private-0.3.0.apm
schift pack push dist/room821-bizplan-private-0.3.0.apm \
  --private-with org_room821 --private-with org_partner
```

`schift pack push`는 global admin key를 사용하지 않는다. publisher가 속한 조직의
`agents:manage` credential로 요청하고, registry가 release receipt를 발행한다.

패키지가 특정 실행기 protocol을 선호하면 `runtime_ref`에
`apm://runtime/<name>@<semver>`만 기록한다. Cloud Run resource name, Lambda ARN,
Cloudflare Worker binding, endpoint, token audience, secret은 패키지 밖의 deployment
binding으로 해석한다. 즉 같은 `.apm` hash를 유지한 채 어느 cloud/local adapter에
연결할지 바꿀 수 있다. 상세 규약은 [`docs/runtime-binding.md`](docs/runtime-binding.md)와
[`docs/runtime-invocation.md`](docs/runtime-invocation.md)다.

`.zip`처럼 파일까지 통째로 봉인하고, content-hash가 곧 주소이며, 요구하는 호스트
능력을 스스로 선언한다. 같은 팩이 **Schift, Cloudflare Workers, 로컬 Runtime,
사용자 정의 호스트**에서 돌 수 있다.

> **규범적 사양은 [`SPEC.md`](SPEC.md)** — `.agent`/`.apm` 경계, 컨테이너 바이트 레이아웃 · content-hash
> 산출식 · 능력 계약 · 발행 게이트 · 버전 판정. 이 README는 *왜*를 설명하고,
> SPEC은 *무엇이 참인가*를 정의한다.
>
> ⚠️ 이름 충돌: 여기서 APM 은 **Agent Package**(봉인 아티팩트 포맷)이고,
> `microsoft/apm`("Agent Package Manager", npm 식 의존성 관리자)과 **무관하다** —
> 코드·스키마 어느 쪽도 참조하지 않는다.

---

## 왜 그냥 "스킬"이 아닌가

한 줄로: **스킬은 에이전트가 *참조*하는 것이고, 팩은 에이전트가 *그 위에서 도는* 것이다.**

이 차이가 전부다. 참조 자료는 **우아하게 열화**한다 — 파일 하나 없으면 답이 조금
나빠진다. 실행 정의는 **조용히 오작동**한다 — 파일 하나 없으면 틀린 행동을 한다.
메일을 보내고, 문서를 제출하고, 돈을 쓴다.

그래서 참조 자료에는 없던 요구 셋이 실행 단위에서 생긴다.

### 1. 능력 협상 — 이게 핵심이다

**"이 호스트가 이 팩이 시도할 일을 실제로 할 수 있나"를 실행 전에 물어야 한다.**
스킬 포맷에는 이 질문 자체가 없다 — 협상할 실행 모델이 없기 때문이다.

```
$ apm-kit check image-gen.agent --host local-byo
✗ image-gen.agent: host 'local-byo' lacks ['usage_ledger']
```

못 채우면 **fail-closed로 거절**한다. 두 호스트 체제에서 가장 위험한 실패 모드는
크래시가 아니라 **조용히 반쯤 도는 것**이다.

### 2. 완전성 — 실행 환경은 부분적으로 존재할 수 없다

`.apm`은 팩 디렉토리를 **통째로**(`rglob`) 봉인한다. image-gen이 중첩
`typo-poster/`(14) · `promo/`(8)를 아무 선언 없이 실어 나른 것이 그 예다.

> **정직한 단서**: 이건 "봉인만이 유일한 해법"이라는 뜻은 아니다.
> [microsoft/apm#2023](https://github.com/microsoft/apm/issues/2023)이 형제 모듈
> 누락으로 *"in every project, for every target"* 크래시를 낸 건 사실이지만, 그
> 이슈 본문은 파일이 이미 `apm_modules/`에 **다 받아져 있다**고 말한다 — 배포
> 단계에서 골라 복사해서 깨진 **구현 버그**이고 디렉토리 통째 복사로 고쳐진다.
> 봉인의 값어치는 "이 클래스를 고칠 수 있다"가 아니라 **"고치는 걸 잊을 수 없다"**
> 는 데 있다. 강한 주장은 하지 않는다.

### 3. 행위 provenance — 책임 문제

"무엇을 읽었나"는 감사 대상이 아니지만 "**무엇이 실행됐나**"는 책임 문제다.
`.apm`은 content-hash가 곧 주소이고, 호스트 계약·ACL이 **아티팩트 안에** 있다.
네트워크 밖에서도, 몇 달 뒤 감사할 때도 그대로다.

> **정직한 단서**: hash는 변조를 잡지만 **출처를 증명하지 못한다.** private registry
> release는 `apm.release.v1` receipt로 그 빈칸을 메울 수 있지만, 전역 trust root는
> 일부러 규약이 정하지 않는다. 제3자 팩은 trusted issuer key와 sandbox를 함께
> 구성해야 한다.

### 요약

| | Agent Skill (폴더) | `.apm` |
|---|---|---|
| 역할 | **참조** (열화) | **실행 기반** (오작동) |
| 실행 요건 | 선언 없음 | **선언 + fail-closed 협상** |
| 파일 그래프 | 배포 구현에 달림 | 통째로 봉인 |
| 무결성 | 없음 | content-hash = 주소 |
| 거버넌스 | 외부 | 아티팩트 동봉 |
| 저작 편의 | ✅ 뛰어남 | 동일 (내용물이 곧 스킬) |

**대체가 아니라 포장이다.** 안에 든 것은 여전히 `SKILL.md`와 마크다운이고,
로컬에는 하네스 네이티브 포맷(`.claude/` `.codex/` `.cursor/`)으로 풀어놓는다.
우리 포맷을 강요하지 않는다 — 유통과 검증 단계에서만 봉인이 일한다.

## 왜 서비스 안에 있으면 안 되는가

위 논거들과 **독립적으로**, 팩이 `services/agent-hub/` 안에 사는 것 자체가 틀렸다.
로컬 실행이 영영 안 와도 그렇다.

- **변경 주기가 다르다.** 팩은 콘텐츠 주기(문구 수정)로, 서비스는 릴리즈 주기로 바뀐다.
  지금은 프롬프트 한 줄 고치려고 서비스를 재배포해야 한다.
- **정본이 둘로 갈린다.** 팩 메타가 `apm.yml`과 서비스 코드(`agent_packs.py`
  `manifest_overrides`) 양쪽에 선언돼, 한쪽만 갱신돼 번들이 구버전으로 나갈 뻔했다
  (2026-07-20, 실제 발생).
- **"DB가 SoT"가 성립 불가.** 팩이 2,237줄 서비스 모듈에 하드코딩된 채로는 거짓이다.
- **작업이 충돌한다.** 팩 작업과 서비스 작업이 같은 트리를 놓고 싸운다.

> **선결 조건**: 분리를 반쪽만 하면(=`manifest_overrides`를 남긴 채 repo만 추가)
> 정본이 2개인 채로 동기화 지점만 3개(repo → checkout → 이미지)로 늘어난다.
> **이중 선언 제거가 이동보다 먼저다.** 그리고 agent-hub는 팩을 디렉토리 이웃이
> 아니라 **빌드된 아티팩트로 소비**해야 한다 — 경로만 바꾸면 그냥 폴더 이사다.

---

## `.agent`와 `.apm`

`.agent`는 사람이 편집하는 source package다. `apm.yml`과 파일 트리가 저작 입력이고,
Runtime-specific endpoint나 secret은 넣지 않는다.

`.apm`은 `apm-kit build`가 만든 validated, hashed, distributable artifact다.
Registry에 올리거나 Runtime에 설치하는 것은 `.apm`이며, 개발 편의를 위해 Runtime이
`.agent`를 직접 받는 dev mode를 제공할 수 있어도 내부적으로는 먼저 validate해야 한다.

```text
research-to-creative.agent/       # Git source
├── apm.yml
├── agent.md
├── skills/
├── references/
└── operations/

research-to-creative-0.1.0.apm     # built artifact
```

## 구조

```
packs/<name>.agent/     apm.yml · agent.md · skills/**   ← 팩 정본
kit/                    apm-kit — 점검/빌드 키트 (agent-hub 비의존)
.claude-plugin/         marketplace.json (kit이 생성, 손으로 고치지 말 것)
```

## Runtime adapter와 capability

패키지 규약은 실행 서비스를 고정하지 않는다. 팩은 필요한 capability만 선언하고,
Runtime adapter가 실제 구현을 제공한다.

```yaml
capabilities:
  required:
    - llm.generate
    - artifact.write
  optional:
    - source.search
    - image.reference
```

같은 `.apm`을 다음처럼 연결할 수 있다.

```text
Schift adapter       → Agent Hub, Schift search, Schift artifact store
Cloudflare adapter   → Workers AI, R2, Durable Objects, Queues
Local adapter        → Ollama/ComfyUI, filesystem, SQLite
Custom adapter       → 사용자가 제공하는 API·GPU·스토리지
```

Runtime 설정은 패키지 계약과 분리한다. 예를 들어 `env.AI`, `R2_BUCKET`,
`SCHIFT_API_URL`은 `.agent`에 넣지 않고 각 adapter의 배포 설정으로 둔다.

자세한 adapter 작성 규칙은 [`docs/runtime-adapter.md`](docs/runtime-adapter.md)를
참조한다.

### 한 패키지, 여러 실행 환경

```text
.agent source
    │ lint / check / build
    ▼
.apm + content hash
    │ capability negotiation · policy · sandbox
    ├── local adapter       → BYO model, local files, SQLite
    ├── Schift adapter      → Agent Hub, search, artifact store
    ├── Cloudflare adapter  → Workers AI, R2, Durable Objects, Queues
    ├── Vercel adapter      → model provider, storage, edge/server runtime
    └── AWS adapter         → Lambda, Bedrock, S3, Step Functions
```

APM이 정하는 것은 패키지의 내용과 실행 전 계약이다. adapter가 정하는 것은
구체적인 provider SDK, credential, 배포 방식, 비용 계량, 격리 구현이다. 따라서
Schift를 사용하지 않아도 APM 규약을 구현할 수 있고, Schift Runtime을 사용해도
패키지 자체는 같은 APM 계약으로 교환할 수 있다.

`runtime_ref` binding과 task-turn transport는 Cloud Run, AWS Lambda,
Cloudflare Workers, Vercel Edge, Supabase Edge, local, custom Runtime에 같은
형태로 적용한다. Cloud Run과 Lambda reference adapter는 패키지 실행 Runtime을
대상으로 하고, Worker/Vercel/Supabase reference adapter는 현재 sealed transport,
private checkpoint, host-mediated input, redaction만 검증하는 Edge conformance
canary다. Edge canary는 Docker sandbox나 model inference를 제공한다고 주장하지
않는다. 상세 binding 형식은 [`docs/runtime-binding.md`](docs/runtime-binding.md),
wire contract는 [`docs/runtime-invocation.md`](docs/runtime-invocation.md)를 따른다.

### Agent Plugins · A2A를 기본 호환 profile로 채택

APM은 자체 플러그인 포맷이나 agent-to-agent wire protocol을 만들지 않는다.
새 runtime-services v1 패키지는 필요할 때 upstream **Agent Plugins 1.0**의
`plugin.json` · `skills/` · `mcp.json` layout과 **A2A 1.0**의 Agent Card/task
계약을 그대로 선언한다. APM이 더하는 것은 sealed artifact hash, capability
negotiation, host authorization, and sandbox/egress policy다.

```text
Agent Plugins  → plugin distribution and component discovery
A2A            → remote-agent discovery, tasks, artifacts, multi-turn input
MCP            → tool/resource wire protocol
APM            → verified package + permission + runtime/sandbox boundary
```

이 경계와 `runtime_contract`의 model DI, human input, CCLG memory transfer,
external search/data, governed MCP, and isolation rules are
[`docs/runtime-services-v1.md`](docs/runtime-services-v1.md)와
[`docs/interoperability.md`](docs/interoperability.md)에 규범적으로 정의한다.

## 유통 경로

| 경로 | 대상 | 형태 |
|---|---|---|
| **Git source** | 개발자·Runtime adapter | `<name>.agent/`를 clone해 수정·검증 |
| **`.apm` 아티팩트** | Schift·Cloudflare·local·custom Runtime | tar+매니페스트 봉인 → content-hash → 선택한 registry/store |
| **Marketplace** | Claude Code 등 로컬 하네스 | 각 팩의 public repo 또는 release (SHA 핀) |

## 규약과 상용 서비스의 경계

이 저장소의 규약·reference kit은 **Apache License 2.0**으로 공개한다. 누구나
`.agent`/`.apm` 포맷과 kit을 구현·수정·재배포할 수 있으며, 정확한 조건은
[`LICENSE`](LICENSE)를 따른다.

Schift Cloud, managed Runtime, SLA, 조직 governance, 과금, private connector는
이 repository에 포함되지 않는 별도 서비스다. APM을 구현하는 Runtime은 Schift와
무관하게 동일한 package·capability·release provenance contract를 채택할 수 있다.

## 호스트 능력 계약

```yaml
runtime_boundary:
  host_services_only: [auth, image_generation_connector, usage_ledger]
```

어휘 정본은 `kit/capabilities.json`.

```bash
python3 kit/apm_kit.py check --host agent-hub   # Cloud
python3 kit/apm_kit.py check --host local-byo   # 로컬 BYO-LLM
python3 kit/apm_kit.py lint                     # 어휘·필수필드·정체성
python3 kit/apm_kit.py market                   # marketplace.json 생성
```

`local-byo`가 제공 못 하는 것(=Cloud 전용): `usage_ledger`·`credit_metering`
(유저 머신에서 과금 원장을 강제할 방법이 없다), 서버 워커, 외부 핸드오프.

> BYO-LLM에서 과금 표면은 **데이터 레이어**(MCP 검색·ingest·저장)이지 생성이 아니다.
> 생성은 유저 구독이 낸다. 그래서 로컬 팩은 미터링 능력을 요구하지 않도록 설계한다.

## 발행은 fail-closed

이 repo는 **오픈소스 규약·키트 정본**이다. 실제 조직 전용 팩은 별도 private/public
repository에서 관리할 수 있고, `marketplace.json`은 공개 배포할 팩의 source를
가리키기만 한다. 이 repo에 조직 전용 콘텐츠를 넣지 않는 것이 원칙이다.

```yaml
marketplace:
  publish: true
  repo: https://github.com/schift-io/<pack>.git
  ref: main
  sha: <40-hex>     # 없으면 재현 불가 — kit이 경고한다
```

`lint`는 발행 대상에 한해 **테넌트 정체성 스캔**을 돌린다. 특정 org 이름/브랜드가
하드코딩된 팩은 다른 org가 설치했을 때 그 정체성이 새므로 발행을 막는다.

## 제3자 팩 실행 전 남은 필수 게이트

제3자 팩을 안전하게 받으려면 다음이 필요하다:

1. **registry release receipt** — private/corporate 배포는 `apm.release.v1`과 trusted
   issuer key 검증을 필수로 둔다. public third-party distribution도 strict Runtime에서는
   unsigned release를 거절해야 한다.
2. **프롬프트 인젝션 / 숨은 유니코드 스캔**
3. **SBOM** (SPDX/CycloneDX)

근거: 모노레포 `docs/research/2026-07-20-agent-packaging-ecosystem-survey.md`

## Runtime 예시

Cloudflare는 Workers AI와 R2를 binding으로 연결할 수 있고, Durable Objects로
상태 있는 agent 실행을 구성할 수 있다. 이 repo는 Cloudflare 계정이나 Schift
서비스를 요구하지 않는다. Runtime adapter가 `llm.generate`, `artifact.write`,
`state.durable` 같은 capability를 제공하면 같은 `.apm`을 실행할 수 있다.

공식 참고: [Workers AI bindings](https://developers.cloudflare.com/workers-ai/configuration/bindings/),
[R2 Workers API](https://developers.cloudflare.com/r2/api/workers/workers-api-reference/),
[Durable Objects](https://developers.cloudflare.com/durable-objects/)
