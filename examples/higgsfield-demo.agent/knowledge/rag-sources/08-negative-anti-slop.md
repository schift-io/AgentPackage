# Negative anti-slop: image and video block

```json
{
  "chunk_id": "hf-negative-video-001",
  "title": "Always-on anti-slop block — continuity and realism",
  "kind": "negative_anti_slop",
  "summary": "Attach a concise, stable negative block to every panel and clip; add only shot-specific exclusions when evidence requires them.",
  "prompt_snippet": "preserve subject identity, stable anatomy, stable environment geometry, physically plausible motion, natural skin texture, readable silhouette, no generated typography",
  "negative": "no camera teleport, no identity drift, no face morphing, no melting, no warping, no extra fingers or limbs, no plastic skin, no floating objects, no flicker, no watermark, no logo mutation, no UI text, no subtitles baked into image",
  "tags": {
    "risk": ["identity-drift", "anatomy", "temporal-flicker", "typography", "watermark"],
    "application": ["always-on", "txt2img", "imgs2vid"],
    "realism": ["natural-skin", "physical-motion"]
  },
  "use_when": "Attach to every generation request after the positive prompt; never replace the positive description with a longer negative list.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "phone-camera credibility, natural exposure, subtle grain, real-time pace, physically plausible inertia",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://negative/video-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
