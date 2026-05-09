"""Counter-choice picker for Smart Gary's Battle 2 / Battle 3 setup.

Per-slot counter logic:
  rival slot 0 counters player slot 0 (the starter)
  rival slot 1 counters player slot 1 (the latest caught Pokemon)
  rival slot 2 (B3 only) is a complementary mon

Encoding (gRivalAIBuffer.counterChoice u8):
  counter_choice = starter_idx * 3 + caught_idx [+ 9 if Battle 3]

  starter_idx is the RIVAL's starter (the counter to player's starter):
    0 = rival CHARMANDER  (player picked Bulbasaur, grass)
    1 = rival SQUIRTLE    (player picked Charmander, fire)
    2 = rival BULBASAUR   (player picked Squirtle, water)

  caught_idx is the bucket for player's latest caught:
    0 = anti-Flying  (player has Pidgey, Spearow, Zubat, ...)
    1 = anti-Normal  (player has Rattata, Meowth, Doduo, ...)
    2 = Default      (anything else, including no second mon)

  B2 range: 0..8.   B3 range: 9..17.
"""

from __future__ import annotations

from typing import Any

# Species → primary (Gen 1) type. Keep tight — we only need to bucket the
# species the player can realistically have on the demo path before Pewter.
SPECIES_PRIMARY_TYPE: dict[int, str] = {
    1: "Grass", 2: "Grass", 3: "Grass",          # Bulbasaur line
    4: "Fire", 5: "Fire", 6: "Fire",             # Charmander line
    7: "Water", 8: "Water", 9: "Water",          # Squirtle line
    10: "Bug", 11: "Bug", 12: "Bug",             # Caterpie line
    13: "Bug", 14: "Bug", 15: "Bug",             # Weedle line
    16: "Flying", 17: "Flying", 18: "Flying",    # Pidgey line
    21: "Flying", 22: "Flying",                  # Spearow line
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
    66: "Fighting", 67: "Fighting", 68: "Fighting",
    69: "Grass", 70: "Grass", 71: "Grass",
    74: "Rock", 75: "Rock", 76: "Rock",          # Geodude line
    77: "Fire", 78: "Fire",                      # Ponyta line
    79: "Water", 80: "Water",                    # Slowpoke line
    81: "Electric", 82: "Electric",              # Magnemite line
    84: "Normal", 85: "Normal",                  # Doduo line
    92: "Ghost", 93: "Ghost", 94: "Ghost",
    95: "Rock",                                  # Onix
    100: "Electric", 101: "Electric",            # Voltorb line
    104: "Ground", 105: "Ground",                # Cubone line
    109: "Poison", 110: "Poison",                # Koffing line
    129: "Water", 130: "Water",                  # Magikarp / Gyarados
}

# Which rival starter counters which player starter type?
#   player Grass  -> rival Charmander (Fire beats Grass)         starter_idx 0
#   player Fire   -> rival Squirtle   (Water beats Fire)         starter_idx 1
#   player Water  -> rival Bulbasaur  (Grass beats Water)        starter_idx 2
_STARTER_COUNTER_IDX: dict[str, int] = {
    "Grass":  0,
    "Fire":   1,
    "Water":  2,
}

# Default starter_idx when player's starter type is unknown — pick rival
# Charmander (most demo-friendly: visible fire animations).
_DEFAULT_STARTER_IDX = 0

# Caught-bucket mapping for slot 1.
_CAUGHT_BUCKET: dict[str, int] = {
    "Flying":   0,
    "Normal":   1,
    # Everything else (Bug, Poison, Electric, Rock, Fire, Water, Grass, Fighting,
    # Ground, Ghost) falls through to the "Default" bucket.
}
_DEFAULT_CAUGHT_IDX = 2

_BATTLE_3_OFFSET = 9


def _species_type(species: int | None) -> str | None:
    if species is None:
        return None
    return SPECIES_PRIMARY_TYPE.get(int(species))


def _label_for(starter_idx: int, caught_idx: int, battle_index: int) -> str:
    starter_names = {0: "rival-Char", 1: "rival-Squirt", 2: "rival-Bulba"}
    caught_names = {0: "anti-Flying", 1: "anti-Normal", 2: "default"}
    return f"B{battle_index} {starter_names[starter_idx]} + {caught_names[caught_idx]}"


def pick_counter_choice(
    party: list[Any] | None,
    battle_index: int,
) -> tuple[int, str]:
    """Pick a counter-choice ID for the given battle (2 or 3).

    Inspects party[0] (player starter) to pick the rival's starter counter,
    and party[1] (latest caught) to pick the slot-1 counter bucket.
    """
    starter_idx = _DEFAULT_STARTER_IDX
    caught_idx = _DEFAULT_CAUGHT_IDX

    if party:
        starter_type = _species_type(getattr(party[0], "species", None))
        if starter_type and starter_type in _STARTER_COUNTER_IDX:
            starter_idx = _STARTER_COUNTER_IDX[starter_type]

        if len(party) >= 2:
            caught_type = _species_type(getattr(party[1], "species", None))
            if caught_type and caught_type in _CAUGHT_BUCKET:
                caught_idx = _CAUGHT_BUCKET[caught_type]

    base = starter_idx * 3 + caught_idx
    if battle_index == 3:
        base += _BATTLE_3_OFFSET

    return base, _label_for(starter_idx, caught_idx, battle_index)


def battle_index_for_trigger(trigger: str) -> int:
    if trigger == "first_capture":
        return 2
    if trigger == "second_capture":
        return 3
    return 0
