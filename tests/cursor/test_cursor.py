import pytest
from git_repository import EDITED_FILE
from harness_contract import HarnessContract
from payload import pre_tool_use

from edit_gate import EditGate
from harness import Cursor

EDIT_GATE = EditGate(Cursor())


class TestCursor(HarnessContract):
    harness = Cursor()
    manifest_folder = ".cursor-plugin"
    hook_event = "preToolUse"
    file_tool = "Write"


@pytest.mark.parametrize("tool_name", ["Write", "Delete"])
def test_file_tool_on_main_is_denied(git_repo, tool_name):
    payload = pre_tool_use(git_repo, tool_name, file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == Cursor.deny_output


def test_shell_write_without_cwd_uses_workspace_root(git_repo):
    payload = pre_tool_use(git_repo, "Shell", cwd="", command="echo bye > file.txt")
    assert EDIT_GATE.decide(payload) == Cursor.deny_output


def test_denial_is_in_cursor_format(git_repo):
    payload = pre_tool_use(git_repo, "Write", file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == {
        "permission": "deny",
        "agent_message": "This repository is on the main branch.",
    }
