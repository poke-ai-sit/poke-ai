"""Pokémon FireRed map ID → human-readable name lookup.

Sourced from pokefirered/include/constants/map_groups.h. Covers the early-game
scope (Pallet Town through Pewter Gym) plus the buildings the player commonly
transitions through, so the rival's prompt and memory log read like locations
rather than raw integer pairs.
"""

# (map_group, map_num) → name
MAP_NAMES: dict[tuple[int, int], str] = {
    # Group 1 — Viridian Forest
    (1, 0): "Viridian Forest",
    # Group 3 — outdoor overworld (Kanto south)
    (3, 0): "Pallet Town",
    (3, 1): "Viridian City",
    (3, 2): "Pewter City",
    (3, 19): "Route 1",
    (3, 20): "Route 2",
    (3, 41): "Route 22",
    # Group 4 — Pallet Town interiors
    (4, 0): "Players House 1F",
    (4, 1): "Players House 2F",
    (4, 2): "Rivals House",
    (4, 3): "Professor Oaks Lab",
    # Group 5 — Viridian City interiors
    (5, 0): "Viridian House",
    (5, 1): "Viridian Gym",
    (5, 2): "Viridian School",
    (5, 3): "Viridian Mart",
    (5, 4): "Viridian Pokemon Center 1F",
    (5, 5): "Viridian Pokemon Center 2F",
    # Group 6 — Pewter City interiors
    (6, 0): "Pewter Museum 1F",
    (6, 1): "Pewter Museum 2F",
    (6, 2): "Pewter Gym",
    (6, 3): "Pewter Mart",
    (6, 4): "Pewter House",
    (6, 5): "Pewter Pokemon Center 1F",
    (6, 6): "Pewter Pokemon Center 2F",
    (6, 7): "Pewter House 2",
}


def map_name(map_group: int, map_num: int) -> str:
    """Return a human-readable name for the given map ID, with fallback."""
    return MAP_NAMES.get((map_group, map_num), f"area {map_group}:{map_num}")


def resolve_map_signature(sig: str) -> str:
    """Translate a 'group:num' signature (as Lua sends it) to a name."""
    try:
        group_str, num_str = sig.split(":", 1)
        return map_name(int(group_str), int(num_str))
    except (ValueError, AttributeError):
        return sig
