# Shot Grammar (enum, free-text 금지)

샷 필드는 아래 enum만 쓴다. free-text로 두면 필터·재생성·QC가 안 된다.

## camera_angle
| 값 | 용도 |
|----|------|
| `wide` | 상황·공간 설정(설정샷) |
| `medium` | 인물+맥락(대화·행동) |
| `close-up` | 감정·표정(hook/pain에 강함) |
| `extreme-close-up` | 디테일·제품·눈(proof/urgency) |
| `bird-eye` | 위에서(구성·비교) |
| `worm-eye` | 아래에서(권위·규모) |

## composition (자유서술 허용, 단 명시적으로)
- 인물 위치(좌/중/우 1/3), 여백(카피 자리), 시선 방향, 전경/배경 관계.

## lighting
- 광원 1개를 motivated(동기 있는)로: 자연광/창측광/제품 스포트. "studio 3-point" 남발 금지(AI티).

## mood
- 이 컷이 유발할 감정 1~2개(브리프 `must_feel` / 세그먼트 감정 드라이버와 정렬).

## beat (패널 라벨)
`HOOK → AGITATE → REVEAL → PROOF → OFFER → CTA`
- 5부 타이밍에 매핑: Hook 0-3 / Pain(AGITATE) 3-10 / Value(REVEAL+PROOF) 10-25 / OFFER 25-45 / CTA 45-60.

## aspect ratio
- 채널 따라: `9:16`(릴스/쇼츠), `4:5`(피드), `1:1`(정사각), `16:9`(유튜브/디스플레이).
- grid 초안은 패널 프레임 안에 각 컷 비율을 유지해 배치한다.
