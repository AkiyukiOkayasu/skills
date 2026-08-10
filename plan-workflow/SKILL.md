---
name: plan-workflow
description: Maintain repository plans as Markdown files under plan/ with checkbox-based item lists, apply risk-proportional plan review before implementation, track completion, and carry completed plan content into Git commit messages while removing completed items or fully completed plan files. Use when planning work, updating plan/*.md, checking task completion, reviewing an implementation plan, or committing changes associated with a plan.
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

## Pre-implementation plan review

Use risk-proportional review. Do not route ordinary multi-file work through the highest-friction loop unless the change is genuinely high-risk.

### 軽微

Use self-review only when the plan is isolated, reversible, and has low uncertainty, such as a small doc update, narrow test addition, or a single obvious code change.

- Write or update only the needed checklist items.
- Confirm the plan has a clear completion condition and no obvious ordering issue.
- State briefly that independent review is unnecessary because the change is lightweight.

### 通常

Use one independent review for normal substantive work, such as a medium-sized feature, multiple related files, non-public refactors, or a plan with some dependency ordering to validate.

1. Write the draft plan to the relevant `plan/*.md` file, including scope, evidence-backed assumptions, ordered work items, validation, and completion conditions.
2. Ask one reviewer to challenge assumptions, direction, dependency order, missing prerequisites, compatibility risks, and validation gaps. When using `codex-reviewer` or DeepSeek for this review, aim it at premises, direction, and ordering; do not treat it as the sole blocker-clearing authority.
3. opencode classifies findings as blocking, material, or optional. Resolve every blocking finding; resolve material findings or record a specific evidence-based rationale for declining them.
4. opencode performs the concrete plan-quality pass: specificity, executable steps, missing files or tests, measurable completion conditions, and fit with local repo conventions.
5. Begin implementation after the blocking issues are closed and the remaining tradeoffs are explicit.

### 高リスク

Use the stricter loop for migrations, public API or compatibility changes, data/state transitions, security-sensitive work, release gates, multi-component rollouts, irreversible decisions, or plans with significant unresolved architecture risk.

1. Complete the normal review flow first.
2. Send the revised plan, prior findings, and dispositions to a different reviewer where one is available. Require it to verify that resolutions are evidence-backed and have not introduced contradictions.
3. Repeat review and revision until no blocking issue remains.
4. Re-run the high-risk loop whenever assumptions, interfaces, ordering, validation, or completion conditions materially change during phased implementation.
5. If review reveals an unknown product, compatibility, or architectural choice that needs user preference, stop before implementation and ask the user.

Keep review prompts evidence-based and challenge-oriented; do not ask the reviewer merely to approve the plan. If no independent reviewer can be started, proceed with self-review for 軽微 plans, disclose the limitation for 通常 plans, and do not implement 高リスク plans without explicit user authorization.

## Reviewer model selection

Choose the reviewer model and reasoning effort when starting each subagent. Do not hard-code a model name: inspect the models and reasoning levels currently available to the launcher, honor an explicit user pin, and otherwise choose by the provider's current capability, cost, and latency labels.

Use the following policy:

1. For 軽微 plans, do not start a reviewer by default.
2. For 通常 plans, prefer one currently available strong, balanced model at medium reasoning effort.
3. For 高リスク plans, start with a strong, balanced model at medium reasoning effort. Do not automatically escalate to the flagship model or high/extra-high reasoning; the final reviewer must be at least as capable as the plan author.
4. Reserve fast or economy-oriented models for lightweight checklist passes, premise/order review through `codex-reviewer`, or additional non-blocking feedback. Do not use them as the only blocker-clearing reviewer for 高リスク plans.
5. Prefer a different reviewer agent for the final pass. For 高リスク plans, also prefer a different model tier or family when the current launcher offers one; otherwise use a fresh agent with an independent prompt and context.
6. When representative review evaluations or prior outcome data exist, choose the lowest-cost, lowest-latency option that meets the required review quality. Without evidence, use the balanced Medium default rather than assuming the flagship model or higher reasoning effort is worthwhile.

State the chosen reviewer profile and why it fits the plan's risk. If Medium cannot resolve a finding, do not silently increase cost or latency; disclose the limitation and request user direction.

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
