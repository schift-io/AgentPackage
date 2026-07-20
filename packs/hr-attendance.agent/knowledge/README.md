# HR/근태 APM 법률 RAG 콘텐츠 가이드

이 디렉토리는 Schift HR/근태 APM이 근로기준법, 연차, 주 52시간, 대체공휴일 등을 근거로 검토할 때 사용하는 RAG 콘텐츠를 관리합니다.

> 법률 자문이 아닙니다. 모든 법률 적용 판단은 사람/노무 전문가가 최종 확인해야 합니다.

## 1. 대상 버킷

- 버킷 ID/이름: `kr-labor-law-reference`
- 역할(role): `regulation_reference`
- 사용 Agent: `services/agent-hub/apm/hr-attendance.agent/`
- APM 정의: `apm.yml`의 `knowledge` 섹션 참조

## 2. 콘텐츠 파일 목록 (`rag-sources/`)

| 파일 | 주제 | 법률 영역 |
|---|---|---|
| `01-labor-standards-act-overview.md` | 근로기준법 개요, 적용 범위, 근로규칙 | general |
| `02-annual-paid-leave.md` | 연차유급휴가 발생, 사용, 소멸 | annual_leave |
| `03-working-hours-and-52h.md` | 근로시간, 연장근로, 주 52시간, 휴게시간 | working_hours |
| `04-holidays-and-substitute-holidays.md` | 휴일, 유급휴일, 대체공휴일 | holiday |
| `05-overtime-night-holiday-premium.md` | 연장·야간·휴일 가산수당 | premium_pay |
| `06-leave-types-and-company-rules.md` | 반차, 병가, 경조휴가 등 휴가 유형 | leave_types |
| `07-annual-leave-promotion-and-payout.md` | 연차 촉진, 미사용 연차수당 | annual_leave |
| `08-enforcement-and-dispute-remedies.md` | 시정조치, 구제절차, 분쟁 대응 | enforcement |
| `09-hr-attendance-faq.md` | HR/근태 상황별 FAQ | faq |

## 3. 청킹 및 메타데이터 권장 설정

- `chunk_size`: 512
- `chunk_overlap`: 50
- `ocr_strategy`: auto (마크다운이므로 실제로는 텍스트 추출)
- 파일 형식: Markdown (`.md`)

### 자동 메타데이터 태그

업로드 스크립트는 각 문서에 다음 메타데이터를 부여합니다.

- `agent_hub_bucket_role`: `regulation_reference`
- `agent_hub_contract`: `SCHIFT_RAG_BUCKET` 또는 `kr-labor-law-reference`
- `source_group`: `kr-labor-law`
- `memory_kind`: `regulation_reference`
- `law_area`: `annual_leave`, `working_hours`, `holiday`, `premium_pay`, `leave_types`, `enforcement`, `faq`, `general`
- `canonicality`: `reference`
- `product_area`: `hr_attendance`
- `source_rel_path`: `rag-sources/` 기준 상대 경로
- `source_sha256`: 파일 SHA-256 해시
- `effective_date`: 법령 기준일(스크립트 실행일)
- `seed_batch`: 업로드 배치 ID

## 4. 업로드 방법

### 4.1 전용 스크립트 사용 (권장)

```bash
cd services/agent-hub/apm/hr-attendance.agent

# dry-run으로 미리보기
python3 scripts/upload_labor_rag.py --dry-run

# 실제 업로드
SCHIFT_API_KEY=<your-key> python3 scripts/upload_labor_rag.py

# 버킷 이름 변경
SCHIFT_API_KEY=<your-key> python3 scripts/upload_labor_rag.py --bucket my-labor-bucket
```

### 4.2 Schift CLI 사용

```bash
# 버킷이 없으면 자동 생성됩니다.
schift upload knowledge/rag-sources/*.md --bucket kr-labor-law-reference \
  --chunk-size 512 --chunk-overlap 50
```

### 4.3 Python SDK 사용

```python
import os
from pathlib import Path
from schift import get_client

bucket_id = "kr-labor-law-reference"
files = list(Path("services/agent-hub/apm/hr-attendance.agent/knowledge/rag-sources").glob("*.md"))

with get_client(api_key=os.environ["SCHIFT_API_KEY"]) as client:
    for f in files:
        client.buckets.upload(
            bucket_id,
            files=[(f.name, f.read_bytes(), "text/markdown")],
            metadata={
                "source_group": "kr-labor-law",
                "law_area": f.stem.split("-")[0],
                "memory_kind": "regulation_reference",
            },
            chunk_size=512,
            chunk_overlap=50,
        )
```

## 5. 업데이트 주기

- 법령 개정 시 즉시 업데이트
- 대체공휴일 지정 발표 시 `04-holidays-and-substitute-holidays.md` 업데이트
- 분기별 전체 검토 권장
- 업데이트 시 `effective_date`와 `seed_batch`를 갱신하여 버전 관리

## 6. 회사 내규와의 관계

- 이 콘텐츠는 법률의 일반 원칙을 담고 있습니다.
- 회사 내규는 근로기준법보다 불리할 수 없습니다(최저기준).
- Agent는 법률 적용을 단정하지 않고, 위반 가능성 수준만 제시해야 합니다.
- 회사별 규정(연차 기준, 반차 단위, 결재선 등)은 `{SCHIFT_COMPANY_RAG_BUCKET}` 버킷에 별도 관리합니다.
