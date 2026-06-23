# trello-cli

LLM-friendly command-line interface for Trello.

All commands write JSON to stdout. Errors are written to stderr and exit with
code 1.

## Install for local development

```bash
cd ~/Workspace/trello-cli
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

This installs a `trello-cli` executable into the active environment. To deploy
it onto your normal `$PATH`, install it with the Python used by that path, or
use `pipx`:

```bash
pipx install -e ~/Workspace/trello-cli
```

## Credentials

Credential loading priority:

1. `TRELLO_API_KEY` and `TRELLO_TOKEN`
2. `~/.config/trello-cli/config.toml`

Run:

```bash
trello-cli auth
```

## Commands

```bash
trello-cli list-boards
trello-cli list-lists --board-id <id>
trello-cli list-cards --list-id <id>
trello-cli get-card --card-id <id>
trello-cli get-card --short-id 413
trello-cli create-card --list-id <id> --name "Task title" --desc "Details"
trello-cli update-card --card-id <id> --name "New title"
trello-cli update-card --card-id <id> --due 2025-12-31T09:00:00.000Z
trello-cli update-card --card-id <id> --closed
trello-cli create-checklist --card-id <id> --name "Checklist"
trello-cli create-checklist --card-id <id> --name "Todos" --items-file /path/to/items.md
trello-cli add-checkitem --checklist-id <id> --name "Item text"
trello-cli list-checklists --card-id <id>
```
