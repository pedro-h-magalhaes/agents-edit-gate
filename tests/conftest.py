import pytest

pytest.register_assert_rewrite("harness_contract")

# Shared fixtures: run_claude, from claude_session.py.
pytest_plugins = ["claude_session"]

from git_repository import EDITED_FILE, GitRepo


@pytest.fixture
def git_repo(tmp_path):
    return GitRepo(tmp_path, files={EDITED_FILE: "hello\n"})
