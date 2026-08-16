# Server Runner contract v1 (normative)

## 범위

이 문서는 **Server Runner** — Schift가 운영하고 고객이 구독/사용량으로 지불하는 호스트
프로필 — 이 base runtime 계약(`runner-selection.md`, `execution-modes.md`,
`run-result-v1.md`, `runtime-services-v1.md`)에 더해 **반드시** 구현해야 하는 것을
정의한다. Local Runner는 개발자가 자기 머신에서 패키지를 검증하는 참조 호스트다
(`docs/runtime-adapter.md`의 `local-byo` 프로필). Server Runner는 그 상위 집합이며,
과금·격리·자격증명 브로커링을 신뢰 경계로 추가한다.

이 문서가 규정하지 않는 것: `.apm` 바이트 레이아웃(SPEC.md §3–4), 능력 협상 판정식
(SPEC.md §6, 이미 정의됨), 특정 클라우드/리전 선택, 가격 정책. 가격의 정본은
`docs/research/PRICING.md`(코드값 `server/billing/pricing.py`)이며 이 문서는 가격 숫자를
적지 않는다.

Server Runner는 `runtime_boundary.host_services_only`로 선언되는 능력의 **제공자 중
하나**다(SPEC.md §6 "호스트 목록은 열려 있다"). 이 계약은 그 호스트 프로필이 "능력을
파싱할 수 있다"는 것과 "능력을 실제로 안전하게 제공한다"는 것 사이의 간극을 막는다.

## 용어

- **Server Runner** — 이 계약을 구현하는 호스트. 하나 이상의 실행 표면(agent-hub 워커,
  agent-run MIG, Cloud Run 등)일 수 있으며 어떤 표면인지는 이 문서의 범위 밖이다.
- **entitlement** — org의 구독/플랜이 특정 package + operation 조합의 실행을 허용하는지에
  대한 판정. 크레딧 잔액과는 별개다(잔액 소진은 실행 중 과금 실패이지 entitlement 거절이
  아니다).
- **usage receipt** — 런 종료 후 Server Runner가 생성하는, 과금과 감사의 근거가 되는
  구조화 기록. `apm.run.result.v1`의 추가 필드다.
- **credential broker** — 패키지 대신 자격증명을 보유·주입·프록시하는 host 컴포넌트.

## 1. Entitlement gate

Server Runner는 패키지 코드를 실행하기 **전에** 호출 org의 entitlement를 판정해야
한다(MUST). 판정은 다음을 입력으로 받는다: 검증된 `content_hash`, `package_ref`, 요청
`operation`, 호출 org id, 호출 principal.

```json
{
  "protocol": "apm.entitlement.check.v1",
  "org_id": "org_...",
  "package_ref": "portable-hello@0.1.0",
  "content_hash": "<64 lowercase hex characters>",
  "operation": "run",
  "decision": "allow",
  "reason": "plan_includes_package_class"
}
```

- `decision`이 `allow`가 아니면 Server Runner는 `apm.run.result.v1`을
  `status: "rejected"`로, 패키지 코드를 한 줄도 실행하지 않고 반환해야 한다(MUST). 이는
  `execution-modes.md`가 이미 규정하는 "판정을 통과 못 하면 실행 전에 거절한다"의
  entitlement 버전이다.
- Server Runner는 entitlement 거절과 capability 거절(SPEC.md §6)과 크레딧 소진 거절을
  **서로 다른 error code**로 구분해야 한다(MUST). 셋을 뭉뚱그리면 호출자가 "권한이 없다"와
  "잔액이 없다"와 "이 패키지가 이 host에서 아예 못 돈다"를 구분할 수 없다.
- Entitlement 판정은 런 시작 시점의 스냅샷이다. 런 도중 org의 플랜이 바뀌어도 이미 시작한
  task turn을 중단시키지 않는다(SHOULD NOT) — 재개(resume) 시점에는 다시 판정한다(MUST).
- private 패키지의 registry ACL 판정(`release-provenance-v1.md`의 `allowed_orgs`)과
  entitlement 판정은 **별개 게이트**다. ACL은 "이 org가 이 코드를 볼 수 있나", entitlement는
  "이 org의 플랜이 이 실행을 지불하나"다. 둘 다 통과해야 실행된다(MUST).

## 2. Model dependency injection

`runtime_contract.model`(`runtime-services-v1.md`)을 선언하는 패키지에 대해, Server
Runner가 벤더·모델·엔드포인트·API 키를 선택한다. 패키지는 `interface: chat.v1` 외의
어떤 provider 세부사항도 알지 못한다(MUST NOT know).

