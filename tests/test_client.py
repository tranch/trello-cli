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


def test_add_comment_posts_text_as_query_param(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    calls: list[tuple[str, dict]] = []

    def post_params(path: str, **params: object) -> object:
        calls.append((path, params))
        return {
            "id": "action-1",
            "type": "commentCard",
            "data": {"text": "Looks good"},
        }

    monkeypatch.setattr(client, "_post_params", post_params)

    assert client.add_comment("card-1", "Looks good")["id"] == "action-1"
    assert calls == [
        (
            "/cards/card-1/actions/comments",
            {"text": "Looks good"},
        )
    ]


def test_add_comment_rejects_empty_text() -> None:
    client = object.__new__(TrelloClient)

    with pytest.raises(ValueError, match="must not be empty"):
        client.add_comment("card-1", "  ")


def test_update_checklist_sends_supported_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    calls: list[tuple[str, dict]] = []

    def put(path: str, **data: object) -> object:
        calls.append((path, data))
        return {"id": "checklist-1", "name": "Updated", "pos": 3}

    monkeypatch.setattr(client, "_put", put)

    result = client.update_checklist("checklist-1", name="Updated", pos=3)

    assert result["name"] == "Updated"
    assert calls == [("/checklists/checklist-1", {"name": "Updated", "pos": 3})]


def test_update_checklist_requires_a_field() -> None:
    client = object.__new__(TrelloClient)

    with pytest.raises(ValueError, match="At least one field"):
        client.update_checklist("checklist-1")


def test_add_checkitem_maps_optional_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    calls: list[tuple[str, dict]] = []

    def post(path: str, **data: object) -> object:
        calls.append((path, data))
        return {"id": "item-1"}

    monkeypatch.setattr(client, "_post", post)

    client.add_checkitem(
        "checklist-1",
        "Item",
        pos=2,
        checked=True,
        due="2026-08-01T09:00:00.000Z",
        due_reminder=60,
        member_id="member-1",
    )

    assert calls == [
        (
            "/checklists/checklist-1/checkItems",
            {
                "name": "Item",
                "pos": 2,
                "checked": True,
                "due": "2026-08-01T09:00:00.000Z",
                "dueReminder": 60,
                "idMember": "member-1",
            },
        )
    ]


def test_update_checkitem_maps_all_supported_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    calls: list[tuple[str, dict]] = []

    def put(path: str, **data: object) -> object:
        calls.append((path, data))
        return {"id": "item-1", "state": "complete"}

    monkeypatch.setattr(client, "_put", put)

    client.update_checkitem(
        "card-1",
        "item-1",
        name="Updated",
        state="complete",
        checklist_id="checklist-2",
        pos=4,
        due="2026-08-01T09:00:00.000Z",
        due_reminder=60,
        member_id="member-1",
    )

    assert calls == [
        (
            "/cards/card-1/checkItem/item-1",
            {
                "name": "Updated",
                "state": "complete",
                "idChecklist": "checklist-2",
                "pos": 4,
                "due": "2026-08-01T09:00:00.000Z",
                "dueReminder": 60,
                "idMember": "member-1",
            },
        )
    ]


def test_delete_checkitem_uses_delete_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object.__new__(TrelloClient)
    calls: list[str] = []

    def delete(path: str) -> object:
        calls.append(path)
        return {"success": True}

    monkeypatch.setattr(client, "_delete", delete)

    assert client.delete_checkitem("card-1", "item-1") == {"success": True}
    assert calls == ["/cards/card-1/checkItem/item-1"]
