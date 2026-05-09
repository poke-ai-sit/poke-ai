from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import pokelive_bridge.main as bridge_main
from pokelive_bridge.main import app
from pokelive_bridge.pokemon_text import format_dialog_hex


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_latest_game_state() -> None:
    bridge_main.latest_game_state = None


def test_health_returns_service_status() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "pokelive-bridge",
    }


def test_game_state_accepts_and_echoes_valid_payload() -> None:
    payload = {
        "map_group": 4,
        "map_num": 1,
        "x": 9,
        "y": 4,
        "frame": 42354,
    }

    response = client.post("/game-state", json=payload)

    assert response.status_code == 200
    assert response.json() == {
        "received": True,
        "game_state": payload,
    }


def test_game_state_rejects_missing_required_coordinate() -> None:
    response = client.post(
        "/game-state",
        json={
            "map_group": 4,
            "map_num": 1,
            "x": 9,
        },
    )

    assert response.status_code == 422


def test_get_game_state_returns_404_before_any_state_is_posted() -> None:
    response = client.get("/game-state")

    assert response.status_code == 404
    assert response.json() == {"detail": "No game state has been received yet."}


def test_get_game_state_returns_latest_posted_state() -> None:
    first_payload = {
        "map_group": 3,
        "map_num": 0,
        "x": 11,
        "y": 6,
        "frame": 167402,
    }
    latest_payload = {
        "map_group": 3,
        "map_num": 0,
        "x": 8,
        "y": 2,
        "frame": 167702,
    }

    client.post("/game-state", json=first_payload)
    response = client.post("/game-state", json=latest_payload)
    assert response.status_code == 200

    response = client.get("/game-state")

    assert response.status_code == 200
    assert response.json() == {"game_state": latest_payload}


def test_codex_chat_returns_404_before_any_state_is_posted() -> None:
    response = client.post("/codex-chat", json={"message": "What should I do next?"})

    assert response.status_code == 404
    assert response.json() == {"detail": "No game state has been received yet."}


def test_codex_chat_can_accept_inline_game_state() -> None:
    payload = {
        "map_group": 3,
        "map_num": 0,
        "x": 12,
        "y": 9,
        "frame": 220000,
    }

    with patch("pokelive_bridge.main.ask_codex", return_value="Hello, researcher!"):
        response = client.post(
            "/codex-chat",
            json={
                "message": "What should I do next?",
                "game_state": payload,
            },
        )

    assert response.status_code == 200
    assert response.json()["game_state"] == payload


def test_codex_chat_returns_ai_message_and_hex() -> None:
    payload = {
        "map_group": 3,
        "map_num": 0,
        "x": 11,
        "y": 11,
        "frame": 182644,
    }
    ai_message = "Head north, young researcher!"
    client.post("/game-state", json=payload)

    with patch("pokelive_bridge.main.ask_codex", return_value=ai_message):
        response = client.post("/codex-chat", json={"message": "What should I do next?"})

    assert response.status_code == 200
    data = response.json()
    assert data["speaker"] == "Professor GPT 5.5"
    assert data["message"] == "Head north young researcher."
    assert data["message_hex"] == format_dialog_hex(data["message"], chars_per_line=200, lines_per_page=1)
    assert data["game_state"] == payload


def test_codex_chat_sanitizes_message_before_returning_hex() -> None:
    payload = {
        "map_group": 4,
        "map_num": 3,
        "x": 6,
        "y": 4,
        "frame": 66842,
    }
    ai_message = "Ah, you're in Oak's Lab! Choose wisely."

    with patch("pokelive_bridge.main.ask_codex", return_value=ai_message):
        response = client.post(
            "/codex-chat",
            json={
                "message": "Professor Oak is speaking in Oak's Lab.",
                "game_state": payload,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Ah youre in Oaks Lab. Choose wisely."
    assert data["message_hex"] == format_dialog_hex(data["message"], chars_per_line=200, lines_per_page=1)


def test_codex_chat_accepts_party_data_for_advice() -> None:
    payload = {
        "message": "What should I do next?",
        "game_state": {
            "map_group": 4,
            "map_num": 3,
            "x": 6,
            "y": 4,
            "frame": 100,
        },
        "request_kind": "ADVICE",
        "party": [
            {
                "species": 7,
                "level": 10,
                "hp": 28,
                "max_hp": 30,
                "moves": [33, 39, 0, 0],
                "attack": 14,
                "defense": 16,
                "speed": 12,
                "sp_attack": 12,
                "sp_defense": 13,
            }
        ],
    }
    with patch(
        "pokelive_bridge.main.ask_codex",
        return_value="Train your Squirtle to level 14",
    ) as mock_ask:
        response = client.post("/codex-chat", json=payload)
    assert response.status_code == 200
    called_party = mock_ask.call_args.kwargs.get("party") or mock_ask.call_args.args[2]
    assert called_party is not None
    assert called_party[0].species == 7


def test_codex_chat_forwards_oak_codex_prompt_to_ai_client() -> None:
    payload = {
        "map_group": 4,
        "map_num": 3,
        "x": 6,
        "y": 4,
        "frame": 446026,
    }
    oak_prompt = (
        "Professor Oak is speaking in Oak's Lab. "
        "Answer as Professor Codex using the current game state."
    )

    with patch("pokelive_bridge.main.ask_codex", return_value="The lab is ready. Professor Codex is online.") as ask_codex:
        response = client.post(
            "/codex-chat",
            json={
                "message": oak_prompt,
                "game_state": payload,
            },
        )

    assert response.status_code == 200
    ask_codex.assert_called_once()
    args = ask_codex.call_args.args
    forwarded_message = args[0]
    forwarded_state = args[1]
    assert forwarded_message == oak_prompt
    assert forwarded_state.map_group == 4
    assert forwarded_state.map_num == 3
    assert forwarded_state.x == 6
    assert forwarded_state.y == 4
