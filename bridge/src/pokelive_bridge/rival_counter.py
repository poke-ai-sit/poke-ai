"""Counter picker for Smart Gary.

Two outputs per call:

1. ``pick_rival_party(player_party, battle_index)`` — a list of
   ``RivalSlot(species, level, moves[4])`` tuples. The ROM-side hook
   ``ApplyPokeliveRivalPartyOverride`` materialises this list directly
   into ``gEnemyParty`` at battle setup time, so the rival shows up with
   a freshly composed counter team every encounter — no pre-baked trainer
   parties involved.

2. ``pick_counter_choice(...)`` — a legacy 0..17 index used by the
   in-ROM dispatcher (``EventScript_AIRivalDispatchTrainerBattle``) to
   pick *some* base trainer to fire ``trainerbattle_no_intro`` against.
   The base trainer's party is irrelevant — it's overwritten by the
   override hook before the first turn — but a valid trainer ID is still
   required for the trainer-battle script command.

Per Edmund's demo spec:
  * slot 0 (rival starter) is always level 5
  * slot 1+ are always level 3
  * slot 0's species hard-counters the player's starter type
  * slot 1's species hard-counters the player's latest caught type
  * slot 2 (B3 only) hard-counters the player's earlier caught type
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Species + move IDs (FireRed). Hard-coded so we don't ship a dependency on a
# pokemon-data package. Keep the list tight — only species the picker emits.
# ---------------------------------------------------------------------------
SPECIES_BULBASAUR = 1
SPECIES_CHARMANDER = 4
SPECIES_SQUIRTLE = 7
SPECIES_PIDGEY = 16
SPECIES_RATTATA = 19
SPECIES_PIKACHU = 25
SPECIES_GEODUDE = 74
SPECIES_MANKEY = 56

MOVE_NONE = 0
MOVE_TACKLE = 33
MOVE_SCRATCH = 10
MOVE_GROWL = 45
MOVE_LEER = 43
MOVE_TAIL_WHIP = 39
MOVE_LEECH_SEED = 73
MOVE_EMBER = 52
MOVE_BUBBLE = 145
MOVE_THUNDER_SHOCK = 84
MOVE_LOW_KICK = 67
MOVE_DEFENSE_CURL = 111
MOVE_SAND_ATTACK = 28
MOVE_QUICK_ATTACK = 98


@dataclass
class RivalSlot:
    species: int
    level: int
    moves: list[int]  # length 4, MOVE_NONE = empty slot

    def to_dict(self) -> dict[str, Any]:
        return {"species": self.species, "level": self.level, "moves": list(self.moves)}


# ---------------------------------------------------------------------------
# Type lookup. Keep limited to species the player can realistically have on
# the demo path before Pewter.
# ---------------------------------------------------------------------------
SPECIES_PRIMARY_TYPE: dict[int, str] = {
    1: "Grass", 2: "Grass", 3: "Grass",
    4: "Fire", 5: "Fire", 6: "Fire",
    7: "Water", 8: "Water", 9: "Water",
    10: "Bug", 11: "Bug", 12: "Bug",
    13: "Bug", 14: "Bug", 15: "Bug",
    16: "Flying", 17: "Flying", 18: "Flying",
    21: "Flying", 22: "Flying",
    19: "Normal", 20: "Normal",
    23: "Poison", 24: "Poison",
    25: "Electric", 26: "Electric",
    27: "Ground", 28: "Ground",
    29: "Poison", 30: "Poison", 31: "Poison",
    32: "Poison", 33: "Poison", 34: "Poison",
    35: "Normal", 36: "Normal",
    37: "Fire", 38: "Fire",
    39: "Normal", 40: "Normal",
    41: "Poison", 42: "Poison",
    43: "Grass", 44: "Grass", 45: "Grass",
    46: "Bug", 47: "Bug",
    48: "Bug", 49: "Bug",
    50: "Ground", 51: "Ground",
    52: "Normal", 53: "Normal",
    54: "Water", 55: "Water",
    56: "Fighting", 57: "Fighting",
    58: "Fire", 59: "Fire",
    60: "Water", 61: "Water", 62: "Water",
    66: "Fighting", 67: "Fighting", 68: "Fighting",
    69: "Grass", 70: "Grass", 71: "Grass",
    74: "Rock", 75: "Rock", 76: "Rock",
    77: "Fire", 78: "Fire",
    79: "Water", 80: "Water",
    81: "Electric", 82: "Electric",
    84: "Normal", 85: "Normal",
    92: "Ghost", 93: "Ghost", 94: "Ghost",
    95: "Rock",
    100: "Electric", 101: "Electric",
    104: "Ground", 105: "Ground",
    109: "Poison", 110: "Poison",
    129: "Water", 130: "Water",
}


def _species_type(species: int | None) -> str | None:
    if species is None:
        return None
    return SPECIES_PRIMARY_TYPE.get(int(species))


# ---------------------------------------------------------------------------
# Counter tables. The picker emits whatever it gets; the C-side hook calls
# CreateMon(species, level) and SetMonData for each move slot.
# ---------------------------------------------------------------------------
_BULBA = (SPECIES_BULBASAUR,  [MOVE_TACKLE, MOVE_GROWL, MOVE_LEECH_SEED, MOVE_NONE])
_CHAR  = (SPECIES_CHARMANDER, [MOVE_SCRATCH, MOVE_GROWL, MOVE_EMBER, MOVE_NONE])
_SQUIRT = (SPECIES_SQUIRTLE,  [MOVE_TACKLE, MOVE_TAIL_WHIP, MOVE_BUBBLE, MOVE_NONE])
_PIKA  = (SPECIES_PIKACHU,    [MOVE_THUNDER_SHOCK, MOVE_GROWL, MOVE_QUICK_ATTACK, MOVE_NONE])
_GEO   = (SPECIES_GEODUDE,    [MOVE_TACKLE, MOVE_DEFENSE_CURL, MOVE_NONE, MOVE_NONE])
_MANKEY = (SPECIES_MANKEY,    [MOVE_SCRATCH, MOVE_LEER, MOVE_LOW_KICK, MOVE_NONE])
_PIDGEY = (SPECIES_PIDGEY,    [MOVE_TACKLE, MOVE_SAND_ATTACK, MOVE_QUICK_ATTACK, MOVE_NONE])

# Slot 0 — counter to player's STARTER type. Pick a starter so the rival's
# lead mirrors the canonical FireRed rival behaviour (their starter beats yours).
STARTER_COUNTER: dict[str, tuple[int, list[int]]] = {
    "Grass":  _CHAR,    # player Bulbasaur -> rival Charmander
    "Fire":   _SQUIRT,  # player Charmander -> rival Squirtle
    "Water":  _BULBA,   # player Squirtle -> rival Bulbasaur
}
_STARTER_DEFAULT = _CHAR

# Slot 1+ — counter to whatever the player just caught. Non-starter species,
# so the slot doesn't visually duplicate the rival's lead.
NON_STARTER_COUNTER: dict[str, tuple[int, list[int]]] = {
    "Flying":   _PIKA,
    "Normal":   _MANKEY,
    "Bug":      _PIDGEY,
    "Fighting": _PIDGEY,
    "Rock":     _SQUIRT,    # rock beaten by water — Squirtle counter is fine even as slot 1
    "Ground":   _BULBA,
    "Electric": _GEO,
    "Poison":   _GEO,
    "Grass":    _CHAR,
    "Fire":     _SQUIRT,
    "Water":    _BULBA,
    "Ghost":    _PIKA,
    "Ice":      _GEO,
    "Psychic":  _PIDGEY,
    "Dragon":   _GEO,
    "Steel":    _GEO,
}
_NON_STARTER_DEFAULT = _PIDGEY


def _build_slot(species_moves: tuple[int, list[int]], level: int) -> RivalSlot:
    species, moves = species_moves
    return RivalSlot(species=species, level=level, moves=list(moves))


def pick_rival_party(
    party: list[Any] | None,
    battle_index: int,
) -> list[RivalSlot]:
    """Compose the rival's party slot-by-slot to counter ``party``.

    Returns 2 slots for battle 2, 3 slots for battle 3. Every emitted slot
    has level 5 (slot 0) or level 3 (slot 1+). Each slot's species is a
    type counter to the corresponding player slot; falls back to a sensible
    default when the player slot is missing or unrecognised.
    """
    slots: list[RivalSlot] = []
    target_size = 3 if battle_index == 3 else 2

    # Slot 0 — counter to player's starter (party[0]).
    starter_type = _species_type(getattr(party[0], "species", None)) if party else None
    starter_choice = STARTER_COUNTER.get(starter_type or "", _STARTER_DEFAULT)
    slots.append(_build_slot(starter_choice, level=5))

    # Slots 1..N-1 — counter each subsequent player party member.
    for idx in range(1, target_size):
        if party and idx < len(party):
            ptype = _species_type(getattr(party[idx], "species", None))
        else:
            ptype = None
        choice = NON_STARTER_COUNTER.get(ptype or "", _NON_STARTER_DEFAULT)
        slots.append(_build_slot(choice, level=3))

    return slots


# ---------------------------------------------------------------------------
# Legacy counter-choice index (kept so the in-ROM dispatcher still has a
# valid trainer ID to fire against — the dispatched trainer's actual party
# is overwritten by the runtime override before the first turn).
# ---------------------------------------------------------------------------
_STARTER_INDEX = {"Grass": 0, "Fire": 1, "Water": 2}
_CAUGHT_INDEX = {"Flying": 0, "Normal": 1}
_BATTLE_3_OFFSET = 9


def pick_counter_choice(
    party: list[Any] | None,
    battle_index: int,
) -> tuple[int, str]:
    starter_idx = 0
    caught_idx = 2
    if party:
        starter_type = _species_type(getattr(party[0], "species", None))
        if starter_type in _STARTER_INDEX:
            starter_idx = _STARTER_INDEX[starter_type]
        if len(party) >= 2:
            caught_type = _species_type(getattr(party[1], "species", None))
            if caught_type in _CAUGHT_INDEX:
                caught_idx = _CAUGHT_INDEX[caught_type]

    base = starter_idx * 3 + caught_idx
    if battle_index == 3:
        base += _BATTLE_3_OFFSET

    starter_names = {0: "rival-Char", 1: "rival-Squirt", 2: "rival-Bulba"}
    caught_names = {0: "anti-Flying", 1: "anti-Normal", 2: "default"}
    label = f"B{battle_index} {starter_names[starter_idx]} + {caught_names[caught_idx]}"
    return base, label


def battle_index_for_trigger(trigger: str) -> int:
    if trigger == "first_capture":
        return 2
    if trigger == "second_capture":
        return 3
    return 0
