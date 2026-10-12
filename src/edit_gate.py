#!/usr/bin/env python3
"""Hold EditGate, which denies a tool call that writes into a checkout on a protected branch, and run it for the harness named on the command line."""

import json
import os
import subprocess
import sys

from harness import HARNESSES, Harness

PROTECTED_BRANCHES = ["main", "master"]


class Checkout:
    """The Git checkout that holds a path, read from the closest folder above it that exists."""

    def __init__(self, path: str) -> None:
        """Find the closest existing folder above `path`, which may not exist yet.

        Args:
            path: A file the tool call would write.
        """
        folder = os.path.dirname(path)
        while folder and not os.path.isdir(folder):
            folder = os.path.dirname(folder)
        self.folder = folder

    @property
    def branch(self) -> str:
        """The checkout's current branch, or "" when the folder is in no repository."""
        return subprocess.run(
            ["git", "-C", self.folder, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

    @property
    def is_protected(self) -> bool:
        """Whether the checkout is on a protected branch."""
        return self.branch in PROTECTED_BRANCHES


class EditGate:
    """The check a harness runs before each tool call, denying writes on a protected branch."""

    def __init__(self, harness: Harness) -> None:
        """Hold the harness whose tool calls the gate checks.

        Args:
            harness: The coding agent's tools and deny answer.
        """
        self.harness = harness

    def decide(self, payload: dict) -> dict | None:
        """Deny a tool call that writes into a repository on a protected branch.

        Args:
            payload: The pre-tool hook input.

        Returns:
            The harness's `deny_output`, or None when the call may go on.
        """
        if any(Checkout(path).is_protected for path in self.harness.written_files(payload)):
            return self.harness.deny_output
        return None


if __name__ == "__main__":
    gate = EditGate(HARNESSES[sys.argv[1]]())
    decision = gate.decide(json.load(sys.stdin))
    if decision is not None:
        json.dump(decision, sys.stdout)
