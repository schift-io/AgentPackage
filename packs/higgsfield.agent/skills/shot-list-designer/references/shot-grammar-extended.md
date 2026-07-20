# Shot Grammar Extended (enum, free-text 금지)

ad-creative `shot-grammar.md`를 **계승**하되, 광고 5부 구조가 아니라 **일반 연출 이중축**을 쓴다.
enum 필드는 아래 값만. free-text로 두면 필터·재생성·QC가 안 된다(`composition`만 명시 슬롯 자유서술).

## 이중축 beat (ad-creative와의 차이)

상위는 항상 내러티브 `scene_beat`. 광고 비트는 `channel=ad`일 때만 `ad_beat` 하위로 보존.

### scene_beat (상위, 항상)
| 값 | 용도 |
|----|------|
| `ESTABLISH` | 공간·인물·상황 설정 |
| `INCITE` | 사건·호기심 촉발(문제 제기) |
| `REVEAL` | 핵심·제품·반전 공개 |
| `ESCALATE` | 긴장·속도·밀도 상승 |
| `CLIMAX` | 감정/동작의 정점 |
| `RESOLVE` | 해소·정리·여운 |
| `TRANSITION` | 장면 전환·시간/공간 이동 브리지 |

### ad_beat (하위 보존, channel=ad 전용)
`HOOK → AGITATE → REVEAL → PROOF → OFFER → CTA` (ad-creative 5부와 동일 의미. narrative일 땐 `null`.)

## camera_angle (카메라 위치/높이)
| 값 | 용도 |
|----|------|
| `eye-level` | 중립·공감 기본선 |
| `high-angle` | 위에서 내려다봄(취약·객관화) |
| `low-angle` | 아래에서 올려다봄(권위·규모) |
| `bird-eye` | 정수리 탑다운(구성·패턴) |
| `worm-eye` | 지면 극저각(웅장·압도) |
| `dutch` | 기울임(불안·긴장) |
| `pov` | 인물 시점(몰입) |
| `over-the-shoulder` | 어깨너머(대화·관계) |

## shot_size (프레이밍 크기)
| 값 | 용도 |
|----|------|
| `extreme-wide` | 대지·스케일(설정) |
| `wide` | 전신+공간(설정샷) |
| `medium-wide` | 무릎/허벅지부터(행동+맥락) |
| `medium` | 허리부터(대화 기본) |
| `medium-close` | 가슴부터(감정+맥락) |
| `close-up` | 얼굴(감정·표정, hook/incite에 강함) |
| `extreme-close-up` | 눈·손·디테일(reveal/긴장) |
| `insert` | 사물 클로즈(정보·전환) |

## composition (자유서술 허용, 단 명시 슬롯)
- 피사체 위치(좌/중/우 1/3), 헤드룸, 리드룸(시선·이동 여백), 카피 세이프 영역, 전경/배경 관계.
- 채널별 세이프 영역은 그리드 패널 안 각 컷 비율을 유지해 배치.

## lighting (motivated single source, enum/프리셋)
| 값 | 용도 |
|----|------|
| `window-side` | 창측광(자연·부드러운 그림자) |
| `natural-overcast` | 흐린 자연광(무그림자·다큐) |
| `product-spot` | 제품 집중 소프트 스포트 |
| `golden-hour` | 저녁 역광·따뜻한 림 |
| `neon-practical` | 네온/간판 실용광(야간·도시) |
| `tungsten-practical` | 전구색 실용광(실내·따뜻) |
| `single-hard-source` | 단일 하드 소스(그림자 강함) |
| `low-key-single` | 로우키 단일광(긴장·미스터리) |

> 광원 1개만. "studio 3-point" 남발 금지(AI티). 프리셋별 snippet/negative는 `lighting-camera-taxonomy.md`.

## mood (1~2개/샷)
| 값 | 용도 |
|----|------|
| `calm` / `intimate` | 차분·가까움(establish/resolve) |
| `tension` / `ominous` | 긴장·불길(incite/escalate) |
| `wonder` / `epic` | 경이·웅장(reveal/climax) |
| `warmth` / `playful` | 따뜻·유쾌(친밀·가벼움) |
| `urgency` | 촉박(escalate/climax) |
| `melancholy` | 쓸쓸·회한(resolve) |

## lens_focus (짧은 사양 문자열)
| 값 | 용도 |
|----|------|
| `24mm deep DoF` | 공간 넓게·전체 선명(establish) |
| `35mm f/2.0 shallow DoF` | 시네마틱 기본·자연스러운 분리 |
| `50mm f/1.8` | 인물 기준·배경 흐림 |
| `85mm portrait compressed` | 압축·초상·제품 히어로 |
| `macro 100mm` | 극접 디테일(insert/reveal) |
| `rack-focus` | 초점 이동(주의 전환) |
| `tilt-shift` | 미니어처·선택 초점(스타일) |

## aspect ratio (channel 매핑)
- `9:16`(릴스/쇼츠), `4:5`(피드), `1:1`(정사각), `16:9`(유튜브/디스플레이).
- grid 초안은 패널 프레임 안에 각 컷 비율을 유지해 배치한다.
