"""Hold GitRepo, a real git repository that edit gate tests run against, and the names they share."""

import subprocess

EDITED_FILE = "file.txt"

UNPROTECTED_BRANCH = "feat/test-branch"


class GitRepo:
    """A git repository in a folder, born on main with its first files committed."""

    def __init__(self, path, files=None):
        """Create the repository in `path`, on main, with `files` committed.

        Args:
            path: An existing, empty folder.
            files: `{name: content}` to write and commit first; None commits nothing.
        """
        self.path = path
        self._git_init()
        self.add_files(files or {})
        self._stage_all()
        self._commit("init")

    @property
    def branch(self):
        """The branch checked out now, as git reports it."""
        return self._git("rev-parse", "--abbrev-ref", "HEAD")

    def file(self, *parts):
        """Return the path of a file in the repository, which may not exist yet.

        Args:
            parts: The folders and file name, relative to the repository.

        Returns:
            The file's full path, as text.
        """
        return str(self.path.joinpath(*parts))

    def add_files(self, files):
        """Write each file into the repository folder, without staging it.

        Args:
            files: `{name: content}`, names relative to the folder.
        """
        for name, content in files.items():
            (self.path / name).write_text(content)

    def set_branch(self, name):
        """Create `name` from the current commit and check it out.

        Staying on the branch already checked out does nothing.

        Args:
            name: The branch to be on.
        """
        if name != self.branch:
            self._git("switch", "-q", "-c", name)

    def status(self):
        """List what `git status --porcelain` reports, one entry per line.

        Returns:
            One line per changed or untracked file; empty when the tree is clean.
        """
        return self._git("status", "--porcelain").splitlines()

    def _git(self, *args):
        """Run git in the repository.

        Args:
            args: The git arguments, after `git`.

        Returns:
            What git printed, stripped.
        """
        return subprocess.run(
            ["git", *args], cwd=self.path, check=True, capture_output=True, text=True
        ).stdout.strip()

    def _git_init(self):
        self._git("init", "-q", "-b", "main")

    def _stage_all(self):
        self._git("add", "-A")

    def _commit(self, message):
        self._git(
            "-c", "user.name=test", "-c", "user.email=test@example.com",
            "commit", "-q", "--allow-empty", "-m", message,
        )
