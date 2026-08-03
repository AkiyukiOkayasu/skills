#!/usr/bin/env python3
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import delegate_agent  # noqa: E402


class DelegateAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="delegate-agent-test-")
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.run_cmd(["git", "init", "-q"])
        self.run_cmd(["git", "config", "user.name", "Delegate Test"])
        self.run_cmd(["git", "config", "user.email", "delegate@example.invalid"])
        (self.root / "safe.txt").write_text("safe\n", encoding="utf-8")
        (self.root / ".env").write_text("API_KEY=must-not-copy\n", encoding="utf-8")
        self.run_cmd(["git", "add", "safe.txt", ".env"])
        self.run_cmd(["git", "commit", "-qm", "fixture"])
        self.bin = Path(self.temp.name) / "bin"
        self.bin.mkdir()
        self.fake_pi = self.bin / "pi"
        self.fake_pi.write_text(
            "#!/bin/sh\n"
            "if [ \"$1\" = \"--version\" ]; then echo 0.83.0; exit 0; fi\n"
            "if [ \"$1\" = \"--list-models\" ]; then echo 'opencode-go deepseek-v4-flash'; exit 0; fi\n"
            "if [ \"${FAKE_BAD:-0}\" = 1 ]; then\n"
            "  printf '%s\\n' '{\"type\":\"tool_execution_start\",\"toolName\":\"edit\"}'\n"
            "fi\n"
            "printf '%s\\n' '{\"type\":\"message_end\",\"message\":{\"role\":\"assistant\",\"content\":[{\"type\":\"text\",\"text\":\"READY\"}]}}'\n"
            "printf '%s\\n' '{\"type\":\"agent_end\"}'\n",
            encoding="utf-8",
        )
        self.fake_pi.chmod(0o755)
        self.old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = str(self.bin) + os.pathsep + self.old_path
        os.environ["OPENCODE_API_KEY"] = "test-only"

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        os.environ.pop("OPENCODE_API_KEY", None)
        os.environ.pop("FAKE_BAD", None)
        self.temp.cleanup()

    def run_cmd(self, argv):
        return subprocess.run(argv, cwd=self.root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def call(self, *extra):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = delegate_agent.main(
                [
                    "--backend",
                    "pi",
                    "--mode",
                    "explore",
                    "--repo",
                    str(self.root),
                    "--goal",
                    "Return a smoke-test result",
                    "--acceptance",
                    "Return READY without changes",
                    *extra,
                ]
            )
        return code, json.loads(output.getvalue())

    def test_read_only_delegation_uses_sanitized_copy(self):
        code, result = self.call("--output-dir", str(Path(self.temp.name) / "artifact"))
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["parent_worktree_unchanged"])
        self.assertEqual(result["changed_paths"], [])
        workspace = Path(result["artifacts"]["directory"]) / "workspace"
        self.assertTrue((workspace / "safe.txt").is_file())
        self.assertFalse((workspace / ".env").exists())

    def test_forbidden_tool_fails_closed(self):
        os.environ["FAKE_BAD"] = "1"
        code, result = self.call()
        self.assertNotEqual(code, 0)
        self.assertEqual(result["status"], "failed")
        self.assertIn("edit", json.dumps(result))

    def test_pi_contract_requires_agent_end(self):
        raw = b"\n".join(
            [
                b'{"type":"session","version":3}',
                b'{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"READY"}]}}',
            ]
        )
        parsed = delegate_agent.parse_pi(raw, {"read", "grep", "find", "ls"})
        self.assertFalse(parsed["terminal"])
        self.assertEqual(parsed["final_text"], "READY")

    def test_synthetic_smoke_probe(self):
        probe = delegate_agent.smoke_probe("opencode-go/deepseek-v4-flash", 10)
        self.assertTrue(probe["success"], probe)

    def test_work_requires_explicit_opt_in(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = delegate_agent.main(
                [
                    "--mode",
                    "work",
                    "--goal",
                    "change",
                    "--acceptance",
                    "test",
                ]
            )
        self.assertNotEqual(code, 0)
        self.assertIn("--allow-work", json.loads(output.getvalue())["reason"])

    def test_pi_is_the_only_backend(self):
        self.assertEqual(delegate_agent.parse_args(["--mode", "explore"]).backend, "pi")
        self.assertEqual(delegate_agent.DEFAULT_MODEL, "opencode-go/deepseek-v4-flash")


if __name__ == "__main__":
    unittest.main()
