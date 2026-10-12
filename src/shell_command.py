"""Hold ShellCommand, which reads a shell command line and lists the files it writes."""

import os
import re
import shlex
from dataclasses import dataclass
from typing import Self

REDIRECTS = {">", ">>"}

SEPARATORS = {";", "&&", "||", "|", "&"}

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")

WRITERS = {
    "touch": lambda command: command.arguments,
    "rm": lambda command: command.arguments,
    "tee": lambda command: command.arguments,
    "cp": lambda command: command.arguments[-1:],
    "mv": lambda command: command.arguments[-1:],
    "sed": lambda command: _sed_in_place(command),
    "python": lambda command: _inline_code(command),
    "python3": lambda command: _inline_code(command),
    "dd": lambda command: [
        argument.removeprefix("of=")
        for argument in command.arguments
        if argument.startswith("of=")
    ],
}


@dataclass
class ShellCommand:
    """One simple command of a shell command line, as the words it is made of."""

    words: list[str]

    @classmethod
    def parse_all(cls, text: str) -> list[Self]:
        """Split a command line into its simple commands.

        Splits on `;`, `&&`, `||`, `|` and `&`, one line at a time, and skips
        the bodies of heredocs.

        Args:
            text: The command line, as given to the Bash tool.

        Returns:
            Each simple command in order; empty commands are left out.
        """
        commands = []
        for line in _without_heredoc_bodies(text):
            lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
            lexer.whitespace_split = True
            words = []
            for word in lexer:
                if word in SEPARATORS:
                    commands.append(cls(words))
                    words = []
                else:
                    words.append(word)
            commands.append(cls(words))
        return [command for command in commands if command.words]

    @property
    def command_words(self) -> list[str]:
        """The words from the program name on, without `sudo` or `VAR=value` before it."""
        words = list(self.words)
        while words and _is_prefix(words[0]):
            words.pop(0)
        return words

    @property
    def name(self) -> str:
        """The program's base name, so `/bin/rm` is `rm`; empty when there is none."""
        words = self.command_words
        return os.path.basename(words[0]) if words else ""

    @property
    def arguments(self) -> list[str]:
        """The words after the program name that are not empty and are not flags."""
        return [
            word for word in self.command_words[1:] if word and not word.startswith("-")
        ]

    @property
    def redirect_targets(self) -> list[str]:
        """The files after each `>` or `>>`."""
        return [
            after
            for before, after in zip(self.words, self.words[1:])
            if before in REDIRECTS
        ]

    @property
    def written_files(self) -> list[str]:
        """The files the command writes, through redirects or the program in WRITERS."""
        writer = WRITERS.get(self.name, lambda command: [])
        return self.redirect_targets + writer(self)


def _is_prefix(word: str) -> bool:
    return word == "sudo" or ("=" in word and word.split("=", 1)[0].isidentifier())


def _without_heredoc_bodies(text: str) -> list[str]:
    lines = []
    end_marker = None
    for line in text.splitlines():
        if end_marker is not None:
            if line.strip() == end_marker:
                end_marker = None
            continue
        lines.append(line)
        match = HEREDOC.search(line)
        if match:
            end_marker = match.group(1)
    return lines


def _sed_in_place(command: ShellCommand) -> list[str]:
    in_place = any(
        word.startswith("-i") or word == "--in-place" for word in command.words
    )
    return command.arguments[1:] if in_place else []


def _inline_code(command: ShellCommand) -> list[str]:
    """Return the folder the command runs in when it runs code given with `-c`."""
    return ["."] if "-c" in command.command_words else []
