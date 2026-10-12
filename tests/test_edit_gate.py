from typing import ClassVar

import pytest
from git_repository import EDITED_FILE, UNPROTECTED_BRANCH
from payload import pre_tool_use

from edit_gate import EditGate
from harness import Harness


class StandIn(Harness):
    """A harness with one file tool and one shell tool, standing for any real one."""

    name: ClassVar[str] = "stand_in"
    file_tools: ClassVar[list[str]] = ["Write"]
    shell_tools: ClassVar[list[str]] = ["Shell"]
    deny_output: ClassVar[dict] = {"deny": True}


EDIT_GATE = EditGate(StandIn())

# Shell commands that write EDITED_FILE, each one a way the edit gate has to catch.
SHELL_WRITES = [
    "echo bye > file.txt",
    "echo bye>file.txt",
    "echo bye >> file.txt",
    "touch file.txt",
    "rm file.txt",
    "tee file.txt",
    "cp other.txt file.txt",
    "mv other.txt file.txt",
    "sed -i '' 's/hello/bye/' file.txt",
    "dd if=/dev/zero of=file.txt",
    "ls | tee file.txt",
    "true; rm file.txt",
    "echo bye 2>/dev/null > file.txt",
    "cat > file.txt <<'EOF'\nit's done\nEOF",
    "sed -i.bak 's/hello/bye/' file.txt",
    "sed --in-place 's/hello/bye/' file.txt",
    "sudo rm file.txt",
    "/bin/rm file.txt",
    "python3 -c \"open('file.txt', 'w').write('bye')\"",
]


def test_write_on_main_is_denied(git_repo):
    payload = pre_tool_use(git_repo, "Write", file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == StandIn.deny_output


def test_write_on_master_is_denied(git_repo):
    git_repo.set_branch("master")
    payload = pre_tool_use(git_repo, "Write", file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == StandIn.deny_output


def test_write_in_a_new_folder_on_main_is_denied(git_repo):
    payload = pre_tool_use(git_repo, "Write", file_path=git_repo.file("new_folder", EDITED_FILE))
    assert EDIT_GATE.decide(payload) == StandIn.deny_output


@pytest.mark.parametrize("command", SHELL_WRITES)
def test_shell_write_on_main_is_denied(git_repo, command):
    payload = pre_tool_use(git_repo, "Shell", command=command)
    assert EDIT_GATE.decide(payload) == StandIn.deny_output


def test_write_on_unprotected_branch_passes(git_repo):
    git_repo.set_branch(UNPROTECTED_BRANCH)
    payload = pre_tool_use(git_repo, "Write", file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) is None


def test_shell_write_on_unprotected_branch_passes(git_repo):
    git_repo.set_branch(UNPROTECTED_BRANCH)
    payload = pre_tool_use(git_repo, "Shell", command="echo bye > file.txt")
    assert EDIT_GATE.decide(payload) is None


def test_shell_read_on_main_passes(git_repo):
    payload = pre_tool_use(git_repo, "Shell", command="cat file.txt")
    assert EDIT_GATE.decide(payload) is None


def test_other_tool_on_main_passes(git_repo):
    payload = pre_tool_use(git_repo, "Read", file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) is None
