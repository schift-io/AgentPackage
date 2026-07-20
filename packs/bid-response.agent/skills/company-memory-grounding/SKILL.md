---
name: company-memory-grounding
description: Ground each scoring item in the requirement map against the tenant's core memory (APM 3-tier default memory, NOT a knowledge bucket) so proposal drafting only ever asserts facts that exist in the company's memory.
---

# 회사 메모리 그라운딩 (tenant core memory 조회)

## Purpose

`requirement-scoring-map`이 만든 평가항목별 매핑 골격에 **tenant core
memory**(APM 3-tier 디폴트 메모리의 Core/tenant 레벨)에서 조회한 회사
capabilities/references/constraints를 채운다. **지식 버킷 RAG 검색이 아니다** —
회사 컨텍스트는 항상 이 회사가 소유한 core memory에서만 끌어온다.

## 배경 (owner 확정 사항)

- 회사 메모리는 `company-memory-pack`(`schema_version: company-memory-pack/0.1`)
  스키마로 정의되고, **IMPORT되면 지식 버킷이 아니라 tenant core memory로 들어간다.**
  이 팩은 `company`, `capabilities`, `references`, `team`, `compliance`,
  `constraints`, `usage_map` 6개 섹션을 갖는다(정본: 회사 로컬 메모리 팩 문서 —
  경로는 IMPORT 시점에 org별로 다르다).
- 런타임 조회는 `schift.memory.query`(agent-hub의 3-tier
  `memory_repo.py` core/agent/session 중 **core** 스코프)로 한다.

## Inputs

- `requirement-scoring-map`이 만든 `scoring_to_capability_map` 골격.
- tenant core memory (company-memory-pack IMPORT 결과 — **이 슬라이스에서는
  IMPORT 배선이 없다.** 아래 "현재 상태" 참조).

## Pipeline (단계)

1. **평가항목별 조회** — 각 `scoring_item`에 대해 `schift.memory.query`로 core
   memory를 조회해 관련 `capabilities`/`references`를 찾는다(memory-pack의
   `usage_map` 섹션이 있으면 그 매핑을 그대로 재사용 — 임의 재해석 금지).
2. **constraints 적용** — 조회된 capability/reference에 해당하는
   `constraints`(전역 기재 금지 목록 + blocker)를 함께 가져와 이후 드래프팅
   단계에 전달한다.
3. **MISSING-ask 가드** — core memory에 해당 평가항목을 뒷받침할 capability가
   없으면 캐내지 않는다 — `"MISSING — ask"` 또는 `[확인 필요]`로 남기고 사람에게
   질문 목록으로 묶어 올린다(오길비 브리프 스킬과 동일한 가드 패턴).

## 현재 상태 (블로커 해소 — 운영 단계만 남음)

과거 이 섹션은 "md→core memory 배선이 없다"를 블로커로 기록했다. 이제 배선 자체는
끝났고, 남은 것은 **실제 org의 memory-pack을 만들어 넣는 운영 단계**뿐이다.

- **버킷 → md**: `company-memory-curation` 스킬(코어: `agent_hub.bucket_curation`)이
  org의 잡다한 default 지식 버킷을 분류·추출해 `company-memory-pack/0.1` 마크다운을
  만든다. keep 0건이면 실패하는 fail-closed 계약이라 근거 없는 팩은 나오지 않는다.
- **md → `.cclg`**: `agent_hub.memory_pack_import.build_cclg_from_memory_pack`이
  이 마크다운을 파싱(`memory_pack_to_nodes`)해 `.cclg` 컨테이너로 빌드한다. 이
  어댑터는 이미 존재한다 — memory-pack 문서를 `.cclg` 형식으로 변환하는 코드가
  없다는 과거 서술은 stale.
- **`.cclg` → core memory (pending)**: `memory_import.import_scope_cclg`가
  `.cclg` 컨테이너를 파싱해 pending 상태로 기록한다. 팩 시드 경로라면
  `apm_memory_seed.install_pack_seeds()`가 이 함수를 경유한다. **호출부도 이제
  존재한다**: `apm_publish._install_seeds_from_bundle`가 레지스트리 폴백
  (`apm_publish.load_registry_pack`)에서 받은 `.apm` 번들의 선언된 시드에 대해
  이 함수를 호출한다 — 이중 opt-in 피처플래그(`APM_REGISTRY_RESOLVE` +
  `APM_REGISTRY_SEED_INSTALL`)로 게이트되어 둘 다 켜지 않으면 동작하지 않는다
  (기본은 꺼짐 — 한 팩을 켠다고 다른 팩이 자동으로 메모리를 얻지 않게 하는
  의도적 설계).
- **승인 게이트**: 위 어느 경로든 pending으로 기록될 뿐 즉시 tenant 진실로
  승격되지 않는다. Ops Console에서 사람이 승인해야 core memory로 올라간다.

**남은 운영 단계**: (1) 이 org의 실제 memory-pack을 정리 룰로 생성, (2)
`seeds/`에 커밋하거나 런타임 import 경로로 밀어넣기, (3) 두 피처플래그를 켜거나
직접 `import_scope_cclg` 호출로 pending 등록, (4) Ops Console 승인. 이 4단계가
끝나기 전까지, 또는 이 org가 아직 memory-pack을 넣지 않은 상태에서는 core memory가
비어 있고 이 스킬은 여전히 전부 `[확인 필요]`로 떨어진다 — 이는 fail-closed 상
정상 동작이다(창조 금지 원칙 유지, 배선이 끝났다고 빈 core memory에서 사실을
지어내지 않는다).

## Rules

- 절대 지식 버킷(company_rag_bucket) 검색으로 대체하지 않는다 — 이 팩의 회사
  컨텍스트는 core memory 전용 경로로만 조회한다.
- constraints에 있는 항목(LPDM 특허 방법론, 임베딩 모델명, 엔진 내부, 3-tier
  메모리 구현 상세, 비용/마진, 사고 이력 등)은 **draft 단계로 절대 전달하지 않는다.**
- core memory 조회 결과가 없으면 "미확인" 상태로 명시하고, 회사가 아직
  memory-pack을 IMPORT하지 않았을 가능성을 안내한다.

## 도구 경계

- 조회: `schift.memory.query`(core 스코프). append/flush는 이 스킬 책임이 아니다
  (그건 세션 메모리 쓰기, agent-hub의 다른 훅 소관).
- 버킷 → memory-pack md 생성은 `company-memory-curation` 스킬 소관이다. md →
  `.cclg` 변환(`memory_pack_import.build_cclg_from_memory_pack`), IMPORT
  실행(`memory_import.import_scope_cclg` / `apm_memory_seed.install_pack_seeds`)은
  이 스킬 밖의 하류 체인 — 이 스킬은 그 결과물(core memory)을 조회만 한다.

## Output Contract

- {id, title, bullets:[{claim, details[]}]} — 평가항목별 채워진
  `capability_keys`/`reference_keys`/`constraint_keys` + [확인 필요] 목록.
