# Shot grammar: size, angle, and purpose

```json
{
  "chunk_id": "hf-shot-grammar-001",
  "title": "Shot grammar — size and angle selection",
  "kind": "shot_grammar",
  "summary": "Use a small, explicit vocabulary for shot size and camera angle so each panel has one readable dramatic purpose.",
  "prompt_snippet": "shot_size: medium-close-up; camera_angle: eye-level; composition: single subject with clear eyeline and stable horizon",
  "negative": "no random angle change, no dutch angle unless specified, no cropped joints, no ambiguous subject scale",
  "tags": {
    "shot_size": ["establishing", "wide", "medium", "medium-close-up", "close-up", "extreme-close-up"],
    "camera_angle": ["eye-level", "low-angle", "high-angle", "overhead", "over-shoulder", "pov"],
    "beat": ["ESTABLISH", "INCITE", "REVEAL", "CLIMAX", "RESOLVE"]
  },
  "use_when": "Choose wide or establishing for spatial orientation, medium for action, close-up for emotion or product detail, and one motivated angle per beat.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "natural perspective, stable anatomy, real-time pace, subtle sensor grain",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://shot/grammar-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
