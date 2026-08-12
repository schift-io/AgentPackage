# Agent Package (`.agent` → `.apm`) — 공개 포맷 사양 v1

이 문서가 **`.apm` 의 규범적 사양**이다. 여기 적힌 것과 구현이 다르면 **구현이 버그**다.
README 는 "왜 이 포맷인가"를 논증하고, 이 문서는 "무엇이 참인가"를 정의한다.

- 상태: **v1, source-available 사양**. 서명은 아직 없다(§9).
- 정본 구현: `kit/apm_codec.py`(컨테이너·해시) · `kit/capabilities.json`(능력 어휘) ·
  `kit/apm_kit.py`(검증·빌드 CLI).
- 라이선스: PolyForm Small Business License 1.0.0 (`LICENSE`). OSI 오픈소스 라이선스가 아니다.

> ⚠️ **이름 충돌.** 이 `APM` 은 **Agent Package** — 봉인된 단일 아티팩트 포맷이다.
> [`microsoft/apm`](https://github.com/microsoft/apm)("Agent Package Manager", npm 식
> 의존성 관리자로 `apm_modules/` 에 풀어놓는 방식)과 **무관하며 코드·스키마 어느 쪽도
> 참조하지 않는다.** README 가 그 프로젝트의 이슈를 인용하는 건 설계 논증의 반례로서일
> 뿐이다. 외부 문서에서는 첫 등장에 ``Agent Package (`.apm`)`` 로 적는다.

---

## 1. 범위

실행 결과 계약은 프로토콜 0.1.0의 규범 문서인
docs/version-0.1.0.md, docs/runner-selection.md, docs/run-result-v1.md,
docs/artifact-results.md, docs/execution-modes.md, docs/permissions.md,
docs/runtime-services-v1.md, docs/interoperability.md에
정의한다. 이 문서들은 호스트 구현을 고정하지 않지만 결과·권한·격리의
의미를 바꾸는 것을 허용하지 않는다.

| 규정한다 | 규정하지 않는다 |
|---|---|
| `.apm` 컨테이너 바이트 레이아웃(§3) | 팩이 무엇을 하는지(도메인 정책 — `agent.md` 의 몫) |
| content-hash 산출식(§4) | 호스트의 실행 모델·스케줄링 |
| 매니페스트 정본 판정 순서(§5) | 레지스트리 API 표면(호스트 소관) |
| 호스트 능력 계약과 fail-closed 판정(§6) | 결제·과금 정책 |
| 발행 게이트(§7) · 버전 판정(§8) | 서명·발행자 신뢰(§9, 미정) |
| `.agent` source와 `.apm` artifact의 관계(§2) | 특정 Runtime의 내부 API |

## 2. 용어

- **`.agent` source package** — 디렉터리 `<slug>.agent/`. Git에서 편집하는 저작 단위.
- **`.apm` artifact** — `.agent` 디렉터리를 통째로 봉인한 단일 아티팩트. 배포·설치 단위.
- **매니페스트(manifest)** — `.apm` 안 `manifest.json` 의 JSON 객체. 등록·실행 메타의 정본.
- **호스트(host)** — `.apm`을 실행하는 Runtime. Schift, Cloudflare, local, custom 등
  규약 밖의 구현도 같은 capability 판정식을 사용한다.
- **능력(capability)** — 팩이 호스트에 요구하는 서비스 이름. 어휘는 §6.

## 3. 컨테이너 — 결정적 tar.gz

`.apm` 은 **gzip 으로 감싼 tar** 이며, 같은 입력은 **바이트 단위로 같은 출력**을 낸다.
결정성이 깨지면 content-hash 가 주소로서 쓸모가 없어지므로 아래는 전부 규범이다.

| 항목 | 값 |
|---|---|
| gzip `mtime` | `0` (헤더 타임스탬프 제거) |
| tar 엔트리 이름 | 팩 루트 기준 **상대경로**, POSIX 구분자 |
| tar 엔트리 순서 | 이름 **오름차순 정렬** |
| tar `mtime` / `uid` / `gid` | 전부 `0` |
| tar `uname` / `gname` | 전부 `""` |
| tar `mode` | `0o644` |
| 매니페스트 경로 | `manifest.json` (루트, 상수 `MANIFEST_NAME`) |
| 디렉터리 엔트리 | **싣지 않는다** (파일만) |
| `__pycache__` | 번들에서 제외 |

