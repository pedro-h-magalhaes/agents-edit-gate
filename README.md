# Edit gate

A Claude Code and Cursor plugin that denies a tool call that would write into a
repository on `main` or `master`.

## What it does

Before each tool call that can write, the harness's hook runs the gate. The
gate finds the files the call would write: the file a file tool names, or the
files a shell command writes through redirects, `touch`, `rm`, `tee`, `cp`,
`mv`, `sed -i` or `dd`. A `python -c` counts as a write to the command's folder,
since the gate does not read the code. When any of those files is in a
repository on `main` or `master`, the gate denies the call in the harness's own
format; otherwise it prints nothing and the call goes on.

| Harness | Hook | File tools | Shell tool |
|---|---|---|---|
| Claude Code | `PreToolUse` | `Edit`, `Write`, `NotebookEdit` | `Bash` |
| Cursor | `preToolUse` | `Write`, `Delete` | `Shell` |

How it works inside: [classes](docs/classes.md), [flow](docs/flow.md) and
[sequence](docs/sequence.md).

## Not covered yet

- Writes through a script or any other program the gate does not know.
- Harnesses other than Claude Code and Cursor.
- A live Cursor session loading the plugin.

## Files

```text
agents-edit-gate/
├── .claude-plugin/
│   ├── plugin.json              Claude Code manifest
│   └── marketplace.json         installs the plugin from this repository
├── .cursor-plugin/plugin.json   Cursor manifest
├── docs/                        class, flow and sequence diagrams
├── hooks/                       one hooks file per harness, each running src/edit_gate.py
├── LICENSE                      MIT
├── requirements.txt             what the tests need: pytest
├── pytest.ini                   finds src/ and tests/
├── src/
│   ├── edit_gate.py             EditGate, run with the harness's name
│   ├── harness.py               Harness, and one subclass per harness
│   └── shell_command.py         reads the files a shell command writes
└── tests/
    ├── test_edit_gate.py        shared rules, on a stand-in harness
    ├── harness_contract.py      the tests every harness passes, written once
    ├── payload.py               builds the hook input every test sends
    ├── claude_command.py        builds the `claude -p` command a live session runs
    ├── claude_session.py        runs a live Claude Code session and reads it
    ├── claude_code/             Claude Code: decisions, hook process, live sessions
    └── cursor/                  Cursor: decisions and hook process
```

Each harness reads only its own manifest, and Cursor does not import the hooks
of Claude Code plugins, so the two manifests stay apart.

## Use

Needs `python3` and `git` on `PATH`, and no other dependencies.

Install it for every Claude Code session from this repository's marketplace:

```bash
claude plugin marketplace add pedro-h-magalhaes/agents-edit-gate
claude plugin install edit-gate@agents-edit-gate --scope user
```

Or load it for one session only, from a clone:

```bash
git clone https://github.com/pedro-h-magalhaes/agents-edit-gate.git
claude --plugin-dir agents-edit-gate
```

## Test

Install what the tests need, then run them from the repository's root:

```bash
pip install -r requirements.txt
pytest
```

The `test_session_*` tests start real `claude` sessions on Haiku, so they need
the `claude` CLI and use your Claude account. `pytest -k "not session"` leaves
them out.

## License

MIT, in [LICENSE](LICENSE).
