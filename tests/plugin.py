"""Hold PluginHook, the pre-tool hook a harness's plugin registers, as edit gate tests read and run it."""

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

PLUGIN = Path(__file__).parents[1]


@dataclass
class PluginHook:
    """The one pre-tool hook a plugin manifest registers."""

    command: str
    matcher: str

    @classmethod
    def read(cls, manifest_folder, event):
        """Read the hook a manifest registers for `event`.

        Claude Code nests the command under the matcher; Cursor puts both side by side.

        Args:
            manifest_folder: The manifest's folder in the plugin, such as `.cursor-plugin`.
            event: The harness's name for the pre-tool event.

        Returns:
            The hook's command and matcher.
        """
        manifest = _read_json(PLUGIN / manifest_folder / "plugin.json")
        [entry] = _read_json(PLUGIN / manifest["hooks"])["hooks"][event]
        [command] = [hook["command"] for hook in entry.get("hooks", [entry])]
        return cls(command=command, matcher=entry["matcher"])

    def tools_missed(self, harness):
        """List the harness's writing tools the matcher does not match.

        Args:
            harness: The Harness whose file and shell tools have to match.

        Returns:
            The tools the hook would skip; empty when it catches them all.
        """
        writing_tools = [*harness.file_tools, *harness.shell_tools]
        return [tool for tool in writing_tools if not re.fullmatch(self.matcher, tool)]

    def run(self, payload):
        """Run the command as the harness does and return its decision.

        Sends `payload` as JSON on stdin, with the plugin root in both harnesses'
        variables, and fails the test when the command exits with an error or
        prints something that is not JSON.

        Args:
            payload: The hook input, as a dict.

        Returns:
            The decision the command printed as JSON, or None when it printed nothing.
        """
        plugin_root = {"CLAUDE_PLUGIN_ROOT": str(PLUGIN), "CURSOR_PLUGIN_ROOT": str(PLUGIN)}
        result = subprocess.run(
            self.command,
            shell=True,
            env={**os.environ, **plugin_root},
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        if not result.stdout:
            return None
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"The hook printed something that is not JSON: {result.stdout!r}")


def _read_json(path):
    return json.loads(path.read_text())