**Canonical JSON** — 매니페스트 직렬화는 `json.dumps(obj, ensure_ascii=False,
sort_keys=True, separators=(",", ":"))` 의 UTF-8 인코딩이다. 공백·키 순서가 달라지면
해시가 달라진다.

**완전성.** 번들은 팩 디렉터리를 `rglob` 로 **통째로** 담는다. 선언된 파일만 골라 담지
않는다 — 실행 정의는 부분적으로 존재할 수 없고, 고르는 순간 "고르는 걸 잊는" 실패가
생긴다.

## 4. content-hash

주소는 sha256 hex 이며 다음 바이트열의 해시다:

```
sha256(
    b"apm-v1\n"
  + hex(sha256(canonical_json(hashable_manifest(manifest)))).encode()
  + b"\n"
  + Σ_{path ∈ sorted(files)} ( path.encode("utf-8") + b"\0"
                             + hex(sha256(files[path])).encode() + b"\n" )
)
```

- 파일은 **경로 정렬 후** (경로, 내용해시) 쌍으로 누적한다 → 순회 순서와 무관하고
  전 파일을 덮는다.
- 접두사 `apm-v1\n` 이 **포맷 버전**이다. 산출식이 바뀌면 이 문자열을 올린다.

### 4.1 해시에서 제외되는 키 (`HASH_EXCLUDED_KEYS`)

아래 21개 키는 **팩의 내용이 아니라 호스트가 이 팩을 어떻게 등록/전시하는가**(라우터
힌트·허브 UI 라벨·플래그·소유 org)라서 주소 계산에서 뺀다. **번들에는 그대로 실린다 —
해시 범위에서만 빠진다.**

```
schema_version
router_enabled  router_topic_hints  router_shortcut_keywords  router_slash_commands
router_requires_attachment  router_scope  router_session_scope  router_min_confidence
router_description  router_default_handler
hub_label  hub_role  hub_inputs  hub_output  hub_review
intake_question  intake_options  feature_flag  hidden  owner_org_id
```

> ⚠️ **이 목록은 모든 구현에서 동일해야 한다.** 한쪽만 바꾸면 같은 팩에 다른 hash 가
> 나와 두 발행자가 서로 덮어쓰거나 409 를 무한 반복한다. 실제로 이 불일치 때문에 발행
> 자동화를 켤 수 없던 기간이 있었다(2026-07-21). 현재 `kit/apm_codec.py` 와 소비자 측
> 사본은 21개로 일치한다(§9 부채 1).

### 4.2 검증

수신측은 언팩 후 재계산한 hash 를 기대값과 대조하고, 다르면 **`ApmHashMismatch` 로
거절**한다. 해시 검증과 매니페스트 화이트리스트 검증(`validate_manifest`)은 **별개
단계**이며 둘 다 통과해야 등록된다.

## 5. `.agent` 레이아웃과 매니페스트 정본

```
<slug>.agent/
  agent.md          # 필수 — 에이전트 정의(산문)
  apm.yml           # 필수 — 저작 매니페스트(YAML)
  pack.json         # 선택 — canonical 매니페스트(JSON). 있으면 이것이 정본
  scripts/<op>.py   # 선택 — script-runtime 오퍼레이션 (`async def run(ctx, inputs)`)
  skills/*/SKILL.md # 선택
```

**정본 판정 순서 (규범):**

1. `pack.json` 이 있으면 **그대로** 매니페스트로 쓴다. 파생을 거치지 않으므로 **누가
   빌드하든 같은 매니페스트**가 나오고, 따라서 hash 가 자동으로 일치한다.
   `agent_id` 만 없으면 디렉터리명에서 채운다.
2. 없으면 `apm.yml` 에서 파생한다.

`apm.yml` 이 **저작 포맷**이지 정본이 아닌 이유: 로더가 제한된 자체 YAML 파서라 중첩
리스트를 못 받고 블록 스칼라의 빈 줄을 버리며, `tools`/`skills` 처럼 파생이 이중으로
잡히는 키가 있다. 등록 메타 격차 52건이 이 한계에 막혀 있었다(2026-07-21 실측).

