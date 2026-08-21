import json
import webbrowser
from pathlib import Path

import typer

from .client import TrelloClient, TrelloError
from .config import CONFIG_PATH, load_config_file, write_config

app = typer.Typer(
    help="LLM-friendly Trello CLI. All output is JSON.",
    add_completion=False,
)


def main() -> None:
    app()


def _print(data: object) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


def _fail(message: str) -> None:
    typer.echo(json.dumps({"error": message}, ensure_ascii=False), err=True)
    raise typer.Exit(code=1)


def _client() -> TrelloClient:
    try:
        return TrelloClient()
    except RuntimeError as exc:
        _fail(str(exc))


def _read_markdown_file(path: str) -> str:
    """Read Markdown from a file, or stdin when path is ``-``."""
    if path == "-":
        return typer.get_text_stream("stdin").read()
    file_path = Path(path)
    if not file_path.is_file():
        _fail(f"File not found: {path}")
    return file_path.read_text(encoding="utf-8")


def _resolve_board(board_id: str | None) -> str:
    """Return the explicit board_id or fall back to the configured default."""
    if board_id:
        return board_id
    cfg = load_config_file()
    default = cfg.get("default_board", "")
    if not default:
        _fail("No board specified and no default_board configured.")
    return default


def _init(
    api_key: str = typer.Option(
        ...,
        "--api-key",
        prompt="Trello API Key",
        help="Your Trello Power-Up API key.",
    ),
    token: str = typer.Option(
        ...,
        "--token",
        prompt="Trello Token",
        hide_input=True,
        help="Your Trello OAuth token.",
    ),
    default_board: str = typer.Option(
        "",
        "--default-board",
        help="Default board ID to use when --board-id is omitted.",
    ),
) -> None:
    """Write credentials to ~/.config/trello-cli/config.toml."""
    write_config(api_key=api_key, token=token, default_board=default_board)
    typer.echo(f"Config written to {CONFIG_PATH}")


@app.command("auth")
def auth(
    api_key: str = typer.Option(
        ...,
        "--api-key",
        prompt="Trello API Key",
        help="Your Trello Power-Up API key.",
    ),
    expiration: str = typer.Option(
        "never",
        "--expiration",
        help="Token expiration: never / 30days / 1day.",
    ),
    default_board: str = typer.Option(
        "",
        "--default-board",
        help="Default board ID to use when --board-id is omitted.",
    ),
) -> None:
    """Open the Trello authorization URL in your browser to obtain a token."""
    url = (
        "https://trello.com/1/authorize"
        f"?expiration={expiration}"
        "&name=trello-cli"
        "&scope=read,write"
        "&response_type=token"
        f"&key={api_key}"
    )
    typer.echo(f"Opening: {url}")
    webbrowser.open(url)
    typer.echo("Copy the token shown in the browser")

    token = typer.prompt("Trello Token", hide_input=True)

    if not token:
        _fail("Token is required.")

    _init(api_key=api_key, token=token, default_board=default_board)


@app.command("list-boards")
def list_boards() -> None:
    """List all Trello boards accessible to the authenticated user."""
    try:
        _print(_client().list_boards())
    except TrelloError as exc:
        _fail(str(exc))


@app.command("whoami")
def whoami() -> None:
    """Get the Trello member represented by the configured API token."""
    try:
        _print(_client().get_current_user())
    except TrelloError as exc:
        _fail(str(exc))


@app.command("list-lists")
def list_lists(
    board_id: str | None = typer.Option(None, "--board-id", help="Trello board ID."),
) -> None:
    """List all open lists (columns) in a board."""
    try:
        _print(_client().list_lists(board_id=_resolve_board(board_id)))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("list-cards")
def list_cards(
    list_id: str = typer.Option(..., "--list-id", help="Trello list ID."),
) -> None:
    """List all open cards in a list."""
    try:
        _print(_client().list_cards(list_id=list_id))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("get-card")
