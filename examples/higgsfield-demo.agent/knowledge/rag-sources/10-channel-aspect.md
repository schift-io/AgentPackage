# Channel aspect: frame and grid mapping

```json
{
  "chunk_id": "hf-channel-aspect-001",
  "title": "Channel aspect mapping — preserve the final crop in every panel",
  "kind": "channel_aspect",
  "summary": "Choose the delivery aspect ratio before storyboarding and render every grid cell with that internal frame instead of cropping after generation.",
  "prompt_snippet": "delivery aspect: 9:16; each storyboard panel preserves a vertical 9:16 inner frame; keep critical face, hands, product, and motion path inside the central 80 percent safe zone",
  "negative": "no mixed aspect ratios in one grid, no critical detail outside safe zone, no landscape composition squeezed into vertical frame, no post-crop dependency",
  "tags": {
    "aspect_ratio": ["9:16", "4:5", "1:1", "16:9"],
    "channel": ["shorts-reels-tiktok", "feed", "square-social", "youtube-web"],
    "grid_rule": ["fixed-inner-frame", "shared-safe-zone"]
  },
  "use_when": "Map 9:16 to Shorts/Reels/TikTok, 4:5 to portrait feed, 1:1 to square social, and 16:9 to YouTube or web before composing shots.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "native-aspect composition, consistent panel geometry, protected faces and products, no forced crop",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://channel/aspect-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