### 5.1 `apm.yml` 필드

| 키 | 필수 | 의미 |
|---|---|---|
| `name` | ✔ | **패키지 슬러그**(`package_ref` 조립용). 표시명이 아니다 |
| `display_name` | | 콘솔 표시명. 없으면 `name` 폴백(슬러그가 raw 로 노출됨) |
| `version` | ✔ | semver 문자열 |
| `description` | | 한 줄 설명 |
| `runtime_boundary.host_services_only` | | 요구 능력 목록(§6). 문자열 단수도 허용 |
| `runtime_contract` | | model/입력/CCLG/data/MCP/sandbox/상호운용 호스트 계약. [`docs/runtime-services-v1.md`](docs/runtime-services-v1.md) |
| `runtime_ref` | | 논리 실행기 URI (`apm://runtime/<name>@<semver>`). provider endpoint가 아닌 binding lookup key |
| `artifacts.package_ref` | | `<slug>@<version>`. **버전 판정의 실체**(§8) |
| `marketplace.*` | | 발행 선언(§7) |
| `router_*` · `hub.*` | | 등록/전시 메타 — 해시 제외(§4.1) |
| `memory.seed` | | 선언하면 발행 전 seed 검증이 fail-closed 로 돈다 |

`agent.md` 누락, `name`/`version` 누락은 **lint 실패**다.

`.agent`는 npm package source와 같은 역할을 한다. `apm-kit build`의 산출물인
`.apm`만 배포·설치할 수 있으며, 개발용 direct mode도 같은 validation을 먼저
통과해야 한다. `.agent`를 검증 없이 Runtime에 전달하는 것은 규약 준수가 아니다.

## 5.2 Runtime-neutral 규칙

`.agent`와 `.apm`은 특정 vendor의 endpoint, secret, binding, database, queue를
가정하지 않는다. 팩은 capability와 operation의 요구만 선언한다.

```yaml
capabilities:
  required: [llm.generate, artifact.write]
  optional: [source.search, image.reference]
```

Runtime adapter는 capability를 실제 서비스에 연결한다. 예를 들어 Schift는 Agent
Hub와 Schift artifact store를, Cloudflare는 Workers AI·R2·Durable Objects를,
local adapter는 Ollama·ComfyUI·filesystem을 제공할 수 있다. 이 매핑은 package
hash의 내용이 아니라 Runtime 배포 설정이다.

`runtime_contract`를 선언하는 팩은 model DI, 사용자 입력 재개, CCLG memory,
host-mediated data/MCP, 격리 sandbox, Agent Plugins/A2A 호환을 같은 방식으로
선언한다. 이 블록은 provider endpoint·secret·임의 네트워크 권한을 담지 않으며,
각 선언이 요구하는 capability를 `runtime_boundary.host_services_only`에도 반드시
명시해야 한다. 상세 shape와 파생 capability는
[`docs/runtime-services-v1.md`](docs/runtime-services-v1.md)가 정한다.

특정 실행기를 우선 선택해야 할 때에는 optional `runtime_ref`를 쓴다. 이 값은
`apm://runtime/human-input-runner@0.1.0`처럼 **논리 이름과 SemVer**만 담는다.
Cloud Run URL, Lambda ARN, Worker route, service account, token audience, secret은
모두 deployment-owned `apm.runtime.binding.v1` 문서에 둔다. 따라서 같은 `.apm`의
content hash를 바꾸지 않고 provider를 교체할 수 있다. binding 문서의 규범적 shape와
Cloud Run 예시는 [`docs/runtime-binding.md`](docs/runtime-binding.md)에 있다.

필수 capability를 제공하지 못하는 호스트는 실행 전에 fail-closed로 거절해야 한다.
어떤 호스트가 capability를 제공하는지는 공개 포맷의 고정 목록이 아니며, 새 Runtime
adapter를 추가해도 `.apm` 포맷을 바꿀 필요가 없어야 한다.

## 6. 호스트 능력 계약 — fail-closed 협상

**"이 호스트가 이 팩이 시도할 일을 실제로 할 수 있나"를 실행 전에 묻는다.** 이것이
포맷의 핵심이며, 참조용 스킬 포맷에는 이 질문 자체가 없다.

