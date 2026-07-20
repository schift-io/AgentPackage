# seeds/ — 비어 있음 (배선 완료, 콘텐츠만 없음)

`apm.yml`의 `memory.seed`(`apm_memory_seed.py` 참조) 선언은 팩 안에 동봉된
`.cclg` 컨테이너를 참조한다. 이 팩은 아직 `memory.seed`를 선언하지 않는다 — 단,
과거 이 문서가 적었던 두 가지 blocker는 **이제 둘 다 해소됐다**:

1. ~~company-memory-pack → `.cclg` 어댑터가 없다~~ → **있다**.
   `agent_hub.memory_pack_import.build_cclg_from_memory_pack`이
   `company-memory-pack/0.1` 마크다운을 파싱(`memory_pack_to_nodes`)해 `.cclg`
   컨테이너로 빌드한다.
2. ~~`apm_memory_seed.install_pack_seeds()`에 호출부가 없다~~ → **있다**.
   `apm_publish._install_seeds_from_bundle`가 레지스트리 폴백
   (`apm_publish.load_registry_pack`)에서 받은 `.apm` 번들의 선언된 시드에 대해
   `install_pack_seeds()`를 호출한다. 이중 opt-in 피처플래그
   (`APM_REGISTRY_RESOLVE` + `APM_REGISTRY_SEED_INSTALL`, 둘 다 기본 꺼짐)로
   게이트되어 있어, 한 팩을 켠다고 다른 팩들이 자동으로 메모리를 얻지 않는다.

버킷 → md 생성 자체도 이제 스킬로 존재한다: `company-memory-curation`(코어
`agent_hub.bucket_curation.curate_company_memory_pack`)이 org의 잡다한 default
지식 버킷을 분류·추출해 `company-memory-pack/0.1` 마크다운을 만든다. keep 0건이면
실패하는 fail-closed 계약이라 근거 없는 팩이 나오지 않는다.

## 남은 것 — 운영 단계 (콘텐츠가 없을 뿐, 코드 배선은 끝)

`seeds/`가 비어 있는 이유는 이제 "만들 수 없어서"가 아니라 **아직 이 org의
memory-pack을 실제로 정리해서 넣지 않아서**다. 남은 절차:

1. `company-memory-curation` 스킬로 이 org의 default 버킷을 정리해
   `company-memory-pack/0.1` 마크다운을 생성한다.
2. 두 경로 중 하나를 고른다:
   - **팩 시드로 커밋**: `build_cclg_from_memory_pack`으로 `.cclg`를 빌드해
     `seeds/company-memory.cclg`로 여기 놓고, `apm.yml`에
     `memory: {seed: [{ref: ./seeds/company-memory.cclg, install: import_pending}]}`을
     추가한다. 이 경로로 실제 동작하려면 배포 환경에
     `APM_REGISTRY_RESOLVE`/`APM_REGISTRY_SEED_INSTALL`이 켜져 있어야 한다
     (레지스트리 폴백을 타는 설치 경로 전제).
   - **런타임 즉시 import**: `memory_import.import_scope_cclg`를 직접 호출해
     pending으로 등록한다(팩 시드 경로를 거치지 않는 경우).
3. Ops Console에서 pending import를 승인 → tenant core memory로 승격 확인.

이 절차가 끝나기 전까지, 또는 두 피처플래그가 꺼져 있는 배포 환경에서는
`company-memory-grounding` 스킬은 core memory가 비어 있는 상태로 동작하며, 이는
fail-closed 상 정상이다(창조 금지 원칙 유지 — 빈 core memory에서 사실을 지어내지
않는다).
