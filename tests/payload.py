"""Hold pre_tool_use, which builds the input a harness sends its pre-tool hook, as edit gate tests need it."""


def pre_tool_use(git_repo, tool_name, cwd=None, **tool_input):
    """Build the pre-tool hook input for a tool called inside `git_repo`.

    Args:
        git_repo: The repository the call runs in, also its only workspace root.
        tool_name: The tool the agent calls.
        cwd: The folder the call runs in; None means the repository.
        tool_input: The tool's input fields, such as `file_path` or `command`.

    Returns:
        The hook input, as the harness sends it on stdin.
    """
    return {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "cwd": str(git_repo.path) if cwd is None else cwd,
        "workspace_roots": [str(git_repo.path)],
    }