- 팩은 `runtime_boundary.host_services_only` 로 요구 능력을 선언한다.
- 능력 이름의 **전체 집합(어휘)은 `kit/capabilities.json` 이 단일 정본**이다. 어휘에
  없는 이름을 선언하면 lint/check 가 실패한다(오타·무단 신규 차단).
- 호스트는 제공하는 능력을 **명시 목록**으로 선언한다. 새 어휘가 추가되었다는 이유로
  기존 호스트가 이를 자동으로 제공한다고 주장해서는 안 된다.
  - `agent-hub` — 검증된 기존 Cloud capability 목록
  - `local-byo` — 검증된 기존 로컬 capability 목록(과금·서버 워커 제외)
  - `docker-codex-isolated` — `model_inference_adapter`, `isolated_sandbox`,
    `provider_egress_proxy`만 제공; CCLG/search/MCP/A2A/Agent Plugins는 별도 adapter 전까지 거절
- ⚠️ **호스트 프로필은 소비자 구현과 반드시 같아야 한다.** 갈리면 느슨한 쪽이 아니라
  **엄격한 쪽**에 맞춘다 — 느슨한 쪽이 정본이 되면 팩 저자는 `check` 통과를 보고도
  실제로는 못 도는 팩을 낸다(2026-08-10 실측: 어휘는 28/28 같은데 `local-byo` 만
  `hwpx_render_connector` 를 제공한다고 잘못 적혀 있었다).
- **판정 (규범):** `required = 선언집합`, `unknown = required − 어휘`,
  `missing = (required ∩ 어휘) − host_provides`.
  `unknown` 또는 `missing` 이 비어 있지 않으면 **거절한다.** 요구가 아예 없으면 통과.
- `cloud_only`(`usage_ledger`, `credit_metering`) = 유저 머신에서 강제 불가능한 능력.
  이걸 요구하는 팩은 로컬 호스트에서 항상 거절된다.

두 호스트 체제에서 가장 위험한 실패 모드는 크래시가 아니라 **조용히 반쯤 도는 것**이다.
그래서 판정은 fail-open 이 아니라 fail-closed 다.

**호스트 목록은 열려 있다.** 팩은 "나는 이게 필요하다"만 말하고 *누가 제공하는지*는
호스트 쪽 선언이므로, 고객 인프라·로컬 GPU 같은 제3의 실행기를 붙이는 것은 `hosts` 에
항목 하나를 더하는 일이지 포맷 변경이 아니다. 판정식도 그대로 돈다. 없는 것은 포맷이
아니라 **"이 능력을 지금 어느 실행기가 충족하나"를 고르는 라우터**이고, 그건 호스트
구현의 몫이다(§9-6).

```
$ apm-kit check image-gen.agent --host local-byo
✗ image-gen.agent: host 'local-byo' lacks ['usage_ledger']
```

### 6.1 능력의 실행 위치 — `transport` (표현만, 2026-08-10)

능력마다 **어디서 도는가**를 선언한다. legacy host capability와 runtime-services v1
capability가 공존하며, `http` capability는 host 바깥의 정책·연결 경계를 뜻한다.

| `transport` | 뜻 |
|---|---|
| `in_process` | 호스트 프로세스 안에서 실행 |
| `http` | 호스트 **밖**에서 실행하고 HTTP 로 호출 |

`http` 가 중요한 이유: 어휘가 닫혀 있던 진짜 이유는 "이름이 28개라서"가 아니라 **각
이름이 우리 인프로세스 구현에 묶여 있어서**다. 능력이 HTTP 계약이면 새 능력을 더하는
일이 우리 코드 배포가 아니라 **엔드포인트 등록**이 된다. 남의 코드가 우리 프로세스에
안 들어오므로 **격리가 곧 신뢰 축**이 되고(§9-5 의 서명 대신 샌드박스), 제3의 실행기
중개(§9-6)도 같은 메커니즘 하나로 풀린다.

**⚠️ `http` 능력은 비동기 계약이어야 한다.** 호출은 잡 핸들을 돌려주고 끝나며 완료는
콜백/폴링으로 받는다. 동기로 붙들면 호스트의 런 슬롯이 남의 계산을 기다리며 놀고,
**계산은 저쪽이 하는데 대기 비용은 이쪽이 낸다.** 팩 스크립트가 타임아웃·재시도를
다루게 해서도 안 된다 — 애초에 기다리지 않는 것이 규약이다.

