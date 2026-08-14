# Human Review Gate

Create `artifacts/review-checklist.md` after any draft is generated or refreshed. This gate is mandatory and terminates package execution.

Use this structure:

```markdown
# Human Review Checklist

## Shared brief
- [ ] Confirmed facts still have valid sources
- [ ] `needs_confirmation` fields are resolved, removed, or visibly retained
- [ ] Downstream drafts affected by changes were refreshed

## Email draft
- [ ] Recipient, claims, tone, and commitments approved
- [ ] Explicit human approval before send

## Decision deck
- [ ] Decision request, evidence, risks, and speaker notes approved

## Proposal structure
- [ ] Template, evidence, assumptions, and submission requirements approved

## Landing-page brief
- [ ] Claims, CTA, legal review, and publication readiness approved
- [ ] Explicit human approval before publish

## Optional handoff after approval
- Email runtime adapter: draft handoff only
- Deck runtime adapter: render handoff only
- Business-plan runtime adapter: format handoff only
- Landing-page runtime adapter: implementation/publish handoff only
```

Rules:

- Never mark an approval complete unless a human explicitly supplies it.
- Do not hand off automatically. Report which adapter could receive an approved draft, but do not claim that an adapter is installed or invoked.
- Do not send, publish, submit, store credentials, or access the network.
