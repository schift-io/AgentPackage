# 5 Orthogonal Segmentation Axes (팬아웃 엔진)

브리프 `segment_axis`로 하나를 고른다. 각 축은 그대로 세그먼트 테이블이 된다.

## 1. lifecycle (생애주기)
Prospect → Lead → New(<30d) → Active → At-Risk → Churned
- 기준: 마지막 구매/활동 시점. 목표: 각 단계의 다음 행동 촉발.

## 2. engagement (참여도)
Power / Regular / Casual / Dormant
- 기준: 사용 빈도·깊이. 목표: 상위는 확장, 하위는 재활성.

## 3. value_fit (가치·적합도)
Ideal Fit(ICP·고LTV) / Good Fit / Poor Fit
- 기준: ICP 매칭 + 예상 LTV. 목표: 획득 우선순위·객단가 전략.

## 4. role (역할·페르소나)  ← B2B 기본
Decision Maker(ROI 메시지) / Influencer(역량 메시지) / End User(사용성 메시지)
- 기준: 구매 결정에서의 역할. 목표: 역할별 설득 포인트.

## 5. industry (산업·버티컬)
섹터별 행(제조/유통/의료/공공…)
- 기준: 업종. 목표: 업종 맥락·규제·용례 특화.

## 연령대 팬아웃(요청 흔함)

연령은 별도 축이 아니라 위 축의 **criteria 값**으로 쓴다. 예: value_fit 축에서 "20대 Ideal Fit"
vs "40대 Ideal Fit". 나이 자체보다 그 나이대의 **감정 드라이버·소통 선호**가 세그먼트를 가른다
(segment-fanout SKILL의 persona 참조).

## 선택 가이드

- 셀프서브 SMB → lifecycle 또는 value_fit.
- B2B 계약 → role.
- 캠페인이 "특정 상황"이면 그 상황을 겪는 집단을 value_fit로 좁힌다.
