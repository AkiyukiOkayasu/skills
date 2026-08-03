---
name: delegate-agent
description: Safely delegate bounded repository exploration, independent review, commit preparation, or explicitly opt-in macOS-sandboxed edits to an external agent while preserving Codex as the final verifier. Use when a task benefits from a fast independent viewpoint, especially for large codebases and broad analysis; do not use for ambiguous design decisions, security judgments, broad migrations, or unisolated file-changing work.
---

# Delegate Agent

Use the bundled runner as a controlled child-agent boundary. Keep Codex responsible for the final interpretation, edits, tests, and commits.

## Select the mode

- `explore`: map structure, entry points, data flow, relevant files, facts, and unknowns. No changes. Treat the result as an index and hypothesis; verify important claims in the source.
- `review`: inspect a bounded design or diff and report findings with file and line evidence. No changes.
- `commit-prep`: inspect the current diff and propose the commit scope and message. Never stage or commit.
- `work`: bounded edits in a sanitized project workspace. It requires explicit `--allow-work` and macOS Seatbelt isolation; the parent repository is never auto-modified.
- `commit`: a separate, explicitly authorized stage/commit operation after Codex has verified the diff. The current runner exposes `commit-prep`; do not infer direct commit permission.

The default delegated model is `opencode-go/deepseek-v4-flash`. Use it as a fast, low-cost worker for broad exploration, clear-plan implementation, documentation, and commit preparation. For important changes it can also provide an independent high-level review; that is one use case, not the only one.

For an important change, use this reviewer as a complementary pass: keep Sol/Codex focused on implementation details and local correctness, and ask DeepSeek to focus independently on assumptions, overall approach, architecture consistency, unnecessary complexity, and simpler alternatives. Do not pass the other reviewer's findings into the independent prompt.

## Run a delegation

From the target repository root, provide a goal and acceptance criteria. Use repeated `--scope`, `--constraint`, `--known-fact`, and `--unknown` options when they add useful context. Put the detailed request in a file when it is more than a sentence.

```bash
delegate-agent/scripts/delegate-agent \
  --mode explore \
  --goal "Find the request path and its main extension points" \
  --acceptance "Report facts with paths, evidence, and unknowns; make no changes" \
  --scope src \
  --prompt-file /tmp/delegation-request.md
```

The runner creates a sanitized copy, excludes credentials and context files, records the parent Git state, applies a fixed context-packet limit, executes the delegated model with mechanical result checks, stores raw JSONL and stderr as local artifacts, and prints only a compact JSON result. A successful child answer is not proof of correctness: inspect its evidence and verify important claims in Codex.

Use `--preflight-only` during setup or after changing the local runner, model, runtime, or credential. It checks the executable, supported version, credential presence without printing secrets, and the requested model catalog.

Read [mode-prompts.md](references/mode-prompts.md) when constructing a mode-specific prompt or validating parent-side output handling. It contains the explore/review/work/commit contracts, routing guidance, and failure conditions.

## Safety rules

- Keep `explore`, `review`, and `commit-prep` read-only. The delegated process receives only `read,grep,find,ls`.
- `work` may use `edit`, `write`, and `bash`, but only inside the sanitized delegation workspace. On macOS the child process is wrapped with Seatbelt so file writes outside the workspace are denied. The result contains changed paths and a bounded patch artifact; Codex must inspect and apply any patch manually.
- Do not pass `.env`, auth files, `.git`, `.pi`, `.opencode`, `.agents`, or symlinks resolving outside the repository. Provide any required context explicitly in the packet.
- Treat dirty-worktree state as input, never as permission to overwrite it. The runner does not stash, reset, checkout, restore, stage, commit, amend, rebase, or push.
- A timeout, non-zero exit, malformed JSONL, missing terminal event, forbidden tool, changed public copy, changed parent worktree, or truncated result is a failure.
- Never include API keys in prompts or results. Raw artifacts may contain model output, so review them locally before sharing.

## Evaluate whether delegation is worthwhile

Delegate large initial exploration, broad independent reviews, and approved repetitive work. Keep small edits, single-file questions, complex design, security decisions, and broad migrations in Codex. Compare the end-to-end time and verification effort, not just model latency. For changes to the runner, parser, or model profile, use one warmup plus at least three trials for structure exploration, a seeded-defect review, and commit preparation; require zero forbidden changes and zero critical misses.

Read [pi-contract.md](references/pi-contract.md) when changing the runner's local adapter or parser. Read [usage.md](references/usage.md) when integrating the skill into another Skill.

Use a synthetic smoke probe and at least three representative trials when changing the local adapter, parser, or model. Record first-event latency, total time, quality anchors, safety, and packet/output byte proxies in the plan or task artifact.
