---
name: trello-cli
description: Use this skill when Codex needs to operate Trello from the command line with this LLM-friendly Trello CLI, or when maintaining the trello-cli Python project. It covers authentication, board/list/card/checklist workflows, JSON output expectations, short card IDs, and the local development and test workflow for this repository.
---

# trello-cli

Use `trello-cli` to inspect and update Trello boards from shell workflows. Prefer it when a user asks Codex to create, update, archive, inspect, comment on, or manage Trello cards, lists, boards, checklists, or checklist items.

All command output is JSON on stdout. Errors are JSON on stderr and exit with status 1. Parse stdout as JSON instead of scraping human text.

## Setup

If the executable is not available, install this repository in a Python 3.11+ environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

For a user-level install:

```bash
pipx install -e /path/to/trello-cli
```

Credentials are loaded in this order:

1. `TRELLO_API_KEY` and `TRELLO_TOKEN`
2. `~/.config/trello-cli/config.toml`

Run `trello-cli auth` only when interactive browser authentication is acceptable. Never print, commit, or summarize credential values. If automation needs a default board for short IDs or omitted `--board-id`, configure `default_board` during auth or in the config file.

## Common Workflow

Discover IDs before mutating Trello:

```bash
trello-cli list-boards
trello-cli list-lists --board-id <board-id>
trello-cli list-cards --list-id <list-id>
```

Inspect cards:

```bash
trello-cli get-card --card-id <card-id>
trello-cli get-card --short-id <board-scoped-number>
```

Create and update cards:

```bash
trello-cli create-card --list-id <list-id> --name "Task title" --desc "Markdown details"
trello-cli update-card --card-id <card-id> --name "New title"
trello-cli update-card --card-id <card-id> --due 2026-08-01T09:00:00.000Z
trello-cli update-card --card-id <card-id> --due null
trello-cli update-card --card-id <card-id> --closed
trello-cli update-card --card-id <card-id> --open
```

Comment on cards:

```bash
trello-cli add-comment --card-id <card-id> --text "Markdown comment"
trello-cli add-comment --short-id <board-scoped-number> --text "Markdown comment"
```

Use `--short-id` only when `default_board` is configured. Trello short IDs are board-scoped, not globally unique.

## Checklists

Create a checklist directly:

```bash
trello-cli create-checklist --card-id <card-id> --name "Checklist"
```

Create a checklist from a Markdown checklist file:

```bash
trello-cli create-checklist --card-id <card-id> --name "Todos" --items-file /path/to/items.md
```

Each non-empty line becomes an item. Lines beginning with `- [x]` are marked complete; lines beginning with `- [ ]` are open. The checkbox prefix is stripped from the item name.

Manage checklists and items:

```bash
trello-cli list-checklists --card-id <card-id>
trello-cli get-checklist --checklist-id <checklist-id>
trello-cli update-checklist --checklist-id <checklist-id> --name "Updated"
trello-cli delete-checklist --checklist-id <checklist-id>
trello-cli add-checkitem --checklist-id <checklist-id> --name "Item text" --checked
trello-cli get-checkitem --card-id <card-id> --checkitem-id <item-id>
trello-cli update-checkitem --card-id <card-id> --checkitem-id <item-id> --state complete
trello-cli update-checkitem --card-id <card-id> --checkitem-id <item-id> --state incomplete
trello-cli delete-checkitem --card-id <card-id> --checkitem-id <item-id>
```

Checklist item `--pos`, `--due`, `--due-reminder`, and `--member-id` are advanced Trello features and may depend on the target board's Trello plan.

## Maintaining This Project

The CLI entrypoint is `trello_cli.cli:main`.

Use these files as the main map:

- `src/trello_cli/cli.py`: Typer commands, JSON printing, CLI validation, short-ID resolution.
- `src/trello_cli/client.py`: Trello REST API wrapper, response formatting, domain errors.
- `src/trello_cli/config.py`: config file loading/writing and credential path.
- `tests/`: pytest coverage for config and client behavior.

When adding or changing a command:

1. Add or update the Typer command in `src/trello_cli/cli.py`.
2. Put Trello API calls and response shaping in `src/trello_cli/client.py`.
3. Keep stdout as JSON and errors as JSON on stderr with exit code 1.
4. Preserve the stable card shape from `TrelloClient._fmt` unless a change is intentional.
5. Add focused tests for client payload mapping, response formatting, validation, and config behavior.
6. Update `README.md` command examples when the user-facing CLI changes.

Run tests with:

```bash
python -m pytest
```

If the package is not installed in the current environment, install it first with:

```bash
pip install -e ".[dev]"
```