- Server Runner는 실제로 호출에 쓰인 provider와 모델을 실행 provenance에 기록해야 한다
  (MUST) — Snowflake식 자체 호스팅, 외부 API(OpenRouter 경유 포함), 또는 다른 내부
  라우팅 대상 중 어느 것을 썼든 동일하다.
- 모델 선택 로직(폴백 체인, 리전, 비용 최적화)은 Server Runner의 배포 설정이며 `.apm`의
  content hash에 영향을 주지 않는다(SPEC.md §5.2와 일관).
- 같은 패키지가 다른 org·다른 시점에 다른 모델로 라우팅될 수 있다. 이 계약은 그것을
  금지하지 않지만, §4의 usage receipt가 매 런마다 실제 모델을 기록하도록 요구함으로써
  "무슨 모델이 실제로 응답했는지 아무도 모른다"는 실패 모드를 막는다.
- 패키지가 `runtime_contract.model`을 선언하지 않고 모델을 호출하면 Server Runner는 그
  요청을 거절해야 한다(MUST) — capability 미선언 호출은 SPEC.md §6의 fail-closed 판정을
  실행 중에 우회하는 것과 같다.

## 3. Credential broker

패키지는 원시 API 키, OAuth 토큰, 클라우드 자격증명, MCP bearer 토큰을 어떤 형태로도
받지 않는다(MUST NOT). Server Runner는 다음 두 방식 중 하나로 모든 외부 호출을
중개한다:

1. **프록시 호출** — 패키지가 host-mediated 요청(모델 호출, `scoped_connector_proxy`,
   `scoped_mcp_binding`)을 보내면 Server Runner가 자격증명을 채워 실제 provider에
   전달하고 결과만 돌려준다. 패키지는 목적지 URL도 보지 못한다.
2. **단기 스코프 자격증명** — Server Runner가 이 런/이 도구 호출에만 유효한 짧은 TTL의
   스코프 토큰을 발급하고, 패키지 격리 경계 안에서만 유효하게 만든다. 이 경로를 쓰더라도
   자격증명은 export 불가능해야 한다(MUST NOT be exfiltratable) — 로그, 아티팩트,
   워크스페이스 파일 어디에도 평문으로 남지 않아야 한다.

MCP 도구 호출은 예외 없이 Server Runner의 프록시를 경유해야 한다(MUST) — 이는
`.claude/rules/integrations.md`의 "MCP는 항상 Connector Server를 강제 경유"와 동일한
원칙을 프로토콜 레벨에서 재확인한다. 패키지가 `mcp.bindings`에 선언한 `id`/`scopes`/
`tools` 밖의 서버·도구를 호출하려 하면 거절한다(MUST).

`runtime_contract.governance.credentials.exposure: brokered-only`를 선언한 패키지에
대해서는 이 섹션이 이미 필수이던 것을 명시적으로 재확인하는 것 이상의 새 의무는
없다 — governance 선언은 감사 이벤트(`credential.lease`)를 **추가로** 요구할 뿐이다
(`runtime-services-v1.md` 참조).

## 4. Usage receipt

런이 terminal 상태(`succeeded`, `failed`, `cancelled`, `rejected`)에 도달하면 Server
Runner는 `apm.run.result.v1`에 다음 추가 필드를 채워야 한다(MUST, 단 `estimated_cost_*`와
`network_egress_bytes`는 SHOULD):

```json
{
  "usage_receipt": {
    "protocol": "apm.usage.receipt.v1",
    "run_id": "run_01...",
    "package_ref": "portable-hello@0.1.0",
    "content_hash": "<64 lowercase hex characters>",
    "runtime_version": "apm.runtime.services.v1",
    "model": {
      "provider": "internal-snowflake",
      "model_id": "schift-embed-1",
      "input_tokens": 1200,
      "output_tokens": 340
    },
    "runtime_seconds": 4.7,
    "network_egress_bytes": 18234,
    "estimated_cost": {"amount": "0.0042", "currency": "USD"},
    "artifacts": ["run_01.../artifacts/summary.md"]
  }
}
```

- `run_id`, `package_ref`, `content_hash`, `runtime_version`은 비어 있지 않은 문자열이어야
  한다(MUST). `content_hash`는 실행에 쓰인 검증된 해시와 정확히 일치해야 한다(MUST) —
  §1의 entitlement 판정과 §4의 과금이 서로 다른 아티팩트를 가리키면 감사가 끊긴다.
