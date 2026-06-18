from trello_cli.client import TrelloClient


def test_fmt_handles_missing_optional_fields() -> None:
    assert TrelloClient._fmt({"id": "card-1", "name": "Example"}) == {
        "id": "card-1",
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
