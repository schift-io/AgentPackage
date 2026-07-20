# 지원 계약 유형 (P1 MVP 4종)

| 유형 | 코드 | 대가 질문 여부 | 비고 |
|------|------|----------------|------|
| 업무협약서(MOU) | `mou` | 없음 | 법적 구속력 있는 채무를 원칙적으로 부과하지 않음(협약 성격) |
| 비밀유지계약서(NDA) | `nda` | 없음 | 정의/예외/반환폐기 조항이 핵심 |
| 용역/서비스계약서 | `service` | 있음(용역대가) | 발주자/수행자 표기, 지재권 귀속 조항 포함 |
| 공동사업협약서 | `joint_business` | 있음(수익배분 기준) | 역할분담·비용부담 조항 포함 |

새 유형 추가 절차:

1. `contract_writer_contracts.py`의 `ContractType` enum에 값 추가.
2. `contract_writer_templates.py`에 해당 유형의 `ClauseTemplate` 목록 등록
   (`_TEMPLATES` dict에 매핑).
3. `contract_writer_intake.py`의 `_TYPE_EXTRA_ASK_FIELDS`에 대가/특수 질문이
   필요하면 추가.
4. `apm.yml`/`agent.md`의 유형 목록 언급 갱신.
