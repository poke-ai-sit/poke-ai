"""Counter-choice picker for Smart Gary's Battle 2 / Battle 3 setup.

The picker is intentionally hard-coded and offline — no PokéAPI calls at
runtime. Given a player's party, it identifies a primary type (the type of
the highest-level party member) and maps that to one of six bucket choices.

counterChoice ID assignments (gRivalAIBuffer.counterChoice u8):
  Battle 2 (low level, 7-9):
    0 = anti-fire   (player's strongest mon is fire)
    1 = anti-water  (player's strongest mon is water)
    2 = anti-grass  (player's strongest mon is grass)
    3 = anti-flying (player has heavy flying — Pidgey/Spearow dominant)
    4 = anti-bug    (player has bug-heavy team — Caterpie/Weedle dominant)
    5 = balanced    (no clear lead / mixed)
  Battle 3 (mid level, 11-13): same scheme, +6 offset
    6  = anti-fire
    7  = anti-water
    8  = anti-grass
    9  = anti-flying
    10 = anti-bug
    11 = balanced
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Species → primary (Gen 1) type. Only species realistically catchable on
# Routes 1/2/22 + Viridian Forest + early dungeons before Pewter are mapped
# in detail; everything else falls through to None and the picker returns
# "balanced".
# ---------------------------------------------------------------------------
SPECIES_PRIMARY_TYPE: dict[int, str] = {
    # Starters
    1: "Grass", 2: "Grass", 3: "Grass",          # Bulbasaur line
    4: "Fire", 5: "Fire", 6: "Fire",             # Charmander line
    7: "Water", 8: "Water", 9: "Water",          # Squirtle line
    # Bug — Viridian Forest staples
    10: "Bug", 11: "Bug", 12: "Bug",             # Caterpie line
    13: "Bug", 14: "Bug", 15: "Bug",             # Weedle line
    # Flying — Route 1/2 staples
    16: "Flying", 17: "Flying", 18: "Flying",    # Pidgey line (Normal/Flying — Flying primary for our purposes)
    21: "Flying", 22: "Flying",                  # Spearow line
    # Other early-route critters (mostly Normal/Poison; map for completeness)
    19: "Normal", 20: "Normal",                  # Rattata line
    23: "Poison", 24: "Poison",                  # Ekans line
    25: "Electric", 26: "Electric",              # Pikachu line
    27: "Ground", 28: "Ground",                  # Sandshrew line
    29: "Poison", 30: "Poison", 31: "Poison",    # Nidoran F line
    32: "Poison", 33: "Poison", 34: "Poison",    # Nidoran M line
    35: "Normal", 36: "Normal",                  # Clefairy line
    37: "Fire", 38: "Fire",                      # Vulpix line
    39: "Normal", 40: "Normal",                  # Jigglypuff line
    41: "Poison", 42: "Poison",                  # Zubat line
    43: "Grass", 44: "Grass", 45: "Grass",       # Oddish line
    46: "Bug", 47: "Bug",                        # Paras line
    48: "Bug", 49: "Bug",                        # Venonat line
    50: "Ground", 51: "Ground",                  # Diglett line
    52: "Normal", 53: "Normal",                  # Meowth line
    54: "Water", 55: "Water",                    # Psyduck line
    56: "Fighting", 57: "Fighting",              # Mankey line
    58: "Fire", 59: "Fire",                      # Growlithe line
    60: "Water", 61: "Water", 62: "Water",       # Poliwag line
    66: "Fighting", 67: "Fighting", 68: "Fighting",  # Machop line
    69: "Grass", 70: "Grass", 71: "Grass",       # Bellsprout line
    74: "Rock", 75: "Rock", 76: "Rock",          # Geodude line
    77: "Fire", 78: "Fire",                      # Ponyta line
    79: "Water", 80: "Water",                    # Slowpoke line
    81: "Electric", 82: "Electric",              # Magnemite line
    84: "Normal", 85: "Normal",                  # Doduo line
    92: "Ghost", 93: "Ghost", 94: "Ghost",       # Gastly line
    95: "Rock",                                  # Onix
    100: "Electric", 101: "Electric",            # Voltorb line
    104: "Ground", 105: "Ground",                # Cubone line
    109: "Poison", 110: "Poison",                # Koffing line
    129: "Water", 130: "Water",                  # Magikarp / Gyarados
}

# The five "anti-X" bucket types (in counter-choice ID order).
_BUCKETS_BATTLE_2 = {
    "Fire": 0,
    "Water": 1,
    "Grass": 2,
    "Flying": 3,
    "Bug": 4,
}
_BALANCED_BATTLE_2 = 5
_BATTLE_3_OFFSET = 6


def primary_type_of_party(party: list[Any] | None) -> str | None:
    """Return the type of the highest-level party member, or None if unknown.

    Tie-break on level: pick the first mon at that level (Lua sends slot order).
    Falls back to None if every member's species isn't in SPECIES_PRIMARY_TYPE.
    """
    if not party:
        return None

    # Find the highest level member that has a known type.
    best_level = -1
    best_type: str | None = None
    for entry in party:
        species = getattr(entry, "species", None)
        if species is None:
            continue
        ptype = SPECIES_PRIMARY_TYPE.get(int(species))
        if ptype is None:
            continue
        level = int(getattr(entry, "level", 0) or 0)
        if level > best_level:
            best_level = level
            best_type = ptype

    return best_type


def pick_counter_choice(
    party: list[Any] | None,
    battle_index: int,
) -> tuple[int, str]:
    """Pick a counter-choice ID for the given battle (2 or 3).

    Returns a tuple of (counter_choice_id, label).
      - id is in [0..5] for battle 2, [6..11] for battle 3.
      - label is a short human-readable bucket name like "anti-fire".
    """
    primary = primary_type_of_party(party)

    if primary in _BUCKETS_BATTLE_2:
        bucket_id = _BUCKETS_BATTLE_2[primary]
        label = f"anti-{primary.lower()}"
    else:
        bucket_id = _BALANCED_BATTLE_2
        label = "balanced"

    if battle_index == 3:
        return (bucket_id + _BATTLE_3_OFFSET, label)
    # Default / battle_index == 2
    return (bucket_id, label)


def battle_index_for_trigger(trigger: str) -> int:
    """Map a /rival-event trigger to its corresponding battle index (2 or 3).

    Returns 0 for triggers that don't map to a battle setup (caller should
    treat the picker output as ignorable in that case).
    """
    if trigger == "first_capture":
        return 2
    if trigger == "pewter_step":
        return 3
    return 0
