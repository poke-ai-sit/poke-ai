"""Type-chart-driven rival party picker.

Replaces the prior static "anti-X -> species" lookup with a real-ish
Gen-1/3 type effectiveness table. For each player party slot, the picker:

  1. Resolves the player Pokemon's primary type (e.g. Pidgey -> Flying).
  2. Looks up which attack types deal 2x damage to that defender type
     (e.g. Flying is weak to Electric and Rock).
  3. Picks the first roster Pokemon whose primary attack type is on that
     2x-list (and ideally also resists the player's STAB type).
  4. Records a one-line reasoning string per slot so the host can echo
     it to the audience: "Pidgey is Flying. Pikachu (Electric) is 2x
     super effective vs Flying."

The bridge sends both the (species, level, moves) tuple AND the reasoning
strings; Lua materialises the party via gRivalAIBuffer.partyOverride and
prints the reasoning to the script console so the dynamic decision is
visible during the demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Species + move IDs (FireRed). Kept hard-coded so we don't ship a dep.
# ---------------------------------------------------------------------------
SPECIES_BULBASAUR = 1
SPECIES_CHARMANDER = 4
SPECIES_SQUIRTLE = 7
SPECIES_PIDGEY = 16
SPECIES_RATTATA = 19
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
MOVE_DEFENSE_CURL = 111
MOVE_ROCK_THROW = 88
MOVE_SAND_ATTACK = 28
MOVE_GUST = 16
MOVE_QUICK_ATTACK = 98
MOVE_PECK = 64


@dataclass
class RivalSlot:
    species: int
    level: int
    moves: list[int]
    species_name: str = ""
    attack_type: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"species": self.species, "level": self.level, "moves": list(self.moves)}


# ---------------------------------------------------------------------------
# Species -> primary defender type. Kept tight to the species the demo path
# can reasonably involve.
# ---------------------------------------------------------------------------
SPECIES_PRIMARY_TYPE: dict[int, str] = {
    1: "Grass", 2: "Grass", 3: "Grass",
    4: "Fire", 5: "Fire", 6: "Fire",
    7: "Water", 8: "Water", 9: "Water",
    10: "Bug", 11: "Bug", 12: "Bug",
    13: "Bug", 14: "Bug", 15: "Bug",
    16: "Flying", 17: "Flying", 18: "Flying",
    19: "Normal", 20: "Normal",
    21: "Flying", 22: "Flying",
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

SPECIES_DISPLAY_NAME: dict[int, str] = {
    SPECIES_BULBASAUR: "BULBASAUR",
    SPECIES_CHARMANDER: "PRATA",       # team renamed Charmander -> PRATA
    SPECIES_SQUIRTLE: "FRANKSON",      # team renamed Squirtle  -> FRANKSON
    SPECIES_PIDGEY: "PIDGEY",
    SPECIES_RATTATA: "RATTATA",
    SPECIES_PIKACHU: "PIKACHU",
    SPECIES_GEODUDE: "GEODUDE",
    SPECIES_MANKEY: "MANKEY",
    SPECIES_MACHOP: "MACHOP",
}


# ---------------------------------------------------------------------------
# Type effectiveness — attacker_type -> {defender_type: multiplier}.
# Mirrors the canonical Gen-1/3 type chart the user shared. Only the 2x
# entries actually drive picking; 0.5x and 0x are kept so we can print
# resistance/immunity reasoning when relevant.
# ---------------------------------------------------------------------------
TYPE_EFFECTIVENESS: dict[str, dict[str, float]] = {
    "Normal":   {"Rock": 0.5, "Ghost": 0.0, "Steel": 0.5},
    "Fire":     {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 2, "Bug": 2,
                 "Rock": 0.5, "Dragon": 0.5, "Steel": 2},
    "Water":    {"Fire": 2, "Water": 0.5, "Grass": 0.5, "Ground": 2,
                 "Rock": 2, "Dragon": 0.5},
    "Electric": {"Water": 2, "Electric": 0.5, "Grass": 0.5, "Ground": 0.0,
                 "Flying": 2, "Dragon": 0.5},
    "Grass":    {"Fire": 0.5, "Water": 2, "Grass": 0.5, "Poison": 0.5,
                 "Ground": 2, "Flying": 0.5, "Bug": 0.5, "Rock": 2,
                 "Dragon": 0.5, "Steel": 0.5},
    "Ice":      {"Fire": 0.5, "Water": 0.5, "Grass": 2, "Ice": 0.5,
                 "Ground": 2, "Flying": 2, "Dragon": 2, "Steel": 0.5},
    "Fighting": {"Normal": 2, "Ice": 2, "Poison": 0.5, "Flying": 0.5,
                 "Psychic": 0.5, "Bug": 0.5, "Rock": 2, "Ghost": 0.0,
                 "Dark": 2, "Steel": 2, "Fairy": 0.5},
    "Poison":   {"Grass": 2, "Poison": 0.5, "Ground": 0.5, "Rock": 0.5,
                 "Ghost": 0.5, "Steel": 0.0, "Fairy": 2},
    "Ground":   {"Fire": 2, "Electric": 2, "Grass": 0.5, "Poison": 2,
                 "Flying": 0.0, "Bug": 0.5, "Rock": 2, "Steel": 2},
    "Flying":   {"Electric": 0.5, "Grass": 2, "Fighting": 2, "Bug": 2,
                 "Rock": 0.5, "Steel": 0.5},
    "Psychic":  {"Fighting": 2, "Poison": 2, "Psychic": 0.5, "Dark": 0.0,
                 "Steel": 0.5},
    "Bug":      {"Fire": 0.5, "Grass": 2, "Fighting": 0.5, "Poison": 0.5,
                 "Flying": 0.5, "Psychic": 2, "Ghost": 0.5, "Dark": 2,
                 "Steel": 0.5, "Fairy": 0.5},
    "Rock":     {"Fire": 2, "Ice": 2, "Fighting": 0.5, "Ground": 0.5,
                 "Flying": 2, "Bug": 2, "Steel": 0.5},
    "Ghost":    {"Normal": 0.0, "Psychic": 2, "Ghost": 2, "Dark": 0.5},
    "Dragon":   {"Dragon": 2, "Steel": 0.5, "Fairy": 0.0},
}


# ---------------------------------------------------------------------------
# Rival roster — every counter species we are willing to ship onto the field.
# Each entry declares its primary attack type (used for type-chart lookups)
# alongside a level-appropriate moveset.
# ---------------------------------------------------------------------------
@dataclass
class RosterMon:
    species: int
    name: str
    attack_type: str  # the type whose chart row we use to gauge effectiveness
    self_type: str    # the mon's own primary type (for resistance reasoning)
    moves: list[int] = field(default_factory=list)


ROSTER: list[RosterMon] = [
    RosterMon(SPECIES_BULBASAUR,  "BULBASAUR", "Grass",    "Grass",
              [MOVE_TACKLE, MOVE_VINE_WHIP, MOVE_LEECH_SEED, MOVE_GROWL]),
    RosterMon(SPECIES_CHARMANDER, "PRATA",     "Fire",     "Fire",
              [MOVE_SCRATCH, MOVE_EMBER, MOVE_GROWL, MOVE_LEER]),
    RosterMon(SPECIES_SQUIRTLE,   "FRANKSON",  "Water",    "Water",
              [MOVE_TACKLE, MOVE_BUBBLE, MOVE_TAIL_WHIP, MOVE_NONE]),
    RosterMon(SPECIES_PIKACHU,    "PIKACHU",   "Electric", "Electric",
              [MOVE_THUNDER_SHOCK, MOVE_QUICK_ATTACK, MOVE_GROWL, MOVE_THUNDER_WAVE]),
    RosterMon(SPECIES_GEODUDE,    "GEODUDE",   "Rock",     "Rock",
              [MOVE_TACKLE, MOVE_ROCK_THROW, MOVE_DEFENSE_CURL, MOVE_NONE]),
    # Per Edmund's demo spec: Rattata (Normal) -> Machop. Mankey is also
    # Fighting but Machop is the more iconic / readable counter visually.
    RosterMon(SPECIES_MACHOP,     "MACHOP",    "Fighting", "Fighting",
              [MOVE_LOW_KICK, MOVE_KARATE_CHOP, MOVE_LEER, MOVE_NONE]),
    RosterMon(SPECIES_PIDGEY,     "PIDGEY",    "Flying",   "Flying",
              [MOVE_TACKLE, MOVE_GUST, MOVE_QUICK_ATTACK, MOVE_SAND_ATTACK]),
]


def _species_type(species: int | None) -> str | None:
    if species is None:
        return None
    return SPECIES_PRIMARY_TYPE.get(int(species))


def _species_name(species: int | None) -> str:
    if species is None:
        return "?"
    return SPECIES_DISPLAY_NAME.get(int(species), f"sp{int(species)}")


def _effectiveness(attack: str, defender: str) -> float:
    return TYPE_EFFECTIVENESS.get(attack, {}).get(defender, 1.0)


def _pick_counter(
    defender_type: str | None,
    *,
    avoid: set[int] | None = None,
    fallback_idx: int = 0,
) -> tuple[RosterMon, str]:
    """Return (roster_mon, reason). Picks the first roster mon whose attack
    type hits ``defender_type`` for 2x. Tie-breaker: prefer a mon whose own
    type RESISTS the defender's STAB (multiplier <= 0.5 the other way).
    Falls through to a ranked default if nothing super-effective is found.
    """
    avoid = avoid or set()
    candidates: list[tuple[RosterMon, float, float]] = []  # mon, atk_mult, def_mult
    for mon in ROSTER:
        if mon.species in avoid:
            continue
        atk_mult = _effectiveness(mon.attack_type, defender_type or "Normal")
        # How much does the defender's STAB hurt this candidate? Lower is better.
        def_mult = _effectiveness(defender_type or "Normal", mon.self_type)
        candidates.append((mon, atk_mult, def_mult))

    # Prefer 2x super-effective hitters; among them, pick the one that least
    # eats damage from the defender's STAB.
    super_effective = [c for c in candidates if c[1] >= 2]
    if super_effective:
        super_effective.sort(key=lambda c: (c[2], -c[1]))
        mon, atk, _def = super_effective[0]
        reason = (
            f"{mon.name} ({mon.attack_type}) hits {defender_type} for {int(atk)}x"
        )
        return mon, reason

    # No 2x option in the roster — pick the candidate that takes the least
    # damage from the defender's STAB and isn't a no-op against it.
    candidates.sort(key=lambda c: (c[2], -c[1]))
    mon, atk, def_mult = candidates[fallback_idx % len(candidates)]
    if def_mult <= 0.5:
        reason = (
            f"No super-effective answer; {mon.name} ({mon.self_type}) resists "
            f"{defender_type}"
        )
    else:
        reason = (
            f"No clear counter for {defender_type}; default to {mon.name}"
        )
    return mon, reason


# Slot 0 must be a starter so the encounter visually mirrors the canonical
# rival "I picked the one that beats yours" moment. Restrict the candidate
# pool to the 3 starters when picking slot 0.
_STARTER_SPECIES = {SPECIES_BULBASAUR, SPECIES_CHARMANDER, SPECIES_SQUIRTLE}


def _pick_starter_counter(defender_type: str | None) -> tuple[RosterMon, str]:
    starter_pool = [m for m in ROSTER if m.species in _STARTER_SPECIES]
    best = starter_pool[0]
    best_atk = _effectiveness(best.attack_type, defender_type or "Normal")
    best_def = _effectiveness(defender_type or "Normal", best.self_type)
    for mon in starter_pool[1:]:
        atk = _effectiveness(mon.attack_type, defender_type or "Normal")
        def_mult = _effectiveness(defender_type or "Normal", mon.self_type)
        if (atk, -def_mult) > (best_atk, -best_def):
            best, best_atk, best_def = mon, atk, def_mult

    if best_atk >= 2:
        reason = (
            f"Starter pick {best.name} ({best.attack_type}) hits "
            f"{defender_type} for {int(best_atk)}x"
        )
    elif best_def <= 0.5:
        reason = (
            f"Starter pick {best.name} resists {defender_type} STAB"
        )
    else:
        reason = f"Starter pick {best.name} (default counter)"
    return best, reason


def pick_rival_party(
    party: list[Any] | None,
    battle_index: int,
) -> list[RivalSlot]:
    """Compose the rival's party slot-by-slot from the type chart."""
    slots: list[RivalSlot] = []
    target_size = 3 if battle_index == 3 else 2

    # Slot 0 — starter counter.
    starter_species = getattr(party[0], "species", None) if party else None
    starter_type = _species_type(starter_species)
    starter_label = _species_name(starter_species) if starter_species else "?"
    starter_mon, starter_reason = _pick_starter_counter(starter_type)
    slots.append(RivalSlot(
        species=starter_mon.species, level=5,
        moves=list(starter_mon.moves),
        species_name=starter_mon.name,
        attack_type=starter_mon.attack_type,
        reason=(
            f"Player slot 0: {starter_label} ({starter_type or '?'}). "
            f"{starter_reason}."
        ),
    ))
    used = {starter_mon.species}

    # Slot 1..N-1 — counter the rest of the player's party. Per Edmund's
    # demo spec, every slot ships at level 5 (no level scaling); the
    # type-counter is the visible signal, not the levels.
    for idx in range(1, target_size):
        if party and idx < len(party):
            p_species = getattr(party[idx], "species", None)
        else:
            p_species = None
        p_type = _species_type(p_species)
        p_label = _species_name(p_species) if p_species else "?"
        mon, reason = _pick_counter(p_type, avoid=used, fallback_idx=idx)
        used.add(mon.species)
        slots.append(RivalSlot(
            species=mon.species, level=5,
            moves=list(mon.moves),
            species_name=mon.name,
            attack_type=mon.attack_type,
            reason=f"Player slot {idx}: {p_label} ({p_type or '?'}). {reason}.",
        ))

    return slots


# ---------------------------------------------------------------------------
# Legacy counter-choice index — still emitted so the in-ROM dispatcher has
# a valid trainer ID to fire against. The dispatched trainer's static party
# is overwritten by the runtime override before the first turn anyway.
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
