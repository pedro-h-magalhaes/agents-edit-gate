"""Hold HarnessContract, the tests every harness passes, written once."""

from git_repository import EDITED_FILE, UNPROTECTED_BRANCH
from payload import pre_tool_use
from plugin import PluginHook

from harness import Harness


class HarnessContract:
    """The tests every harness passes, run once for each subclass.

    A subclass sets the harness, the manifest folder and hook event its plugin
    registers, and a file tool that writes through `file_path`.
    """

    harness: Harness
    manifest_folder: str
    hook_event: str
    file_tool: str

    def test_plugin_hooks_every_writing_tool(self):
        assert self._hook().tools_missed(self.harness) == []

    def test_hook_prints_the_denial_on_main(self, git_repo):
        payload = pre_tool_use(git_repo, self.file_tool, file_path=git_repo.file(EDITED_FILE))
        assert self._hook().run(payload) == self.harness.deny_output

    def test_hook_prints_nothing_on_an_unprotected_branch(self, git_repo):
        git_repo.set_branch(UNPROTECTED_BRANCH)
        payload = pre_tool_use(git_repo, self.file_tool, file_path=git_repo.file(EDITED_FILE))
        assert self._hook().run(payload) is None

    def _hook(self):
        return PluginHook.read(self.manifest_folder, self.hook_event)
