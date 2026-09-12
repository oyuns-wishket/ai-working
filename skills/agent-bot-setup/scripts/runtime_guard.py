#!/usr/bin/env python3
"""Render a pinned native permission profile or probe it without auth/model calls.

Python 3.9+. command/exec is operator-only; never expose it in a chat adapter.
"""

import argparse
import hashlib
import http.server
import json
import os
import selectors
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

PROFILE = "agent-readonly"
MANIFEST = "SOURCE_MANIFEST.json"


def native_path(path):
    path = Path(path)
    if not path.is_absolute() or not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError("native binary must be an existing absolute executable")
    resolved = path.resolve()
    with resolved.open("rb") as handle:
        magic = handle.read(4)
    if magic not in (
        b"\x7fELF",
        b"\xcf\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xca\xfe\xba\xbe",
    ):
        raise ValueError("use the native executable, not a shell/Node wrapper")
    return resolved


def verify_projection(path):
    root = Path(path)
    if (
        not root.is_absolute()
        or root.is_symlink()
        or not root.is_dir()
        or root.resolve() == Path("/")
    ):
        raise ValueError("an absolute, dedicated projection directory is required")
    root = root.resolve()
    manifest = root / MANIFEST
    if (
        manifest.is_symlink()
        or not manifest.is_file()
        or manifest.stat().st_size > 4 * 1024 * 1024
    ):
        raise ValueError("regular bounded source manifest required")
    document = json.loads(manifest.read_text())
    if not isinstance(document, dict):
        raise TypeError("manifest must be a JSON object")
    expected = document.get("files")
    if not isinstance(expected, dict) or not 1 <= len(expected) <= 10000:
        raise ValueError("manifest must list 1..10000 source files")
    actual = {}
    for parent, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            entry = Path(parent) / name
            mode = entry.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ValueError("projection symlinks and special files are forbidden")
        for name in files:
            entry = Path(parent) / name
            relative = entry.relative_to(root).as_posix()
            if relative == MANIFEST:
                continue
            if len(actual) >= 10000 or entry.stat().st_size > 16 * 1024 * 1024:
                raise ValueError("projection exceeds verification limits")
            with entry.open("rb") as handle:
                digest = hashlib.sha256()
                for chunk in iter(lambda: handle.read(65536), b""):
                    digest.update(chunk)
                actual[relative] = digest.hexdigest()
    if actual != expected:
        raise ValueError("manifest mismatch: rebuild and review the projection")
    return root


def permission_config(workspace, binary):
    """Host-owned immutable paths only. Kept shared by render and real OS probe."""
    lines = [
        'approval_policy = "never"',
        f'default_permissions = "{PROFILE}"',
        'cli_auth_credentials_store = "file"',
        'web_search = "disabled"',
        "project_doc_max_bytes = 0",
        "",
        "[shell_environment_policy]",
        'inherit = "none"',
        "include_only = []",
        'set = { PATH = "/usr/bin:/bin", LANG = "C.UTF-8" }',
        "",
        "[features]",
    ]
    disabled = (
        "hooks",
        "apps",
        "plugins",
        "remote_plugin",
        "multi_agent",
        "multi_agent_v2",
        "shell_snapshot",
        "skill_search",
        "skill_mcp_dependency_install",
    )
    lines.extend(f"{feature} = false" for feature in disabled)
    lines.extend(
        [
            "skip_host_skill_discovery = true",
            "",
            f"[permissions.{PROFILE}.filesystem]",
            '":root" = "deny"',
            '":minimal" = "read"',
            f'{json.dumps(str(workspace))} = "read"',
            f'{json.dumps(str(binary))} = "read"',
            "",
            f"[permissions.{PROFILE}.network]",
            "enabled = false",
            "",
        ]
    )
    return "\n".join(lines)


def runtime_environment(private_home):
    return {
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "HOME": str(private_home),
        "CODEX_HOME": str(private_home),
    }


