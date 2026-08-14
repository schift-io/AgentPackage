# Decision Deck Outline and Speaker Notes

Create `artifacts/decision-deck-outline.md` for a decision-maker. The output is an outline and speaker notes, not a rendered or published presentation.

Use this structure:

```markdown
# Decision Deck Outline

- decision requested:
- audience:
- shared-brief revision:

## Slide 1 — Decision context
- on-slide message:
- evidence / source fields:
- speaker notes:

## Slide N — Recommendation and next step
- on-slide message:
- evidence / source fields:
- speaker notes:

## Open questions and review flags
```

Rules:

- Start with the decision, then context, options/evidence, recommendation, risks, and requested next step. Omit sections that the brief cannot support.
- Keep on-slide copy concise; put explanation, caveats, and transitions in speaker notes.
- Mark unsupported metrics, outcomes, or competitor claims `needs_confirmation`.
- A later deck runtime adapter may render an approved outline; no adapter is embedded here.
