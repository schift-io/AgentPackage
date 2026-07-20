# 정리 룰 택소노미 — keep/drop 기준 + 섹션 매핑

`company-memory-curation` 스킬의 분류/추출 단계가 따르는 참조표. 코어 구현은
`agent_hub.bucket_curation`(`heuristic_verdict`의 `_NOISE_TITLE_PATTERNS` /
`_COMPANY_SIGNAL_PATTERNS`가 정본 정규식 — 이 표는 그 패턴이 왜 이렇게 잡혔는지의
설명 + 실측 관측 예시다. 정규식 자체를 바꾸려면 코어 코드를 고쳐야 한다).

## Keep — 회사 관련 (memory-pack에 들어감)

| 범주 | 실측 default 버킷 관측 예시 | 대략 비중 |
|------|------------------------------|-----------|
| 회사 정체성 | "Room821/Schift 소개", "스키프트 회사 개요" | 소수 |
| 역량(capabilities) | "RAG 파이프라인 기술 소개", "OCR/임베딩 엔진 스펙" | 다수 |
| 실적·레퍼런스(references) | "청창사 수주 사례", "고객사 레퍼런스 정리", "견적 대응 이력" | 다수 |
| 팀 | "조직도", "핵심 인력 프로필" | 소수 |
| 컴플라이언스 | "인증 현황", "보안 규정 준수 문서" | 소수 |
| 제약(constraints) | "기재 금지 목록", "영업 비밀 가이드" | 소수 |
| 영업·사업 문서 | "사업 설명회 자료", "사업 계획", "정부 지원 과제 신청 내역" | 다수 |
| 보도자료·채용·경쟁사 | "보도자료 초안", "채용 공고", "경쟁사 비교" | 소수 |
| 평가항목 매핑(usage_map) | "평가배점별 대응 근거 정리" | 소수 |

## Drop — 노이즈 (memory-pack에서 제외)

| 범주 | 실측 default 버킷 관측 예시 |
|------|------------------------------|
| 지원 티켓·오류 문의 | "파일 로딩 5% 멈춤", "학교 인증 메일 안와요", "버그 리포트" |
| 학습/교육 자료 | "국어 비문학 문제 제작 도구", "박상진 N주차 N단원", "모의고사" |
| 봇 설치 가이드 | "봇 설치 가이드", "어떻게 하나요" 계열 사용법 문의 |
| 애널리틱스 이벤트 | `begin_checkout`, `purchase`, `sign_up`, `add_to_cart`, `page_view`, `view_item` 등 GA 이벤트명 그대로 문서화된 항목 |
| 로그인/계정 잡음 | "인증 메일", "비밀번호 찾기", "로그인 안됨" |
| 무관 잡담 | 위 어느 범주에도 안 걸리고 회사 신호도 없는 나머지 |

프리필터는 **노이즈 패턴에 걸리고 회사 신호가 전혀 없을 때만** drop을 확정한다.
노이즈/신호가 둘 다 있거나(예: "OCR 봇 설치 가이드"), 신호가 있어도
`strong_signal_autokeeps=False`(기본값)면 LLM `classify_fn`이 최종 판단한다 —
휴리스틱은 명백한 케이스의 LLM 호출 비용만 아낀다.

## 버킷 문서 → company-memory-pack 섹션 매핑

| 버킷 문서 유형 | memory-pack 섹션 | node type (`.cclg` 변환 후, 참고) |
|-----------------|-------------------|-------------------------------------|
| 회사 소개, 연혁 | `company` | `identity_fact` |
| 역량/기술 소개, 제품 스펙 | `capabilities` | `project_fact` (`### cap.<key>` 소제목별로 분리) |
| 실적, 수주, 레퍼런스, 견적 이력 | `references` | `artifact_reference` (`- **ref.<key>**` 불릿별로 분리) |
| 조직도, 팀 프로필 | `team` | `project_fact` |
| 인증, 보안/규정 준수 | `compliance` | `project_fact` |
| 기재 금지 목록, 영업 비밀, blocker | `constraints` | `constraint` (`### <소제목>` 하위 번호/불릿 항목별로 분리) |
| 평가항목 ↔ capability/reference 매핑 | `usage_map` | `project_fact` |

섹션 매핑은 추출 단계(`extract_fn`)가 keep 문서의 **내용**을 보고 결정한다 — 버킷
문서 하나가 여러 섹션에 걸쳐 인용될 수 있다(예: "청창사 수주 사례" 문서가
`references`뿐 아니라 `usage_map`의 근거로도 쓰일 수 있음). 이 표는 일반적인
1차 매핑 가이드이며, 정확한 파싱 규칙(소제목/불릿 형식)은
`memory_pack_import._SECTION_NODE_TYPE` / `_CAP_HEADING_RE` /
`_REF_BULLET_RE` / `_CONSTRAINT_HEADING_RE`가 정본이다.
