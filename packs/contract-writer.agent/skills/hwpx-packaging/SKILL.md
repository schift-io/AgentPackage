---
name: hwpx-packaging
description: Convert the review-gate-passed contract markdown into a single HWPX file via document-helper. HWPX only — DOCX is forbidden for Korean documents.
---

# markdown → HWPX 패키징

## Purpose

`review-gate`를 통과한(`passed=True`) 계약 조항 markdown을 HWPX로 변환한다.
**한글 문서는 HWPX, DOCX 금지** 원칙(gentz 사고 이력)을 따른다.

## 선행 게이트

- `review-gate`가 `passed=False`이면 이 스킬은 실행되지 않는다 —
  `contract_writer_operation.run_contract_writer_operation`이 게이트 결과를
  먼저 확인하고, 실패 시 HWPX 변환 자체를 건너뛴다(all-or-nothing — 계약
  문서는 부분 완성 상태로 패키징하지 않는다. bid-response의 섹션별 부분실패
  원칙과 다른 지점).
- intake에 `missing_questions`가 남아 있는 경우도 마찬가지로 HWPX 변환을
  보류한다.

## Pipeline (단계)

1. **단일 HWPX 생성** — 조립된 조항 markdown 전체를 document-helper
   `/v1/document-helper/hwpx/generate`로 변환한다(bid-response 본문 생성과
   동일 라우트·동일 클라이언트 `DocumentHelperClient` 재사용, 새 클라이언트를
   만들지 않는다).
2. **실패 처리** — document-helper 호출이 실패(`DocumentHelperError`)하면
   HWPX 산출물 없이 markdown 초안만 반환하고 run report에 실패를 기록한다
   (markdown 자체는 이미 완성돼 있으므로 완전 실패로 취급하지 않는다).

## Rules

- HWPX만 생성한다. DOCX로 대체하지 않는다.
- 인감/서명 이미지 삽입은 사람이 실제 이미지를 제공한 이후에만 트리거한다
  — 이 스킬이 임의 이미지를 넣지 않는다.

## 도구 경계

- HWPX 변환은 document-helper AWP 노드에 위임한다. 이 스킬은 변환할
  markdown만 정의한다.
- `.apm` 레지스트리 등록·배포는 이 팩의 스캐폴딩 범위 밖(`apm.yml
  scaffold_status` 참조).

## Output Contract

- 생성 파일 1개(계약 본문 HWPX, 조항 순서 그대로) + document-helper 응답
  artifact URI. 실패 시 `null` + 실패 사유.
