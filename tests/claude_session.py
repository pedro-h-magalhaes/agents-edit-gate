"""Hold Session and the run_claude fixture, which run one Claude Code session for a test and read it.

Load it with `pytest_plugins = ["claude_session"]` in the top conftest.
"""

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

import pytest
from claude_command import ClaudeCommand

SESSION_DIR = "session"


@dataclass
class Session:
    """Hold one session's stream-json events and folder, and read the session's details from the events."""

    events: list
    folder: Path

    @property
    def start(self):
        """The session's init event; an empty dict when there is none."""
        return next((event for event in self.events if event.get("subtype") == "init"), {})

    @property
    def end(self):
        """The session's result event; an empty dict when it was stopped before one."""
        return next((event for event in reversed(self.events) if event.get("type") == "result"), {})

    @property
    def id(self):
        """The session's id, or None when there is no init event."""
        return self.start.get("session_id")

    @property
    def reply(self):
        """The text the session ended on; an empty string when there is none."""
        return self.end.get("result") or ""

    @property
    def plugins(self):
        """The names of the plugins the session loaded."""
        return [plugin["name"] for plugin in self.start.get("plugins", [])]

    @property
    def tool_calls(self):
        """Every tool call the session made, in order, as `{"name": ..., "input": ...}`."""
        return [{"name": block["name"], "input": block["input"]} for block in self._blocks_of("tool_use")]

    def tried(self, tool_names):
        """Tell whether the session called any of `tool_names`.

        Args:
            tool_names: The tools to look for.

        Returns:
            True when at least one call used one of them.
        """
        return any(call["name"] in tool_names for call in self.tool_calls)

    def answered(self, tool_names):
        """Tell whether a call to any of `tool_names` already has its result.

        Args:
            tool_names: The tools to look for.

        Returns:
            True when a tool_result answers a call to one of them.
        """
        asked = {block["id"] for block in self._blocks_of("tool_use") if block["name"] in tool_names}
        return any(block["tool_use_id"] in asked for block in self._blocks_of("tool_result"))

    def _blocks_of(self, block_type):
        return [block for event in self.events for block in _blocks(event) if block.get("type") == block_type]


@pytest.fixture
def run_claude(tmp_path, request):
    """Provide `run`, which runs one Claude Code session for the test and returns it as a Session.

    `run` runs `claude -p` in the session's folder and prints the transcript and
    a summary. It works once per test.

    `run` takes:
        prompt: The user's request.
        folder: An existing folder to run in; None creates one under the test's
            tmp_path, kept afterwards.
        files: `{path: content}` to write into the created folder.
        stop_after: Tool names; the session ends once one of them has its result.
        flags: Flag name to value for ClaudeCommand, over its defaults.

    Returns:
        `run`.
    """

    def run(prompt, folder=None, files=None, stop_after=(), flags=None):
        session = Session([], folder or _set_up_folder(tmp_path / SESSION_DIR, files or {}))
        command = ClaudeCommand(prompt, **(flags or {})).argv()
        seconds = _run_session(command, session, stop_after, request.node.name)
        _print_summary(session, request.node.name, seconds)
        return session

    return run


def _set_up_folder(folder, files):
    """Create the session's folder with the test's files.

    Args:
        folder: The folder to create; it must not exist yet.
        files: `{path: content}` to write into it.

    Returns:
        `folder`.
    """
    folder.mkdir()
    _write_files(folder, files)
    return folder


def _run_session(command, session, stop_after, test_name):
    """Print the test's name, then run the session and time it.

    Args:
        command: The `claude -p` command.
        session: The Session to fill with the events, in its folder.
        stop_after: As `run` takes it.
        test_name: The name printed before the transcript.

    Returns:
        The session's wall time in seconds.
    """
    print(f"\n--- {test_name}", flush=True)
    start = time.monotonic()
    _read_events(command, session, stop_after)
    return time.monotonic() - start


def _write_files(root, files):
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _read_events(command, session, stop_after):
    """Run `command` in the session's folder, add each stream-json event to it and print a readable line for each block.

    The session ends early once a tool in `stop_after` has its result.

    Args:
        command: The `claude -p` command.
        session: The Session to fill.
        stop_after: Tool names; empty lets the session run to its end.
    """
    process = subprocess.Popen(
        command, cwd=session.folder, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True
    )
    try:
        for line in process.stdout:
            if not line.strip():
                continue
            session.events.append(json.loads(line))
            for transcript_line in _transcript_lines(session.events[-1]):
                print(transcript_line, flush=True)
            if stop_after and session.answered(stop_after):
                break
    finally:
        process.terminate()
        process.wait()


def _blocks(event):
    """List the content blocks of a message event.

    Args:
        event: One stream-json event.

    Returns:
        The blocks of an assistant or user message; empty for any other event, or
        when the message's content is plain text.
    """
    if event.get("type") not in ("assistant", "user"):
        return []
    content = event["message"]["content"]
    return content if isinstance(content, list) else []


def _print_summary(session, test_name, seconds):
    lines = [
        f"\n--- session {session.id} ({test_name})",
        f"folder: {session.folder}",
        _setup_line(session.start),
        _ending_line(session.end),
        _time_and_cost_line(session.end, seconds),
        _tokens_line(_token_usage(session.events, session.end)),
    ]
    print("\n".join(lines))


def _setup_line(start):
    return (
        f"model: {start.get('model')}; permissions: {start.get('permissionMode')}; "
        f"output style: {start.get('output_style')}"
    )


def _ending_line(end):
    if not end:
        return "ended: stopped early, after stop_after"
    return f"ended: {end['subtype']} after {end['num_turns']} turns"


def _time_and_cost_line(end, seconds):
    parts = [f"wall time {seconds:.1f}s"]
    if end:
        parts.append(f"API time {end.get('duration_api_ms', 0) / 1000:.1f}s")
        parts.append(f"API-equivalent cost ${end.get('total_cost_usd', 0):.4f}")
    return "; ".join(parts)


def _tokens_line(tokens):
    return (
        f"tokens: input {tokens['input']}, cache write {tokens['cache write']}, "
        f"cache read {tokens['cache read']}, output {tokens['output']}"
    )


def _token_usage(events, result):
    keys = {
        "input": "input_tokens",
        "cache write": "cache_creation_input_tokens",
        "cache read": "cache_read_input_tokens",
        "output": "output_tokens",
    }
    if result.get("usage"):
        usages = [result["usage"]]
    else:
        by_message = {}
        for event in events:
            if event.get("type") == "assistant" and event["message"].get("usage"):
                by_message[event["message"].get("id")] = event["message"]["usage"]
        usages = by_message.values()
    totals = dict.fromkeys(keys, 0)
    for usage in usages:
        for name, key in keys.items():
            totals[name] += usage.get(key) or 0
    return totals


def _transcript_lines(event):
    lines = []
    for block in _blocks(event):
        line = _transcript_line(block)
        if line:
            lines.append(line)
    return lines


def _transcript_line(block):
    match block.get("type"):
        case "thinking":
            return f"[thinking] {block.get('thinking') or '(empty)'}"
        case "redacted_thinking":
            return "[thinking] (redacted)"
        case "text":
            return f"[assistant] {block['text']}"
        case "tool_use":
            return f"[tool] {block['name']} {json.dumps(block['input'])[:200]}"
        case "tool_result":
            label = "error" if block.get("is_error") else "result"
            return f"[{label}] {_tool_result_text(block)[:200]}"
    return None


def _tool_result_text(block):
    content = block.get("content") or ""
    if isinstance(content, list):
        return " ".join(part.get("text", "") for part in content)
    return content