**`metered_by`** 는 누가 계량하는가다: `host`(우리가 제공하니 우리가 잰다) ·
`provider`(외부가 제공하니 **우리는 안 잰다** — 우리 원가가 아닌 것을 우리 원장에
올리면 숫자가 거짓이 된다) · `none`.

**판정에는 아직 안 쓴다.** §6 의 fail-closed 식은 그대로다. `http` 능력이 실재하면
판정이 둘로 갈린다 — **발행 시점**(계약이 선언돼 있나)과 **실행 시점**(그 엔드포인트가
지금 사나). 후자를 안 만들면 등록은 통과하고 런타임에 조용히 죽는다.

## 7. 발행 게이트

- **fail-closed:** `apm.yml` 에 `marketplace.publish: true` 를 **명시하지 않은 팩은
  마켓플레이스에 실리지 않는다.** 선언 없음이 기본이고 그게 안전한 기본값이다.
- **테넌트 정체성 스캔:** `publish: true` 인 팩에 한해 `.md`/`.yml`/`.yaml` 전 파일을
  스캔해 특정 org 정체성이 하드코딩돼 있으면 **발행을 막는다**(다른 org 가 설치하면
  그 정체성이 샌다 — 2026-07-20 tenancy leakage 감사에서 실재 확인). 패턴은 소스에
  하드코딩하지 않고 `identity-patterns.json`(레포 루트. `--identity-patterns` 로 경로 변경
  가능)에서 읽는다 — 정체성을 leak 으로부터 막는 코드 자체가 정체성을 담고 있으면
  분리 의미가 없기 때문. 이 kit 을 이 repo 밖으로 떼어낼 때는 이 파일을 안 가져가거나
  `--identity-patterns /dev/null` 처럼 빈 경로를 지정하면 스캔이 비활성화되고, 그 사실을
  명시적으로 출력한다(조용히 건너뛰지 않는다).
  형식은 `{"patterns": [{"pattern": "<정규식>", "label": "<사람이 읽는 이름>"}]}`.
  ⚠️ **여기에 실제 패턴 값을 옮겨 적지 않는다.** 이 문서는 kit 과 함께 배포되므로,
  값을 나열하는 순간 파일을 `kit/` 밖으로 뺀 의미가 사라진다 — 실제로 이 문단이
  한 번 그 실수를 했다. 값을 보려면 운영 중인 repo 의 `identity-patterns.json` 을
  직접 열어라.
- **소스 위치:** 마켓플레이스 항목의 `source` 는 이 repo 안 상대경로가 아니라 **각 팩의
  공개 repo** 를 가리킨다. 규약 repo와 조직 전용 팩 repo의 공개 범위는 분리할 수 있다.
  이 규약 repo를 공개한다고 별도 private 팩 repo가 공개되는 것은 아니다.
  `marketplace.json`은 *목록에 뭘 싣느냐*만 통제하므로, private 팩은 애초에 별도 repo에서
  관리해야 한다.
- **`sha` 핀이 없으면 재현 불가**이므로 경고한다. 빠진 팩·미핀 팩은 항상 이름을 출력한다
  (조용한 누락 금지).

## 8. 버전 판정 (레지스트리 409)

레지스트리 버전을 가르는 값은 **`package_ref` 의 `@` 뒤 버전 하나**다
(`_version_of(package_ref)`). top-level `version` 은 `package_ref` 에 `@버전` 이 없을
때만 쓰는 **폴백**이다.

그럼에도 실무에서는 **세 곳을 같이 올린다** — `apm.yml: version` ·
`pack.json: package_ref` · `pack.json: manifest_overrides.version`.
`pack.json` 전체가 `.apm` 해시에 그대로 들어가므로, 내용이 바뀌었는데 `package_ref` 만
그대로면 **hash 는 바뀌고 등록 버전은 그대로**라 409 가 난다.

## 9. 알려진 부채 / 미정

