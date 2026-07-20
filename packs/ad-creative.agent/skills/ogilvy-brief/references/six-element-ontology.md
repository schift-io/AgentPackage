# 6-Element Ad Ontology (커버리지 게이트)

모든 광고는 아래 6요소를 **전부** 커버해야 한다. 스토리보드 생성 **전에** 각 요소가 어느
앵글로 커버되는지 `coverage_check`에 적고, 빈 요소가 있으면 진행하지 않는다.

| 요소 | 정의 | 브리프 필드 연결 |
|------|------|------------------|
| **Hook** | 첫 1~2초 스크롤을 멈추게 하는 것 | `core_thought` + 스토리보드 첫 컷 |
| **Pain** | 타깃이 겪는 문제/불편 | `target_raw`, `must_feel` |
| **Value / Proof** | 제품이 주는 가치 + 그 증거 | `must_know`, `core_thought` |
| **Offer** | 구체적 제안(가격/혜택/번들) | `mandatories`, `the_do` |
| **Urgency** | 지금 행동해야 할 이유 | `how`, `success_metric` |
| **CTA** | 명확한 다음 행동 | `the_do` |

## 앵글 뱅크 (요소를 채우는 심리 앵글, 택 3~5)

`pain_point · outcome · social_proof · curiosity · comparison · urgency ·
identity · contrarian · story · authority`

- 세그먼트마다 잘 먹히는 앵글이 다르다(감정 드라이버 기반). segment-fanout에서 세그먼트별로
  앵글을 고른다.
- 한 앵글이 여러 요소를 커버할 수 있다. 커버리지 표는 "요소 × 어느 앵글" 매핑으로 채운다.

## 검증 규칙

- 6요소 중 하나라도 빈 칸 → **생성 차단**. 브리프를 먼저 보강한다.
- 커버리지는 "있다/없다"가 아니라 "어느 앵글이 이 요소를 책임지는가"로 적는다.
- 이 게이트는 `ad-qc` 17점 스코어카드의 사전 버전이다(생성 전 / 생성 후 두 번 건다).
