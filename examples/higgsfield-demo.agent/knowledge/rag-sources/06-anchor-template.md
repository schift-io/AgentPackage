# Anchor template: identity and environment lock

```json
{
  "chunk_id": "hf-anchor-identity-lock-001",
  "title": "MEGA-ANCHOR — repeat identity before variation",
  "kind": "anchor_template",
  "summary": "Repeat the same environment, character, attire, and invariant prop wording at the start of every panel and clip prompt.",
  "prompt_snippet": "[ENV: location, time, fixed layout] [CHARACTER: stable physical identity] [ATTIRE: unchanged clothing and accessories] [PROP: invariant product shape and color] — then append only this shot's action, camera, light, and movement",
  "negative": "no identity drift, no wardrobe change, no age change, no environment rearrangement, no prop redesign, no duplicate character",
  "tags": {
    "anchor_slots": ["environment", "character", "attire", "prop"],
    "continuity": ["identity-lock", "wardrobe-lock", "environment-lock"],
    "application": ["prepend-every-panel", "prepend-every-clip"]
  },
  "use_when": "Use whenever a subject, product, or location persists across two or more panels; copy invariant text verbatim before shot-specific wording.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "consistent face geometry, wardrobe texture, body proportions, product silhouette, and spatial layout",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://anchor/identity-lock-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
