# Agent Package (`.apm`)

에이전트 팩을 **봉인된 아티팩트 하나**로 유통하는 포맷 + 그 정본 저장소.

`.zip`처럼 파일까지 통째로 봉인하고, content-hash가 곧 주소이며, 요구하는 호스트
능력을 스스로 선언한다. 같은 팩이 **Schift Cloud와 로컬 Claude Code/Codex 양쪽에서**
돈다.

---

## 왜 그냥 "스킬"이 아닌가

Agent Skill(폴더 + `SKILL.md`)은 훌륭하지만 **배포 단위가 아니라 저작 단위**다.
남에게 건네는 순간 네 가지가 깨진다.

### 1. 파일 그래프가 안 따라온다

스킬 배포는 "참조된 파일만 골라 복사"하는 경향이 있다. 형제 모듈이 빠지면 터진다.
실제 사례 — [microsoft/apm#2023](https://github.com/microsoft/apm/issues/2023):

> *"required sibling modules are not copied... Every deployed hook crashes with
> `Cannot find module './ponytail-config'`, **in every project, for every target**."*
> 게다가 패키지 자신의 `package.json`이 뒤에 남겨져, 소비자의 `"type": "module"`이
> 남의 CommonJS에 적용돼 더 일찍 죽는다.

`.apm`은 팩 디렉토리를 **통째로**(`rglob`) 봉인한다. 이 버그 클래스가 **구조적으로
발생 불가능**하다. image-gen 팩이 중첩 `typo-poster/`(14) · `promo/`(8)를 아무 선언
없이 그대로 실어 나른 것이 그 증거다.

### 2. "이게 진짜 그건지" 알 수 없다

폴더 복사에는 무결성 개념이 없다. `.apm`은 **canonical-JSON 매니페스트 + 전체 파일
집합의 content-hash가 곧 주소**다. 받은 쪽이 hash를 재계산해 변조/드리프트를 잡는다
(`verify_apm_bundle`). 태그는 편의고 hash가 진실이다.

### 3. 돌아갈 환경인지 사전에 알 수 없다

스킬은 "뭐가 있어야 도는지"를 선언하지 않는다. 없으면 **런타임에 조용히 반쯤 돌다가**
틀린 답을 낸다 — 두 호스트 체제에서 가장 위험한 실패 모드다.

`.apm`은 요구 능력을 선언하고, 호스트가 못 채우면 **실행 전에 fail-closed로 거절**한다:

```
$ apm-kit check image-gen.agent --host local-byo
✗ image-gen.agent: host 'local-byo' lacks ['usage_ledger']
```

### 4. 거버넌스가 아티팩트와 함께 여행하지 않는다

git-fetch 모델은 연결이 끊기면 계약도 사라진다. `.apm`은 호스트 계약·ACL·provenance가
**아티팩트 안에** 있다. 네트워크 밖에서도, 몇 달 뒤 감사할 때도 그대로다.

### 요약

| | Agent Skill (폴더) | `.apm` |
|---|---|---|
| 파일 그래프 | 참조된 것만 | **통째로 봉인** |
| 무결성 | 없음 | **content-hash = 주소** |
| 실행 요건 | 선언 없음 | **선언 + fail-closed 검사** |
| 거버넌스 | 외부(레지스트리/네트워크) | **아티팩트 동봉** |
| 저작 편의 | ✅ 뛰어남 | 동일 (내용물이 곧 스킬) |

**대체가 아니라 포장이다.** 안에 든 것은 여전히 `SKILL.md`와 마크다운이고,
로컬에는 하네스 네이티브 포맷(`.claude/` `.codex/` `.cursor/`)으로 풀어놓는다.
우리 포맷을 강요하지 않는다 — 유통과 검증 단계에서만 봉인이 일한다.

---

## 구조

```
packs/<name>.agent/     apm.yml · agent.md · skills/**   ← 팩 정본
kit/                    apm-kit — 점검/빌드 키트 (agent-hub 비의존)
.claude-plugin/         marketplace.json (kit이 생성, 손으로 고치지 말 것)
```

## 두 가지 유통 경로

| 경로 | 대상 | 형태 |
|---|---|---|
| **`.apm` 아티팩트** | Schift Cloud (agent-hub) | tar+매니페스트 봉인 → content-hash → R2 → `apm_refs` DB |
| **Claude Code 마켓플레이스** | 로컬 하네스 (BYO-LLM) | `/plugin marketplace add` → 각 팩의 public repo (SHA 핀) |

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

이 repo는 **private**이고 내부 팩을 담는다. 공개 팩은 **자기 public repo**를 갖고,
여기 `marketplace.json`은 그걸 가리키기만 한다 (`marketplace.json`은 *목록*만
통제하지 *repo 가시성*은 통제하지 못하므로, 이 repo를 public으로 뒤집으면 내부 팩이
통째로 샌다).

```yaml
marketplace:
  publish: true
  repo: https://github.com/schift-io/<pack>.git
  ref: main
  sha: <40-hex>     # 없으면 재현 불가 — kit이 경고한다
```

`lint`는 발행 대상에 한해 **테넌트 정체성 스캔**을 돌린다. 특정 org 이름/브랜드가
하드코딩된 팩은 다른 org가 설치했을 때 그 정체성이 새므로 발행을 막는다.

## 마켓플레이스 개방 전 필수 (아직 없음)

제3자 팩을 받기 시작하면 필요하고, 지금은 셋 다 없다:

1. **아티팩트 서명** — 현재는 변조 감지만 하고 발행자 신원 증명이 없다
2. **프롬프트 인젝션 / 숨은 유니코드 스캔**
3. **SBOM** (SPDX/CycloneDX)

근거: 모노레포 `docs/research/2026-07-20-agent-packaging-ecosystem-survey.md`

## 상태

원본(`services/agent-hub/apm/`)은 아직 제거하지 않았다 — 타 세션 워커가 같은 트리에서
실행 중이었기 때문. 착지 후 제거 + agent-hub 경로 재배선.
상세: 모노레포 `docs/plans/2026-07-20-schift-packs-repo-and-marketplace.md`
