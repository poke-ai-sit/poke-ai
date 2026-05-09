"""Hard-coded rival party picker for the demo.

Per Edmund's spec — every rival encounter ships at level 5 with a fixed
mapping from player species to rival counter species. No type-chart
inference, no fallback heuristics, no GPT-driven choices: just a couple
of dicts that the picker reads. Predictable enough to memorise during
the demo run-through; obvious enough that the audience can call out
"that's the right counter" before the rival even finishes walking up.

  Starter (player slot 0 -> rival slot 0)
    BULBASAUR (1)  -> PRATA / Charmander (4)
    PRATA      (4) -> FRANKSON / Squirtle (7)
    FRANKSON   (7) -> BULBASAUR (1)

  Caught (player slot 1+ -> rival slot 1+)
    PIDGEY  (16)  -> PIKACHU (25)
    RATTATA (19)  -> MACHOP  (66)
    other         -> PIKACHU (25)   (visually safe default)

Every slot ships at level 5 — the type-counter is the visible signal,
not the level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Species + move IDs (FireRed). Hard-coded so we don't ship a dep.
# ---------------------------------------------------------------------------
SPECIES_BULBASAUR = 1
SPECIES_IVYSAUR = 2
SPECIES_VENUSAUR = 3
SPECIES_CHARMANDER = 4
SPECIES_CHARMELEON = 5
SPECIES_CHARIZARD = 6
SPECIES_SQUIRTLE = 7
SPECIES_WARTORTLE = 8
SPECIES_BLASTOISE = 9
SPECIES_PIDGEY = 16
SPECIES_PIDGEOTTO = 17
SPECIES_PIDGEOT = 18
SPECIES_RATTATA = 19
SPECIES_RATICATE = 20
SPECIES_PIKACHU = 25
SPECIES_GEODUDE = 74
SPECIES_MANKEY = 56
SPECIES_MACHOP = 66

MOVE_NONE = 0
MOVE_TACKLE = 33
MOVE_SCRATCH = 10
MOVE_GROWL = 45
MOVE_LEER = 43
MOVE_TAIL_WHIP = 39
MOVE_LEECH_SEED = 73
MOVE_VINE_WHIP = 22
MOVE_EMBER = 52
MOVE_BUBBLE = 145
MOVE_THUNDER_SHOCK = 84
MOVE_THUNDER_WAVE = 86
MOVE_LOW_KICK = 67
MOVE_KARATE_CHOP = 2
MOVE_QUICK_ATTACK = 98


# Display names — Charmander/Squirtle were renamed by the team.
SPECIES_DISPLAY_NAME: dict[int, str] = {
    SPECIES_BULBASAUR: "BULBASAUR",
    SPECIES_IVYSAUR:   "IVYSAUR",
    SPECIES_VENUSAUR:  "VENUSAUR",
    SPECIES_CHARMANDER: "PRATA",
    SPECIES_CHARMELEON: "PRATA PRO",
    SPECIES_CHARIZARD:  "CHARIZARD",
    SPECIES_SQUIRTLE:   "FRANKSON",
    SPECIES_WARTORTLE:  "WARTORTLE",
    SPECIES_BLASTOISE:  "BLASTOISE",
    SPECIES_PIDGEY:     "PIDGEY",
    SPECIES_RATTATA:    "RATTATA",
    SPECIES_PIKACHU:    "PIKACHU",
    SPECIES_MACHOP:     "MACHOP",
    SPECIES_MANKEY:     "MANKEY",
    SPECIES_GEODUDE:    "GEODUDE",
}


def _name(species: int | None) -> str:
    if species is None:
        return "?"
    return SPECIES_DISPLAY_NAME.get(int(species), f"sp{int(species)}")


@dataclass
class RivalSlot:
    species: int
    level: int
    moves: list[int]
    species_name: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"species": self.species, "level": self.level, "moves": list(self.moves)}


# ---------------------------------------------------------------------------
# Movesets — keyed by species. Used so the picker can emit a complete
# RivalSlot from a species ID alone.
# ---------------------------------------------------------------------------
MOVES_BY_SPECIES: dict[int, list[int]] = {
    SPECIES_BULBASAUR:  [MOVE_TACKLE, MOVE_VINE_WHIP, MOVE_LEECH_SEED, MOVE_GROWL],
    SPECIES_CHARMANDER: [MOVE_SCRATCH, MOVE_EMBER, MOVE_GROWL, MOVE_LEER],
    SPECIES_SQUIRTLE:   [MOVE_TACKLE, MOVE_BUBBLE, MOVE_TAIL_WHIP, MOVE_NONE],
    SPECIES_PIKACHU:    [MOVE_THUNDER_SHOCK, MOVE_QUICK_ATTACK, MOVE_GROWL, MOVE_THUNDER_WAVE],
    SPECIES_MACHOP:     [MOVE_LOW_KICK, MOVE_KARATE_CHOP, MOVE_LEER, MOVE_NONE],
    SPECIES_MANKEY:     [MOVE_SCRATCH, MOVE_LOW_KICK, MOVE_KARATE_CHOP, MOVE_LEER],
    SPECIES_PIDGEY:     [MOVE_TACKLE, MOVE_QUICK_ATTACK, MOVE_GROWL, MOVE_NONE],
    SPECIES_GEODUDE:    [MOVE_TACKLE, MOVE_LEER, MOVE_NONE, MOVE_NONE],
}


# ---------------------------------------------------------------------------
# Hard-coded matchup tables. Both maps cover the canonical evolution lines
# so a player who has somehow evolved (Oak's evolve special, level-up) still
# resolves to the right counter — Venusaur counts as Bulbasaur for picker
# purposes.
# ---------------------------------------------------------------------------

# Player starter species -> rival starter species (slot 0).
STARTER_COUNTER: dict[int, int] = {
    SPECIES_BULBASAUR: SPECIES_CHARMANDER,    # Bulbasaur -> PRATA
    SPECIES_IVYSAUR:   SPECIES_CHARMANDER,
    SPECIES_VENUSAUR:  SPECIES_CHARMANDER,
    SPECIES_CHARMANDER: SPECIES_SQUIRTLE,     # PRATA -> FRANKSON
    SPECIES_CHARMELEON: SPECIES_SQUIRTLE,
    SPECIES_CHARIZARD:  SPECIES_SQUIRTLE,
    SPECIES_SQUIRTLE:   SPECIES_BULBASAUR,    # FRANKSON -> BULBASAUR
    SPECIES_WARTORTLE:  SPECIES_BULBASAUR,
    SPECIES_BLASTOISE:  SPECIES_BULBASAUR,
}
_STARTER_DEFAULT = SPECIES_BULBASAUR

# Per Edmund's demo spec: rival's slot 1+ is ALWAYS Pikachu, regardless of
# what the player caught. Map kept for future per-catch tuning, but currently
# every entry resolves to Pikachu so the table can be reintroduced quickly.
CATCH_COUNTER: dict[int, int] = {
    SPECIES_PIDGEY:    SPECIES_PIKACHU,
    SPECIES_PIDGEOTTO: SPECIES_PIKACHU,
    SPECIES_PIDGEOT:   SPECIES_PIKACHU,
    SPECIES_RATTATA:   SPECIES_PIKACHU,
    SPECIES_RATICATE:  SPECIES_PIKACHU,
}
_CATCH_DEFAULT = SPECIES_PIKACHU


def _make_slot(rival_species: int, *, reason: str) -> RivalSlot:
    return RivalSlot(
        species=rival_species,
        level=5,
        moves=list(MOVES_BY_SPECIES.get(rival_species, [MOVE_TACKLE, 0, 0, 0])),
        species_name=_name(rival_species),
        reason=reason,
    )


def pick_rival_party(
    party: list[Any] | None,
    battle_index: int,
) -> list[RivalSlot]:
    """Compose the rival's party from the hard-coded matchup tables.

    Battle 2 = 2 slots. Battle 3 = 3 slots. All level 5. The dicts above
    are the entire decision surface — no fallbacks beyond the explicit
    DEFAULT entries.
    """
    slots: list[RivalSlot] = []
    target_size = 3 if battle_index == 3 else 2

    # Slot 0 — starter counter.
    starter_species = (
        getattr(party[0], "species", None) if party else None
    )
    if starter_species and int(starter_species) in STARTER_COUNTER:
        rival_starter = STARTER_COUNTER[int(starter_species)]
        reason = (
            f"Player slot 0: {_name(starter_species)} -> rival "
            f"{_name(rival_starter)} (hard-coded counter)."
        )
    else:
        rival_starter = _STARTER_DEFAULT
        reason = (
            f"Player slot 0: {_name(starter_species)} -> default "
            f"{_name(rival_starter)} (no hard-coded entry)."
        )
    slots.append(_make_slot(rival_starter, reason=reason))

    # Slot 1..N-1 — catch counter.
    for idx in range(1, target_size):
        if party and idx < len(party):
            caught_species = getattr(party[idx], "species", None)
        else:
            caught_species = None

        if caught_species and int(caught_species) in CATCH_COUNTER:
            rival_counter = CATCH_COUNTER[int(caught_species)]
            r = (
                f"Player slot {idx}: {_name(caught_species)} -> rival "
                f"{_name(rival_counter)} (hard-coded counter)."
            )
        else:
            rival_counter = _CATCH_DEFAULT
            r = (
                f"Player slot {idx}: {_name(caught_species)} -> default "
                f"{_name(rival_counter)} (no hard-coded entry)."
            )
        slots.append(_make_slot(rival_counter, reason=r))

    return slots


# ---------------------------------------------------------------------------
# Legacy counter-choice index — still emitted so the in-ROM dispatcher has
# a valid trainer ID to fire against. The dispatched trainer's static party
# is overwritten by the runtime override before the first turn anyway.
# ---------------------------------------------------------------------------
_STARTER_TYPE_BY_SPECIES = {
    SPECIES_BULBASAUR: "Grass", SPECIES_IVYSAUR: "Grass", SPECIES_VENUSAUR: "Grass",
    SPECIES_CHARMANDER: "Fire", SPECIES_CHARMELEON: "Fire", SPECIES_CHARIZARD: "Fire",
    SPECIES_SQUIRTLE: "Water", SPECIES_WARTORTLE: "Water", SPECIES_BLASTOISE: "Water",
}
_CAUGHT_TYPE_BY_SPECIES = {
    SPECIES_PIDGEY: "Flying", SPECIES_PIDGEOTTO: "Flying", SPECIES_PIDGEOT: "Flying",
    SPECIES_RATTATA: "Normal", SPECIES_RATICATE: "Normal",
}
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
        s_species = getattr(party[0], "species", None)
        s_type = _STARTER_TYPE_BY_SPECIES.get(int(s_species)) if s_species else None
        if s_type in _STARTER_INDEX:
            starter_idx = _STARTER_INDEX[s_type]
        if len(party) >= 2:
            c_species = getattr(party[1], "species", None)
            c_type = _CAUGHT_TYPE_BY_SPECIES.get(int(c_species)) if c_species else None
            if c_type in _CAUGHT_INDEX:
                caught_idx = _CAUGHT_INDEX[c_type]

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
