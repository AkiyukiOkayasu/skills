# Pi contract

The adapter invokes Pi with an explicit model, `--mode json`, `--no-session`, `--no-extensions`, `--no-skills`, `--no-context-files`, and `--no-approve`. Read-only modes allow only `read,grep,find,ls`. `work` additionally allows `edit,write,bash`, but the whole child process is wrapped by macOS Seatbelt and can write only inside the sanitized workspace.

The parser accepts Pi's `session`, lifecycle, message, and tool execution events. Success requires exit code 0, an `agent_end`, non-empty assistant text, valid JSONL, no forbidden tool, unchanged sanitized workspace for read-only modes, unchanged parent Git state, and no truncated result. In `work`, changed paths and a bounded patch are returned for Codex review.

## Common failure rules

Treat blank or non-JSON stdout lines, missing terminal events, timeout, non-zero exit, malformed output, a forbidden tool, result truncation, or any parent file-state change as failure. Keep raw stdout and stderr in the artifact directory, but return only a redacted bounded summary to the parent agent.
