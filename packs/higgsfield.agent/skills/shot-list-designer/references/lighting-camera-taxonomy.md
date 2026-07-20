# Lighting & Camera-Rig Taxonomy

광원은 **동기 있는 단일 소스**, 카메라는 **리그/안정성 축**으로 분류한다(모션 동사는 `movement-composer`).
각 항목은 패널/클립 프롬프트에 그대로 붙일 `prompt_snippet` + `negative` + `use_when`을 가진다.

## lighting_preset

| id | prompt_snippet | negative | use_when |
|----|----------------|----------|----------|
| `window-side` | soft window side light from camera-left, gentle falloff, natural shadow | no flat even lighting, no studio 3-point, no over-lit | 낮 실내·다큐·친밀. establish/intimate. |
| `natural-overcast` | overcast soft daylight, shadowless, desaturated documentary | no harsh sun, no golden flare, no glossy skin | 흐린 날·사실적 톤·피부 결 보존. |
| `product-spot` | single soft spotlight on product, dark falloff background, clean edge | no multi-source clutter, no color spill, no hotspot burn | 제품 공개·히어로 insert/reveal. |
| `golden-hour` | low golden-hour backlight, warm rim, soft lens haze | no blown highlights, no orange oversaturation | 감성·여운·resolve/climax. |
| `neon-practical` | neon practical sign light, colored rim, night urban ambience | no full-rgb wash, no plastic glow, no logo text | 야간 도시·긴장·escalate. |
| `tungsten-practical` | warm tungsten practical lamp, cozy interior, gentle shadow | no mixed color temperature clash, no waxy skin | 실내·따뜻·대화. |
| `single-hard-source` | single hard directional source, crisp shadow, high contrast | no soft fill, no even beauty light | 드라마·그림자 강조·ominous. |
| `low-key-single` | low-key single source, deep shadow, minimal fill | no bright background, no flat exposure | 미스터리·긴장·reveal 전. |

공통 규칙: 광원 1개만 명시, 샷 간 광원 일관(같은 환경이면 같은 preset), 과포화/과대광 금지.

## camera_rig (안정성/지지 축 — motion 아님)

| id | prompt_snippet | negative | use_when |
|----|----------------|----------|----------|
| `locked-tripod` | locked-off tripod, perfectly stable frame, level horizon | no shake, no drift, no handheld jitter | 설정샷·제품 정적·대비 기준선. |
| `gimbal-smooth` | gimbal-smooth glide, stabilized float, clean horizon | no wobble, no micro-jitter | 부드러운 접근·tracking 기반. |
| `handheld-doc` | subtle handheld documentary micro-movement, alive frame | no shake-cam chaos, no motion blur smear | 다큐·긴장·현장감(강도는 subtle). |
| `shoulder-rig` | shoulder-mounted organic sway, human operator feel | no robotic glide, no locked stiffness | 인물 동행·친밀 추적. |
| `steadicam-walk` | steadicam walk-through, floating following, smooth corners | no bounce, no horizon tilt | 공간 통과·긴 take·reveal. |
| `crane-jib` | crane/jib vertical reach, slow rise or descend | no jerky motor, no overshoot | 스케일 공개·climax·전환. |
| `drone-aerial` | drone aerial float, high vantage, slow drift | no fast FPV dive unless fpv shot | 대지·establish·전환 브리지. |

분류 원칙: 리그는 "카메라가 어떻게 지지되는가"만 담고, 실제 이동 동사(`dolly-in/pan/orbit` 등)와
강도(`subtle/moderate/dynamic`)는 `movement-composer`에서 배치한다. 한 샷에 리그 1개.
