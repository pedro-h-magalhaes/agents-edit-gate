import pytest
from plugin import PLUGIN

# Flags every edit gate session passes to ClaudeCommand, over its defaults.
SESSION_FLAGS = {
    "--plugin-dir": PLUGIN,
    "--include-hook-events": True,
}


@pytest.fixture
def run_claude(run_claude):
    """Provide `run`, which runs a session with the edit gate loaded, in `folder`.

    `run` takes the instruction, the folder and the tool names to stop after, and
    fails the test when the plugin did not load or the model never used those tools.

    Returns:
        `run`.
    """

    def run(instruction, folder, stop_after):
        prompt = f"{instruction} Do nothing else."
        session = run_claude(prompt, folder=folder, stop_after=stop_after, flags=SESSION_FLAGS)
        assert "edit-gate" in session.plugins, "the edit gate plugin did not load"
        assert session.tried(stop_after), f"the model never used {stop_after}: {session.tool_calls}"
        return session

    return run
