---
name: form-filling
description: Fill the RFP's attached annex forms (입찰참가신청서, 보증금각서, 동의서, 확인서, 보안각서 등) with company context and explicit placeholders for values a human must supply.
---

# 별지 서식 채움

## Purpose

공고 첨부의 별지서식(입찰참가신청서·보증금각서·동의서·확인서·보안각서·국가계약법
서약서·사용인감계·제안서표지·제안업체일반사항·사업수행인력현황·개인정보동의서 등)
필드를 회사 컨텍스트(tenant core memory) + placeholder 규칙으로 채운다.

## Inputs

- `rfp-intake`가 확보한 별지서식 원본(양식 구조 그대로 새로 작성 — 외부 서식
  파일을 그대로 재사용하지 않고, 필드 구조만 옮긴다).
- `company-memory-grounding`이 조회한 `company`/`team`/`compliance` 섹션.

## Pipeline (단계)

1. **서식 필드 목록화** — 각 서식의 필드(상호/법인명칭·대표자·사업자등록번호·
   주소·인력 학력/경력·금액·직위·서명란)를 원본 구조 그대로 뽑는다.
2. **알려진 값 채움** — tenant core memory의 `company`/`team` 값이 있으면
   채우고, placeholder(실값 미확정) 상태면 그대로 `[상호/법인명칭]` 형태
   placeholder를 유지한다 — 임의로 지어내지 않는다.
3. **compliance 서류 상태 첨부** — `compliance` 섹션(소프트웨어사업자 신고확인서,
   G2B 등록, 중소기업확인서, 직접생산확인증명서 등)의 보유/확인필요 상태를 서식
   옆에 각주로 남긴다. **[확인필요 — 최우선]** 표시가 있는 항목은 별도 경고
   섹션으로 승격한다.
4. **날인/서명란 표시** — 인감·서명이 필요한 칸은 값으로 채우지 않고
   "[날인 필요]"/"[서명 필요]"로 명확히 남긴다(kordoc `seal` 같은 도장 이미지
   부유 배치는 hwpx-packaging 단계에서 사람이 트리거하는 별도 작업).

## Rules

- 회사 등록정보(사업자번호·인감 등)는 항상 placeholder 유지 — 실값 치환은
  별도 원장 대조로 사람이 한다.
- 인력 현황(학력·경력·연구제목 등)은 team 섹션이 placeholder 구조인 경우
  placeholder 그대로 유지하고, 지어내지 않는다.
- 서식 구조(칸 배치·필수 기재사항)는 RFP 원본 그대로 보존한다 — 임의로 칸을
  줄이거나 재배치하지 않는다.

## 도구 경계

- 값 치환·XML 매핑·HWPX 렌더링은 document-helper의 `hwpx_mutate`(기존 템플릿
  값 치환)를 쓴다. 서식이 원본 HWPX 템플릿이 아니라 markdown 골격뿐이면
  `hwpx-packaging` 스킬의 markdown→HWPX 경로로 넘긴다.

## Output Contract

- {id, title, bullets:[{claim, details[]}]} — 서식별 채운 필드 + placeholder
  잔여 개수 + [확인필요 — 최우선] 경고 목록.