- 모델을 하나 이상 호출한 런은 `model` 배열(또는 다중 호출 시 배열)에 실제로 호출된 모든
  provider/model_id와 각각의 input/output 토큰을 기록해야 한다(MUST). §2가 요구하는
  provenance 기록의 실체가 이 필드다.
- `runtime_seconds`는 패키지 코드가 실제로 실행된 wall-clock 시간이며, entitlement 판정
  대기나 큐잉 시간을 포함하지 않는다(MUST NOT).
- `network_egress_bytes`는 `sandbox.model_egress: provider-proxy` 또는 커넥터 경유 트래픽의
  총합이다. 측정 불가능한 배포(예: in-process 커넥터가 바이트 수를 계측하지 않음)에서는
  생략할 수 있다(MAY omit) — 단 생략과 0은 다른 값이므로 필드 자체를 비워야 한다(누락을
  0으로 채워 넣지 않는다).
- `estimated_cost`는 Server Runner의 책임이며 패키지가 계산하거나 검증할 수 없다.
  `.claude/rules`의 "metered_by: provider인 능력은 우리가 계량하지 않는다" 원칙과
  일관되게, Server Runner가 원가를 실제로 지불하지 않는 항목(예: 고객 BYOK로 직접 호출된
  provider 비용)은 `estimated_cost`에서 제외하거나 별도 필드로 분리해야 한다(MUST).
- `artifacts`는 `artifact-results.md`가 정의하는 완전한 아티팩트 참조만 담는다. usage
  receipt는 새로운 아티팩트 경로 규칙을 만들지 않는다.
- Server Runner는 receipt를 자체 과금 원장에 **한 번만** 반영해야 한다(MUST). 재시도나
  재조회로 같은 `run_id`의 receipt를 두 번 청구해서는 안 된다(idempotent).

## 5. Egress policy

Server Runner는 `runtime_contract.sandbox.model_egress`와 `data.*`가 요구하는 것보다
더 넓은 네트워크 경계를 실행에 부여해서는 안 된다(MUST NOT grant broader). 세 단계를
지원한다:

| 정책 | 의미 | 대응하는 sandbox 선언 |
| --- | --- | --- |
| `none` | 패키지 프로세스에서 외부 네트워크 호출이 전혀 없다. 모델 호출은 internal in-process adapter가 대신 수행한다. | `sandbox.model_egress: none` |
| `proxy_only` | 오직 승인된 프록시(model gateway, `scoped_connector_proxy`)를 통해서만 나간다. 프록시가 허용 목록 밖 목적지를 거절한다. | `sandbox.model_egress: provider-proxy` |
| `approved_connectors` | `mcp.bindings`/`data.connected_sources`에 이름으로 선언된 커넥터만 허용한다. 목록 밖 서버·도구는 존재하지 않는 것처럼 거절한다. | `mcp.bindings` 비어 있지 않음, 또는 `data.connected_sources.*` |

- 세 정책은 상호 배타적이지 않다 — 한 런이 `none`(패키지 egress 없음) +
  `approved_connectors`(host가 대신 호출하는 MCP 바인딩)를 동시에 가질 수 있다. 규범은
  **패키지가 직접 여는 소켓**에 대한 것이고, host가 중개해서 나가는 트래픽은 §3의 브로커
  경로로 별도 다스려진다.
- `runtime-services-v1.md`의 `sandbox.package_network: none`은 항상 참이어야 한다(MUST) —
  이 셋 중 어느 정책을 쓰든 패키지 프로세스 자체는 직접 네트워크를 갖지 않는다. egress
  정책은 오직 host-mediated 경로에 적용된다.
- Server Runner는 실제로 강제한 egress 모드를 usage receipt 또는 result envelope의
  provenance에 기록해야 한다(MUST) — `execution-modes.md`가 이미 요구하는 "advertise한
  격리를 증명하지 못하면 격리라고 label하지 않는다"의 네트워크 버전이다.
- `governance.sandbox.network`(`runtime-services-v1.md` §governance)를 선언한 패키지에
  대해서는 `default: deny` + 명시적 allowlist가 곧 이 섹션의 `proxy_only`/
  `approved_connectors`를 구체화한 것이다. 두 계약이 상충하면 더 엄격한 쪽이 이긴다(MUST).

## 6. Deterministic equivalence

같은 `.apm`(같은 `content_hash`) + 같은 입력 + 같은 model/version + 같은 runtime profile로
실행한 두 런은 다음이 **구조적으로** 같아야 한다(MUST):

