import json

# Claude settings payload to pass to the --settings flag.
DEFAULT_SETTINGS = {
    "autoMemoryEnabled": False,  # Memory is not loaded and not saved
    "alwaysThinkingEnabled": False,
    "permissions": {
        "blockReadsOutsideWorkingDirectories": True,
    },
    "sandbox": {
        "enabled": True,
        "allowUnsandboxedCommands": False,
        "failIfUnavailable": True,
    },
}

# Fixed flags to pass to every Claude Code session a test starts.
DEFAULT_FLAGS = {
    "--verbose": True,
    "--strict-mcp-config": True,
    "--settings": json.dumps(DEFAULT_SETTINGS),  # JSON string of the settings payload.
    "--mcp-config": json.dumps({"mcpServers": {}}),
    "--setting-sources": "project",
    "--model": "haiku",
    "--effort": "low",
    "--permission-mode": "acceptEdits",
    "--output-format": "stream-json",
    "--max-turns": 10,
    "--max-budget-usd": 0.1
}


class ClaudeCommand:
    """Build the `claude -p` command for one test session."""

    def __init__(self, prompt, **flags):
        """Hold the prompt and the flags.

        Args:
            prompt: The user's request.
            flags: Flag name to value, over DEFAULT_FLAGS; None or False drops a flag.
        """
        self.prompt = prompt
        self.flags = {**DEFAULT_FLAGS, **flags}
        self._check_max_turns()

    def argv(self):
        """List the command's arguments, starting with `claude -p <prompt>`.

        True adds the flag on its own, False and None leave it out, and any
        other value goes after the flag as text.

        Returns:
            The command as a list of strings.
        """
        args = ["claude", "-p", self.prompt]
        for flag, value in self.flags.items():
            if value is True: # Trues adds flags without arguments.
                args.append(flag)
            elif value is False or value is None: # False and None leave flags out.
                continue
            else: 
                args += [flag, str(value)]
        return args

    def _check_max_turns(self):
        """Check that the max turns flag is not set to a negative number."""
        if self.flags.get("--max-turns") is None:
            raise ValueError("Without --max-turns, the session can run forever.")