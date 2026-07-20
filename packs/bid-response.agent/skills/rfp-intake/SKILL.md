---
name: rfp-intake
description: Download the selected 나라장터 공고's RFP/제안요청서 attachments and ingest them into the session bucket (OCR → chunk → embed) so downstream skills can retrieve requirements.
---

# RFP Intake (공고 첨부 다운로드 → 세션 버킷 ingest)

## Purpose

선택한 나라장터 공고의 제안요청서·과업지시서·공고서 첨부를 다운로드해 **세션 전용
버킷**(회사 core memory 버킷이 아님)에 ingest한다. 이후 스킬들이 이 RFP를
schift-rag로 검색해 평가배점에 맞춘 제안서를 쓴다.

## Inputs

- `bid_ntce_no`(공고번호) — 사용자가 선택한 공고.
- (선택) 이미 알고 있는 첨부 카테고리 우선순위: 제안요청서 > 과업지시서 > 공고서.

## Pipeline (단계)

1. **첨부 URL 조회** — 공고 아이템의 `raw_json`(`ntceSpecDocUrl1~10` /
   `ntceSpecFileNm1~10`)에서 제안요청서·과업지시서·공고서를 우선 추린다. 별도
   첨부 API는 없다 — 공고 아이템 캐시를 조회 도구로 재사용한다(`zodal_resolve_rfp_urls`
   계열 계약, 나라장터 일반으로 파라미터화).
2. **다운로드 → ingest** — 첨부를 다운로드해 세션 버킷에 OCR→청킹→임베딩
   (`schift_default` ingest 경로)한다.
3. **첨부 목록 확인** — 어떤 첨부가 ingest됐는지, 제안요청서/과업지시서/공고서
   중 어느 것이 빠졌는지 확인 문구로 남긴다. 빠진 문서가 있으면 [확인 필요].

## Rules

- **read + own-storage write만** — 공개 RFP 다운로드 → 사용자 자기 세션 버킷.
  제3자 외부 write가 아니므로 human_approval은 불필요하지만, egress는
  allowlist(공공조달 포털 도메인만)로 제한한다.
- credential 불필요(공개 다운로드).
- 첨부가 스캔 PDF/HWP 혼재일 수 있으므로 OCR 실패·저품질 페이지는 [확인 필요]로
  남기고 진행한다(자동 확정 금지).

## 도구 경계

- 다운로드·ingest 자체는 AWP 도구(`zodal_fetch_rfp` 계열 계약, 도메인만
  나라장터 일반으로 파라미터화)가 처리한다. 이 스킬은 어떤 첨부를 어떤 우선순위로
  가져올지의 판단만 정의한다.
- ingest된 RFP 검색은 `schift-rag`(세션 버킷 스코프)로 한다. 회사 core memory는
  이 스킬이 아니라 `company-memory-grounding` 스킬이 별도로 조회한다.

## Output Contract

- `{id, title, bullets:[{claim, details[]}]}` — 확보된 첨부 목록 + 누락 첨부
  + ingest 상태.
