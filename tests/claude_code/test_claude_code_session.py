from git_repository import EDITED_FILE, UNPROTECTED_BRANCH

EDIT_TOOLS = ("Write", "Edit", "NotebookEdit")
EDIT = f"Use the Edit tool to replace 'hello' with 'bye' in {EDITED_FILE}."
SED = f"Use the Bash tool to run: sed -i '' 's/hello/bye/' {EDITED_FILE}."


def test_session_edit_on_main_is_held(git_repo, run_claude):
    run_claude(EDIT, git_repo.path, stop_after=EDIT_TOOLS)
    assert git_repo.status() == []


def test_session_edit_on_unprotected_branch_lands(git_repo, run_claude):
    git_repo.set_branch(UNPROTECTED_BRANCH)
    run_claude(EDIT, git_repo.path, stop_after=EDIT_TOOLS)
    assert (git_repo.path / EDITED_FILE).read_text() == "bye\n"


def test_session_bash_write_on_main_is_held(git_repo, run_claude):
    run_claude(SED, git_repo.path, stop_after=("Bash",))
    assert git_repo.status() == []
