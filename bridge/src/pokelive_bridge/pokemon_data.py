import logging
from functools import lru_cache

import httpx

from pokelive_bridge.gym_data import move_name_offline, species_name_offline

_POKEAPI = "https://pokeapi.co/api/v2"
_TIMEOUT = 5.0


@lru_cache(maxsize=512)
def species_name(species_id: int) -> str:
    """Return uppercase species name for a numeric species ID.

    Checks the patched-ROM offline table first (instant, no network).
    Falls back to PokéAPI for species IDs not in the offline table.
    Custom Pokémon injected outside known slots fall back to 'CUSTOM#<id>'.
    """
    if species_id <= 0:
        return f"#{species_id}"

    offline = species_name_offline(species_id)
    if offline is not None:
        return offline

    try:
        resp = httpx.get(
            f"{_POKEAPI}/pokemon-species/{species_id}/",
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["name"].upper()
    except Exception as exc:
        logging.warning("PokéAPI species lookup failed for id=%d: %s", species_id, exc)
        return f"CUSTOM#{species_id}"


@lru_cache(maxsize=512)
def move_name(move_id: int) -> str:
    """Return uppercase move name for a numeric move ID.

    Checks the offline Gen 1 table first (instant, no network).
    Falls back to PokéAPI for moves not in the offline table.
    """
    if move_id <= 0:
        return f"#{move_id}"

    offline = move_name_offline(move_id)
    if offline is not None:
        return offline

    try:
        resp = httpx.get(
            f"{_POKEAPI}/move/{move_id}/",
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        raw = resp.json()["name"]
        return raw.upper().replace("-", " ")
    except Exception as exc:
        logging.warning("PokéAPI move lookup failed for id=%d: %s", move_id, exc)
        return f"MOVE#{move_id}"
