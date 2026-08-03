#!/usr/bin/env python3
"""Bounded delegation runner for external OpenCode Go agents.

The runner deliberately has no dependency outside the Python standard library.
It treats model output as untrusted evidence and makes filesystem state and
backend event contracts part of the success decision.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Sequence, Tuple


MAX_PACKET_BYTES = 16 * 1024
MAX_RESULT_BYTES = 12 * 1024
MAX_DIFF_BYTES = 32 * 1024
MAX_CONTEXT_PATHS = 64
MAX_PUBLISHED_FILES = 10_000
MAX_PUBLISHED_BYTES = 512 * 1024 * 1024
MAX_TEXT_PARSE_BYTES = 64 * 1024 * 1024
READ_ONLY_MODES = {"explore", "review", "commit-prep"}
MODES = READ_ONLY_MODES | {"work"}
BACKENDS = {"pi"}
DEFAULT_MODEL = "opencode-go/deepseek-v4-flash"
READ_ONLY_TOOLS = {"read", "grep", "find", "ls", "glob", "list"}
WORK_TOOLS = READ_ONLY_TOOLS | {"edit", "write", "bash"}
SENSITIVE_PARTS = {
    ".git",
    ".pi",
    ".opencode",
    ".agents",
    ".codex",
    ".claude",
}
SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "auth.json",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
    "agents.md",
    "claude.md",
}
SENSITIVE_LINE = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret|private[_-]?key)"
)
SEMVER = re.compile(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)")


class DelegateError(Exception):
    """A fail-closed configuration or execution error."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounded_text(value: str, limit: int) -> Tuple[str, bool]:
    encoded = value.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return value, False
    return encoded[:limit].decode("utf-8", errors="ignore") + "\n[TRUNCATED]", True


def redact_text(value: str) -> str:
    value = re.sub(
        r"-----BEGIN [^-]+-----.*?-----END [^-]+-----",
        "[REDACTED PRIVATE KEY]",
        value,
        flags=re.DOTALL,
    )
    redacted_lines: List[str] = []
    for line in value.splitlines():
        if SENSITIVE_LINE.search(line) and re.search(r"[:=]", line):
            redacted_lines.append(re.sub(r"([:=]).*$", r"\1 [REDACTED]", line))
        else:
            redacted_lines.append(line)
    return "\n".join(redacted_lines)


