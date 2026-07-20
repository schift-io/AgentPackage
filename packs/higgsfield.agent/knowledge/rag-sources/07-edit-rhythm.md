# Edit rhythm: match cut continuity

```json
{
  "chunk_id": "hf-edit-match-cut-001",
  "title": "Match cut — carry shape or motion across clips",
  "kind": "edit_rhythm",
  "summary": "End one clip and begin the next on a shared shape, gaze, or motion direction so a hard cut feels intentional and continuous.",
  "prompt_snippet": "transition: match-cut; outgoing action ends frame-right with circular silhouette centered; incoming action begins on the same screen position and motion direction; cut on movement peak",
  "negative": "no direction reversal, no subject scale jump, no mismatched eyeline, no dissolve unless specified, no unmotivated speed ramp",
  "tags": {
    "transition": ["match-cut"],
    "rhythm": ["cut-on-action", "continuity"],
    "duration_sec": ["2", "3", "4"],
    "beat": ["TRANSITION", "REVEAL", "ESCALATE"]
  },
  "use_when": "Use between clips that share a dominant shape or movement; align screen position and direction before generating either clip.",
  "compatible_models": {
    "txt2img_grid": ["gemini-3.1-flash-lite-image", "flux-2-klein-9b"],
    "imgs2vid": ["seedance_2_0", "kling3_0", "minimax_hailuo", "veo3_1"]
  },
  "duration_hint_sec": 3,
  "realism_block": "continuous screen direction, plausible action timing, stable scale, no artificial transition overlay",
  "locale": "ko-KR",
  "version": "2026-07-10",
  "metadata": {
    "source_id": "hf://edit/match-cut-001",
    "agent_hub_bucket_role": "directing_reference",
    "canonicality": "reference",
    "product_area": "higgsfield"
  }
}
```
