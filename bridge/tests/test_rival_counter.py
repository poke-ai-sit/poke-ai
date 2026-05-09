"""Unit tests for the rival counter-choice picker."""

from dataclasses import dataclass

from pokelive_bridge.rival_counter import (
    SPECIES_PRIMARY_TYPE,
    battle_index_for_trigger,
    pick_counter_choice,
    primary_type_of_party,
)


@dataclass
class _Mon:
    species: int
    level: int


# ---------------------------------------------------------------------------
# primary_type_of_party
# ---------------------------------------------------------------------------


def test_primary_type_picks_highest_level_member():
    # Charmander L8 (Fire) > Pidgey L5 (Flying)
    party = [_Mon(4, 8), _Mon(16, 5)]
    assert primary_type_of_party(party) == "Fire"


def test_primary_type_returns_none_for_empty_party():
    assert primary_type_of_party([]) is None
    assert primary_type_of_party(None) is None


def test_primary_type_handles_unknown_species_gracefully():
    # Unknown species 999 + known Bulbasaur L7 → Grass wins.
    party = [_Mon(999, 50), _Mon(1, 7)]
    assert primary_type_of_party(party) == "Grass"


def test_primary_type_returns_none_when_all_unknown():
    party = [_Mon(999, 50), _Mon(998, 30)]
    assert primary_type_of_party(party) is None


# ---------------------------------------------------------------------------
# pick_counter_choice
# ---------------------------------------------------------------------------


def test_pick_counter_battle_2_fire():
    party = [_Mon(4, 8)]  # Charmander
    choice, label = pick_counter_choice(party, 2)
    assert choice == 0
    assert label == "anti-fire"


def test_pick_counter_battle_2_water():
    party = [_Mon(7, 9)]  # Squirtle
    choice, label = pick_counter_choice(party, 2)
    assert choice == 1
    assert label == "anti-water"


def test_pick_counter_battle_2_grass():
    party = [_Mon(1, 7)]  # Bulbasaur
    choice, label = pick_counter_choice(party, 2)
    assert choice == 2
    assert label == "anti-grass"


def test_pick_counter_battle_2_flying_pidgey_dominant():
    party = [_Mon(16, 9), _Mon(10, 4)]  # Pidgey + Caterpie
    choice, label = pick_counter_choice(party, 2)
    assert choice == 3
    assert label == "anti-flying"


def test_pick_counter_battle_2_bug_caterpie_dominant():
    party = [_Mon(10, 8), _Mon(16, 5)]  # Caterpie + Pidgey
    choice, label = pick_counter_choice(party, 2)
    assert choice == 4
    assert label == "anti-bug"


def test_pick_counter_battle_2_balanced_when_lead_is_normal():
    party = [_Mon(19, 8)]  # Rattata (Normal)
    choice, label = pick_counter_choice(party, 2)
    assert choice == 5
    assert label == "balanced"


def test_pick_counter_battle_3_offsets_by_six():
    # Same Charmander team as battle 2 fire test → ID 0 + 6 = 6
    party = [_Mon(4, 12)]
    choice, label = pick_counter_choice(party, 3)
    assert choice == 6
    assert label == "anti-fire"


def test_pick_counter_battle_3_balanced():
    party = [_Mon(19, 11)]  # Rattata
    choice, label = pick_counter_choice(party, 3)
    assert choice == 11
    assert label == "balanced"


def test_pick_counter_empty_party_returns_balanced():
    choice, label = pick_counter_choice([], 2)
    assert choice == 5
    assert label == "balanced"


# ---------------------------------------------------------------------------
# battle_index_for_trigger
# ---------------------------------------------------------------------------


def test_battle_index_first_capture_is_2():
    assert battle_index_for_trigger("first_capture") == 2


def test_battle_index_pewter_step_is_3():
    assert battle_index_for_trigger("pewter_step") == 3


def test_battle_index_unknown_returns_zero():
    assert battle_index_for_trigger("caught_pokemon") == 0
    assert battle_index_for_trigger("won_battle") == 0


# ---------------------------------------------------------------------------
# Coverage sanity — the species table at minimum maps the 3 starters
# ---------------------------------------------------------------------------


def test_species_table_covers_starters():
    assert SPECIES_PRIMARY_TYPE[1] == "Grass"
    assert SPECIES_PRIMARY_TYPE[4] == "Fire"
    assert SPECIES_PRIMARY_TYPE[7] == "Water"
