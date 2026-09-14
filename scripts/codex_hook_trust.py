#!/usr/bin/env python3
"""Inspect native Codex hook trust; --apply trusts only reviewed manifest matches.

Uses hooks/list's currentHash, never guesses the native hash or bypasses trust.
No thread, turn, tool, or hook is started by this helper. Existing disabled hooks
and hooks outside the manifest are left untouched unless an explicit local UI
allowlist requests restoration of an already-trusted unchanged definition.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import selectors
import subprocess
import sys
import time


class NativeError(RuntimeError):
    pass


class NativeClient:
    def __init__(self, binary="codex", *, env=None, cwd=None, timeout=15):
        self.timeout = timeout
        self.serial = 0
        self.buffer = b""
        try:
            self.process = subprocess.Popen(
                [binary, "app-server", "--stdio"], env=env, cwd=cwd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            raise NativeError("Codex app-server could not start; check the installed CLI.") from error
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        try:
            self.request("initialize", {
                "clientInfo": {"name": "ai-working-hook-trust", "version": "1"},
                "capabilities": {"experimentalApi": True},
            })
            self._send({"method": "initialized", "params": {}})
        except Exception:
            self.close()
            raise

    def _send(self, value):
        try:
            self.process.stdin.write((json.dumps(value) + "\n").encode())
            self.process.stdin.flush()
        except (OSError, BrokenPipeError) as error:
            raise NativeError("Codex app-server closed before responding.") from error

    def request(self, method, params):
        self.serial += 1
        request_id = self.serial
        self._send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if b"\n" not in self.buffer:
                if not self.selector.select(max(0, deadline - time.monotonic())):
                    break
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise NativeError("Codex app-server ended without a response.")
                self.buffer += chunk
                if len(self.buffer) > 8 * 1024 * 1024:
                    raise NativeError("Codex app-server response exceeded the bounded size.")
                continue
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                response = json.loads(line)
            except (ValueError, UnicodeDecodeError) as error:
                raise NativeError("Codex app-server returned invalid JSON.") from error
            if response.get("id") != request_id:
                continue
            if "error" in response:
                # Do not expose config contents or native error payloads.
                raise NativeError(f"Native {method} failed (code {response['error'].get('code')}); no fallback trust override was attempted.")
            if "result" not in response:
                raise NativeError(f"Native {method} returned an unsupported response.")
            return response["result"]
        raise NativeError(f"Native {method} timed out.")

    def close(self):
        self.selector.close()
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        self.process.stdin.close()
        self.process.stdout.close()


def fingerprint(hook):
    return tuple(hook.get(k) for k in (
        "eventName", "matcher", "handlerType", "command", "timeoutSec",
        "additionalContextLimit", "statusMessage", "async",
    ))


def native_manifest(shared):
    """Apply the same Codex-only fields as bootstrap's shared manifest renderer."""
    native = json.loads(json.dumps(shared))
    for event, records in native["hooks"].items():
        for record in records:
            if event == "SessionEnd":
                record["matcher"] = "other"
            for hook in record["hooks"]:
                if event == "SessionStart":
                    hook["additionalContextLimit"] = 10000
                elif event == "UserPromptSubmit":
                    hook["additionalContextLimit"] = 1200
    return native


def manifest_fingerprints(manifest):
    result = Counter()
    for event, groups in manifest["hooks"].items():
        for group in groups:
            for handler in group["hooks"]:
                if handler.get("type") != "command":
                    raise NativeError("The managed manifest must contain command hooks only.")
                command = handler.get("command", "")
                # Review is scoped to ai-working installed hook programs, never
                # arbitrary plugin/UI commands accidentally added to a manifest.
                if not re.fullmatch(r'(?:node|bash|sh) (?:"\$HOME/\.(?:claude|agents|codex)/hooks/[\w.-]+"|\$HOME/\.(?:claude|agents|codex)/hooks/[\w.-]+)', command):
                    raise NativeError("The manifest contains a command outside owned hook paths.")
                timeout = handler.get("timeout", 1 if event in ("SessionEnd", "Interrupt") else 600)
                if event in ("SessionEnd", "Interrupt"):
                    timeout = min(3, max(1, timeout))
                result[fingerprint({
                    "eventName": event[0].lower() + event[1:],
                    "matcher": group.get("matcher"), "handlerType": "command",
                    "command": command, "timeoutSec": timeout,
                    "additionalContextLimit": handler.get("additionalContextLimit"),
                    "statusMessage": handler.get("statusMessage"),
                    "async": handler.get("async", False),
                })] += 1
    return result


