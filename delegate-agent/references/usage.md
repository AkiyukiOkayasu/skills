# Usage contract

## Required input

Every real delegation requires:

- `--mode explore|review|commit-prep|work`
- `--goal <one-sentence goal>`
- at least one `--acceptance <condition>`

The default delegated model is `opencode-go/deepseek-v4-flash`. The local execution detail is intentionally hidden from callers.

Use `--scope` for the smallest set of relative files or directories. Use `--prompt-file` for task-specific details. The runner rejects absolute paths, repository escapes, sensitive paths, oversized packets, and work requests without explicit macOS sandbox opt-in.

## Recommended calls

### Code exploration

```bash
delegate-agent/scripts/delegate-agent \
  --mode explore \
  --model opencode-go/deepseek-v4-flash \
  --goal "Locate the main request path and data flow" \
  --acceptance "List facts, evidence paths, and unknowns without changing files" \
  --scope src
```

Use this for broad structure, entry points, module responsibilities, data flow, tests, and the files Codex should read first. The report is an index, not a substitute for reading the source.

Do not treat the exploration as authoritative. Re-open important files, confirm call relationships and contracts, and use GPT/Codex for detailed debugging or local design questions.

### Independent high-level review

```bash
delegate-agent/scripts/delegate-agent \
  --mode review \
  --model opencode-go/deepseek-v4-flash \
  --goal "Review the approach independently" \
  --acceptance "Assess assumptions, architecture consistency, complexity, alternatives, and concrete risks with evidence" \
  --scope src --scope tests
```

Do not include Sol's findings in the prompt. Sol/Codex should cover local implementation correctness; DeepSeek should independently challenge the approach and assumptions. Codex compares both results and decides what to verify.

### Bounded work

```bash
delegate-agent/scripts/delegate-agent \
  --mode work --allow-work \
  --goal "Apply the approved small refactor" \
  --acceptance "Change only the requested files and report tests" \
  --scope src
```

The worker edits a sanitized project workspace under Seatbelt. The result points to `work.patch` and `changed_paths`; apply it after the lightweight work gate passes:

- runner status is success and the parent worktree is unchanged
- `changed_paths` are inside the requested scope and match the approved Plan
- `git apply --check <work.patch>` succeeds
- requested format, build, or test checks pass

Keep the check proportional for approved low-discretion work. Do not redo a full design review or reimplement the patch unless one of these gates fails, the patch is surprising, or it touches a sensitive contract.

Use the same `work` mode for document updates or other mechanical edits when the target files and acceptance criteria are explicit. For a completed diff, use `commit-prep` to summarize scope, tests, and a commit message candidate; Codex performs the actual commit.

### Setup checks

```bash
delegate-agent/scripts/delegate-agent \
  --model opencode-go/deepseek-v4-flash \
  --preflight-only
```

The result lists the executable, version, credential presence, catalog result, and errors without printing credential contents.

## Commit boundary

`commit` is a separate operation after Codex has verified the implementation diff and tests. It requires explicit target paths and must prohibit broad staging, destructive history operations, and push. The current runner exposes `commit-prep` only; use [mode-prompts.md](mode-prompts.md) as the contract until an explicit commit boundary is implemented.

## Parent-agent handling

Read the JSON result, then inspect the cited files in Codex. The result must identify mode, model, termination state, output, file changes, and Codex follow-up checks. Treat `final_text` as a report, not as a patch. For `work`, the patch artifact is the source of changes and may be applied after the lightweight gate above passes. For `commit-prep`, use the report to prepare a Codex-side commit; never ask the external agent to stage or commit until the explicit commit boundary exists.
