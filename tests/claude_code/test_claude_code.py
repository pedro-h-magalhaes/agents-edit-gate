import pytest
from git_repository import EDITED_FILE
from harness_contract import HarnessContract
from payload import pre_tool_use

from edit_gate import EditGate
from harness import ClaudeCode

EDIT_GATE = EditGate(ClaudeCode())


class TestClaudeCode(HarnessContract):
    harness = ClaudeCode()
    manifest_folder = ".claude-plugin"
    hook_event = "PreToolUse"
    file_tool = "Edit"


@pytest.mark.parametrize("tool_name", ["Edit", "Write"])
def test_file_tool_on_main_is_denied(git_repo, tool_name):
    payload = pre_tool_use(git_repo, tool_name, file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == ClaudeCode.deny_output


def test_notebook_edit_on_main_is_denied(git_repo):
    payload = pre_tool_use(git_repo, "NotebookEdit", notebook_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == ClaudeCode.deny_output


def test_bash_write_on_main_is_denied(git_repo):
    payload = pre_tool_use(git_repo, "Bash", command="echo bye > file.txt")
    assert EDIT_GATE.decide(payload) == ClaudeCode.deny_output


def test_denial_is_in_claude_code_format(git_repo):
    payload = pre_tool_use(git_repo, "Edit", file_path=git_repo.file(EDITED_FILE))
    assert EDIT_GATE.decide(payload) == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "This repository is on the main branch.",
        }
    }
