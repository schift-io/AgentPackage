# Agent Package (.apm)

[English](README.md)

> **Docker가 앱을 봉인했다. APM은 에이전트를 봉인한다.**

프롬프트는 내 노트북에 있다. 모델, 검색 엔진, 메모리, 도구는 남의 서버에
있다. APM은 내가 보내는 것과 Runner가 제공하는 것 사이에 선을 긋고,
실행 전에 그 선을 강제한다.

```
my-agent.agent/            ← 이걸 편집한다
  → apm-kit build
my-agent-0.1.0.apm         ← Runner가 이걸 실행한다
```

같은 `.apm`, 같은 hash, 같은 계약 — 내 컴퓨터든, 회사 서버든, 호스팅
플랫폼이든.

## Docker for Agents

APM은 Docker가 아니다. 하지만 사고방식은 같다.

| Docker | APM |
|---|---|
| 앱 소스 → 이미지 | `.agent` 소스 → `.apm` 아티팩트 |
| 컨테이너 런타임 | Runner (로컬, 서버, 커스텀) |
| 포트, env, 볼륨 | capability 선언 |
| 네트워크 격리 | 샌드박스 + egress 정책 |
| 이미지 digest | content hash (결정적) |

Docker는 *앱이 하는 일*을 봉인한다. APM은 *에이전트가 하는 일*을 봉인한다 —
지시문, 스킬, 도구, 메모리 계약, 권한 경계까지. 모델은 Runner가 주입한다.
Docker가 env를 주입하는 것과 같다.

## 설치

```bash
pip install apm-kit           # PyPI
# 또는
npx apm-kit                   # npm (설치 없이 실행)
# 또는
brew install schift-io/tap/apm-kit   # Homebrew
# 또는
git clone https://github.com/schift-io/AgentPackage && python3 kit/apm_kit.py
```

| 채널 | 패키지 | 상태 |
|---|---|---|
| PyPI | `apm-kit` | 예정 |
| npm | `apm-kit` | 예정 |
| Homebrew | `schift-io/tap/apm-kit` | 예정 |
| 소스 | 이 저장소 | **지금 사용 가능** |

Python 3.10+. 의존성 하나: `pyyaml`.

## 시작하기

```bash
# 새 에이전트 만들기
apm-kit init my-agent --display-name "내 에이전트" --description "회의록에서 주간 보고서 작성"

# 결과:
# my-agent.agent/
# ├── agent.md     ← 여기에 지시문 작성
# ├── apm.yml      ← 이름, 버전, 설명
# └── pack.json    ← 런타임 설정

# 검증
apm-kit lint my-agent.agent
apm-kit check my-agent.agent --host local-byo

# 봉인된 아티팩트 빌드
apm-kit build my-agent.agent
# → my-agent-0.1.0.apm

# 실행
# 로컬:  내 Runner, 내 모델. 무료.
# 서버:  schift publish → Schift Runner. 관리형 검색, 거버넌스, 과금.
```

## 패키지 안에 뭐가 들어가나

```
my-agent.agent/
├── apm.yml          이름, 버전, 공개 범위
├── agent.md         지시문 — 실제 프롬프트
├── pack.json        런타임 설정, 스킬, 도구, 파이프라인
├── skills/          재사용 가능한 스킬 정의
├── scripts/         실행 가능한 작업 (선택)
└── references/      에이전트가 참조할 정적 데이터 (선택)
```

패키지에 **절대 넣지 않는 것**: API 키. 모델 엔드포인트. 클라우드 리소스 ID.
과금 설정. 시크릿. Runner가 실행 시점에 전부 주입한다. 패키지는 이식 가능하게
유지한다.

## Capability 협상

핵심 아이디어다. 뭔가를 실행하기 전에, Runner가 패키지가 요구하는 것을
실제로 제공할 수 있는지 확인한다.

```yaml
runtime_boundary:
  host_services_only:
    - model_inference_adapter
    - human_input_channel
    - cclg_memory_read
```

Runner가 선언된 capability를 제공하지 못하면 **실행 전에 거절**한다.
조용한 폴백 없다. 반쯤 도는 실행 없다. 가장 위험한 실패는 크래시가
아니라 — 에이전트가 조용히 잘못된 일을 하는 것이다.

```bash
$ apm-kit check my-agent.agent --host local-byo
✗ my-agent.agent: host 'local-byo' lacks ['usage_ledger']
```

## 실행 구조

```
.agent 소스
    │  lint → check → build
    ▼
.apm 아티팩트 (결정적 tar.gz, content-addressed)
    │  capability 협상
    ├── apm-runner        아무 모델(Claude/GPT/Kimi/Ollama). 무료, 오픈.
    ├── Agent Runtime     관리형 검색, 거버넌스, 모델 게이트웨이, 과금.
    └── Custom Runner     내 인프라, 내 어댑터, 내 규칙.
```

### apm-runner (오픈, 무료)

