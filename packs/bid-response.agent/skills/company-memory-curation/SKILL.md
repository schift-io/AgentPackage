---
name: company-memory-curation
description: Curate the org's messy default knowledge bucket (company docs + support tickets + unrelated notes + analytics events all mixed together) into a company-memory-pack/0.1 markdown document — the pre-step that feeds tenant core memory.
---

# 회사 메모리 정리 룰 (bucket curation)

## Purpose

org의 `default` 지식 버킷은 손으로 깨끗하게 관리되지 않는다 — 회사 문서, 지원
티켓, 학습 자료, 무관 잡담, 애널리틱스 이벤트가 한데 섞여 쌓인다. 이 스킬은 그
잡다한 버킷을 **정리 룰(bucket curation)**로 걸러 `company-memory-pack/0.1`
마크다운(company/capabilities/references/team/compliance/constraints/usage_map
6개 섹션)으로 정리한다. 이 마크다운이 곧 `company-memory-grounding` 스킬이 조회할
tenant core memory의 원재료다 — **정리 룰이 채우고, grounding이 읽는다.**

코어 구현: `agent_hub.bucket_curation.curate_company_memory_pack`
(`services/agent-hub/src/agent_hub/bucket_curation.py`).

## Inputs

- `documents: list[BucketDoc]` — 정리 대상 버킷 문서 리스트 (`id`, `title`, `text`).
  대상은 org의 `default` 지식 버킷 전체(또는 그 하위 스코프).
- `company_key: str` — 정리 결과가 귀속될 회사 식별자. 필수, 빈 문자열이면
  `ValueError`.
- (선택) `strong_signal_autokeeps: bool` — 회사 신호 패턴에 걸리고 노이즈가 없으면
  LLM classify 없이 바로 keep 확정할지(LLM 비용 절감용, 기본 False).

## Pipeline (단계)

1. **휴리스틱 프리필터** (`heuristic_verdict`) — 결정적 정규식으로 명백한 케이스만
   싸게 처리한다. 노이즈 패턴(지원 티켓/오류 문의/학습 자료/봇 설치 가이드/GA
   이벤트명 등)에 걸리고 회사 신호가 전혀 없으면 drop 확정. 애매하면 절대 단정하지
   않고 `None`을 반환해 다음 단계로 위임한다.
2. **LLM 분류** (`classify_fn`) — 프리필터가 확정하지 못한 문서만 LLM에게 keep/drop
   판정을 받는다. 실제 LLM 배선 기본값은 `bucket_curation_prompts.py`가 제공한다
   (`classify_fn`/`extract_fn`은 둘 다 주입식 — 테스트는 fake로 갈아끼운다).
3. **LLM 추출** (`extract_fn`) — keep으로 판정된 문서 전체를 한 번에 LLM에 넘겨
   `company-memory-pack/0.1` 마크다운(YAML frontmatter + `## company` /
   `## capabilities` / `## references` / `## team` / `## compliance` /
   `## constraints` / `## usage_map`)으로 구조화한다. **kept 문서에 있는 사실만
   옮긴다 — 추론·창조 금지.**
4. **스키마 검증** (`validate=True`, 기본값) — 반환 전에
   `agent_hub.memory_pack_import.memory_pack_to_nodes`로 파싱해 fail-closed
   검증한다. 프런트매터 누락, `schema_version` 불일치, 인식 불가 섹션이면 여기서
   `MemoryPackParseError`가 나서 하류로 넘어가지 않는다.
5. **(이 스킬 밖) 하류 체인** — 검증된 마크다운은
   `memory_pack_import.build_cclg_from_memory_pack`으로 `.cclg` 컨테이너가 되고,
   `memory_import.import_scope_cclg`(또는 팩 시드 경로면
   `apm_memory_seed.install_pack_seeds`)로 **pending** 상태로 core memory에
   올라간다. Ops Console에서 승인해야 tenant core memory로 승격된다 — 이 스킬은
   pending까지만 책임지고, 승인 게이트는 건드리지 않는다.

## Rules

- **창조 금지**: 추출 단계는 kept 문서에 실제로 적힌 사실만 옮긴다. 문서에 없는
  capability/reference/수치를 지어내지 않는다.
- **keep 0건이면 실패**: `curate_company_memory_pack`은 keep으로 판정된 문서가
  하나도 없으면 추출을 시도하지 않고 `ValueError`를 던진다(근거 없는 memory-pack을
  만들지 않는다 — fail-closed).
- **pending → 승인 게이트 유지**: 이 스킬의 산출물이 core memory에 자동으로
  승격되지 않는다. `import_scope_cclg`/`install_pack_seeds` 모두 pending 상태로
  기록하고 Ops Console 승인을 거친다. 정리 룰이 이 게이트를 우회하도록 만들지
  않는다.
- **애매하면 LLM에 위임**: 프리필터가 노이즈/신호 둘 다 있거나 둘 다 없는 문서를
  자체 판단으로 keep/drop 확정하지 않는다(`heuristic_verdict`가 이미 이렇게
  설계됨 — 이 계약을 재구현하지 않는다).
- 지식 버킷 자체(원본 문서)를 이 스킬이 수정/삭제하지 않는다 — 읽어서 별도
  memory-pack 산출물을 만들 뿐이다.

## 도구 경계

- 버킷 문서 열람은 org의 지식 버킷 조회 경로(이 스킬 밖 — RAG 검색 도구)를 그대로
  쓴다. 이 스킬은 이미 모아진 `BucketDoc` 리스트를 입력으로 받는다.
- `.cclg` 빌드(`build_cclg_from_memory_pack`)와 core memory import
  (`import_scope_cclg`/`install_pack_seeds`)는 이 스킬의 책임 밖이다 — 산출물
  마크다운을 넘기기만 한다.
- `company-memory-grounding`과의 관계: 이 스킬이 버킷 → memory-pack md를 만들고
  하류 체인이 그것을 core memory로 올리면, `company-memory-grounding`이 그 core
  memory를 조회해 bid-response 드래프팅에 근거를 공급한다. 이 스킬은 조회하지
  않는다 — 채우기만 한다.

## Output Contract

- `CurationResult`:
  - `pack_markdown: str` — 검증 통과한 `company-memory-pack/0.1` 마크다운 전체.
  - `company_key: str`
  - `kept_doc_ids: list[str]` / `dropped_doc_ids: list[str]`
  - `verdicts: list[DocVerdict]` — 문서별 `{doc_id, title, keep, reason}`.
    `reason`은 `"heuristic:noise" | "heuristic:signal" | "llm:keep" | "llm:drop"`
    중 하나 — 어떤 문서가 왜 걸러졌는지 감사 가능하게 남긴다.
