from unittest.mock import MagicMock, patch

import pytest

from pokelive_bridge import pokemon_data
from pokelive_bridge.pokemon_data import move_name, species_name


def _mock_get(json_body: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = json_body
    return resp


@pytest.fixture(autouse=True)
def clear_lru_caches() -> None:
    pokemon_data.species_name.cache_clear()
    pokemon_data.move_name.cache_clear()


# ---------------------------------------------------------------------------
# Offline species lookups (no network call expected)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_species_name_charmander_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert species_name(4) == "CHARMANDER"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_species_name_rattata_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert species_name(19) == "RATTATA"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_species_name_squirtle_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert species_name(7) == "SQUIRTLE"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_species_name_all_gen1_covered() -> None:
    from pokelive_bridge.gym_data import SPECIES_NAMES
    assert len(SPECIES_NAMES) == 151
    for dex in range(1, 152):
        assert dex in SPECIES_NAMES, f"Species {dex} missing from offline table"


@pytest.mark.unit
def test_species_name_zero_skips_api() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        result = species_name(0)
    assert result == "#0"
    mock_get.assert_not_called()


# ---------------------------------------------------------------------------
# Fallback to PokéAPI for IDs not in offline table
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_species_name_unknown_id_calls_pokeapi() -> None:
    with patch(
        "pokelive_bridge.pokemon_data.httpx.get",
        return_value=_mock_get({"name": "custom-mon"}),
    ) as mock_get:
        assert species_name(9999) == "CUSTOM-MON"
    mock_get.assert_called_once()


@pytest.mark.unit
def test_species_name_falls_back_to_custom_label_on_error() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get", side_effect=Exception("timeout")):
        assert species_name(9999) == "CUSTOM#9999"


# ---------------------------------------------------------------------------
# Offline move lookups (no network call expected)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_move_name_scratch_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert move_name(10) == "SCRATCH"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_move_name_tackle_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert move_name(33) == "TACKLE"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_move_name_water_gun_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert move_name(55) == "WATER GUN"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_move_name_growl_offline() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        assert move_name(45) == "GROWL"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_move_name_zero_skips_api() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get") as mock_get:
        result = move_name(0)
    assert result == "#0"
    mock_get.assert_not_called()


@pytest.mark.unit
def test_move_name_unknown_id_calls_pokeapi() -> None:
    with patch(
        "pokelive_bridge.pokemon_data.httpx.get",
        return_value=_mock_get({"name": "hyper-voice"}),
    ) as mock_get:
        assert move_name(304) == "HYPER VOICE"
    mock_get.assert_called_once()


@pytest.mark.unit
def test_move_name_falls_back_on_error() -> None:
    with patch("pokelive_bridge.pokemon_data.httpx.get", side_effect=Exception("network")):
        assert move_name(9999) == "MOVE#9999"


# ---------------------------------------------------------------------------
# Caching — use an ID that goes through PokéAPI (not in offline table)
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_species_name_cached_after_first_call() -> None:
    with patch(
        "pokelive_bridge.pokemon_data.httpx.get",
        return_value=_mock_get({"name": "custom-mon"}),
    ) as mock_get:
        species_name(9998)
        species_name(9998)
    assert mock_get.call_count == 1


@pytest.mark.unit
def test_move_name_cached_after_first_call() -> None:
    with patch(
        "pokelive_bridge.pokemon_data.httpx.get",
        return_value=_mock_get({"name": "hyper-voice"}),
    ) as mock_get:
        move_name(304)
        move_name(304)
    assert mock_get.call_count == 1
