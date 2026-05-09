import pytest
from pokelive_bridge.prompts import (
    ADVICE_HINT,  # noqa: F401 — imported for hint-content tests
    CODEX_ADVICE_PROMPT,
    build_codex_advice_prompt,
    build_codex_system_prompt,
    build_codex_system_prompt_advice,
    build_codex_system_prompt_ask,
)


def _make_state(map_group: int = 4, map_num: int = 1, x: int = 9, y: int = 4) -> object:
    class _State:
        pass

    s = _State()
    s.map_group = map_group
    s.map_num = map_num
    s.x = x
    s.y = y
    return s


class _PartyEntry:
    def __init__(
        self,
        species: int,
        level: int,
        hp: int,
        max_hp: int,
        moves: list[int],
        attack: int,
        defense: int,
        speed: int,
        sp_attack: int,
        sp_defense: int,
    ) -> None:
        self.species = species
        self.level = level
        self.hp = hp
        self.max_hp = max_hp
        self.moves = moves
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.sp_attack = sp_attack
        self.sp_defense = sp_defense


def test_advice_prompt_contains_persona() -> None:
    prompt = build_codex_system_prompt_advice(_make_state())
    assert "Professor GPT 5.5" in prompt


def test_advice_prompt_enforces_40_char_constraint() -> None:
    prompt = build_codex_system_prompt_advice(_make_state())
    assert "40 characters" in prompt


def test_advice_prompt_injects_map_and_position() -> None:
    prompt = build_codex_system_prompt_advice(_make_state(map_group=3, map_num=0, x=11, y=6))
    assert "3" in prompt and "0" in prompt
    assert "11" in prompt and "6" in prompt


def test_advice_prompt_includes_party_block_when_party_given() -> None:
    party = [_PartyEntry(7, 10, 28, 30, [33, 39, 0, 0], 14, 16, 12, 12, 13)]
    prompt = build_codex_system_prompt_advice(_make_state(), party=party)
    assert "SQUIRTLE" in prompt
    assert "L10" in prompt


def test_advice_prompt_omits_party_block_when_party_is_none() -> None:
    prompt = build_codex_system_prompt_advice(_make_state(), party=None)
    assert "<party>" not in prompt


def test_advice_prompt_omits_party_block_when_party_is_empty() -> None:
    prompt = build_codex_system_prompt_advice(_make_state(), party=[])
    assert "<party>" not in prompt


def test_ask_prompt_does_not_include_party_block() -> None:
    party = [_PartyEntry(4, 8, 22, 24, [10, 45, 0, 0], 11, 9, 14, 10, 9)]
    prompt = build_codex_system_prompt_ask(_make_state(), party=party)
    assert "<party>" not in prompt


def test_backward_compat_alias_returns_ask_prompt() -> None:
    prompt = build_codex_system_prompt(_make_state())
    assert "Professor GPT 5.5" in prompt


def test_advice_prompt_fixed_text() -> None:
    assert CODEX_ADVICE_PROMPT == "What should I do next."


def test_advice_user_prompt_includes_map_and_position() -> None:
    prompt = build_codex_advice_prompt(_make_state(map_group=4, map_num=3, x=6, y=4))
    assert "map 4:3" in prompt
    assert "position 6,4" in prompt
    assert "healing" in prompt
    assert "type weaknesses" in prompt


def test_advice_prompt_lists_all_party_members() -> None:
    # Both Pokémon should appear in the party block — no filtering or reordering
    party = [
        _PartyEntry(4, 5, 18, 20, [10, 0, 0, 0], 11, 9, 12, 11, 9),   # Charmander L5
        _PartyEntry(19, 3, 11, 11, [33, 0, 0, 0], 7, 6, 9, 5, 5),      # Rattata L3
    ]
    prompt = build_codex_system_prompt_advice(_make_state(), party=party)
    assert "CHARMANDER" in prompt
    assert "RATTATA" in prompt
    assert "FOCUS:" not in prompt


def test_advice_prompt_preserves_party_order() -> None:
    # Party block should list Pokémon in their original slot order (Charmander first)
    party = [
        _PartyEntry(4, 5, 18, 20, [10, 0, 0, 0], 11, 9, 12, 11, 9),   # Charmander L5 slot 0
        _PartyEntry(19, 3, 11, 11, [33, 0, 0, 0], 7, 6, 9, 5, 5),      # Rattata L3 slot 1
    ]
    prompt = build_codex_system_prompt_advice(_make_state(), party=party)
    party_start = prompt.index("<party>")
    party_section = prompt[party_start:]
    assert party_section.find("CHARMANDER") < party_section.find("RATTATA")


