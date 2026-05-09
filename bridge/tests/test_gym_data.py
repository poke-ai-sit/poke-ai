import pytest
from pokelive_bridge.gym_data import (
    GYM_SEQUENCE,
    gym_for_location,
    is_super_effective,
    move_type,
)


# ---------------------------------------------------------------------------
# gym_for_location
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_pallet_town_maps_to_brock() -> None:
    assert gym_for_location(3, 0).leader == "Brock"


@pytest.mark.unit
def test_viridian_forest_maps_to_brock() -> None:
    assert gym_for_location(1, 0).leader == "Brock"


@pytest.mark.unit
def test_pewter_city_maps_to_brock() -> None:
    assert gym_for_location(3, 2).leader == "Brock"


@pytest.mark.unit
def test_oaks_lab_maps_to_brock() -> None:
    # MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB = (3 | (4 << 8))
    assert gym_for_location(4, 3).leader == "Brock"


@pytest.mark.unit
def test_cerulean_city_maps_to_misty() -> None:
    assert gym_for_location(3, 3).leader == "Misty"


@pytest.mark.unit
def test_mt_moon_maps_to_misty() -> None:
    assert gym_for_location(1, 1).leader == "Misty"


@pytest.mark.unit
def test_vermilion_city_maps_to_lt_surge() -> None:
    assert gym_for_location(3, 5).leader == "Lt Surge"


@pytest.mark.unit
def test_celadon_city_maps_to_erika() -> None:
    assert gym_for_location(3, 6).leader == "Erika"


@pytest.mark.unit
def test_unknown_map_defaults_to_brock() -> None:
    assert gym_for_location(99, 99).leader == "Brock"


@pytest.mark.unit
def test_gym_sequence_has_four_entries() -> None:
    assert len(GYM_SEQUENCE) == 4


# ---------------------------------------------------------------------------
# move_type
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_move_type_water_gun() -> None:
    assert move_type(55) == "Water"


@pytest.mark.unit
def test_move_type_thundershock() -> None:
    assert move_type(84) == "Electric"


@pytest.mark.unit
def test_move_type_ember() -> None:
    assert move_type(52) == "Fire"


@pytest.mark.unit
def test_move_type_vine_whip() -> None:
    assert move_type(22) == "Grass"


@pytest.mark.unit
def test_move_type_earthquake() -> None:
    assert move_type(89) == "Ground"


@pytest.mark.unit
def test_move_type_tackle() -> None:
    assert move_type(33) == "Normal"


@pytest.mark.unit
def test_move_type_unknown_returns_none() -> None:
    assert move_type(99999) is None


# ---------------------------------------------------------------------------
# is_super_effective — gym-relevant matchups
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_water_super_effective_vs_rock_ground() -> None:
    # Brock's Gym
    assert is_super_effective("Water", ["Rock", "Ground"]) is True


@pytest.mark.unit
def test_grass_super_effective_vs_rock_ground() -> None:
    assert is_super_effective("Grass", ["Rock", "Ground"]) is True


@pytest.mark.unit
def test_electric_super_effective_vs_water() -> None:
    # Misty's Gym
    assert is_super_effective("Electric", ["Water"]) is True


@pytest.mark.unit
def test_ground_super_effective_vs_electric() -> None:
    # Lt Surge's Gym
    assert is_super_effective("Ground", ["Electric"]) is True


@pytest.mark.unit
def test_fire_super_effective_vs_grass_poison() -> None:
    # Erika's Gym — Fire hits Grass super-effectively
    assert is_super_effective("Fire", ["Grass", "Poison"]) is True


@pytest.mark.unit
def test_psychic_super_effective_vs_poison() -> None:
    # Erika's Gym — Psychic hits Poison
    assert is_super_effective("Psychic", ["Grass", "Poison"]) is True


@pytest.mark.unit
def test_normal_not_super_effective_vs_rock() -> None:
    assert is_super_effective("Normal", ["Rock"]) is False


@pytest.mark.unit
def test_normal_not_super_effective_vs_ground() -> None:
    assert is_super_effective("Normal", ["Ground"]) is False


@pytest.mark.unit
def test_fighting_super_effective_vs_rock() -> None:
    # Karate Chop/Low Kick are Fighting — super-effective vs Brock's Rock
    assert is_super_effective("Fighting", ["Rock", "Ground"]) is True


@pytest.mark.unit
def test_karate_chop_is_fighting_type() -> None:
    # Karate Chop = move_id 2; Fighting in FireRed (was Normal in Gen 1)
    assert move_type(2) == "Fighting"