def render(workspace, binary, output):
    root, executable = verify_projection(workspace), native_path(binary)
    target = Path(output)
    if not target.is_absolute() or target.name != "config.toml":
        raise ValueError("output must be an absolute private config.toml path")
    parent = target.parent.resolve()
    if parent == root or parent.is_relative_to(root) or root.is_relative_to(parent):
        raise ValueError("private state and projection must be disjoint directories")
    if not parent.is_dir() or parent.stat().st_mode & 0o077:
        raise ValueError(
            "create a separate private state directory with mode 0700 first"
        )
    if executable.is_relative_to(parent):
        raise ValueError("native executable must be outside private state")
    # O_EXCL refuses existing files AND dangling symlinks; never mutate a config.
    fd = os.open(parent / target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(permission_config(root, executable))
    return parent / target.name


class NativeProbe:
    def __init__(self, binary, workspace, private_home):
        env = runtime_environment(private_home)
        env["BOT_SECRET_FIXTURE"] = "SYNTHETIC_PARENT_CREDENTIAL"
        self.process = subprocess.Popen(
            [str(binary), "app-server", "--strict-config"],
            cwd=workspace,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.buffer, self.sequence = b"", 0
        self.workspace = workspace

    def close(self):
        # Reap the leader and kill its owned group even if the leader exited first.
        failures = []
        try:
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(self.process.pid, sig)
                except ProcessLookupError:
                    pass
                except OSError as error:
                    failures.append(type(error).__name__)
                try:
                    self.process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    pass
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                failures.append("leader_still_running")
        finally:
            self.selector.close()
            self.process.stdin.close()
            self.process.stdout.close()
        if failures:
            raise RuntimeError("owned process cleanup failed")

    def request(self, method, params):
        self.sequence += 1
        payload = {"id": self.sequence, "method": method, "params": params}
        self.process.stdin.write(json.dumps(payload).encode() + b"\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                event = json.loads(line)
                if "method" in event and "id" in event:
                    raise RuntimeError(
                        "unexpected server request; no approvals allowed"
                    )
                if event.get("id") == self.sequence:
                    if "error" in event:
                        raise RuntimeError("native RPC rejected probe request")
                    return event["result"]
            if self.selector.select(timeout=0.25):
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk or len(self.buffer) + len(chunk) > 1024 * 1024:
                    raise RuntimeError("native protocol ended or exceeded frame limit")
                self.buffer += chunk
        raise TimeoutError("native probe deadline exceeded")

    def command(self, script):
        return self.request(
            "command/exec",
            {
                "command": ["/bin/sh", "-c", script],
                "cwd": str(self.workspace),
                "permissionProfile": PROFILE,
                "timeoutMs": 5000,
            },
        )


def probe(binary):
    executable = native_path(binary)
    checks, skipped = {}, []
    with tempfile.TemporaryDirectory(prefix="agent-bot-guard-") as temporary:
        root = Path(temporary).resolve()
        source, private = root / "source", root / "private"
        source.mkdir()
        private.mkdir(mode=0o700)
        version = subprocess.run(
            [str(executable), "--version"],
            capture_output=True,
            env=runtime_environment(private),
            timeout=10,
            check=True,
        )
        version_text = version.stdout.decode().strip()
        if not version_text:
            raise ValueError("native binary did not report a version")
        allowed = source / "read.txt"
        allowed.write_text("ALLOWED_SOURCE_FIXTURE")
        (source / MANIFEST).write_text(
            json.dumps(
                {
                    "files": {
                        "read.txt": hashlib.sha256(allowed.read_bytes()).hexdigest(),
                    }
                }
            )
        )
        render(source, executable, private / "config.toml")
        features = subprocess.run(
            [str(executable), "features", "list"],
            cwd=source,
            env=runtime_environment(private),
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        feature_values = {
            parts[0]: parts[-1]
            for line in features.stdout.splitlines()
            if len(parts := line.split()) >= 3
        }
        checks["native_hooks_disabled"] = feature_values.get("hooks") == "false"
        # Deliberately insert a malicious link AFTER render to exercise OS enforcement.
        secret = root / "outside.txt"
        secret.write_text("DENIED_OUTSIDE_FIXTURE")
        auth = private / "auth-fixture.txt"
        auth.write_text("DENIED_AUTH_FIXTURE")
        (source / "escape").symlink_to(secret)
        hits = []

        class Listener(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(True)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"fixture")

            def log_message(self, *_args):
                pass

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Listener)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        client = None
        try:
            url = f"http://127.0.0.1:{server.server_port}/"
            # Bypass host HTTP proxies; test only this owned local listener.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(url, timeout=2) as response:
                checks["network_fixture_reachable_from_host"] = (
                    response.read() == b"fixture"
                )
            hits.clear()
            client = NativeProbe(executable, source, private)
            client.request(
                "initialize",
                {
                    "clientInfo": {"name": "agent_bot_guard", "version": "1"},
                    "capabilities": {"experimentalApi": True},
                },
            )
            client.process.stdin.write(b'{"method":"initialized"}\n')
            client.process.stdin.flush()
            result = client.command("/bin/cat read.txt")
            checks["allowed_read"] = (
                result["exitCode"] == 0
                and result["stdout"].strip() == "ALLOWED_SOURCE_FIXTURE"
            )
            # curl must actually exist and run; command-not-found is not a network proof.
            result = client.command("/usr/bin/curl --version")
            checks["network_client_available"] = (
                result["exitCode"] == 0 and "curl" in result["stdout"]
            )
            commands = {
                "outside_read_denied": "/bin/cat " + shlex.quote(str(secret)),
                "private_state_denied": "/bin/cat " + shlex.quote(str(auth)),
                "symlink_escape_denied": "/bin/cat escape",
                "create_denied": "echo changed > new.txt",
                "overwrite_denied": "echo changed > read.txt",
                "network_denied": f"/usr/bin/curl --noproxy '*' --connect-timeout 1 --max-time 2 {url}",
            }
            proc_file = Path(f"/proc/{client.process.pid}/environ")
            if sys.platform.startswith("linux"):
                checks["proc_fixture_exists"] = proc_file.is_file()
                commands["proc_environment_denied"] = "/bin/cat " + str(proc_file)
            else:
                skipped.append("proc_environment: no Linux procfs on this platform")
            for name, script in commands.items():
                result = client.command(script)
                leaked = any(
                    marker in result["stdout"]
                    for marker in (
                        "DENIED_OUTSIDE_FIXTURE",
                        "DENIED_AUTH_FIXTURE",
                        "SYNTHETIC_PARENT_CREDENTIAL",
                    )
                )
                checks[name] = result["exitCode"] != 0 and not leaked
            result = client.command("/usr/bin/env")
            checks["parent_credential_filtered"] = (
                result["exitCode"] == 0
                and "SYNTHETIC_PARENT_CREDENTIAL" not in result["stdout"]
            )
            checks["network_no_request_received"] = not hits
            checks["source_unchanged"] = allowed.read_text() == "ALLOWED_SOURCE_FIXTURE"
            checks["no_file_created"] = not (source / "new.txt").exists()
        finally:
            try:
                if client:
                    client.close()
            finally:
                server.shutdown()
                server.server_close()
                server_thread.join(timeout=2)
        if client:
            try:
                os.killpg(client.process.pid, 0)
                checks["owned_process_group_gone"] = False
            except ProcessLookupError:
                checks["owned_process_group_gone"] = True
    return {
        "passed": all(checks.values()),
        "version": version_text,
        "model_calls": 0,
        "checks": checks,
        "skipped": skipped,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    render_parser = sub.add_parser("render")
    render_parser.add_argument("--workspace", required=True, type=Path)
    render_parser.add_argument("--output", required=True, type=Path)
    render_parser.add_argument("--binary", required=True, type=Path)
    probe_parser = sub.add_parser("probe")
    probe_parser.add_argument("--binary", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == "render":
            result = {"config": str(render(args.workspace, args.binary, args.output))}
        else:
            result = probe(args.binary)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("passed", True) else 1
    except (
        OSError,
        ValueError,
        TypeError,
        RuntimeError,
        subprocess.SubprocessError,
    ) as error:
        # No raw RPC/stderr/token output. Only operator errors from this script.
        print(
            json.dumps({"passed": False, "error": type(error).__name__}),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