def test_advice_hint_references_coverage_and_training() -> None:
    assert "coverage" in ADVICE_HINT.lower() or "MISSING" in ADVICE_HINT
    assert "train" in ADVICE_HINT.lower()


# ---------------------------------------------------------------------------
# Gym context block tests
# ---------------------------------------------------------------------------


def test_advice_prompt_includes_gym_block() -> None:
    # Pallet Town exterior (map_group=3, map_num=0)
    prompt = build_codex_system_prompt_advice(_make_state(map_group=3, map_num=0))
    assert "<gym>" in prompt
    assert "Brock" in prompt


def test_advice_prompt_gym_block_shows_rock_ground_for_brock() -> None:
    prompt = build_codex_system_prompt_advice(_make_state(map_group=3, map_num=0))
    assert "Rock" in prompt
    assert "Ground" in prompt


def test_advice_prompt_warns_missing_coverage_vs_brock() -> None:
    # Rattata L3 with only Tackle (Normal, id=33) and Tail Whip (Normal, id=39)
    # — no Water or Grass move, so coverage vs Rock/Ground is MISSING
    party = [_PartyEntry(19, 3, 11, 11, [33, 39, 0, 0], 7, 6, 9, 5, 5)]
    prompt = build_codex_system_prompt_advice(
        _make_state(map_group=3, map_num=0), party=party
    )
    assert "MISSING" in prompt


def test_advice_prompt_coverage_ok_when_water_gun_present() -> None:
    # Squirtle L10 with Water Gun (id=55) — super-effective vs Rock/Ground
    party = [_PartyEntry(7, 10, 28, 30, [33, 55, 0, 0], 14, 16, 12, 12, 13)]
    prompt = build_codex_system_prompt_advice(
        _make_state(map_group=3, map_num=0), party=party
    )
    assert "Party coverage: OK" in prompt


def test_advice_prompt_warns_when_party_underleveled_for_brock() -> None:
    # Squirtle L6 — below Brock's recommended L14
    party = [_PartyEntry(7, 6, 18, 20, [33, 55, 0, 0], 10, 12, 10, 10, 10)]
    prompt = build_codex_system_prompt_advice(
        _make_state(map_group=3, map_num=0), party=party
    )
    assert "Level warning" in prompt
    assert "L6" in prompt


def test_advice_prompt_no_level_warning_when_ready() -> None:
    # Squirtle L14 — at Brock's recommended level
    party = [_PartyEntry(7, 14, 40, 44, [33, 55, 0, 0], 18, 20, 14, 14, 14)]
    prompt = build_codex_system_prompt_advice(
        _make_state(map_group=3, map_num=0), party=party
    )
    assert "Level warning" not in prompt
    assert "Level status" in prompt


def test_advice_prompt_shows_misty_for_cerulean_coords() -> None:
    # MAP_CERULEAN_CITY = (3 | (3 << 8)) → map_group=3, map_num=3
    prompt = build_codex_system_prompt_advice(_make_state(map_group=3, map_num=3))
    assert "Misty" in prompt


def test_advice_prompt_shows_lt_surge_for_vermilion_coords() -> None:
    # MAP_VERMILION_CITY = (5 | (3 << 8)) → map_group=3, map_num=5
    prompt = build_codex_system_prompt_advice(_make_state(map_group=3, map_num=5))
    assert "Lt Surge" in prompt


def test_advice_prompt_shows_erika_for_celadon_coords() -> None:
    # MAP_CELADON_CITY = (6 | (3 << 8)) → map_group=3, map_num=6
    prompt = build_codex_system_prompt_advice(_make_state(map_group=3, map_num=6))
    assert "Erika" in prompt


def test_advice_prompt_coverage_ok_with_karate_chop_vs_brock() -> None:
    # Mankey with Karate Chop (id=2, Fighting) — super-effective vs Rock/Ground
    party = [_PartyEntry(56, 7, 22, 24, [2, 33, 0, 0], 12, 8, 13, 8, 8)]
    prompt = build_codex_system_prompt_advice(
        _make_state(map_group=3, map_num=0), party=party
    )
    assert "Party coverage: OK" in prompt


def test_gym_block_length_under_300_chars() -> None:
    # Budget regression — gym block alone must not balloon the prompt
    from pokelive_bridge.prompts import _gym_context_block
    block = _gym_context_block(_make_state(map_group=3, map_num=0), party=None)
    assert len(block) < 300, f"Gym block too large: {len(block)} chars"
