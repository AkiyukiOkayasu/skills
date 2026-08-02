---
name: plan-workflow
description: Maintain repository plans as Markdown files under plan/ with checkbox-based item lists, independently review and refine non-trivial plans before implementation, track completion, and carry completed plan content into Git commit messages while removing completed items or fully completed plan files. Use when planning work, updating plan/*.md, checking task completion, reviewing an implementation plan, or committing changes associated with a plan.
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

Before implementing a non-trivial plan, run an independent plan-review loop with a subagent. Treat plans involving multiple components, migrations, externally visible behavior, or significant uncertainty as non-trivial. Do not start implementation while the plan has unresolved logical contradictions or blocking omissions.

1. Write the complete draft plan to the relevant `plan/*.md` file, including scope, evidence-backed assumptions, ordered work items, validation, and completion conditions. For each work item, make clear its prerequisites, produced artifact or contract, state transition, and rollback or forward-only decision; verify that the dependency order has no missing or cyclic prerequisite.
2. Delegate a reviewer subagent that did not author the plan. Supply the plan, an evidence list of inspected sources, and the relevant task-local context. Require a compatibility check against related contracts, active plans, dependencies, feature flags, and deployment or migration constraints. Ask it to identify contradictions, missing prerequisites, invalid ordering, unsafe assumptions, unhandled failure or rollback paths, interface or compatibility risks, and gaps in testing or acceptance criteria.
3. Classify each finding as blocking, material, or optional, and record its disposition and evidence. Blocking findings include any unresolved contradiction, missing prerequisite, incompatible contract, unsafe data or state transition, or unmeasurable completion condition. Resolve every blocking finding. Resolve each material finding or record a specific evidence-based rationale for declining it; do not use a label or an assumption to hide a contradiction.
4. Send the revised plan, the prior findings, and their dispositions to a different reviewer subagent where one is available. Require it to verify that every resolution is supported by evidence and has not introduced a contradiction. Repeat the review-and-revision cycle until the final reviewer confirms that all contradictions are closed and no blocking issue remains. Re-run this loop whenever assumptions, interfaces, ordering, validation, or completion conditions materially change, including during phased implementation.
5. If a review reveals an unknown product, compatibility, or architectural choice that needs user preference, stop before implementation and ask the user. Record only evidence-backed implementation assumptions as assumptions; never substitute one for a user decision.
6. Begin implementation only after the final plan is internally consistent, has an executable dependency order, and provides measurable validation and completion conditions. Summarize the review outcome before moving on.

Keep review prompts evidence-based and challenge-oriented; do not ask the reviewer merely to approve the plan. For trivial, isolated edits, use normal self-review instead and state why a subagent review is unnecessary. If no subagent can be started, do not implement migrations, multi-component changes, or externally visible behavior without explicit user authorization; for lower-risk plans, perform the same checklist yourself and disclose that the independent review was unavailable.

## Reviewer model selection

Choose the reviewer model and reasoning effort when starting each subagent. Do not hard-code a model name: inspect the models and reasoning levels currently available to the launcher, honor an explicit user pin, and otherwise choose by the provider's current capability, cost, and latency labels.

Use the following policy:

1. For a normal non-trivial plan, prefer a currently available strong, balanced model at medium reasoning effort. This is the default trade-off for substantive logical review.
2. For an irreversible migration, security-sensitive change, public compatibility change, multi-system rollout, or plan with unresolved architectural risk, still start with a strong, balanced model at medium reasoning effort. Do not automatically escalate to the flagship model or high/extra-high reasoning; the final reviewer must be at least as capable as the plan author.
3. Reserve fast or economy-oriented models for trivial checklist passes, not as the only blocker-clearing reviewer for a non-trivial plan.
4. Prefer a different reviewer agent for the final pass. For high-risk plans, also prefer a different model tier or family when the current launcher offers one; otherwise use a fresh agent with an independent prompt and context.
5. When representative review evaluations or prior outcome data exist, choose the lowest-cost, lowest-latency option that meets the required review quality. Without evidence, use the balanced Medium default rather than assuming the flagship model or higher reasoning effort is worthwhile.

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
