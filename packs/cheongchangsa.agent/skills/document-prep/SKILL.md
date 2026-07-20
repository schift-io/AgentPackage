# Cheongchangsa Document Prep

## Purpose

Discord로 들어온 청창사 사업비 집행 파일 묶음을 작업 유형별로 분류하고,
2026 청창사 사업비 집행 매뉴얼 근거에 맞춰 증빙 충족/누락/불일치를
검토한다.

## Required Retrieval

- `chungchangsa-2026-execution-manual` 버킷을 먼저 검색한다.
- 매뉴얼 근거가 검색되지 않으면 제출 가능이라고 쓰지 않는다.
- 규정 판단 문장은 가능한 경우 검색 결과의 페이지/문서명을 함께 남긴다.

## Command Contracts

- `/ai사용비집행` (`ai-usage`): AI 구독/사용료 집행 증빙을 검토한다.
  invoice, receipt, 우리카드 매출전표, 해외승인 XLS, 사용 화면/증빙 캡처,
  사업비 사용내역서 템플릿을 우선 매칭한다.
- `/인건비집행` (`payroll`): 인건비 집행 증빙을 검토한다. 송금 확인증,
  지급 근거 서류, 참여/근로 관련 서류, 세금/보험 증빙은 매뉴얼 근거로
  필요 여부를 판정한다.
- `/증빙검토` (`evidence-review`): 제출 패키지 생성 없이 누락/불일치만
  정리한다.
- `/제출패키지생성` (`submission-bundle`): 검토된 자료를 document-helper
  AWP 노드로 HWPX/PDF/합본 PDF 산출물로 만들 실행 계획을 반환한다.

## Rules

- Discord 메시지와 첨부 파일을 기준으로 접수 상태를 정리한다.
- PDF/HWP/HWPX/XLS/이미지에서 확인 가능한 사실과 누락 항목을 분리한다.
- 카드전표/XLS/영수증/invoice 금액·날짜·공급처가 충돌하면 자동 확정하지 않는다.
- 사람이 승인해야 할 제출 전 체크리스트를 반드시 포함한다.
- Discord 회신 문구는 짧고 실행 가능한 다음 단계 중심으로 작성한다.
