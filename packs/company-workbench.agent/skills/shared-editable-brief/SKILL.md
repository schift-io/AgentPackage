# Shared Editable Brief

Maintain `artifacts/shared-brief.md` as the single source of truth for all Company Workbench artifacts. It is editable by the user and by approved corrections; it is not a static intake snapshot.

Use this structure:

```markdown
# Shared Brief

## Purpose and decision
- objective:
- decision requested:
- audience:
- owner and approver:

## Grounded facts
| field | value | source | status |
| --- | --- | --- | --- |
| company/product fact |  | user-provided reference | confirmed |

## Assumptions and open questions
| field | current wording | status | question or owner |
| --- | --- | --- | --- |
|  |  | needs_confirmation |  |

## Constraints
- timing:
- tone:
- legal/compliance constraints:
- prohibited claims:

## Output map
| artifact | purpose | shared-brief fields used | refresh status |
| --- | --- | --- | --- |
| email-draft |  |  | pending |
```

Rules:

- Add a source for every confirmed fact. A user statement, supplied document, or named internal reference is sufficient; a guess is not.
- Keep unknowns as `needs_confirmation`; do not invent evidence, figures, or approvals.
- On a correction, update the brief first, then identify every output whose listed fields changed. Mark those outputs `needs_refresh` until regenerated.
- Keep the brief generic and company-neutral. Never record credentials or private secrets.
