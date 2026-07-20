# Anti-AI-slop Prompt Rules

광고가 "AI티"(왁스·플라스틱 질감, 밀랍 얼굴) 나면 신뢰도가 죽는다. 매 컷 프롬프트에 아래를
포함한다.

## 금지어
- `8K`, `cinematic`, `studio`, `hyperreal`, `masterpiece`, `ultra-detailed` — 이 단어들이
  왁스·플라스틱 룩을 유발한다. **빼라.**

## 넣을 것 (realism block)
- "phone-camera look, natural light, subtle grain, real-time pace"
- 동기 있는 광원 1개(창측광/자연광). 완벽한 3점 조명 금지.
- 인간적 결함 1개(약간의 흐트러짐, 자연스러운 표정).

## Negative prompt (항상 첨부)
```
no morphing, no warping, no melting, no jelly, no extra fingers, no distorted hands,
no slow-mo blur, no plastic skin, no waxy face, no watermark, no logo, no UI text
```

## 텍스트 처리
- 이미지 안에 카피/숫자/로고를 **그리지 않는다**. 오버레이로 나중에 얹는다.
- 부득이 이미지 내 텍스트가 필요하면 정확한 문구를 큰따옴표로 ≤8 단어.

## 제품/인물 픽셀
- 제품이 선명히 보이는 컷은 실제 제품 사진에서 시작(모델이 제품을 상상해 그리지 않게).
- 인물은 히어로 레퍼런스 + face-ref로 고정(character-sheet L2/L3).

## 파일 네이밍(승인 컷 업스케일 시)
`[channel]_[ratio]_[segment]_[beat]_[character]_v[NN]`
예: `reels_9x16_20s_hook_jimin_v03`
