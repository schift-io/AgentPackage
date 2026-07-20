# Meeting Action Review

## Purpose
Prepare meeting action proposals for human approval. This skill belongs to the
Meeting Processing APM; extraction policy stays in the selected AWP.

## Inputs
- meeting note title
- meeting note body
- AWP proposal output
- available client destinations

## Rules
1. Do not create new action items that were not returned by the AWP.
2. Preserve the AWP evidence quote for every proposal.
3. Mark every external write as approval required.
4. Keep iOS Reminders and email alert draft destinations separate.
5. Ask the user only for missing fields that block execution, such as recipient
   or due date.

## Output
Return approval-ready proposals with:
- title
- evidence quote
- editable reminder fields
- editable email draft fields
- destination candidates
- blocked reason, when execution cannot safely continue