def list_hooks(client, cwd):
    response = client.request("hooks/list", {"cwds": [str(cwd)]})
    entries = response.get("data", [])
    if len(entries) != 1 or entries[0].get("errors"):
        raise NativeError("Native hook discovery failed; inspect hooks/list errors before trusting.")
    return entries[0]


def select_owned(entry, expected, hooks_file):
    selected, others = [], []
    remaining = expected.copy()
    for hook in entry["hooks"]:
        own_source = Path(hook["sourcePath"]).resolve() == hooks_file.resolve()
        signature = fingerprint(hook)
        if own_source and not hook.get("isManaged") and remaining[signature] > 0:
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", hook.get("currentHash", "")):
                raise NativeError("Native hook hash format is unsupported.")
            remaining[signature] -= 1
            selected.append(hook)
        else:
            others.append(hook)
    if sum(remaining.values()):
        raise NativeError("Installed owned hooks do not exactly match the managed manifest; run bootstrap and inspect differences first.")
    return selected, others


def reviewed_ui_candidates(others, commands, local_config, hooks_file):
    """Recover positional keys only when the exact native hash was trusted before."""
    if not isinstance(commands, list) or any(not isinstance(c, str) or not c.strip() for c in commands):
        raise NativeError("Reviewed UI commands must be a JSON array of non-empty exact command strings.")
    previous = local_config.get("hooks", {}).get("state", {})
    candidates = []
    for hook in others:
        if (Path(hook["sourcePath"]).resolve() != hooks_file.resolve()
                or hook.get("isManaged") or hook.get("handlerType") != "command"
                or hook.get("command") not in commands or not hook["enabled"]
                or hook["trustStatus"] in ("trusted", "managed")):
            continue
        digest = hook.get("currentHash", "")
        prior = [value for value in previous.values() if value.get("trusted_hash") == digest]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest) or not prior:
            raise NativeError("A reviewed UI command has no previously trusted matching definition; refusing new external trust.")
        if any(value.get("enabled") is False for value in prior):
            # A prior explicit disable must survive index movement. Do not
            # reinterpret it as permission to re-enable or re-trust this hook.
            continue
        candidates.append(hook)
    return candidates