def decode(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def run_capture(
    argv: Sequence[str],
    cwd: Optional[Path] = None,
    timeout: float = 20.0,
) -> Tuple[int, bytes, bytes]:
    try:
        completed = subprocess.run(
            list(argv),
            cwd=str(cwd) if cwd else None,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DelegateError("command failed: " + " ".join(argv[:2]) + ": " + str(exc)) from exc
    return completed.returncode, completed.stdout, completed.stderr


def git_output(root: Path, args: Sequence[str], timeout: float = 30.0) -> bytes:
    code, stdout, stderr = run_capture(["git", *args], root, timeout)
    if code != 0:
        raise DelegateError("git command failed: " + decode(stderr).strip()[:500])
    return stdout


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def normalized_relative(root: Path, value: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute():
        raise DelegateError("absolute paths are not allowed in --scope: " + value)
    target = (root / candidate).resolve(strict=False)
    if not is_within(target, root):
        raise DelegateError("scope escapes repository: " + value)
    relative = target.relative_to(root.resolve()).as_posix()
    if relative in {"", "."}:
        raise DelegateError("repository root is not a valid narrow scope")
    return relative.rstrip("/")


def is_sensitive_path(relative: str) -> bool:
    path = PurePosixPath(relative)
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if parts & SENSITIVE_PARTS:
        return True
    if name in SENSITIVE_NAMES:
        return True
    if name.endswith((".pem", ".key", ".p12", ".pfx")):
        return True
    return False


def read_git_paths(root: Path, include_untracked: bool) -> List[str]:
    tracked = git_output(root, ["ls-files", "-z"])
    values = set(filter(None, decode(tracked).split("\0")))
    if include_untracked:
        untracked = git_output(root, ["ls-files", "-z", "--others", "--exclude-standard"])
        values.update(filter(None, decode(untracked).split("\0")))
    return sorted(values)


def file_fingerprint(path: Path) -> Dict[str, Any]:
    stat = path.lstat()
    mode = stat.st_mode & 0o7777
    if path.is_symlink():
        return {"kind": "symlink", "mode": mode, "target": os.readlink(path)}
    if not path.is_file():
        return {"kind": "other", "mode": mode, "size": stat.st_size}
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"kind": "file", "mode": mode, "size": stat.st_size, "sha256": digest.hexdigest()}


def tree_manifest(root: Path) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for directory, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirnames[:] = [name for name in dirnames if name != ".delegate"]
        base = Path(directory)
        for name in filenames + [name for name in dirnames if (base / name).is_symlink()]:
            path = base / name
            relative = path.relative_to(root).as_posix()
            if relative == ".delegate" or relative.startswith(".delegate/"):
                continue
            result[relative] = file_fingerprint(path)
    return result


def git_snapshot(root: Path) -> Dict[str, Any]:
    head = decode(git_output(root, ["rev-parse", "HEAD"])).strip()
    status = git_output(root, ["status", "--porcelain=v1", "-z"])
    staged = git_output(root, ["diff", "--cached", "--binary"])
    worktree = git_output(root, ["diff", "--binary", "HEAD"])
    modes = git_output(root, ["ls-files", "-s", "-z"])
    untracked_names = decode(
        git_output(root, ["ls-files", "-z", "--others", "--exclude-standard"])
    ).split("\0")
    untracked: Dict[str, Any] = {}
    for relative in filter(None, untracked_names):
        path = root / relative
        if os.path.lexists(path):
            untracked[relative] = file_fingerprint(path)
    return {
        "head": head,
        "status_sha256": sha256_bytes(status),
        "staged_diff_sha256": sha256_bytes(staged),
        "worktree_diff_sha256": sha256_bytes(worktree),
        "tracked_modes_sha256": sha256_bytes(modes),
        "untracked": untracked,
        "status_text": decode(status).replace("\0", "\n"),
    }


def same_snapshot(before: Dict[str, Any], after: Dict[str, Any]) -> bool:
    comparable = (
        "head",
        "status_sha256",
        "staged_diff_sha256",
        "worktree_diff_sha256",
        "tracked_modes_sha256",
        "untracked",
    )
    return all(before.get(key) == after.get(key) for key in comparable)


def diff_for_packet(root: Path) -> str:
    raw = git_output(root, ["diff", "--binary", "HEAD"])
    text = redact_text(decode(raw))
    text, _ = bounded_text(text, MAX_DIFF_BYTES)
    return text


def copy_public_tree(
    root: Path,
    destination: Path,
    scopes: Sequence[str],
    include_untracked: bool,
) -> List[str]:
    scope_values = [normalized_relative(root, item) for item in scopes]
    candidates = read_git_paths(root, include_untracked)
    selected: List[str] = []
    total_bytes = 0
    for relative in candidates:
        if scope_values and not any(
            relative == scope or relative.startswith(scope + "/") for scope in scope_values
        ):
            continue
        sensitive = is_sensitive_path(relative)
        if sensitive:
            if scope_values and any(
                relative == scope or relative.startswith(scope + "/") for scope in scope_values
            ):
                raise DelegateError("scope includes a denied sensitive path: " + relative)
            continue
        source = root / relative
        if not os.path.lexists(source):
            continue
        resolved = Path(os.path.realpath(source))
        if not is_within(resolved, root):
            raise DelegateError("source symlink escapes repository: " + relative)
        if source.is_file() and not source.is_symlink():
            total_bytes += source.stat().st_size
        selected.append(relative)
    if not selected:
        raise DelegateError("no publishable tracked files matched the requested scope")
    if len(selected) > MAX_PUBLISHED_FILES:
        raise DelegateError("published file count exceeds safety limit")
    if total_bytes > MAX_PUBLISHED_BYTES:
        raise DelegateError("published file size exceeds safety limit")

    for relative in selected:
        source = root / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink():
            target.symlink_to(os.readlink(source))
        elif source.is_file():
            shutil.copy2(source, target)
        else:
            raise DelegateError("unsupported published path type: " + relative)
    return selected


def sbpl_literal(path: Path) -> str:
    value = str(path.resolve())
    return value.replace("\\", "\\\\").replace('"', '\\"')


def create_macos_write_sandbox(profile: Path, writable_roots: Sequence[Path]) -> None:
    if sys.platform != "darwin":
        raise DelegateError("work mode requires macOS Seatbelt sandboxing")
    if shutil.which("sandbox-exec") is None:
        raise DelegateError("work mode requires /usr/bin/sandbox-exec")
    if not writable_roots:
        raise DelegateError("work mode has no writable workspace")
    lines = [
        "(version 1)",
        "(allow default)",
        "(deny file-write*)",
    ]
    for root in writable_roots:
        lines.append('(allow file-write* (subpath "' + sbpl_literal(root) + '"))')
    profile.write_text("\n".join(lines) + "\n", encoding="utf-8")


def workspace_diff(root: Path, public_root: Path, changed_paths: Sequence[str]) -> Tuple[str, bool]:
    chunks: List[str] = []
    for relative in changed_paths:
        original = root / relative
        updated = public_root / relative
        if original.is_symlink() or updated.is_symlink():
            old_link = os.readlink(original) if original.is_symlink() else "<not a symlink>"
            new_link = os.readlink(updated) if updated.is_symlink() else "<not a symlink>"
            chunks.append(
                "symlink change: %s: %s -> %s\n" % (relative, old_link, new_link)
            )
            continue
        old_bytes = original.read_bytes() if original.is_file() else b""
        new_bytes = updated.read_bytes() if updated.is_file() else b""
        if len(old_bytes) > MAX_DIFF_BYTES or len(new_bytes) > MAX_DIFF_BYTES:
            chunks.append("binary or oversized change: %s\n" % relative)
            continue
        if b"\0" in old_bytes[:8192] or b"\0" in new_bytes[:8192]:
            chunks.append("binary change: %s\n" % relative)
            continue
        old_text = decode(old_bytes).splitlines(keepends=True)
        new_text = decode(new_bytes).splitlines(keepends=True)
        chunks.extend(
            difflib.unified_diff(
                old_text,
                new_text,
                fromfile="a/" + relative,
                tofile="b/" + relative,
            )
        )
    value = redact_text("".join(chunks))
    return bounded_text(value, MAX_DIFF_BYTES)


def build_packet(
    args: argparse.Namespace,
    snapshot: Dict[str, Any],
    selected_paths: Sequence[str],
    diff_text: str,
) -> str:
    if len(args.scope) > MAX_CONTEXT_PATHS:
        raise DelegateError("--scope count exceeds the context-packet limit")
    request = args.prompt or "No additional request was supplied. Use the goal and acceptance criteria."
    if args.prompt_file:
        request = Path(args.prompt_file).expanduser().read_text(encoding="utf-8")
    default_constraint = (
        "Edit only the delegated workspace; do not commit, push, reset, stash, or invoke another agent."
        if args.mode == "work"
        else "Read-only; do not infer permission to modify anything."
    )
    role_guidance = {
        "explore": (
            "Work as a fast codebase cartographer: identify the project purpose, major directories, "
            "entry points, module responsibilities, data flow, state management, test structure, "
            "relevant files, first files to read, and unknowns. Prefer a concise, evidence-backed index. "
            "Separate observed facts from inferences and identify the files Codex should read first."
        ),
        "review": (
            "Work as an independent reviewer. Challenge assumptions, problem framing, overall approach, "
            "architecture consistency, unnecessary complexity, and simpler alternatives. Report concrete "
            "implementation risks when you find them, but do not assume another reviewer's conclusions. "
            "Structure the result as: (1) policy or design problems, (2) concrete implementation problems, "
            "(3) unverified assumptions or questions, and (4) points judged not problematic."
        ),
        "work": (
            "Implement only the clear, approved work described in the packet. Do not redesign the approach "
            "or expand scope; report changed files, implementation summary, tests, and unresolved issues."
        ),
        "commit-prep": (
            "Prepare a concise, evidence-backed change summary and commit proposal. Check scope and tests, "
            "but do not stage or commit. Identify the target files, test status, and a suitable commit message."
        ),
    }[args.mode]
    fields = [
        ("goal", [args.goal]),
        ("scope", list(args.scope) or ["all publishable tracked files"]),
        ("constraints", list(args.constraint) or [default_constraint]),
        ("acceptance", list(args.acceptance)),
        ("known_facts", list(args.known_fact)),
        ("unknowns", list(args.unknown)),
    ]
    lines = [
        "# Bounded delegation packet",
        "",
        (
            "You are an external bounded coding worker. Treat this packet and the available temporary workspace as the complete authority."
            if args.mode == "work"
            else "You are an external read-only analyst. Treat this packet and the available temporary workspace as the complete authority."
        ),
        (
            "You may edit files in the workspace and run necessary project commands, but never write outside the workspace, commit, push, reset, stash, invoke subagents, load skills, or use the web."
            if args.mode == "work"
            else "Do not modify files, run shell commands, access paths outside the workspace, invoke subagents, load skills, or use the network."
        ),
        "Separate observed facts from inferences. Every finding must include a relative path and evidence. State what you could not verify.",
        "",
        "## Mode",
        args.mode,
        "",
        "## Role guidance",
        role_guidance,
        "",
    ]
    for name, values in fields:
        lines.append("## " + name)
        lines.extend("- " + str(value) for value in values)
        lines.append("")
    lines.extend(
        [
            "## Request",
            request.strip(),
            "",
            "## Parent Git state (redacted metadata)",
            "- HEAD: " + snapshot["head"],
            "- Status:\n```text\n" + redact_text(snapshot["status_text"])[:4000] + "\n```",
            "- Published paths: " + str(len(selected_paths)),
        ]
    )
    if args.mode in {"review", "commit-prep"}:
        lines.extend(["", "## Redacted diff from HEAD", "```diff", diff_text, "```"])
    packet = "\n".join(lines).strip() + "\n"
    packet_bytes = len(packet.encode("utf-8"))
    if packet_bytes > MAX_PACKET_BYTES:
        raise DelegateError(
            "context packet exceeds 16 KiB; narrow --scope or shorten --prompt-file (bytes=%d)"
            % packet_bytes
        )
    return packet


def parse_version(value: str) -> Optional[Tuple[int, int, int]]:
    match = SEMVER.search(value)
    if not match:
        return None
    return tuple(int(item) for item in match.groups())  # type: ignore[return-value]


def preflight(model: str, strict_catalog: bool) -> Dict[str, Any]:
    backend = "pi"
    executable_name = backend
    executable = shutil.which(executable_name)
    installed = executable is not None
    version_text = ""
    version = None
    if installed:
        try:
            code, stdout, stderr = run_capture([executable, "--version"], timeout=10)
            version_text = decode(stdout or stderr).strip()
            version = parse_version(version_text)
        except DelegateError as exc:
            version_text = str(exc)
    version_supported = version is not None and version >= (0, 83, 0)
    credentials = bool(os.environ.get("OPENCODE_API_KEY")) or (
        Path.home() / ".pi/agent/auth.json"
    ).is_file()
    catalog: Optional[bool] = None
    catalog_note = "not checked during normal delegation"
    if strict_catalog and installed and version_supported and credentials:
        try:
            code, stdout, stderr = run_capture([executable_name, "--list-models"], timeout=45)
            output = decode(stdout) + "\n" + decode(stderr)
            model_id = model.split("/", 1)[-1]
            catalog = code == 0 and "opencode-go" in output and model_id in output
            catalog_note = redact_text(output)[-1000:]
        except DelegateError as exc:
            catalog = False
            catalog_note = str(exc)
    errors: List[str] = []
    if not installed:
        errors.append(backend + " executable not found")
    if not version_supported:
        errors.append("unsupported or undetectable " + backend + " version: " + version_text)
    if not credentials:
        errors.append("credential presence not detected; configure the provider without printing its secret")
    if strict_catalog and catalog is not True:
        errors.append("requested model was not confirmed in the backend catalog")
    return {
        "backend": backend,
        "executable": executable,
        "version": version_text,
        "installed": installed,
        "version_supported": version_supported,
        "credentials_configured": credentials,
        "catalog_contains_model": catalog,
        "catalog_note": catalog_note,
        "profile_verified": True,
        "probe_succeeded": False,
        "errors": errors,
    }


def smoke_probe(model: str, timeout: float) -> Dict[str, Any]:
    """Probe a backend with synthetic content only; never use the source repository."""
    with tempfile.TemporaryDirectory(prefix="delegate-agent-probe-") as temporary:
        base = Path(temporary)
        public_root = base / "workspace"
        public_root.mkdir()
        (public_root / "README.md").write_text("Synthetic smoke fixture.\n", encoding="utf-8")
        prompt_file = base / "packet.md"
        prompt_file.write_text(
            "Reply exactly READY. Read-only. Do not use tools unless needed.\n", encoding="utf-8"
        )
        adapter = Path(__file__).resolve().parent / "backends/pi.sh"
        if not adapter.is_file():
            return {"success": False, "reason": "adapter not found"}
        process = run_process(adapter, public_root, prompt_file, model, timeout)
        allowed_tools = {"read", "grep", "find", "ls", "glob", "list"}
        parsed = parse_pi(process["stdout"], allowed_tools)
        success = (
            process["exit_code"] == 0
            and not process["timed_out"]
            and parsed["terminal"]
            and parsed["final_text"].strip() == "READY"
            and not parsed["errors"]
            and not parsed["forbidden_tools"]
            and parsed["invalid_lines"] == 0
        )
        return {
            "success": success,
            "exit_code": process["exit_code"],
            "duration_ms": process["duration_ms"],
            "first_event_ms": process["first_event_ms"],
            "events": parsed["events"],
            "reason": "; ".join(parsed["errors"] or parsed["forbidden_tools"]),
        }


def tool_name(event: Dict[str, Any]) -> Optional[str]:
    for key in ("toolName", "tool", "name"):
        value = event.get(key)
        if isinstance(value, str) and value not in {"tool_use", "tool"}:
            return value
    for key in ("part", "tool", "tool_use"):
        value = event.get(key)
        if isinstance(value, dict):
            found = tool_name(value)
            if found:
                return found
    return None


def content_text(message: Any) -> str:
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    pieces: List[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") in {"text", "output_text"}:
            value = block.get("text")
            if isinstance(value, str):
                pieces.append(value)
    return "".join(pieces)


def event_text(event: Dict[str, Any]) -> str:
    for key in ("text", "delta"):
        if isinstance(event.get(key), str):
            return event[key]
    for key in ("part", "message", "assistantMessageEvent"):
        value = event.get(key)
        if isinstance(value, dict):
            found = event_text(value)
            if found:
                return found
            found = content_text(value)
            if found:
                return found
    return ""


def parse_jsonl(raw: bytes) -> Tuple[List[Dict[str, Any]], int, bool]:
    truncated = len(raw) > MAX_TEXT_PARSE_BYTES
    if truncated:
        raw = raw[:MAX_TEXT_PARSE_BYTES]
    events: List[Dict[str, Any]] = []
    invalid = 0
    for line in decode(raw).splitlines():
        if not line.strip():
            invalid += 1
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            invalid += 1
            continue
        if not isinstance(value, dict):
            invalid += 1
            continue
        events.append(value)
    return events, invalid, truncated


def parse_pi(raw: bytes, allowed_tools: set[str]) -> Dict[str, Any]:
    events, invalid, parse_truncated = parse_jsonl(raw)
    text_parts: List[str] = []
    final_messages: List[str] = []
    errors: List[str] = []
    forbidden: List[str] = []
    terminal = False
    unknown = 0
    usage: Dict[str, Any] = {}
    known = {
        "session",
        "agent_start",
        "agent_end",
        "turn_start",
        "turn_end",
        "message_start",
        "message_update",
        "message_end",
        "tool_execution_start",
        "tool_execution_update",
        "tool_execution_end",
        "queue_update",
        "compaction_start",
        "compaction_end",
        "auto_retry_start",
        "auto_retry_end",
    }
    for event in events:
        kind = event.get("type")
        if kind not in known:
            unknown += 1
        if kind == "message_update":
            update = event.get("assistantMessageEvent")
            if isinstance(update, dict) and update.get("type") == "text_delta":
                delta = update.get("delta")
                if isinstance(delta, str):
                    text_parts.append(delta)
        if kind == "message_end":
            message = event.get("message")
            if isinstance(message, dict) and message.get("role") == "assistant":
                value = content_text(message)
                if value:
                    final_messages.append(value)
        if kind == "agent_end":
            terminal = True
            messages = event.get("messages")
            if isinstance(messages, list):
                for message in messages:
                    if isinstance(message, dict) and message.get("role") == "assistant":
                        value = content_text(message)
                        if value:
                            final_messages.append(value)
        if kind == "tool_execution_start":
            name = event.get("toolName")
            if not isinstance(name, str):
                name = "unknown"
            if name not in allowed_tools:
                forbidden.append(name)
        if kind == "tool_execution_end" and event.get("isError"):
            errors.append("tool execution failed: " + str(event.get("toolName", "unknown")))
        for key in ("usage", "tokens"):
            if key in event:
                usage[key] = event[key]
    final_text = (final_messages[-1] if final_messages else "".join(text_parts)).strip()
    return {
        "events": len(events),
        "invalid_lines": invalid,
        "parse_truncated": parse_truncated,
        "unknown_events": unknown,
        "terminal": terminal,
        "errors": errors,
        "forbidden_tools": sorted(set(forbidden)),
        "final_text": final_text,
        "usage": usage,
    }


def run_process(
    adapter: Path,
    public_root: Path,
    prompt_file: Path,
    model: str,
    timeout: float,
    mode: str = "explore",
    sandbox_profile: Optional[Path] = None,
) -> Dict[str, Any]:
    env = os.environ.copy()
    env.update(
        {
            "DELEGATE_ROOT": str(public_root),
            "DELEGATE_MODEL": model,
            "DELEGATE_PROMPT_FILE": str(prompt_file),
            "DELEGATE_MODE": mode,
        }
    )
    started = time.monotonic()
    first_event: Optional[float] = None
    stdout = bytearray()
    stderr = bytearray()
    timed_out = False
    try:
        command = [str(adapter)]
        if sandbox_profile is not None:
            command = ["sandbox-exec", "-f", str(sandbox_profile), *command]
        process = subprocess.Popen(
            command,
            cwd=str(public_root),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
    except OSError as exc:
        raise DelegateError("failed to start backend adapter: " + str(exc)) from exc
    assert process.stdout is not None
    assert process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    deadline = started + timeout
    kill_deadline: Optional[float] = None
    while selector.get_map():
        now = time.monotonic()
        if process.poll() is None and now >= deadline and not timed_out:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            kill_deadline = now + 3.0
        if timed_out and kill_deadline is not None and now >= kill_deadline and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        wait_for = 0.1
        events = selector.select(wait_for)
        for key, _ in events:
            try:
                data = os.read(key.fileobj.fileno(), 65536)
            except OSError:
                data = b""
            if not data:
                selector.unregister(key.fileobj)
                continue
            if key.data == "stdout":
                stdout.extend(data)
                if first_event is None and data.strip():
                    first_event = time.monotonic() - started
            else:
                stderr.extend(data)
        if process.poll() is not None and not selector.get_map():
            break
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=3)
    process.stdout.close()
    process.stderr.close()
    return {
        "exit_code": process.returncode,
        "stdout": bytes(stdout),
        "stderr": bytes(stderr),
        "duration_ms": round((time.monotonic() - started) * 1000),
        "first_event_ms": round(first_event * 1000) if first_event is not None else None,
        "timed_out": timed_out,
    }


def make_artifact_dir(requested: Optional[str], root: Path) -> Path:
    if requested:
        directory = Path(requested).expanduser().resolve()
        if is_within(directory, root) or is_within(root, directory):
            raise DelegateError("artifact directory must not overlap the source repository")
        directory.mkdir(parents=True, exist_ok=False)
        return directory
    return Path(tempfile.mkdtemp(prefix="delegate-agent-"))


def emit(value: Dict[str, Any]) -> int:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))
    return 0 if value.get("status") == "success" else 1


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely delegate bounded agent work")
    parser.add_argument("--backend", choices=sorted(BACKENDS), default="pi")
    parser.add_argument("--mode", choices=sorted(MODES), default="explore")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--model")
    parser.add_argument("--goal")
    parser.add_argument("--acceptance", action="append", default=[])
    parser.add_argument("--scope", action="append", default=[])
    parser.add_argument("--constraint", action="append", default=[])
    parser.add_argument("--known-fact", action="append", default=[])
    parser.add_argument("--unknown", action="append", default=[])
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--include-untracked", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output-dir")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument(
        "--allow-work",
        action="store_true",
        help="explicitly enable macOS-sandboxed edits in the delegated workspace",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    try:
        args = parse_args(argv)
        if args.mode == "work" and not args.allow_work:
            raise DelegateError(
                "work mode requires --allow-work and macOS Seatbelt isolation"
            )
        if args.mode == "work" and sys.platform != "darwin":
            raise DelegateError("work mode is available only on macOS")
        if args.timeout <= 0 or args.timeout > 3600:
            raise DelegateError("--timeout must be between 1 and 3600 seconds")
        root = Path(args.repo).expanduser().resolve()
        if not root.is_dir():
            raise DelegateError("repository directory does not exist: " + str(root))
        model = args.model or DEFAULT_MODEL
        if args.preflight_only:
            result = preflight(model, True)
            return emit(
                {
                    "status": "success" if not result["errors"] else "failed",
                    "preflight": [result],
                }
            )
        if not args.goal or not args.acceptance:
            raise DelegateError("--goal and at least one --acceptance are required")
        if args.prompt and args.prompt_file:
            raise DelegateError("use only one of --prompt and --prompt-file")
        basic = preflight(model, False)
        if basic["errors"]:
            raise DelegateError("backend preflight failed: " + "; ".join(basic["errors"]))
        artifact_dir = make_artifact_dir(args.output_dir, root)
        public_root = artifact_dir / "workspace"
        public_root.mkdir()
        selected_paths = copy_public_tree(root, public_root, args.scope, args.include_untracked)
        before_parent = git_snapshot(root)
        diff_text = diff_for_packet(root) if args.mode in {"review", "commit-prep"} else ""
        packet = build_packet(args, before_parent, selected_paths, diff_text)
        prompt_file = artifact_dir / "packet.md"
        prompt_file.write_text(packet, encoding="utf-8")
        before_public = tree_manifest(public_root)
        adapter = Path(__file__).resolve().parent / "backends/pi.sh"
        if not adapter.is_file():
            raise DelegateError("backend adapter not found: " + str(adapter))
        sandbox_profile: Optional[Path] = None
        if args.mode == "work":
            sandbox_profile = artifact_dir / "macos-work.sb"
            create_macos_write_sandbox(sandbox_profile, [public_root])
        process = run_process(
            adapter,
            public_root,
            prompt_file,
            model,
            args.timeout,
            args.mode,
            sandbox_profile,
        )
        (artifact_dir / "stdout.jsonl").write_bytes(process["stdout"])
        (artifact_dir / "stderr.log").write_text(redact_text(decode(process["stderr"])), encoding="utf-8")
        after_public = tree_manifest(public_root)
        after_parent = git_snapshot(root)
        changed_public = sorted(
            path
            for path in set(before_public) | set(after_public)
            if before_public.get(path) != after_public.get(path)
        )
        parent_unchanged = same_snapshot(before_parent, after_parent)
        allowed_tools = WORK_TOOLS if args.mode == "work" else READ_ONLY_TOOLS
        parsed = parse_pi(process["stdout"], allowed_tools)
        final_text, text_truncated = bounded_text(redact_text(parsed["final_text"]), MAX_RESULT_BYTES)
        errors = list(parsed["errors"])
        if process["stderr"] and process["exit_code"] != 0:
            errors.append(redact_text(decode(process["stderr"]))[-2000:])
        if process["timed_out"]:
            errors.append("backend timed out and its process group was terminated")
        if parsed["invalid_lines"]:
            errors.append("stdout contained malformed or blank JSONL lines")
        if parsed["parse_truncated"]:
            errors.append("stdout exceeded the JSONL parser safety limit")
        if changed_public and args.mode != "work":
            errors.append("backend changed the sanitized workspace")
        if args.mode == "work":
            unsafe_changes = []
            for relative in changed_public:
                changed_path = public_root / relative
                if is_sensitive_path(relative):
                    unsafe_changes.append(relative)
                elif changed_path.is_symlink() and not is_within(
                    Path(os.path.realpath(changed_path)), public_root
                ):
                    unsafe_changes.append(relative)
            if unsafe_changes:
                errors.append(
                    "work changed denied sensitive or escaping paths: "
                    + ", ".join(unsafe_changes)
                )
        if not parent_unchanged:
            errors.append("parent repository changed during delegation")
        if parsed["forbidden_tools"]:
            errors.append("forbidden tools were requested: " + ", ".join(parsed["forbidden_tools"]))
        if text_truncated:
            errors.append("result exceeded the 12 KiB summary limit")
        work_patch_path: Optional[Path] = None
        work_patch_truncated = False
        if args.mode == "work":
            work_patch_path = artifact_dir / "work.patch"
            patch_text, work_patch_truncated = workspace_diff(root, public_root, changed_public)
            work_patch_path.write_text(patch_text, encoding="utf-8")
            if work_patch_truncated:
                errors.append("work patch exceeded the 32 KiB patch limit")
        success = (
            process["exit_code"] == 0
            and not process["timed_out"]
            and parsed["terminal"]
            and bool(parsed["final_text"].strip())
            and not errors
        )
        result = {
            "status": "success" if success else "failed",
            "backend": "pi",
            "mode": args.mode,
            "model": model,
            "exit_code": process["exit_code"],
            "terminal_state": "completed" if parsed["terminal"] else ("timeout" if process["timed_out"] else "incomplete"),
            "duration_ms": process["duration_ms"],
            "first_event_ms": process["first_event_ms"],
            "events": parsed["events"],
            "unknown_events": parsed["unknown_events"],
            "usage": parsed["usage"],
            "final_text": final_text,
            "changed_paths": changed_public,
            "parent_worktree_unchanged": parent_unchanged,
            "incomplete_summary": text_truncated,
            "errors": errors,
            "artifacts": {
                "directory": str(artifact_dir),
                "stdout_jsonl": str(artifact_dir / "stdout.jsonl"),
                "stderr_log": str(artifact_dir / "stderr.log"),
                "packet": str(prompt_file),
            },
            "codex_verification": [
                "Check every finding against the cited file and line evidence.",
                "Run the relevant tests in Codex before integrating any suggestion.",
                (
                    "Review changed_paths in the delegated workspace and apply only an inspected patch to the parent repository."
                    if args.mode == "work"
                    else "Do not apply or trust external changes automatically."
                ),
            ],
        }
        if sandbox_profile is not None:
            result["sandbox"] = {
                "type": "macos-seatbelt",
                "write_roots": [str(public_root)],
                "profile": str(sandbox_profile),
            }
        if work_patch_path is not None:
            result["work_patch"] = {
                "path": str(work_patch_path),
                "truncated": work_patch_truncated,
            }
        return emit(result)
    except (DelegateError, OSError, UnicodeError) as exc:
        return emit({"status": "failed", "reason": str(exc)})


if __name__ == "__main__":
    sys.exit(main())
