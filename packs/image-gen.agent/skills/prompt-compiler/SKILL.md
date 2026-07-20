# Image Prompt Compiler (English descriptive, multi-model)

Ports the *structure* of image-forge's gongnyang compiler
(`derivatives/image-forge/docs/{PRD,PIPELINE}.md`) — category taxonomy, Format
A/B split, AR-trailing-token rule, HEX palettes, pre-generation validation —
into an **English descriptive, multi-model** compiler. This is not a
translation of gongnyang's Korean hwabo rules; only the structure is reused.

The compile/validate logic is a pure-function Python module
(`agent_hub.image_gen_compiler`) exposed to this agent as the `compile_image_prompt`
tool. **Always call the tool** — never hand-write the compiled prompt yourself.
Doing so would drop the AR-trailing-token guarantee and the negative-scan gate
that make generations reproducible and safe to batch.

## Call contract

`compile_image_prompt(request, category?, look_preset?, resolution_id?,
target_model?, background?, palette?, text_in_image?)` returns:

```json
{
  "compiled_prompt": "Scene: ... . Camera: ... . ar 1:1",
  "format": "A",
  "category": "C11",
  "look_preset": "clean-studio",
  "target_model": "gpt-image-2",
  "ar": "1:1",
  "api_size": "1024x1024",
  "palette": ["#1A73E8"],
  "validation": {"passed": true, "hard_fails": [], "warnings": []}
}
```

## What you decide (APM policy — see references/ for the tables)

- **category** (C1-C12, `references/categories-and-formats.md`): pick from the
  user's subject, or default to C11 (ad banner / marketing key visual) if
  unstated.
- **look_preset** (8 presets, same reference): pick from tone words in the
  request ("moody", "clean", "vintage") or default to `clean-studio`.
- **resolution_id**: map the user's stated aspect ratio / platform (e.g.
  "AdMob banner", "Instagram feed", "wide banner") to a preset id. Never
  invent a raw pixel size — always go through a preset id so `api_size` and
  `ar` stay correctly separated.
- **target_model** (`references/model-profiles.md`): default `gpt-image-2`
  unless the user names a specific style convention ("시네마틱", "카메라무브"
  -> `higgsfield`; "빠르게", "초안만" -> `z-image-turbo`).
- **palette**: only pass HEX colors the user gave or that are in referenced
  brand material — never invent brand colors.
- **text_in_image**: only set when the user wants literal on-image text
  (posters, banners with copy). Quote it exactly as given.

## What the tool decides (never override)

- Format A vs B (derived from category).
- Which axes appear and in what order (derived from target_model profile).
- Where the AR token goes (always last, always exactly once).
- Whether a negative phrase is a Tier-1 quality guard (allowed), a Tier-2
  contrastive pair (allowed), or a hard-fail scene negative (blocked).

## Validation gate (see references/validation-rules.md)

- `validation.passed=false` -> **do not call `generate_image`**. Show the
  `hard_fails` to the user and either fix the offending input (usually
  `text_in_image` or `background` containing a stray "no X"/"without X") and
  recompile, or ask the user to rephrase.
- `validation.warnings` do not block — surface them but proceed if the user
  confirms.
