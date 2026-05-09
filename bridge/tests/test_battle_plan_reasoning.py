"""Tests for the reasoning_steps chain-of-thought added to plan_battle."""

import json
import types
from unittest.mock import MagicMock, patch

import pytest

from pokelive_bridge.battle_agent import plan_battle, _record_battle_plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_party_entry(**kwargs):
    defaults = dict(species=4, level=5, hp=20, max_hp=20, moves=[10, 0, 0, 0],
                    attack=11, defense=11, speed=10, sp_attack=11, sp_defense=11, status=None)
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def _make_gpt_response(payload: dict) -> MagicMock:
    msg = MagicMock()
    msg.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# reasoning_steps parsing
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_plan_battle_returns_reasoning_steps_from_gpt():
    payload = {
        "reasoning_steps": ["Player leads Charmander (Fire)", "Squirtle has advantage", "Boost Water Gun +15"],
        "counter_choice": 0,
        "move_scores": [15, 0, 0, 0],
        "opening_taunt": "You wont last long.",
        "strategy_summary": "Type advantage play.",
    }
    with patch("pokelive_bridge.battle_agent._get_client") as mock_client, \
         patch("pokelive_bridge.battle_agent._append_memory"):
        mock_client.return_value.chat.completions.create.return_value = _make_gpt_response(payload)
        result = plan_battle("battle_1_oaks_lab", [_make_party_entry()])

    assert result["reasoning_steps"] == [
        "Player leads Charmander (Fire)",
        "Squirtle has advantage",
        "Boost Water Gun +15",
    ]


@pytest.mark.unit
def test_plan_battle_reasoning_steps_capped_at_4():
    steps = [f"step {i}" for i in range(10)]
    payload = {
        "reasoning_steps": steps,
        "counter_choice": 0,
        "move_scores": [0, 0, 0, 0],
        "opening_taunt": "Lets go.",
        "strategy_summary": "test",
    }
    with patch("pokelive_bridge.battle_agent._get_client") as mock_client, \
         patch("pokelive_bridge.battle_agent._append_memory"):
        mock_client.return_value.chat.completions.create.return_value = _make_gpt_response(payload)
        result = plan_battle("battle_1_oaks_lab", [_make_party_entry()])

    assert len(result["reasoning_steps"]) == 4


@pytest.mark.unit
def test_plan_battle_reasoning_steps_truncated_to_80_chars():
    long_step = "x" * 200
    payload = {
        "reasoning_steps": [long_step],
        "counter_choice": 0,
        "move_scores": [0, 0, 0, 0],
        "opening_taunt": "Lets go.",
        "strategy_summary": "test",
    }
    with patch("pokelive_bridge.battle_agent._get_client") as mock_client, \
         patch("pokelive_bridge.battle_agent._append_memory"):
        mock_client.return_value.chat.completions.create.return_value = _make_gpt_response(payload)
        result = plan_battle("battle_1_oaks_lab", [_make_party_entry()])

    assert len(result["reasoning_steps"][0]) == 80


@pytest.mark.unit
def test_plan_battle_reasoning_steps_empty_when_missing():
    payload = {
        "counter_choice": 0,
        "move_scores": [0, 0, 0, 0],
        "opening_taunt": "Lets go.",
        "strategy_summary": "test",
    }
    with patch("pokelive_bridge.battle_agent._get_client") as mock_client, \
         patch("pokelive_bridge.battle_agent._append_memory"):
        mock_client.return_value.chat.completions.create.return_value = _make_gpt_response(payload)
        result = plan_battle("battle_1_oaks_lab", [_make_party_entry()])

    assert result["reasoning_steps"] == []


@pytest.mark.unit
def test_plan_battle_reasoning_steps_empty_on_gpt_failure():
    with patch("pokelive_bridge.battle_agent._get_client") as mock_client, \
         patch("pokelive_bridge.battle_agent._append_memory"):
        mock_client.return_value.chat.completions.create.side_effect = RuntimeError("API down")
        result = plan_battle("battle_1_oaks_lab", [_make_party_entry()])

    assert result["reasoning_steps"] == []
    # Fallback values still present
    assert result["counter_choice"] == 0
    assert len(result["move_scores"]) == 4


# ---------------------------------------------------------------------------
# _record_battle_plan includes reasoning in memory
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_record_battle_plan_writes_reasoning_to_memory():
    steps = ["Observed fire type", "Led with water"]
    with patch("pokelive_bridge.battle_agent._append_memory") as mock_append:
        _record_battle_plan("battle_1_oaks_lab", 0, [15, 0, 0, 0], "type advantage", steps)

    written = mock_append.call_args[0][0]
    assert "Reasoning:" in written
    assert "Observed fire type" in written
    assert "Led with water" in written


@pytest.mark.unit
def test_record_battle_plan_without_reasoning_is_valid():
    with patch("pokelive_bridge.battle_agent._append_memory") as mock_append:
        _record_battle_plan("battle_1_oaks_lab", 0, [0, 0, 0, 0], "fallback", [])

    written = mock_append.call_args[0][0]
    assert "PLAN" in written
    assert "Reasoning:" not in written
