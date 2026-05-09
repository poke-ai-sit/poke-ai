from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from pokelive_bridge.openai_client import FALLBACK_RESPONSE, ask_codex


def _make_state(map_group: int = 4, map_num: int = 1, x: int = 9, y: int = 4) -> object:
    class _State:
        pass

    state = _State()
    state.map_group = map_group
    state.map_num = map_num
    state.x = x
    state.y = y
    return state


def _mock_completion(text: str) -> MagicMock:
    choice = MagicMock()
    choice.message.content = text
    return MagicMock(choices=[choice])


def test_ask_codex_returns_response_text() -> None:
    state = _make_state()
    expected = "Head north to Route 1, young researcher!"

    with patch("pokelive_bridge.openai_client._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion(expected)
        result = ask_codex("What should I do next?", state)

    assert result == expected


def test_ask_codex_strips_whitespace_from_response() -> None:
    state = _make_state()

    with patch("pokelive_bridge.openai_client._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion(
            "  Hello there!  \n"
        )
        result = ask_codex("Hello?", state)

    assert result == "Hello there!"


def test_ask_codex_returns_fallback_on_api_error() -> None:
    state = _make_state()

    with patch("pokelive_bridge.openai_client._client") as mock_client:
        mock_client.chat.completions.create.side_effect = Exception("network error")
        result = ask_codex("What should I do?", state)

    assert result == FALLBACK_RESPONSE


def test_ask_codex_sends_game_state_in_system_prompt() -> None:
    state = _make_state(map_group=3, map_num=0, x=11, y=6)

    with patch("pokelive_bridge.openai_client._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion("ok")
        ask_codex("Where am I?", state)

    call_args = mock_client.chat.completions.create.call_args
    messages = call_args.kwargs["messages"]
    system_content = messages[0]["content"]
    assert "3" in system_content
    assert "0" in system_content


def test_ask_codex_sends_party_in_ask_system_prompt() -> None:
    state = _make_state()
    party = [
        SimpleNamespace(
            species=4,
            level=8,
            hp=22,
            max_hp=24,
            moves=[10, 45, 0, 0],
            attack=11,
            defense=9,
            speed=14,
            sp_attack=10,
            sp_defense=9,
        )
    ]

    with patch("pokelive_bridge.openai_client._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion("ok")
        ask_codex("Who is in my party?", state, party=party, request_kind="ASK")

    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    system_content = messages[0]["content"]
    assert "<party>" in system_content
    assert "PRATA" in system_content


def test_ask_codex_uses_enough_completion_tokens_for_reasoning_model() -> None:
    state = _make_state()

    with patch("pokelive_bridge.openai_client._client") as mock_client:
        mock_client.chat.completions.create.return_value = _mock_completion("ok")
        ask_codex("Where am I?", state)

    call_args = mock_client.chat.completions.create.call_args
    assert call_args.kwargs["max_completion_tokens"] >= 512
