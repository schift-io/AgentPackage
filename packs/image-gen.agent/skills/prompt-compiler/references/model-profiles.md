# Model profiles — which axes each target model emphasizes

Not in image-forge (it only ever targeted gpt-image-2 prompt grammar). This
table is the multi-model extension: same compile pipeline, different axis
selection/order/length per target model's documented prompting convention.

| target_model | Format A axes (order) | palette | camera language | style | max clauses |
|---|---|---|---|---|---|
| `gpt-image-2` (default) | Scene, Camera, Lighting, Color grading, Texture, Text-in-image | yes | descriptive (result-described framing) | structured | 8 |
| `higgsfield` | Camera, Lighting, Scene, Color grading, Texture | yes | technical (camera move / lens / motivated framing) | cinematic | 6 |
| `z-image-turbo` | Scene, Lighting, Color grading | no | minimal | terse, plain sentences | 3 |

## Why these choices

- **gpt-image-2** — this is `image_service.DEFAULT_MODEL` (agent_hub's
  existing generation path). Balanced structured prompt; strong text-in-image
  rendering, so that axis stays and HEX palettes are honored literally.
- **higgsfield** — Higgsfield's known convention is camera-move/lens-forward
  even for single-frame generations (it's a motion-control-first model
  family); prompts that read like a director's shot direction outperform
  plain scene description. Text-in-image is dropped because its text
  rendering is weaker than gpt-image-2's.
- **z-image-turbo** — fast natural-language descriptive models perform best
  with short, plain sentences rather than heavy technical camera jargon;
  padding the prompt with axes it doesn't need slows convergence without
  improving output. Palette is dropped for the same terseness reason.

## Picking a target model from user language

- No style words mentioned -> `gpt-image-2` (default, best general quality +
  text rendering).
- "시네마틱", "카메라무브", "영화 같은", "드라마틱한 조명" -> `higgsfield`.
- "빠르게", "초안만", "여러 장 빨리" -> `z-image-turbo`.

Generation execution today only wires `gpt-image-2` to `image_service`
(agent_hub's existing model param) — `higgsfield`/`z-image-turbo` profiles
produce correctly-shaped prompts now, but their adapters are not wired to a
live model yet (same "declared, not wired" state as `ad-creative`'s
`AD_CREATIVE_IMAGE_ADAPTER_URL`). Compiling for those targets is safe and
useful (prompt review, future wiring); generating currently still routes
through `image_service`'s configured model.