- 워크플로 단계 순서와 각 단계의 종류(모델 호출, 도구 호출, human input 요청 등)
- `apm.run.result.v1`의 필드 shape과 `artifacts` 항목의 스키마
- `usage_receipt`의 필드 shape(값은 다를 수 있다 — 토큰 수, 실행 시간)

**바이트 동일 출력은 요구하지 않는다(NOT byte-identical).** LLM 호출은 비결정적이므로
모델 응답 텍스트, 생성 이미지, 토큰 수는 두 런마다 다를 수 있다. 이 조항이 고정하는 것은
"같은 요청이 같은 종류의 일을 같은 순서로 하고 같은 모양의 결과를 낸다"이지 "같은 값을
낸다"가 아니다.

- Server Runner가 내부 인프라를 바꾸더라도(리전 이동, 프록시 교체, provider 폴백) 이
  동치성은 유지되어야 한다(MUST) — 바뀔 수 있는 것은 §2의 실제 모델 provenance뿐이다.
- 워크플로 단계의 **개수나 종류**가 인프라 변경으로 달라지면(예: 어떤 배포에서는 human
  input 단계가 자동 승인되어 사라짐) 이는 동치성 위반이다. `execution-modes.md`가
  금지하는 "격리·권한·능력·결과 의미의 조용한 다운그레이드"의 한 사례다.
- 같은 `content_hash`에 대해 로컬과 서버가 다른 개수의 task turn을 만들어내면 안 된다
  (MUST NOT) — 이는 아래 §7의 parity 요건과 직접 연결된다.

## 7. Local ↔ Server parity

`apm-kit check --host local`을 통과한 패키지는 Server Runner에서도 실행되어야 한다
(MUST), 단 로컬이 제공하지 않고 서버만 제공하는 능력(예: `connected_source_search_connector`,
`cclg_memory_read`, `usage_ledger`, `credit_metering`)을 그 패키지가 실제로 사용하는 경우는
제외한다.

- 두 호스트 간 차이는 **가용 능력의 차이**로만 나타나야 한다(MUST) — 계약 해석의 차이로
  나타나서는 안 된다(MUST NOT). 즉 `runtime_contract.model.selection: host`의 의미, `input_
  required`의 task-turn 상태 기계, `data.*: host-mediated`의 결과 스키마는 로컬과 서버가
  동일한 방식으로 해석해야 한다. SPEC.md §6이 이미 "호스트 프로필이 갈리면 느슨한 쪽이
  아니라 엄격한 쪽에 맞춘다"고 규정한 것의 연장이다.
- Server Runner가 로컬보다 **더 관대한** 판정(예: local이 거절하는 unknown capability를
  서버가 통과시킴)을 내려서는 안 된다(MUST NOT) — 이는 팩 저자가 로컬에서 본 통과가
  서버에서의 통과를 보장하지 못하게 만든다(2026-08-10 실측 사고와 같은 유형, SPEC.md §6
  참조).
- `cloud_only` 능력(`usage_ledger`, `credit_metering`)을 요구하는 패키지는 로컬에서는
  `apm-kit check`이 항상 거절하는 것이 정상 동작이다(SPEC.md §6). Server Runner에서
  이런 패키지가 통과하는 것은 parity 위반이 아니라 parity가 정의하는 대로다 — "로컬이
  통과시키면 서버도 통과한다"의 역은 이 계약의 요구사항이 아니다.
- 새 host-only 능력을 추가할 때 Server Runner 구현자는 그 능력을 사용하지 않는 기존
  패키지의 동작을 바꾸지 않아야 한다(MUST NOT) — capability 추가는 additive해야 한다.

## 부록 — 이 문서가 파생시키는 능력

이 계약이 참인 것으로 요구하지만 SPEC.md §6 어휘에 아직 없는 이름은 도입하지 않는다.
Server Runner는 `governance_policy_enforcer`, `credential_broker`, `audit_siem_export`,
`trusted_runtime_image`, `usage_ledger`, `credit_metering`, `model_inference_adapter`,
`scoped_connector_proxy`, `scoped_mcp_binding`, `provider_egress_proxy`,
`isolated_sandbox` 중 자신이 실제로 제공하는 것만 `kit/capabilities.json`의 host
프로필 목록에 명시해야 한다(MUST) — 새 어휘가 이 문서에 등장했다는 이유로 자동으로
제공한다고 주장해서는 안 된다(SPEC.md §6과 동일 원칙).
