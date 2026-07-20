# schift-packs

Schift 에이전트 팩의 **단일 정본**. 팩은 코드가 아니라 배포물이므로 서비스 트리
(`services/agent-hub/`)가 아니라 여기 산다.

```
packs/<name>.agent/     apm.yml · agent.md · skills/**   ← 팩 정본
kit/                    apm-kit — 점검/빌드 키트 (agent-hub 비의존)
.claude-plugin/         marketplace.json (kit이 생성, 손으로 고치지 말 것)
```

## 두 가지 유통 경로

| 경로 | 대상 | 형태 |
|---|---|---|
| **`.apm` 아티팩트** | Schift Cloud (agent-hub) | tar+매니페스트 봉인 → content-hash → R2 → `apm_refs` DB 등록 |
| **Claude Code 마켓플레이스** | 로컬 하네스 (BYO-LLM) | `/plugin marketplace add schift-io/schift-packs` |

같은 팩, 두 호스트. 그래서 **호스트 능력 계약**이 필요하다.

## 호스트 능력 계약

팩은 `apm.yml`에 자기가 요구하는 호스트 서비스를 선언한다:

```yaml
runtime_boundary:
  host_services_only:
    - auth
    - image_generation_connector
    - usage_ledger
```

어휘 정본은 `kit/capabilities.json`. 호스트가 못 채우면 **fail-closed로 거절**된다 —
"조용히 반쯤 도는 것"이 두 호스트 체제에서 가장 위험한 실패 모드다.

```bash
python3 kit/apm_kit.py check --host agent-hub    # Cloud
python3 kit/apm_kit.py check --host local-byo    # 로컬 BYO-LLM
```

`local-byo`가 제공할 수 없는 것(=Cloud 전용): `usage_ledger`, `credit_metering`
(유저 머신에서 과금 원장을 강제할 방법이 없다), 서버 워커(`render_worker`,
`stitch_worker`), 외부 핸드오프.

> BYO-LLM에서 과금 표면은 **데이터 레이어**(MCP 검색·ingest·저장)이지 생성이 아니다.
> 생성은 유저 구독이 낸다. 그래서 로컬 팩은 미터링 능력을 요구하지 않도록 설계한다.

## 발행은 fail-closed

`apm.yml`에 명시하지 않으면 마켓플레이스에 **실리지 않는다**:

```yaml
marketplace:
  publish: true
  category: productivity
  tags: [image, prompt]
```

`kit lint`는 발행 대상 팩에 한해 **테넌트 정체성 스캔**을 돌린다 — 특정 org 이름/
브랜드 컬러가 하드코딩된 팩은 다른 org가 설치했을 때 그 정체성이 새므로 발행을
막는다 (2026-07-20 tenancy leakage 감사에서 실재 확인된 문제).

```bash
python3 kit/apm_kit.py lint      # 어휘 · 필수 필드 · 정체성
python3 kit/apm_kit.py market    # marketplace.json 생성
```

## 마켓플레이스 개방 전 필수 (아직 없음)

제3자 팩을 받기 시작하는 순간 필요하고, 지금은 셋 다 없다:

1. **아티팩트 서명** — 현재는 content-hash로 변조 감지만 하고 발행자 신원 증명이 없다
2. **프롬프트 인젝션 / 숨은 유니코드 스캔**
3. **SBOM** (SPDX/CycloneDX)

근거: `docs/research/2026-07-20-agent-packaging-ecosystem-survey.md` (모노레포)

## 상태

**이 디렉토리는 아직 독립 repo가 아니다.** 모노레포 `core-dependencies/` 아래 복제본
이며 `core-dependencies/*`는 gitignored다 — 즉 **현재 어디에도 커밋돼 있지 않다.**
`schift-io/schift-packs` repo 생성 + 초기 push가 끝나야 안전하다.

원본(`services/agent-hub/apm/`)은 아직 제거하지 않았다. 타 세션 워커가 같은 트리에서
실행 중이었기 때문이며, 착지 후 제거 + agent-hub 경로 재배선한다.
상세: 모노레포 `docs/plans/2026-07-20-schift-packs-repo-and-marketplace.md`
