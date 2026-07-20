---
name: hwpx-packaging
description: Convert the drafted proposal body and filled annex forms into HWPX files and merge them into a submittable bid-response package.
---

# markdown → HWPX 패키징

## Purpose

`proposal-drafting`의 본문 markdown과 `form-filling`의 서식 값을 HWPX 파일로
변환하고, 제출용 패키지(본문 1 + 별지서식 N)로 묶는다. **한글 문서는 HWPX,
DOCX 금지** 원칙을 따른다.

## 현재 상태 (라우트 실재 — awp 등록/배포는 별도 GO)

- 노트북 지그는 `@clazic/kordoc`의 `markdownToHwpx(markdown, options)`(공문서
  preset)로 markdown → HWPX **신규 생성**을 수행했다.
- `services/document-helper/src/main.py`는 이제 세 라우트를 노출한다:
  `hwpx_mutate`(**기존 HWPX 템플릿의 값 치환**), `hwpx_generate`
  (`/v1/document-helper/hwpx/generate` — kordoc `markdownToHwpx` 기반
  **markdown→HWPX 신규 생성**, 다중 섹션 페이지나눔 병합 포함), `hwpx_package`
  (`/v1/document-helper/hwpx/package` — 본문+서식 HWPX들을 제출 순서 zip으로
  병합, 파트별 구조검증 인라인).
- 따라서 이 스킬의 두 갈래는 둘 다 라우트가 존재한다:
  1. **서식 채움(값 치환 경로)** — 별지서식이 원본 HWPX 템플릿 파일로
     확보되면 `hwpx_mutate`로 값만 채운다.
  2. **본문 신규 생성** — 제안서 본문 markdown은 `hwpx_generate`로 변환한다.
  실제 배선은 `schift-api/awp_packs/first_party/bid-response/package-hwpx.awp.yaml`
  (render_body/fill_forms/merge_package 노드가 위 세 라우트를 direct 호출) —
  `.apm` 레지스트리 등록·배포만 GO 대기(SCAFFOLD.md 참조).

## 선행 게이트

- 이 스킬은 `proposal-drafting` 산출물을 **바로** 받지 않는다 —
  `faithfulness-check` 게이트(`passed=True`)를 통과한 본문만 변환 대상이다.
  게이트 실패 시(`[검증 필요]` 잔여) 사람 확인 또는 재생성 전까지 HWPX 변환을
  보류한다.

## Pipeline (단계, 배선 완료 가정)

1. **본문 변환** — 제안서 본문 markdown을 `markdownToHwpx`(공문서 preset)로
   HWPX 변환.
2. **서식 값 채움** — 별지서식 원본 HWPX 템플릿에 `hwpx_mutate`로 값 치환.
3. **구조 검증** — kordoc `validate`(ZIP·mimetype·필수파일·XML 웰폼드·manifest
   참조)로 생성된 각 HWPX를 검증. 실패 시 해당 파일만 [확인 필요]로 격리하고
   나머지는 계속 진행.
4. **패키지 묶음** — 본문 + 서식 전부를 하나의 다운로드 패키지(zip 또는
   개별 파일 목록)로 묶는다.
5. **볼드→이탤릭 렌더 함정 점검** — kordoc 버전에 따라 markdown bold(`**...**`)가
   italic으로 오매핑되는 함정이 있었다(현재 버전은 재현 안 됨, PROOF.md 확인).
   패키징 후 굵게 표시가 의도대로 렌더됐는지 샘플 점검한다.

## Rules

- HWPX만 생성한다. DOCX로 대체하지 않는다.
- 생성된 모든 HWPX는 kordoc `validate` 통과를 필수 게이트로 삼는다 — 실패한
  파일은 제출물에서 제외하고 사람에게 알린다.
- 인감/서명 이미지 삽입(`kordoc seal`)은 사람이 실제 인감 이미지를 제공한
  이후에만 트리거한다 — 이 스킬이 임의 이미지를 넣지 않는다.

## 도구 경계

- HWPX 변환/렌더/검증은 전부 document-helper AWP 노드에 위임한다. 이 스킬은
  변환할 markdown/값 구조만 정의한다.
- `.apm` 레지스트리 등록·배포는 이 팩의 스캐폴딩 범위 밖 — 별도 GO가
  필요하다(SCAFFOLD.md).

## Output Contract

- 생성 파일 목록(본문 1 + 서식 N) + 각 파일의 kordoc validate 결과 +
  placeholder 잔여 집계(형식은 run-report 스킬이 최종 리포트로 합산).
