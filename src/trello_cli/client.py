import os
from typing import Any

import requests

from .config import load_config_file

TRELLO_BASE = "https://api.trello.com/1"


class TrelloError(Exception):
    pass


class TrelloClient:
    def __init__(self) -> None:
        cfg = load_config_file()
        self.api_key = os.environ.get("TRELLO_API_KEY") or cfg.get("api_key", "")
        self.token = os.environ.get("TRELLO_TOKEN") or cfg.get("token", "")
        if not self.api_key or not self.token:
            raise RuntimeError(
                "Trello credentials not found.\n"
                "Please run 'trello-cli auth' to authenticate and save your credentials."
            )
        self._auth = {"key": self.api_key, "token": self.token}

    def _get(self, path: str, **params: Any) -> Any:
        response = requests.get(
            f"{TRELLO_BASE}{path}",
            params={**self._auth, **params},
            timeout=15,
        )
        if not response.ok:
            raise TrelloError(f"GET {path} -> {response.status_code}: {response.text}")
        return response.json()

    def _post(self, path: str, **data: Any) -> Any:
        response = requests.post(
            f"{TRELLO_BASE}{path}",
            params=self._auth,
            json=data,
            timeout=15,
        )
        if not response.ok:
            raise TrelloError(f"POST {path} -> {response.status_code}: {response.text}")
        return response.json()

    def _put(self, path: str, **data: Any) -> Any:
        response = requests.put(
            f"{TRELLO_BASE}{path}",
            params=self._auth,
            json=data,
            timeout=15,
        )
        if not response.ok:
            raise TrelloError(f"PUT {path} -> {response.status_code}: {response.text}")
        return response.json()

    def list_boards(self) -> list[dict]:
        boards = self._get("/members/me/boards", fields="id,name,url,closed")
        return [
            {"id": b["id"], "name": b["name"], "url": b["url"], "closed": b["closed"]}
            for b in boards
        ]

    def list_lists(self, board_id: str) -> list[dict]:
        lists = self._get(f"/boards/{board_id}/lists", filter="open", fields="id,name,pos")
        return [{"id": item["id"], "name": item["name"], "pos": item["pos"]} for item in lists]

    def list_cards(self, list_id: str) -> list[dict]:
        cards = self._get(
            f"/lists/{list_id}/cards",
            filter="open",
            fields="id,idShort,name,desc,due,url,idList,labels",
        )
        return [self._fmt(card) for card in cards]

    def get_card(self, card_id: str) -> dict:
        card = self._get(
            f"/cards/{card_id}",
            fields="id,idShort,name,desc,due,url,idList,idBoard,labels,closed",
        )
        return self._fmt(card)

    def get_card_by_short_id(self, board_id: str, short_id: int) -> dict:
        """Return a card by its board-scoped Trello ``idShort`` value."""
        cards = self._get(
            f"/boards/{board_id}/cards",
            filter="all",
            fields="id,idShort",
        )
        card_id = next(
            (card["id"] for card in cards if card.get("idShort") == short_id),
            None,
        )
        if card_id is None:
            raise TrelloError(
                f"Card short ID {short_id} was not found on board {board_id}."
            )
        return self.get_card(card_id)

    def create_card(
        self,
        list_id: str,
        name: str,
        desc: str = "",
        due: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {"idList": list_id, "name": name, "desc": desc}
        if due:
            payload["due"] = due
        return self._fmt(self._post("/cards", **payload))

    def update_card(
        self,
        card_id: str,
        name: str | None = None,
        desc: str | None = None,
        due: str | None = None,
        closed: bool | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if desc is not None:
            payload["desc"] = desc
        if due is not None:
            payload["due"] = due
        if closed is not None:
            payload["closed"] = closed
        if not payload:
            raise ValueError("At least one field must be specified.")
        return self._fmt(self._put(f"/cards/{card_id}", **payload))

    def create_checklist(self, card_id: str, name: str) -> dict:
        return self._post(f"/cards/{card_id}/checklists", name=name)

    def add_checkitem(self, checklist_id: str, name: str) -> dict:
        return self._post(f"/checklists/{checklist_id}/checkItems", name=name)

    def update_checkitem(
        self,
        card_id: str,
        checkitem_id: str,
        name: str | None = None,
        state: str | None = None,
    ) -> dict:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if state is not None:
            payload["state"] = state
        if not payload:
            raise ValueError("At least one field must be specified.")
        return self._put(f"/cards/{card_id}/checkItem/{checkitem_id}", **payload)

    def list_checklists(self, card_id: str) -> list[dict]:
        card = self._get(
            f"/cards/{card_id}",
            checklists="all",
            fields="id,name",
        )
        return [
            {
                "id": checklist["id"],
                "name": checklist["name"],
                "items": [
                    {"id": item["id"], "name": item["name"], "state": item["state"]}
                    for item in checklist.get("checkItems", [])
                ],
            }
            for checklist in card.get("checklists", [])
        ]

    @staticmethod
    def _fmt(card: dict) -> dict:
        return {
            "id": card.get("id"),
            "short_id": card.get("idShort"),
            "name": card.get("name"),
            "desc": card.get("desc", ""),
            "due": card.get("due"),
            "url": card.get("url"),
            "list_id": card.get("idList"),
            "board_id": card.get("idBoard"),
            "closed": card.get("closed", False),
            "labels": [label.get("name") for label in card.get("labels", [])],
        }