> ⚠️ **부채 1과 3의 경중을 헷갈리지 말 것.** 두 빌더가 같은 버전에 서로 다른
> content-hash 를 내는 **실제 원인은 3(매니페스트 생성 경로가 둘)이지 1(코덱 사본)이
> 아니다.** 실측: `zodal@0.1.4` → kit `4e675c7eec05` / agent-hub `a38ae237b866`.
> 코덱은 이미 일치하며 테스트로 잠겨 있다. **자동 발행을 켜는 선행 조건은 3이다.**

1. **코덱 사본이 둘이다.** 소비자(agent-hub) 측에 `apm_package.py` 사본이 있다. 현재
   `HASH_EXCLUDED_KEYS` 는 21개로 일치하며, 갈리면 빨개지도록 잠가 뒀다 — 골든 해시·
   골든 번들 바이트·결정성·제외키 목록·크로스 repo 대조
   (`services/agent-hub/tests/test_apm_hash_golden.py`). 수렴 방향은 소비자가
   `kit/apm_codec.py` 를 import 하는 것.
2. **능력 어휘도 사본이 둘이다.** 소비자 측 `host_capabilities.py` 를 이 파일을 읽도록
   수렴시킨다.
3. **~~매니페스트 이중 선언~~ — 2026-08-10 해소.** 원인은 "선언이 둘"이 아니라
   **참조 구현이 자기 사양을 안 지킨 것**이었다. kit 의 `build` 가 `apm.yml` 만 읽고
   §5 의 정본 판정 순서(`pack.json` 우선)를 건너뛰었다. 팩 36/36 이 `pack.json` 을
   갖고 있어서, 고치자 agent-hub 와 **36/36 hash 일치**했다(고치기 전 8/8 불일치).
   `.github/workflows/verify.yml` 이 이 판정을 잠근다.
   **발행 주체 = 모노레포 `./deploy.sh apm-packs`** 로 확정(2026-08-10). 이 repo 의
   `publish.yml` 은 검증 전용이며 라이브 발행 스텝을 두지 않는다 — 자격증명 때문이
   아니라 **여기 `packs/` 가 라이브가 아니기 때문**이다(실측: 27개 vs 라이브 36개,
   9개 누락, 표본 5개가 전부 3 patch 뒤처짐). **hash 가 맞는 것과 내용이 최신인 것은
   다른 문제**이고 §9-3 은 앞의 것만 고쳤다.
4. **봉투를 OCI artifact 로 바꾸는 선택지가 열려 있다.** 지금은 tar.gz + canonical JSON +
   자체 해시를 직접 정의했다(§3·§4). OCI artifact 로 실으면 content-addressable digest 는
   같은 개념이면서 **레지스트리 프로토콜과 cosign/sigstore 서명이 딸려온다** — 5번이 공짜로
   풀린다. 능력 협상(§6)은 OCI 에 없으므로 annotation 이나 별도 레이어로 유지해야 한다.
   즉 "OCI 로 갈아탄다"가 아니라 **봉투만 바꾸고 내용물은 유지**하는 형태다. 결정되면
   해시 접두사 `apm-v1` 을 올려야 하고 **기존 팩 해시가 전부 무효**가 된다.
5. **서명이 없다.** content-hash 는 **변조를 잡지만 출처를 증명하지 못한다.** 자사
   배포에서 hash 는 주로 위생이며, 제3자 팩을 받기 시작하는 순간 서명이 함께 필요하다.
   그 전까지 런타임 설치본 실행(`SCHIFT_PACK_INSTALL`)은 켜지 않는다. 신뢰 축은 서명
   말고 **실행 샌드박스**로도 세울 수 있다(microVM 급 격리).
6. **실행기 중개(브로커링)는 아직 없다.** 팩은 자기 런타임을 실을 수 없고 무거운 일은 전부
   호스트 능력으로 요청한다(배관은 서버, 판단은 팩). 그래서 새 파이프라인이 필요하면 어휘에
   이름을 추가하고 서비스를 만드는 것이 **호스트 소유자의 작업**이 된다 — 제3자 팩에는 이
   길이 없다. 고객 GPU 처럼 우리가 되팔기 애매한 자원은 중개가 맞는 방향이고, §6 이 말하듯
   포맷은 이미 이를 표현할 수 있다. 선행 조건은 **실행 provenance** 다 — 남의 기계에서 돈
   실행은 "누가 시켜서 났나"가 우리 원장에서 끊긴다.
