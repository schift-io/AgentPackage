# Lighting preset: motivated window side light

```json
{
  "chunk_id": "hf-light-window-side-001",
  "title": "Motivated window side light — natural depth",
  "kind": "lighting_preset",
  "summary": "Use one visible or plausible window as the key source, with soft room bounce preserving natural facial depth across cuts.",
  "prompt_snippet": "single motivated daylight source from frame left window, soft side key, gentle room bounce, realistic shadow falloff, consistent direction across panels",
  "negative": "no generic three-point studio setup, no conflicting rim light, no glowing skin, no shadow direction change between panels",
  "tags": {
    "lighting": ["motivated-single-source", "window-side-light", "natural-light"],
    "mood": ["intimate", "credible", "calm"],
    "time_of_day": ["morning", "afternoon"]
  },
  "use_when": "Use for human-scale interiors and grounded product scenes where visual continuity matters more than glossy spectacle.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 4,
  "realism_block": "natural exposure rolloff, plausible bounce light, subtle grain, unretouched skin texture",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://lighting/window-side-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
