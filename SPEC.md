# Agent Package (`.apm`) — 포맷 사양 v1

이 문서가 **`.apm` 의 규범적 사양**이다. 여기 적힌 것과 구현이 다르면 **구현이 버그**다.
README 는 "왜 이 포맷인가"를 논증하고, 이 문서는 "무엇이 참인가"를 정의한다.

- 상태: **v1, 사내 사양**(private). 서명은 아직 없다(§9).
- 정본 구현: `kit/apm_codec.py`(컨테이너·해시) · `kit/capabilities.json`(능력 어휘) ·
  `kit/apm_kit.py`(검증·빌드 CLI).
- 라이선스: Apache-2.0 (`LICENSE`).

> ⚠️ **이름 충돌.** 이 `APM` 은 **Agent Package** — 봉인된 단일 아티팩트 포맷이다.
> [`microsoft/apm`](https://github.com/microsoft/apm)("Agent Package Manager", npm 식
> 의존성 관리자로 `apm_modules/` 에 풀어놓는 방식)과 **무관하며 코드·스키마 어느 쪽도
> 참조하지 않는다.** README 가 그 프로젝트의 이슈를 인용하는 건 설계 논증의 반례로서일
> 뿐이다. 외부 문서에서는 첫 등장에 ``Agent Package (`.apm`)`` 로 적는다.

---

## 1. 범위

| 규정한다 | 규정하지 않는다 |
|---|---|
| `.apm` 컨테이너 바이트 레이아웃(§3) | 팩이 무엇을 하는지(도메인 정책 — `agent.md` 의 몫) |
| content-hash 산출식(§4) | 호스트의 실행 모델·스케줄링 |
| 매니페스트 정본 판정 순서(§5) | 레지스트리 API 표면(호스트 소관) |
| 호스트 능력 계약과 fail-closed 판정(§6) | 결제·과금 정책 |
| 발행 게이트(§7) · 버전 판정(§8) | 서명·발행자 신뢰(§9, 미정) |

## 2. 용어

- **팩(pack)** — 디렉터리 `<slug>.agent/`. 저작 단위.
- **`.apm`** — 팩 디렉터리를 통째로 봉인한 단일 아티팩트. 배포·설치 단위.
- **매니페스트(manifest)** — `.apm` 안 `manifest.json` 의 JSON 객체. 등록·실행 메타의 정본.
- **호스트(host)** — 팩을 실행하는 런타임. 현재 둘: `agent-hub`(Schift Cloud) ·
  `local-byo`(로컬 Claude Code / Codex).
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

## 5. 팩 레이아웃과 매니페스트 정본

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
| `artifacts.package_ref` | | `<slug>@<version>`. **버전 판정의 실체**(§8) |
| `marketplace.*` | | 발행 선언(§7) |
| `router_*` · `hub.*` | | 등록/전시 메타 — 해시 제외(§4.1) |
| `memory.seed` | | 선언하면 발행 전 seed 검증이 fail-closed 로 돈다 |

`agent.md` 누락, `name`/`version` 누락은 **lint 실패**다.

## 6. 호스트 능력 계약 — fail-closed 협상

**"이 호스트가 이 팩이 시도할 일을 실제로 할 수 있나"를 실행 전에 묻는다.** 이것이
포맷의 핵심이며, 참조용 스킬 포맷에는 이 질문 자체가 없다.

- 팩은 `runtime_boundary.host_services_only` 로 요구 능력을 선언한다.
- 능력 이름의 **전체 집합(어휘)은 `kit/capabilities.json` 이 단일 정본**이다. 어휘에
  없는 이름을 선언하면 lint/check 가 실패한다(오타·무단 신규 차단).
- 호스트는 `provides: "*"` 또는 `excludes: [...]` 로 자기 능력을 선언한다.
  - `agent-hub` — `provides: "*"`
  - `local-byo` — `excludes: usage_ledger, credit_metering, render_worker,
    stitch_worker, connector_handoff, higgsfield_mcp`
- **판정 (규범):** `required = 선언집합`, `unknown = required − 어휘`,
  `missing = (required ∩ 어휘) − host_provides`.
  `unknown` 또는 `missing` 이 비어 있지 않으면 **거절한다.** 요구가 아예 없으면 통과.
- `cloud_only`(`usage_ledger`, `credit_metering`) = 유저 머신에서 강제 불가능한 능력.
  이걸 요구하는 팩은 로컬 호스트에서 항상 거절된다.

두 호스트 체제에서 가장 위험한 실패 모드는 크래시가 아니라 **조용히 반쯤 도는 것**이다.
그래서 판정은 fail-open 이 아니라 fail-closed 다.

```
$ apm-kit check image-gen.agent --host local-byo
✗ image-gen.agent: host 'local-byo' lacks ['usage_ledger']
```

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
  명시적으로 출력한다(조용히 건너뛰지 않는다). 현재(이 repo 기준) 루트 `identity-patterns.json`
  의 내용: `Room 821` · `room821` · `#FF4D00` · `kimbyun`.
- **소스 위치:** 마켓플레이스 항목의 `source` 는 이 repo 안 상대경로가 아니라 **각 팩의
  공개 repo** 를 가리킨다. 이 repo 는 private 이고 내부 팩을 담고 있어서, 마켓플레이스로
  쓰려고 public 으로 뒤집으면 그 소스가 통째로 노출된다 — `marketplace.json` 은 *목록에
  뭘 싣느냐*만 통제하지 *repo 에 뭐가 보이느냐*는 통제하지 못한다.
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
3. **매니페스트 이중 선언 — 이것이 자동 발행을 막고 있는 진짜 부채.** kit 은
   `apm.yml` 에서 파생하고 agent-hub 는 코드(`AGENT_PACKS`)에서 만든다. 같은 팩·같은
   버전에 **다른 매니페스트 → 다른 hash** 라, 두 발행자가 동시에 붙으면 매번 409 이거나
   서로 덮어쓴다. `manifest_overrides` 폐기 + `pack.json` 단일화로 수렴한다(§5 의 정본
   판정 순서가 이미 그 방향이다 — `pack.json` 이 있으면 파생을 안 거치므로 hash 가
   자동으로 맞는다). 수렴 전까지 `.github/workflows/publish.yml` 의 자동 발행은 켜지
   않으며, 켤 때 **발행 주체를 하나로 확정**해야 한다.
4. **서명이 없다.** content-hash 는 **변조를 잡지만 출처를 증명하지 못한다.** 자사
   배포에서 hash 는 주로 위생이며, 제3자 팩을 받기 시작하는 순간 서명이 함께 필요하다.
   그 전까지 런타임 설치본 실행(`SCHIFT_PACK_INSTALL`)은 켜지 않는다.
