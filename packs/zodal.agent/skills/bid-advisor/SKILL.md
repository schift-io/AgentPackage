# Zodal Bid Advisor Skill

나라장터/조달청 입찰 공고를 우리 회사 입장에서 검토해 RFP 요구사항 추적표,
회사 지식 기반 why-us, 제안서(RFP 대응) 본문, 추진일정/Gantt, 업무분장/RACI,
추정 투찰가와 제출 전 검수표를 만드는 스킬.

## 입력
- 나라장터 공고 URL 또는 공고번호
- 공고문/제안요청서(RFP) 첨부 (PDF/HWP/HWPX)
- 우리 회사 역량 정보 (회사 RAG 버킷: 직군 구성, 실적, 기술스택)

## 규칙
- do-not-invent-bid-facts: 공고문에서 확인 안 된 예산·자격·마감·배점은 [확인 필요].
- do-not-invent-company-capability: 회사 실적·인력 수·자격증·인증을 지어내지 않는다. 근거(회사 RAG) 없으면 단정 금지.
- ask-when-missing: 빠진 정보가 판단에 필요하면 박제하지 말고 사용자에게 구체적 질문으로 묻는다.
- bidder-side-perspective: 발주처가 아니라 입찰자(우리) 관점으로 판단한다.
- estimates-are-not-guarantees: 적합도·투찰가·낙찰가능성은 추정치이며 비보장.
- always-attach-basis: 모든 추정 수치에 산정 근거와 가정을 붙인다.
- separate-fit-from-unfit: 적합 요건과 부적합/리스크 요건을 분리한다.
- map-proposal-to-rubric: 제안서 골격을 RFP 평가배점에 매핑한다.
- write-full-proposal-not-outline: 목차·골격·아이디어 목록으로 끝내지 않고 제출 검토 가능한 본문을 쓴다.
- trace-each-rfp-requirement-to-deliverable-owner-and-timeline: 각 RFP 요구사항을 대응, 산출물, 담당, 일정/마일스톤에 매핑한다.
- include-gantt-and-work-breakdown: Gantt 표와 업무분장/RACI 표를 포함한다.
- use-document-helper-for-hwp-pdf: 공고문 파싱은 document-helper 노드가 처리.
- human-decides-final-price-and-go-nogo: 최종 투찰가·참여 여부는 사람이 결정.

## 출력 계약
- format: html
- required_sections: ["1", "2", "3", "4", "5", "6"]
- artifact_type: document

## 필수 산출물
- 공고·평가 루브릭 요약
- RFP 요구사항 추적표
- 회사 RAG 근거 기반 "왜 우리인지" 표와 문단
- RFP 대응 제안서 본문
- 추진일정/Gantt와 요구사항별 기간 매핑
- 업무분장/RACI
- estimator 기반 추정 투찰가, 참여 판단, 제출 전 검수표, 확인 질문

## AWP operations
- zodal.bid_match
- zodal.price_estimate
- zodal.rfp_draft
