# Validation rules (pre-generation hard gate)

Reimplements the semantics image-forge documents for `check_prompt.mjs`
(PIPELINE.md R3) — that script was not present in the checked-out image-forge
repo, so these rules are derived from the documented behavior, not copied
code. Implementation: `agent_hub.image_gen_compiler.validate_compiled`.

## Hard fails (block generation)

1. **AR token must trail the prompt exactly once, at the very end.** If the
   resolution preset has an `ar`, the compiled prompt must end with
   `ar <ratio>` — never mid-prompt, never duplicated.
2. **No literal pixel size inlined in prompt text.** A `WxH` pattern (e.g.
   `1024x1024`) anywhere in the prompt body is a hard fail — size is an API
   parameter (`api_size`), never prompt text.
3. **No scene negatives outside the Tier-1/Tier-2 whitelist.** Any `no X` /
   `without X` phrase is scanned; it passes only if:
   - **Tier-1**: a quality guard phrase (`no watermark`, `no logo`,
     `no ui text`, `no jpeg artifacts`, `no blurry`, `no extra fingers`,
     `no distorted hands`, `no morphing`, `no warping`, `no plastic skin`,
     `no waxy face`, ...) — these describe rendering artifacts, not scene
     content, and are always allowed.
   - **Tier-2**: part of a contrastive "X, not Y" pair (e.g. "warm light, not
     harsh") — these describe the *result* and only use "not Y" as a
     disambiguator.
   - Anything else (`no people`, `without clouds`, `not a city`) is a
     free-standing scene negative and hard-fails. Rephrase as a positive
     description instead ("empty street" instead of "no people").

## Soft warnings (surface, don't block)

- No HEX palette supplied for a category that typically wants one (C1
  product, C11 ad banner, C12 poster).
- Compiled prompt is very short (< 24 characters) — likely under-specifies
  the scene.

## Why hard-fail vs soft-warn

Hard fails are structural contract violations (AR placement, size mixing) or
policy violations (unwhitelisted negatives) that would either break the
API contract or produce prompts prone to abuse/ambiguity. Soft warnings are
quality nudges that don't change the pipeline's correctness — the user can
proceed after seeing them.
