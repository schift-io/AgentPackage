# Agentic Refine Loop (P2 — self-critique quality gate)

Optional post-generation loop: generate -> self-critique (multimodal) ->
refine the request -> recompile -> regenerate. Bounded, not automatic —
offer it, don't force it.

## When to use

- The user explicitly asks to refine/improve a result ("다듬어줘", "텍스트가
  깨졌어", "더 그 톤으로"), OR
- The user asked for a text-in-image result (posters/banners with literal
  copy) — text fidelity is worth one automatic verification pass before
  showing the result as final.

Otherwise, show the first generation as-is. Do not loop by default — every
extra round is extra spend (image-gen `awp_operations[image-gen].image_model`
has no free retries).

## Loop shape (runtime: `agent_hub.image_gen_tools.agentic_refine_loop`)

1. Generate (compile -> validate -> `generate_image`, same as the base flow).
2. Critique the result (multimodal call, injected by the runtime as
   `critique_fn` — this skill does not call a vision model directly). The
   critique returns a `score` in [0,1] and, if below `quality_threshold`
   (default 0.75), a `refined_request` — the *next* round's request seed
   (never a raw string glued onto the old prompt; a fresh compile every
   round keeps Format/AR/palette rules enforced).
3. Stop when: score meets the threshold, OR `refined_request` is empty, OR
   `max_iterations` (default 2) is reached.
4. If stopped at `max_iterations` without meeting the threshold, tell the
   user plainly: "N rounds in, still below the quality bar on: <issues>. Want
   one more round, or take the current best?" — never silently loop forever
   and never silently ship a result you know failed the gate.

## What counts as "quality" (folded into the critique's single score)

- **Prompt adherence** — does the image show what the compiled prompt asked
  for (subject, background, palette if specified)?
- **Rendering quality** — no obvious artifacts (extra limbs, warped text,
  smeared logo-like shapes).
- **Text fidelity** (only when `text_in_image` was set) — does the on-image
  text match what was requested, character-for-character where legible?

## What this skill does NOT own

- The critique model/provider — that's a host service
  (`multimodal_critique_scorer` in apm.yml `runtime_boundary.host_services_only`).
- The compile/validate/generate mechanics — same `compile_image_prompt` /
  `generate_image` tools as the base flow, unchanged.