def get_card(
    card_id: str | None = typer.Option(None, "--card-id", help="Trello card ID."),
    short_id: int | None = typer.Option(
        None,
        "--short-id",
        min=1,
        help="Board-scoped card number shown in a Trello card URL.",
    ),
    card_filter: str = typer.Option(
        "open",
        "--card-filter",
        help="Cards to scan for --short-id: open, closed, or all.",
    ),
    output_format: str = typer.Option(
        "json",
        "--format",
        help="Output format: json (default) or markdown (description only).",
    ),
) -> None:
    """Get full details of a single card."""
    try:
        client = _client()
        if output_format not in {"json", "markdown"}:
            _fail("format must be either json or markdown.")
        if card_id and short_id:
            _fail("Specify either --card-id or --short-id, not both.")
        if card_id:
            card = client.get_card(card_id=card_id)
        elif short_id:
            board_id = _resolve_board(None)
            card = client.get_card_by_short_id(
                board_id=board_id,
                short_id=short_id,
                card_filter=card_filter,
            )
        else:
            _fail("Specify either --card-id or --short-id.")
        if output_format == "markdown":
            typer.echo(card.get("desc", ""), nl=bool(card.get("desc", "")))
        else:
            _print(card)
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("create-card")
def create_card(
    list_id: str = typer.Option(..., "--list-id", help="Target list ID."),
    name: str = typer.Option(..., "--name", help="Card title."),
    desc: str = typer.Option("", "--desc", help="Card description (Markdown supported)."),
    text_file: str | None = typer.Option(
        None,
        "--text-file",
        help="Read the Markdown description from a UTF-8 file, or '-' for stdin.",
    ),
    due: str | None = typer.Option(
        None,
        "--due",
        help="Due date in ISO 8601, e.g. 2025-12-31T09:00:00.000Z.",
    ),
) -> None:
    """Create a new card in the specified list."""
    try:
        if text_file is not None and desc:
            _fail("Specify either --desc or --text-file, not both.")
        description = _read_markdown_file(text_file) if text_file is not None else desc
        _print(_client().create_card(list_id=list_id, name=name, desc=description, due=due))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("update-card")
def update_card(
    card_id: str = typer.Option(..., "--card-id", help="Card ID to update."),
    name: str | None = typer.Option(None, "--name", help="New card title."),
    desc: str | None = typer.Option(None, "--desc", help="New card description."),
    text_file: str | None = typer.Option(
        None,
        "--text-file",
        help="Read the new Markdown description from a UTF-8 file, or '-' for stdin.",
    ),
    due: str | None = typer.Option(
        None,
        "--due",
        help="New due date (ISO 8601), or 'null' to clear it.",
    ),
    closed: bool = typer.Option(False, "--closed/--open", help="Archive or unarchive the card."),
) -> None:
    """
    Update one or more fields on an existing card.
    Only provided flags are changed; omitted flags are left untouched.
    """
    resolved_due = None if due == "null" else due
    resolved_closed: bool | None = closed if closed else None
    try:
        if text_file is not None and desc is not None:
            _fail("Specify either --desc or --text-file, not both.")
        description = _read_markdown_file(text_file) if text_file is not None else desc
        _print(
            _client().update_card(
                card_id=card_id,
                name=name,
                desc=description,
                due=resolved_due,
                closed=resolved_closed,
            )
        )
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("add-comment")
def add_comment(
    text: str | None = typer.Option(None, "--text", help="Comment text (Markdown supported)."),
    text_file: str | None = typer.Option(
        None,
        "--text-file",
        help="Read Markdown comment text from a UTF-8 file, or '-' for stdin.",
    ),
    card_id: str | None = typer.Option(None, "--card-id", help="Trello card ID."),
    short_id: int | None = typer.Option(
        None,
        "--short-id",
        min=1,
        help="Board-scoped card number shown in a Trello card URL.",
    ),
    card_filter: str = typer.Option(
        "open",
        "--card-filter",
        help="Cards to scan for --short-id: open, closed, or all.",
    ),
) -> None:
    """Add a comment to a card."""
    try:
        if text_file is not None and text is not None:
            _fail("Specify either --text or --text-file, not both.")
        if text_file is None and text is None:
            _fail("Specify either --text or --text-file.")
        comment_text = _read_markdown_file(text_file) if text_file is not None else text
        client = _client()
        if card_id and short_id:
            _fail("Specify either --card-id or --short-id, not both.")
        if short_id:
            board_id = _resolve_board(None)
            card_id = client.get_card_by_short_id(
                board_id=board_id,
                short_id=short_id,
                card_filter=card_filter,
            )["id"]
        if not card_id:
            _fail("Specify either --card-id or --short-id.")
        _print(client.add_comment(card_id=card_id, text=comment_text))
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("create-checklist")
def create_checklist(
    card_id: str = typer.Option(..., "--card-id", help="Card ID to add the checklist to."),
    name: str = typer.Option(..., "--name", help="Checklist title."),
    items_file: str | None = typer.Option(
        None,
        "--items-file",
        help="Path to a markdown checklist file.",
    ),
) -> None:
    """
    Create a checklist on a card.

    When --items-file is given, each line in the file is parsed as a checklist item.
    Lines starting with '- [x]' are added as completed items; '- [ ]' as open items.
    The [x]/[ ] prefix is stripped from the item name.
    """
    try:
        client = _client()
        checklist = client.create_checklist(card_id=card_id, name=name)
        checklist_id = checklist["id"]

        if items_file:
            path = Path(items_file)
            if not path.exists():
                _fail(f"File not found: {items_file}")
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                is_checked = stripped.startswith("- [x]")
                item_name = stripped[5:].strip() if stripped.startswith("- [") else stripped
                item = client.add_checkitem(checklist_id=checklist_id, name=item_name)
                if is_checked:
                    client.update_checkitem(
                        card_id=card_id,
                        checkitem_id=item["id"],
                        state="complete",
                    )
        _print(client.list_checklists(card_id=card_id))
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("add-checkitem")
def add_checkitem(
    checklist_id: str = typer.Option(..., "--checklist-id", help="Checklist ID."),
    name: str = typer.Option(..., "--name", help="Item text."),
    pos: str | None = typer.Option(None, "--pos", help="Item position."),
    checked: bool = typer.Option(False, "--checked", help="Create the item as completed."),
    due: str | None = typer.Option(None, "--due", help="Due date in ISO 8601."),
    due_reminder: int | None = typer.Option(None, "--due-reminder", help="Due reminder in minutes."),
    member_id: str | None = typer.Option(None, "--member-id", help="Member ID assigned to the item."),
) -> None:
    """Add a single item to an existing checklist.

    Position, due date, due reminder, and member assignment are advanced
    Trello features and may require a subscription on the target board.
    """
    try:
        _print(
            _client().add_checkitem(
                checklist_id=checklist_id,
                name=name,
                pos=pos,
                checked=checked,
                due=due,
                due_reminder=due_reminder,
                member_id=member_id,
            )
        )
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("get-checklist")
def get_checklist(
    checklist_id: str = typer.Option(..., "--checklist-id", help="Checklist ID."),
) -> None:
    """Get a checklist and all of its items."""
    try:
        _print(_client().get_checklist(checklist_id=checklist_id))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("update-checklist")
