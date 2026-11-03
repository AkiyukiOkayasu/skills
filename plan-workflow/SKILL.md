---
name: plan-workflow
description: Use when planning work in plan/*.md, reviewing a plan by risk, tracking completion, or carrying finished plan items into commits.
---

# Plan Workflow

Treat Markdown files under `plan/` as the persistent source of truth. Use the internal plan facility only as temporary working context. Do not create scripts, hooks, or rigid metadata solely for plan management.

## Plan files

- Create or update `plan/<topic>.md` when a task needs persistent planning. Prefer one topic per file and preserve an existing project convention.
- Put an overview checklist near the beginning. Each item should correspond to a readable body section.

```md
## 目次

- [ ] 起動処理を見直す
- [x] 回帰テストを追加する

## 起動処理を見直す

...

## 回帰テストを追加する

...
```

- `[ ]` is incomplete and `[x]` is complete. Judge completion only from the overview checklist, even when body sections contain nested checkboxes.
- Do not impose IDs, special comments, or a mandatory heading style when the existing plan is clear. If item-to-section correspondence is ambiguous, preserve the item and report the ambiguity.

## Updating plans

- Read relevant `plan/*.md` files before starting work.
- Add new items before implementing them, and mark an item `[x]` only when its work and completion conditions are actually finished.
- Keep incomplete items after a partial implementation. Update the plan in the same logical change when scope or completion conditions change.

## Pre-implementation review

Use risk-proportional review. Do not route ordinary multi-file work through the highest-friction loop.

### 軽微

Use self-review only when the plan is isolated, reversible, and low-uncertainty, such as a small doc update, narrow test addition, or one obvious code change.

- Write only the needed checklist items.
- Confirm a clear completion condition and no obvious ordering issue.
- State briefly that independent review is unnecessary.

### 通常

Use one independent review for medium-sized features, multiple related files, non-public refactors, or plans with dependency ordering to validate.

1. Write the draft plan with scope, evidence-backed assumptions, ordered work items, validation, and completion conditions.
2. Ask one reviewer to challenge premises, direction, dependency order, missing prerequisites, compatibility risks, and validation gaps. When using the Paseo `HighLevelReviewer` profile or DeepSeek, aim it at premises, direction, and ordering; do not make it the sole blocker-clearing authority.
3. Classify findings as blocking, material, or optional. Resolve every blocking finding, and resolve material findings or record an evidence-based rationale for declining them.
4. Check specificity, executable steps, missing files or tests, measurable completion conditions, and fit with local repo conventions.
5. Begin implementation after blocking issues are closed and remaining tradeoffs are explicit.

### 高リスク

Use the stricter loop for migrations, public API or compatibility changes, data/state transitions, security-sensitive work, release gates, multi-component rollouts, irreversible decisions, or significant unresolved architecture risk.

1. Complete the normal review flow.
2. Send the revised plan, prior findings, and dispositions to a different reviewer. Require it to verify that resolutions are evidence-backed and have not introduced contradictions.
3. Repeat review and revision until no blocking issue remains.
4. Re-run the high-risk loop when assumptions, interfaces, ordering, validation, or completion conditions materially change during implementation.
5. If a product, compatibility, or architectural choice needs user preference, stop and ask before implementing.

Keep review prompts evidence-based and challenge-oriented; do not ask merely for approval. If no independent reviewer can be started, use self-review for 軽微, disclose the limitation for 通常, and do not implement 高リスク without explicit user authorization.

## Reviewer selection

Do not hard-code a model name. Inspect the models and reasoning levels currently available to the launcher, honor an explicit user pin, and otherwise choose by capability, cost, and latency.

- 軽微: do not start a reviewer.
- 通常: one strong, balanced model at medium reasoning.
- 高リスク: start at medium reasoning and do not automatically escalate to the flagship or high reasoning. The final reviewer must be at least as capable as the plan author. Prefer a different agent, and a different model tier or family when available.
- Reserve fast or economy-oriented models for lightweight checklist passes and non-blocking feedback.
- If Medium cannot resolve a finding, disclose the limitation and ask the user instead of silently increasing cost or latency.

## Committing completed items

Before creating a commit:

1. Inspect the overview checklist in every relevant plan file.
2. For each completed `[x]` item, collect its body section.
3. Include the item title and plan content in the commit body under a heading such as `完了したplan項目`.
4. Remove the completed item from the checklist and its section from the plan file.
5. Delete a plan file when every item is complete; leave files with incomplete items containing only the remaining items.
6. Review the final diff and commit message to confirm completed content was preserved and incomplete work was not removed.

Keep the repository and Git skill conventions for the commit subject and overall format. Plan content belongs in the commit body.
