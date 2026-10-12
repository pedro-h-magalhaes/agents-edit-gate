"""Hold Harness, what tells coding agents apart, and one subclass per agent the edit gate supports."""

import os
from abc import ABC, abstractmethod
from typing import ClassVar

from shell_command import ShellCommand

DENY_MESSAGE = "This repository is on the main branch."


class Harness(ABC):
    """A coding agent, as its tool names and its deny answer tell it apart."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name its hooks file passes to `edit_gate.py`."""

    @property
    @abstractmethod
    def file_tools(self) -> list[str]:
        """The tools that write the file they name."""

    @property
    @abstractmethod
    def shell_tools(self) -> list[str]:
        """The tools that run a shell command."""

    @property
    @abstractmethod
    def deny_output(self) -> dict:
        """What the hook prints to deny a tool call."""

    def written_files(self, payload: dict) -> list[str]:
        """List the files a tool call would write.

        Args:
            payload: The pre-tool hook input.

        Returns:
            Every file a shell command writes, against its folder; the file a file
            tool names; or nothing for any other tool.
        """
        tool_input = payload["tool_input"]
        if payload["tool_name"] in self.shell_tools:
            return [
                os.path.join(self.command_folder(payload), path)
                for command in ShellCommand.parse_all(tool_input["command"])
                for path in command.written_files
            ]
        if payload["tool_name"] in self.file_tools:
            return [self.file_path(tool_input)]
        return []

    def command_folder(self, payload: dict) -> str:
        """Return the folder a shell command runs in."""
        return payload["cwd"]

    def file_path(self, tool_input: dict) -> str:
        """Return the file a file tool writes."""
        return tool_input["file_path"]


class ClaudeCode(Harness):
    """Claude Code's writing tools and deny answer, and its notebook path."""

    name: ClassVar[str] = "claude_code"
    file_tools: ClassVar[list[str]] = ["Edit", "Write", "NotebookEdit"]
    shell_tools: ClassVar[list[str]] = ["Bash"]
    deny_output: ClassVar[dict] = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": DENY_MESSAGE,
        }
    }

    def file_path(self, tool_input: dict) -> str:
        """Return the file a file tool writes, read from `notebook_path` for NotebookEdit."""
        return tool_input.get("file_path") or tool_input["notebook_path"]


class Cursor(Harness):
    """Cursor's writing tools and deny answer, and its shell folder."""

    name: ClassVar[str] = "cursor"
    file_tools: ClassVar[list[str]] = ["Write", "Delete"]
    shell_tools: ClassVar[list[str]] = ["Shell"]
    deny_output: ClassVar[dict] = {"permission": "deny", "agent_message": DENY_MESSAGE}

    def command_folder(self, payload: dict) -> str:
        """Return the folder a shell command runs in, or the first workspace root when `cwd` is empty."""
        return payload.get("cwd") or payload["workspace_roots"][0]


HARNESSES = {harness.name: harness for harness in Harness.__subclasses__()}