**아무 모델로 `.apm`을 실행한다.** Schift 계정 불필요. codex 의존 없음.

```bash
# 배포 파일 생성
npx @schift-io/mcp pack deploy my-agent-0.1.0.apm --target docker

# Claude로 실행
cd deploy && docker build -t my-agent .
docker run -e APM_MODEL_PROVIDER=anthropic -e ANTHROPIC_API_KEY=sk-... \
  -p 8080:8080 my-agent

# 로컬 Ollama로 실행
docker run -e APM_MODEL_PROVIDER=ollama \
  -e APM_MODEL_BASE_URL=http://host.docker.internal:11434/v1 \
  -p 8080:8080 my-agent
```

지원 프로바이더: `anthropic` · `openai` · `kimi` · `deepseek` · `groq` ·
`together` · `ollama` · `google`. 미등록 프로바이더는
`APM_MODEL_BASE_URL` + `APM_MODEL_API_KEY`로 연결.

베이스 이미지: [`ghcr.io/schift-io/apm-runner`](https://github.com/schift-io/schift/pkgs/container/apm-runner)

### Agent Runtime (관리형, 유료)

```bash
npx @schift-io/mcp pack push my-agent-0.1.0.apm
```

검색, 메모리, 거버넌스, 과금 전부 포함. 모든 모델 호출이 원장에 기록된다.

## CLI

| 명령 | 설명 |
|---|---|
| `init <name>` | 새 `.agent` 생성 |
| `import <path>` | SKILL.md / .claude / .cursorrules 변환 |
| `lint <pack>` | 구조, 필드, 정체성 패턴 검증 |
| `check <pack> --host <profile>` | 이 Runner가 이 패키지를 실행할 수 있나? |
| `build <pack>` | `.apm`으로 봉인 |
| `deploy <apm> --target <t>` | 배포 파일 생성 (docker/compose/cloud-run/lambda) |
| `extract <apm> --output <dir>` | 편집 가능한 소스로 추출 |
| `fork <apm> --output <dir> --agent-id <id>` | 새 identity와 버전으로 추출 |

## 발행

```bash
apm-kit build my-agent.agent
schift pack push my-agent-0.1.0.apm --org org_mycompany

# 비공개 발행 (조직 ACL)
schift pack push my-agent-0.1.0.apm \
  --private-with org_mycompany \
  --private-with org_partner
```

발행된 릴리스마다 Ed25519 서명 receipt (`apm.release.v1`)가 붙는다.
content hash + 버전 + 공개 범위 + 허용 조직을 하나로 묶는다. Runner는
실행 전에 이걸 검증한다. 변조되거나 서명 없는 패키지는 거절된다.

## 패키지 vs 스킬

스킬은 에이전트가 *읽는* 것이다. 패키지는 에이전트가 *위에서 도는* 것이다.

스킬 파일이 빠지면 → 답이 나빠진다.
패키지 파일이 빠지면 → 에이전트가 잘못된 메일을 보낸다.

| | 스킬 | 패키지 |
|---|---|---|
| 실패 | 열화 | **오작동** |
| 계약 | 없음 | 선언 + fail-closed |
| 무결성 | 없음 | content hash |
| 거버넌스 | 외부 | 동봉 |

## 상호운용성

APM은 프로토콜을 재발명하지 않는다. 패키지를 봉인하고 경계를 강제한다.

| 표준 | 역할 | APM의 위치 |
|---|---|---|
| Agent Plugins 1.0 | 플러그인 탐색 | APM이 플러그인 매니페스트를 번들 |
| A2A 1.0 | 에이전트 간 작업 | APM이 agent card 템플릿을 선언 |
| MCP | 도구 프로토콜 | APM이 허용 MCP 서버/도구를 제한 |

상세: [`docs/interoperability.md`](docs/interoperability.md)

## 사양

[`SPEC.md`](SPEC.md)가 규범적 사양이다. 컨테이너 바이트 레이아웃, content hash
알고리즘, capability 어휘, 버전 해석, 발행 게이트, release provenance. 이
README에 있는 건 설명이고, SPEC에 있는 건 계약이다.

## 라이선스

**Schift License v2.0** — [`LICENSE`](LICENSE)

Apache 2.0 기반 + §5 매출 문턱. LFM Open License 패턴.

| | |
|---|---|
| 패키지 만들기, 빌드, 수정, 배포 | **무료** |
| 상업적 사용 (연매출 $10M 미만) | **무료** |
| `.apm` 호환 도구 직접 구현 | **무료** (포맷은 오픈 스펙) |
| 상업적 사용 (연매출 $10M 이상) | [상업 라이선스](mailto:hello@schift.io) |

`.apm` 포맷은 오픈 스펙이다. reader, writer, runner를 허락 없이 만들어도
된다 — LICENSE §6.

---

[Spec](SPEC.md) · [Docs](docs/) · [Examples](examples/) · [English](README.md)
