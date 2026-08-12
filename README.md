# Agent Package (`.agent` → `.apm`)

에이전트 팩을 Git에서 만들고, 검증된 배포 아티팩트로 봉인해 어떤 Runtime에서도
실행할 수 있게 하는 오픈소스 규약 + 정본 저장소.

Node module의 흐름과 비슷하다.

```text
<name>.agent/             편집 가능한 소스 패키지
  → apm-kit validate      계약·능력 검증
  → apm-kit build         결정적 bundle 생성
<name>-<version>.apm      설치·배포 가능한 bundle
  → Runtime adapter       Schift, Cloudflare, local, custom host
```

`.agent`는 Git에서 관리하는 원본이고 `.apm`은 그 원본에서 빌드한 배포물이다.
Runtime은 `.agent`의 내부 구현을 직접 알지 않고 `.apm`의 선언과 capability를
자기 서비스에 연결한다.

`.zip`처럼 파일까지 통째로 봉인하고, content-hash가 곧 주소이며, 요구하는 호스트
능력을 스스로 선언한다. 같은 팩이 **Schift, Cloudflare Workers, 로컬 Runtime,
사용자 정의 호스트**에서 돌 수 있다.

> **규범적 사양은 [`SPEC.md`](SPEC.md)** — `.agent`/`.apm` 경계, 컨테이너 바이트 레이아웃 · content-hash
> 산출식 · 능력 계약 · 발행 게이트 · 버전 판정. 이 README 는 *왜* 를 논증하고,
> SPEC 은 *무엇이 참인가* 를 정의한다. 라이선스 Apache-2.0([`LICENSE`](LICENSE)).
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

> **정직한 단서**: hash는 변조를 잡지만 **출처를 증명하지 못한다.** 그건 서명의
> 몫이고 아직 없다. 자사 배포에서 hash는 주로 위생이며, 제3자 팩을 받기 시작할 때
> 비로소 방어가 된다(그때는 서명이 함께 필요하다).

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

## 유통 경로

| 경로 | 대상 | 형태 |
|---|---|---|
| **Git source** | 개발자·Runtime adapter | `<name>.agent/`를 clone해 수정·검증 |
| **`.apm` 아티팩트** | Schift·Cloudflare·local·custom Runtime | tar+매니페스트 봉인 → content-hash → 선택한 registry/store |
| **Marketplace** | Claude Code 등 로컬 하네스 | 각 팩의 public repo 또는 release (SHA 핀) |

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

이 repo는 **공개 규약·키트 정본**이다. 실제 조직 전용 팩은 별도 private/public
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

## 제3자 팩 실행 전 필수 (아직 없음)

제3자 팩을 안전하게 받으려면 다음이 필요하다:

1. **아티팩트 서명** — 현재는 변조 감지만 하고 발행자 신원 증명이 없다
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
