# Transition Library

전환 enum별 **언제 쓰는가** + **i2v에서의 모션 번역** + **드리프트 주의**.
전환은 "다음 샷으로 넘어가는 방식"이다. i2v는 클립 내부 모션만 만들고, 전환 자체는 stitch에서 처리한다.

| transition | use_when | i2v 모션 번역(클립 내부) | drift_caution |
|------------|----------|--------------------------|---------------|
| `cut` | 기본. 리듬·정보 전환 | 각 클립 자체 모션만. 연결은 하드컷 | 가장 안전. identity만 유지하면 됨 |
| `match-cut` | 형태/동작/색을 다음 샷과 맞춰 시각적 연결 | 클립 끝 프레임이 다음 클립 시작과 구도 일치하도록 | 직전·다음 `continuity_ref` 필수. 피사체 위치 어긋나면 깨짐 |
| `jump-cut` | 같은 구도에서 시간 압축·리듬 | 클립 내부 동작 유지, 반복 컷으로 이어 붙임 | 인물 포즈·의상 튐 주의. 앵커 동일 필수 |
| `dissolve` | 시간 경과·회상·부드러운 전환 | 클립 모션 느리게, 겹침 구간 필요 | 겹침 중 identity 이중 노출 위험. 길이 짧게 |
| `whip-pan` | 빠른 팬으로 장면/공간 이동, 에너지 | 클립 끝에 빠른 수평 블러로 끝냄 | 블러 방향이 다음 샷 시작과 같아야 함. 방향 어긋나면 튐 |
| `motion-blur` | 속도감 있는 전환, 동작 연결 | 클립 끝 모션 블러를 다음 클립 시작 블러와 연결 | 블러 방향·속도 불일치 시 끊김. 강도 `dynamic`과만 |
| `smash-cut` | 갑작스러운 대비(조용→시끄러움 등) | 각 클립 자체 모션. 하드컷+오디오/밝기 대비 | 시각 대비가 의도적이어야. 우연한 튐과 구분 |
| `fade` | 시작/끝·시간 간격·여운 | 클립 모션 느리게. 암전/백전으로 빠짐 | resolve 외 남발 금지(지루함) |
| `invisible-cut` | 어두운 프레임/물체 통과로 이음새 숨김 | 클립 끝이 전경 물체/암부로 덮이도록 | 덮는 물체·타이밍 일치 필요. 실패 시 어색한 점프 |

## 공통 원칙

- **i2v는 내부 모션만**: 전환 효과(dissolve/whip/match)는 클립 안에서 완성하지 말고 stitch에서 처리.
  i2v 프롬프트에는 "끝 프레임 상태"(예: end on motion blur, end covered by foreground)만 지시.
- **연속성 전환 = continuity_ref 필수**: `match-cut`/`whip-pan`/`motion-blur`/`invisible-cut`은
  직전 샷의 seed·구도·방향을 `continuity_ref`로 넘긴다.
- **안전 우선**: 확신 없으면 `cut`. 복잡 전환일수록 재생성·드리프트 비용이 큰다.
- **비디오 전용 anti-slop**: 전환 경계에서 `no camera teleport, no identity drift between panels`를
  prompt-composer의 비디오 negative에 항상 포함한다.