def synchronize(client, *, cwd, codex_home, manifest, apply=False, ensure_instructions=False, reviewed_ui=None):
    expected = manifest_fingerprints(manifest)
    hooks_file = codex_home / "hooks.json"
    config_file = (codex_home / "config.toml").resolve()
    source_snapshot = hooks_file.read_bytes()
    entry = list_hooks(client, cwd)
    selected, others = select_owned(entry, expected, hooks_file)
    pending = [h for h in selected if h["enabled"] and h["trustStatus"] not in ("trusted", "managed")]
    before = len(pending)
    config_snapshot = config_file.read_bytes() if config_file.exists() else b""
    config = client.request("config/read", {"cwd": str(cwd), "includeLayers": True})
    layers = [layer for layer in config.get("layers", []) if
              layer.get("name", {}).get("type") == "user" and
              Path(layer["name"]["file"]).resolve() == config_file]
    if len(layers) != 1:
        raise NativeError("Could not identify the writable native user config layer.")
    local_config = layers[0]["config"]
    fallback = local_config.get("project_doc_fallback_filenames", [])
    if not isinstance(fallback, list) or any(not isinstance(name, str) for name in fallback):
        raise NativeError("project_doc_fallback_filenames must be a string list.")
    instruction_pending = ensure_instructions and "CLAUDE.md" not in fallback
    ui_pending = reviewed_ui_candidates(others, reviewed_ui if reviewed_ui is not None else [], local_config, hooks_file)
    if apply and (pending or ui_pending or instruction_pending):
        if hooks_file.read_bytes() != source_snapshot:
            raise NativeError("Hook definitions changed during review; rerun inspection.")
        # Re-query native hashes immediately before writing, including current
        # trust/enablement so a concurrent disable is never overwritten.
        current_entry = list_hooks(client, cwd)
        select_owned(current_entry, expected, hooks_file)
        if [(h["key"], h["currentHash"], h["enabled"], h["trustStatus"]) for h in current_entry["hooks"]] != [
                (h["key"], h["currentHash"], h["enabled"], h["trustStatus"]) for h in entry["hooks"]]:
            raise NativeError("Hook state changed during review; rerun inspection.")
        edits = [{
            "keyPath": "hooks.state." + json.dumps(h["key"]) + ".trusted_hash",
            "value": h["currentHash"], "mergeStrategy": "replace",
        } for h in pending + ui_pending]
        if (config_file.read_bytes() if config_file.exists() else b"") != config_snapshot:
            raise NativeError("User config changed during review; rerun inspection.")
        if instruction_pending:
            edits.append({"keyPath": "project_doc_fallback_filenames",
                          "value": fallback + ["CLAUDE.md"], "mergeStrategy": "replace"})
        client.request("config/batchWrite", {
            "edits": edits, "filePath": str(config_file),
            "expectedVersion": layers[0]["version"], "reloadUserConfig": True,
        })
        entry = list_hooks(client, cwd)
        selected, others = select_owned(entry, expected, hooks_file)
        if hooks_file.read_bytes() != source_snapshot:
            raise NativeError("Hook definitions changed while updating trust; inspect native state.")
        if instruction_pending:
            verified = client.request("config/read", {"cwd": str(cwd), "includeLayers": True})
            user_layers = [layer for layer in verified.get("layers", []) if layer.get("name", {}).get("type") == "user"]
            if len(user_layers) != 1 or user_layers[0]["config"].get("project_doc_fallback_filenames") != fallback + ["CLAUDE.md"]:
                raise NativeError("Native verification did not confirm the preserved instruction fallback list.")
        restored = {h["key"]: h for h in others}
        if any(restored.get(h["key"], {}).get("trustStatus") != "trusted" for h in ui_pending):
            raise NativeError("Native verification did not confirm reviewed UI trust restoration.")
        if any(h["enabled"] and h["trustStatus"] != "trusted" for h in selected):
            raise NativeError("Native verification did not confirm trust for all enabled owned hooks.")
    return {
        "mode": "apply" if apply else "dry-run", "owned": len(selected),
        "updated": before if apply else 0,
        "reviewed_ui_restored": len(ui_pending) if apply else 0,
        "reviewed_ui_restorable": 0 if apply else len(ui_pending),
        "review_required": sum(h["enabled"] and h["trustStatus"] != "trusted" for h in selected),
        "disabled_owned": sum(not h["enabled"] for h in selected),
        "unmanaged_review_required": sum(h["enabled"] and h["trustStatus"] not in ("trusted", "managed") for h in others),
        "instructions_fallback": "CLAUDE.md" in fallback or (apply and instruction_pending),
        "instructions_update_required": bool(instruction_pending and not apply),
        "warnings": entry.get("warnings", []),
        "hooks": [{k: h[k] for k in ("key", "eventName", "enabled", "trustStatus")} for h in selected],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Persist native hashes for reviewed owned definitions only")
    parser.add_argument("--ensure-instructions", action="store_true", help="Also preserve/add CLAUDE.md project fallback using native config writes")
    parser.add_argument("--restore-reviewed-ui", type=Path, help="Local JSON array of exact reviewed UI commands; only reuse previously trusted hashes")
    parser.add_argument("--manifest", type=Path, help="Optional already-native manifest; default adapts global/governance-hooks.json")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--codex", default="codex", help="Installed Codex CLI executable")
    args = parser.parse_args()
    client = None
    try:
        codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()
        manifest_path = args.manifest or Path(__file__).resolve().parents[1] / "global/governance-hooks.json"
        manifest = json.loads(manifest_path.read_text())
        if args.manifest is None:
            manifest = native_manifest(manifest)
        reviewed_ui = json.loads(args.restore_reviewed_ui.read_text()) if args.restore_reviewed_ui else None
        client = NativeClient(args.codex, cwd=args.cwd)
        print(json.dumps(synchronize(client, cwd=args.cwd.resolve(), codex_home=codex_home,
                                     manifest=manifest, apply=args.apply, ensure_instructions=args.ensure_instructions,
                                     reviewed_ui=reviewed_ui), indent=2))
        return 0
    except (NativeError, OSError, ValueError, KeyError, TypeError) as error:
        print(f"Hook trust inspection failed: {error}", file=sys.stderr)
        return 1
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    sys.exit(main())
