import pytest

from trello_cli.client import TrelloClient, TrelloError


def test_fmt_handles_missing_optional_fields() -> None:
    assert TrelloClient._fmt({"id": "card-1", "name": "Example"}) == {
        "id": "card-1",
        "short_id": None,
        "name": "Example",
        "desc": "",
        "due": None,
        "url": None,
        "list_id": None,
        "board_id": None,
        "closed": False,
        "labels": [],
    }


def test_fmt_extracts_label_names() -> None:
    assert TrelloClient._fmt({"labels": [{"name": "bug"}, {"name": ""}, {}]})["labels"] == [
        "bug",
        "",
        None,
    ]


def test_get_card_by_short_id_resolves_within_board(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    calls: list[tuple[str, dict]] = []

    def get(path: str, **params: object) -> object:
        calls.append((path, params))
        if path == "/boards/board-1/cards":
            return [{"id": "card-401", "idShort": 401}, {"id": "card-413", "idShort": 413}]
        assert path == "/cards/card-413"
        return {"id": "card-413", "idShort": 413, "name": "Example"}

    monkeypatch.setattr(client, "_get", get)

    assert client.get_card_by_short_id("board-1", 413)["id"] == "card-413"
    assert calls[0] == (
        "/boards/board-1/cards",
        {"filter": "all", "fields": "id,idShort"},
    )


def test_get_card_by_short_id_rejects_missing_card(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    monkeypatch.setattr(client, "_get", lambda *_args, **_kwargs: [])

    with pytest.raises(TrelloError, match="413.*board-1"):
        client.get_card_by_short_id("board-1", 413)
