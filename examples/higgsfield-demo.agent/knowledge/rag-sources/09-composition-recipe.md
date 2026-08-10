# Composition recipe: copy-safe thirds

```json
{
  "chunk_id": "hf-composition-copy-safe-001",
  "title": "Copy-safe thirds — subject, gaze, and negative space",
  "kind": "composition_recipe",
  "summary": "Place the subject on one vertical third and reserve the opposite third as uncluttered negative space for later overlay copy.",
  "prompt_snippet": "subject on left vertical third, eyeline toward open right-side negative space, foreground depth cue at lower edge, background simplified behind copy-safe area, keep face and hands inside central safe zone",
  "negative": "no centered subject when copy space is required, no bright detail behind text area, no edge-cropped face or hands, no generated text",
  "tags": {
    "composition": ["rule-of-thirds", "copy-safe", "negative-space"],
    "subject_position": ["left-third"],
    "overlay_space": ["right-third"],
    "depth": ["foreground-midground-background"]
  },
  "use_when": "Use for social and product shots that receive copy in post; mirror the recipe when interface placement requires left-side copy.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "plausible spatial layers, uncluttered copy area, natural eyeline, stable subject framing",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://composition/copy-safe-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
