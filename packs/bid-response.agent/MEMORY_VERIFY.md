# 메모리 검증 패스 스펙 (owner 지시 2026-07-11: "cclg cache hit, schift memory 다 체크해")

E2E 실런 완료 직후, 같은 로컬 스택에서 실행하는 검증 체크리스트. 전부 실측 — 추정 금지.

## A. cclg 쪽

1. **임포트 멱등성/캐시 히트**: 동일 schift-memory-pack.md → .cclg를 **2회 연속 import** — 2회차가 (a) 중복 노드를 만들지 않고 (b) 기존 노드 재사용(캐시 히트)으로 처리되는지. memory_pack_import의 결정적 노드 id(sha1)가 실제로 dedup을 보장하는지 노드 수 before/after로 확인.
2. **컨테이너 재빌드 바이트 동일성**: 같은 팩 2회 빌드 → 컨테이너 바이트 diff 0 (빌더 테스트에 있지만 스택 위에서 재확인).
3. **effective-view**: import된 core 노드들이 effective-view 조회에서 실제로 나오는지, 캐시된 조회(2회차 조회)가 히트하는지 — cclg⇄schift 공존 계약(컨테이너+memory.* MCP+effective-view)의 실동작 확인.

## B. Schift memory (3-tier) 쪽

4. **tier 격리**: import 노드들이 정확히 core tier에만 있는지 (agent/session tier 오염 0).
5. **pending 게이트**: import 직후 상태가 pending인지, 승인 라우트(agent_memory_ops) 경유 후 active 전환되는지 — fail-closed 확인.
6. **런타임 grounding 증거**: bid-response 실런의 프롬프트/트레이스에 core memory 내용이 실제로 주입됐는지 (제안서 산출물에 memory-pack 사실이 인용된 것과 대조 — "프롬프트 직삽입"이 아니라 memory 경로로 온 것인지 로그로 구분).
7. **세션 메모리 비오염**: 런 종료 후 session tier에 회사 사실이 승격/복사되지 않았는지 (company vs session 버킷 분리 원칙).
8. **재런 캐시**: 동일 입력 2회차 런에서 memory 조회가 재사용되는지 (쿼리 수/지연 비교).

## 산출

`server-run/full-runtime/MEMORY_VERIFY_REPORT.md` — 항목별 PASS/FAIL/N-A + 근거(노드 수·로그 인용). FAIL은 수정하지 말고 보고만 (수정은 별도 판단).