def update_checklist(
    checklist_id: str = typer.Option(..., "--checklist-id", help="Checklist ID."),
    name: str | None = typer.Option(None, "--name", help="New checklist title."),
    pos: str | None = typer.Option(None, "--pos", help="New checklist position."),
) -> None:
    """Update one or more fields on an existing checklist."""
    try:
        _print(_client().update_checklist(checklist_id=checklist_id, name=name, pos=pos))
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("delete-checklist")
def delete_checklist(
    checklist_id: str = typer.Option(..., "--checklist-id", help="Checklist ID."),
) -> None:
    """Delete a checklist."""
    try:
        _print(_client().delete_checklist(checklist_id=checklist_id))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("get-checkitem")
def get_checkitem(
    card_id: str = typer.Option(..., "--card-id", help="Card ID."),
    checkitem_id: str = typer.Option(..., "--checkitem-id", help="Checklist item ID."),
) -> None:
    """Get a checklist item on a card."""
    try:
        _print(_client().get_checkitem(card_id=card_id, checkitem_id=checkitem_id))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("update-checkitem")
def update_checkitem(
    card_id: str = typer.Option(..., "--card-id", help="Card ID."),
    checkitem_id: str = typer.Option(..., "--checkitem-id", help="Checklist item ID."),
    name: str | None = typer.Option(None, "--name", help="New item text."),
    state: str | None = typer.Option(None, "--state", help="Item state: complete or incomplete."),
    checklist_id: str | None = typer.Option(None, "--checklist-id", help="Destination checklist ID."),
    pos: str | None = typer.Option(None, "--pos", help="New item position."),
    due: str | None = typer.Option(None, "--due", help="Due date in ISO 8601."),
    due_reminder: int | None = typer.Option(None, "--due-reminder", help="Due reminder in minutes."),
    member_id: str | None = typer.Option(None, "--member-id", help="Member ID assigned to the item."),
) -> None:
    """Update one or more fields on a checklist item.

    Position, due date, due reminder, and member assignment are advanced
    Trello features and may require a subscription on the target board.
    """
    try:
        _print(
            _client().update_checkitem(
                card_id=card_id,
                checkitem_id=checkitem_id,
                name=name,
                state=state,
                checklist_id=checklist_id,
                pos=pos,
                due=due,
                due_reminder=due_reminder,
                member_id=member_id,
            )
        )
    except (TrelloError, ValueError) as exc:
        _fail(str(exc))


@app.command("delete-checkitem")
def delete_checkitem(
    card_id: str = typer.Option(..., "--card-id", help="Card ID."),
    checkitem_id: str = typer.Option(..., "--checkitem-id", help="Checklist item ID."),
) -> None:
    """Delete a checklist item from a card."""
    try:
        _print(_client().delete_checkitem(card_id=card_id, checkitem_id=checkitem_id))
    except TrelloError as exc:
        _fail(str(exc))


@app.command("list-checklists")
def list_checklists(
    card_id: str = typer.Option(..., "--card-id", help="Trello card ID."),
) -> None:
    """List all checklists (with their items) on a card."""
    try:
        _print(_client().list_checklists(card_id=card_id))
    except TrelloError as exc:
        _fail(str(exc))
