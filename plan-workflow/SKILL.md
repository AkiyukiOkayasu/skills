---
name: plan-workflow
description: Maintain repository plans as Markdown files under plan/ with checkbox-based item lists, track completion, and carry completed plan content into Git commit messages while removing completed items or fully completed plan files. Use when planning work, updating plan/*.md, checking task completion, or committing changes associated with a plan.
---

# Plan Workflow

Treat Markdown files under `plan/` as the persistent source of truth for task plans. Use the internal plan facility only as temporary working context; do not let it replace the repository plan.

Keep this workflow lightweight. Do not create scripts, hooks, or rigid metadata solely for plan management.

## Plan files

Create or update a suitable `plan/<topic>.md` file when a task needs persistent planning. Prefer one topic per file, but preserve an existing project convention when one exists.

Put an overview or table-of-contents-like checklist near the beginning of the file. Each checklist item should correspond to a readable section in the body.

Use ordinary Markdown checkboxes:

```md
## 目次

- [ ] 起動処理を見直す
- [x] 回帰テストを追加する

## 起動処理を見直す

...

## 回帰テストを追加する

...
```

`[ ]` means incomplete and `[x]` means complete. If detail sections contain nested checkboxes, use only the overview checklist to determine whether a plan item is complete.

Do not impose IDs, special comments, or a mandatory heading style when the existing plan is clear. If item-to-section correspondence is ambiguous, preserve the item and report the ambiguity instead of deleting content.

## Updating plans

Read relevant `plan/*.md` files before starting work. Add new items before implementing them, and mark an item `[x]` only when its work and completion conditions are actually finished.

Keep incomplete items in the plan after a partial implementation. Update the plan as part of the same logical change when the scope or completion conditions change.

## Committing completed items

Before creating a commit:

1. Inspect the overview checklist in every relevant plan file.
2. For each completed `[x]` item, collect the corresponding body section before editing it.
3. Include the completed item title and its plan content in the commit message body under a heading such as `完了したplan項目`.
4. Remove the completed item from the checklist and remove its corresponding body section from the plan file.
5. If every plan item in a file is complete, delete the entire plan file rather than leaving an empty file.
6. Leave files with incomplete items in place, containing only the remaining items and their sections.
7. Review the final diff and commit message to confirm that completed content was preserved in the message and that incomplete work was not removed.

Keep the existing repository and Git skill conventions for the commit subject and overall message format. Plan content belongs in the commit body and must not replace the required subject prefix.
