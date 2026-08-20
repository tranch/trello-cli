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
trello-cli whoami
trello-cli list-lists --board-id <id>
trello-cli list-cards --list-id <id>
trello-cli get-card --card-id <id>
trello-cli get-card --short-id 413
trello-cli get-card --short-id 413 --card-filter all
trello-cli create-card --list-id <id> --name "Task title" --desc "Details"
trello-cli update-card --card-id <id> --name "New title"
trello-cli update-card --card-id <id> --due 2025-12-31T09:00:00.000Z
trello-cli update-card --card-id <id> --closed
trello-cli add-comment --card-id <id> --text "Comment text"
trello-cli add-comment --short-id 413 --text "Comment text"
trello-cli add-comment --short-id 413 --card-filter all --text "Comment text"
trello-cli create-checklist --card-id <id> --name "Checklist"
trello-cli create-checklist --card-id <id> --name "Todos" --items-file /path/to/items.md
trello-cli get-checklist --checklist-id <id>
trello-cli update-checklist --checklist-id <id> --name "Updated checklist"
trello-cli delete-checklist --checklist-id <id>
trello-cli add-checkitem --checklist-id <id> --name "Item text" --checked
trello-cli get-checkitem --card-id <id> --checkitem-id <id>
trello-cli update-checkitem --card-id <id> --checkitem-id <id> --state complete
trello-cli delete-checkitem --card-id <id> --checkitem-id <id>
trello-cli list-checklists --card-id <id>
```

## Agent skill

This repository includes `SKILL.md`, an agent-oriented guide for using and
maintaining `trello-cli`. Codex can install it as a skill; other agents can read
the same file as project-specific operating instructions.
