from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Offline species name table for the current patched ROM.
# IDs match FireRed species constants. PokéLive custom Pokemon currently
# reuse stock starter slots, so this table mirrors species_names.h.
# ---------------------------------------------------------------------------

SPECIES_NAMES: dict[int, str] = {
    1: "BULBASAUR", 2: "IVYSAUR", 3: "VENUSAUR",
    4: "PRATA", 5: "PRATA PRO", 6: "CHARIZARD",
    7: "FRANKSON", 8: "WARTORTLE", 9: "BLASTOISE",
    10: "CATERPIE", 11: "METAPOD", 12: "BUTTERFREE",
    13: "WEEDLE", 14: "KAKUNA", 15: "BEEDRILL",
    16: "PIDGEY", 17: "PIDGEOTTO", 18: "PIDGEOT",
    19: "RATTATA", 20: "RATICATE",
    21: "SPEAROW", 22: "FEAROW",
    23: "EKANS", 24: "ARBOK",
    25: "PIKACHU", 26: "RAICHU",
    27: "SANDSHREW", 28: "SANDSLASH",
    29: "NIDORAN F", 30: "NIDORINA", 31: "NIDOQUEEN",
    32: "NIDORAN M", 33: "NIDORINO", 34: "NIDOKING",
    35: "CLEFAIRY", 36: "CLEFABLE",
    37: "VULPIX", 38: "NINETALES",
    39: "JIGGLYPUFF", 40: "WIGGLYTUFF",
    41: "ZUBAT", 42: "GOLBAT",
    43: "ODDISH", 44: "GLOOM", 45: "VILEPLUME",
    46: "PARAS", 47: "PARASECT",
    48: "VENONAT", 49: "VENOMOTH",
    50: "DIGLETT", 51: "DUGTRIO",
    52: "MEOWTH", 53: "PERSIAN",
    54: "PSYDUCK", 55: "GOLDUCK",
    56: "MANKEY", 57: "PRIMEAPE",
    58: "GROWLITHE", 59: "ARCANINE",
    60: "POLIWAG", 61: "POLIWHIRL", 62: "POLIWRATH",
    63: "ABRA", 64: "KADABRA", 65: "ALAKAZAM",
    66: "MACHOP", 67: "MACHOKE", 68: "MACHAMP",
    69: "BELLSPROUT", 70: "WEEPINBELL", 71: "VICTREEBEL",
    72: "TENTACOOL", 73: "TENTACRUEL",
    74: "GEODUDE", 75: "GRAVELER", 76: "GOLEM",
    77: "PONYTA", 78: "RAPIDASH",
    79: "SLOWPOKE", 80: "SLOWBRO",
    81: "MAGNEMITE", 82: "MAGNETON",
    83: "FARFETCHD",
    84: "DODUO", 85: "DODRIO",
    86: "SEEL", 87: "DEWGONG",
    88: "GRIMER", 89: "MUK",
    90: "SHELLDER", 91: "CLOYSTER",
    92: "GASTLY", 93: "HAUNTER", 94: "GENGAR",
    95: "ONIX",
    96: "DROWZEE", 97: "HYPNO",
    98: "KRABBY", 99: "KINGLER",
    100: "VOLTORB", 101: "ELECTRODE",
    102: "EXEGGCUTE", 103: "EXEGGUTOR",
    104: "CUBONE", 105: "MAROWAK",
    106: "HITMONLEE", 107: "HITMONCHAN",
    108: "LICKITUNG",
    109: "KOFFING", 110: "WEEZING",
    111: "RHYHORN", 112: "RHYDON",
    113: "CHANSEY",
    114: "TANGELA",
    115: "KANGASKHAN",
    116: "HORSEA", 117: "SEADRA",
    118: "GOLDEEN", 119: "SEAKING",
    120: "STARYU", 121: "STARMIE",
    122: "MR MIME",
    123: "SCYTHER",
    124: "JYNX",
    125: "ELECTABUZZ",
    126: "MAGMAR",
    127: "PINSIR",
    128: "TAUROS",
    129: "MAGIKARP", 130: "GYARADOS",
    131: "LAPRAS",
    132: "DITTO",
    133: "EEVEE", 134: "VAPOREON", 135: "JOLTEON", 136: "FLAREON",
    137: "PORYGON",
    138: "OMANYTE", 139: "OMASTAR",
    140: "KABUTO", 141: "KABUTOPS",
    142: "AERODACTYL",
    143: "SNORLAX",
    144: "ARTICUNO", 145: "ZAPDOS", 146: "MOLTRES",
    147: "DRATINI", 148: "DRAGONAIR", 149: "DRAGONITE",
    150: "MEWTWO", 151: "MEW",
}

# ---------------------------------------------------------------------------
# Offline move name table
# IDs sourced from pokefirered/include/constants/moves.h
# Covers all IDs in MOVE_TYPES plus common early-game moves.
# ---------------------------------------------------------------------------

MOVE_NAMES: dict[int, str] = {
    1: "POUND", 2: "KARATE CHOP", 3: "DOUBLESLAP", 4: "COMET PUNCH",
    5: "MEGA PUNCH", 6: "PAY DAY", 7: "FIRE PUNCH", 8: "ICE PUNCH",
    9: "THUNDER PUNCH", 10: "SCRATCH", 11: "VICEGRIP", 12: "GUILLOTINE",
    13: "RAZOR WIND", 14: "SWORDS DANCE", 15: "CUT", 16: "GUST",
    17: "WING ATTACK", 18: "WHIRLWIND", 19: "FLY", 20: "BIND",
    21: "SLAM", 22: "VINE WHIP", 23: "STOMP", 24: "DOUBLE KICK",
    25: "MEGA KICK", 26: "JUMP KICK", 27: "ROLLING KICK", 28: "SAND ATTACK",
    29: "HEADBUTT", 30: "HORN ATTACK", 31: "FURY ATTACK", 32: "HORN DRILL",
    33: "TACKLE", 34: "BODY SLAM", 35: "WRAP", 36: "TAKE DOWN",
    37: "THRASH", 38: "DOUBLE EDGE", 39: "TAIL WHIP", 40: "POISON STING",
    41: "TWINEEDLE", 42: "PIN MISSILE", 43: "LEER", 44: "BITE",
    45: "GROWL", 46: "ROAR", 47: "SING", 48: "SUPERSONIC",
    49: "SONICBOOM", 50: "DISABLE", 51: "ACID", 52: "EMBER",
    53: "FLAMETHROWER", 54: "MIST", 55: "WATER GUN", 56: "HYDRO PUMP",
    57: "SURF", 58: "ICE BEAM", 59: "BLIZZARD", 60: "PSYBEAM",
    61: "BUBBLEBEAM", 62: "AURORA BEAM", 63: "HYPER BEAM", 64: "PECK",
    65: "DRILL PECK", 66: "SUBMISSION", 67: "LOW KICK", 68: "COUNTER",
    69: "SEISMIC TOSS", 70: "STRENGTH", 71: "ABSORB", 72: "MEGA DRAIN",
    73: "LEECH SEED", 74: "GROWTH", 75: "RAZOR LEAF", 76: "SOLARBEAM",
    77: "POISONPOWDER", 78: "STUN SPORE", 79: "SLEEP POWDER",
    80: "PETAL DANCE", 81: "STRING SHOT", 82: "DRAGON RAGE",
    83: "FIRE SPIN", 84: "THUNDERSHOCK", 85: "THUNDERBOLT",
    86: "THUNDER WAVE", 87: "THUNDER", 88: "ROCK THROW",
    89: "EARTHQUAKE", 90: "FISSURE", 91: "DIG", 92: "TOXIC",
    93: "CONFUSION", 94: "PSYCHIC", 95: "HYPNOSIS", 96: "MEDITATE",
    97: "AGILITY", 98: "QUICK ATTACK", 99: "RAGE", 100: "TELEPORT",
    101: "NIGHT SHADE", 102: "MIMIC", 103: "SCREECH", 104: "DOUBLE TEAM",
    105: "RECOVER", 106: "HARDEN", 107: "MINIMIZE", 108: "SMOKESCREEN",
    109: "CONFUSE RAY", 110: "WITHDRAW", 111: "DEFENSE CURL",
    112: "BARRIER", 113: "LIGHT SCREEN", 114: "HAZE", 115: "REFLECT",
    116: "FOCUS ENERGY", 117: "BIDE", 118: "METRONOME",
    119: "MIRROR MOVE", 120: "SELFDESTRUCT", 121: "EGG BOMB",
    122: "LICK", 123: "SMOG", 124: "SLUDGE", 125: "BONE CLUB",
    126: "FIRE BLAST", 127: "WATERFALL", 128: "CLAMP", 129: "SWIFT",
    130: "SKULL BASH", 131: "SPIKE CANNON", 132: "CONSTRICT",
    133: "AMNESIA", 134: "KINESIS", 135: "SOFTBOILED",
    136: "HI JUMP KICK", 137: "GLARE", 138: "DREAM EATER",
    139: "POISON GAS", 140: "BARRAGE", 141: "LEECH LIFE",
    142: "LOVELY KISS", 143: "SKY ATTACK", 144: "TRANSFORM",
    145: "BUBBLE", 146: "DIZZY PUNCH", 147: "SPORE", 148: "FLASH",
    149: "PSYWAVE", 150: "SPLASH", 151: "ACID ARMOR",
    152: "CRABHAMMER", 153: "EXPLOSION", 154: "FURY SWIPES",
    155: "BONEMERANG", 156: "REST", 157: "ROCK SLIDE",
    158: "HYPER FANG", 159: "SHARPEN", 160: "CONVERSION",
    249: "ROCK SMASH",
}


def species_name_offline(species_id: int) -> str | None:
    """Return uppercase species name from offline table, or None if not found."""
    return SPECIES_NAMES.get(species_id)


def move_name_offline(move_id: int) -> str | None:
    """Return uppercase move name from offline table, or None if not found."""
    return MOVE_NAMES.get(move_id)


# ---------------------------------------------------------------------------
# Offline move/type tables (no network calls)
# Move IDs sourced from pokefirered/include/constants/moves.h
# ---------------------------------------------------------------------------

# move_id -> type name; returns None for IDs not in this table.
# Callers must skip None before coverage checks — unknown moves must not
# contribute to super-effective coverage detection.
MOVE_TYPES: dict[int, str] = {
    1: "Normal",     # Pound
    2: "Fighting",   # Karate Chop (Fighting in FireRed, unlike Gen 1)
    7: "Fire",       # Fire Punch
    8: "Ice",        # Ice Punch
    9: "Electric",   # ThunderPunch
    10: "Normal",    # Scratch
    15: "Normal",    # Cut
    16: "Flying",    # Gust
    17: "Flying",    # Wing Attack
    19: "Flying",    # Fly
    22: "Grass",     # Vine Whip
    24: "Fighting",  # Double Kick
    28: "Ground",    # Sand Attack
    33: "Normal",    # Tackle
    34: "Normal",    # Body Slam
    36: "Normal",    # Take Down
    39: "Normal",    # Tail Whip
    40: "Poison",    # Poison Sting
    43: "Normal",    # Leer
    44: "Normal",    # Bite (Normal in Gen III FireRed)
    45: "Normal",    # Growl
    47: "Normal",    # Sing
    51: "Poison",    # Acid
    52: "Fire",      # Ember
    53: "Fire",      # Flamethrower
    55: "Water",     # Water Gun
    56: "Water",     # Hydro Pump
    57: "Water",     # Surf
    58: "Ice",       # Ice Beam
    59: "Ice",       # Blizzard
    61: "Water",     # Bubble Beam
    64: "Flying",    # Peck
    65: "Flying",    # Drill Peck
    66: "Fighting",  # Submission
    67: "Fighting",  # Low Kick
    68: "Fighting",  # Counter
    70: "Normal",    # Strength
    72: "Grass",     # Mega Drain
    73: "Grass",     # Leech Seed
    75: "Grass",     # Razor Leaf
    76: "Grass",     # Solar Beam
    83: "Fire",      # Fire Spin
    84: "Electric",  # ThunderShock
    85: "Electric",  # Thunderbolt
    86: "Electric",  # Thunder Wave
    87: "Electric",  # Thunder
    88: "Rock",      # Rock Throw
    89: "Ground",    # Earthquake
    91: "Ground",    # Dig
    93: "Psychic",   # Confusion
    94: "Psychic",   # Psychic
    98: "Normal",    # Quick Attack
    127: "Water",    # Waterfall
    136: "Fighting", # High Jump Kick
    145: "Water",    # Bubble
    157: "Rock",     # Rock Slide
    249: "Fighting", # Rock Smash
}

# defender_type -> frozenset of attacker types that are super-effective
# Gen III 17-type chart (no Fairy), verified against pokefirered type data
SUPER_EFFECTIVE: dict[str, frozenset[str]] = {
    "Normal":   frozenset(),
    "Fire":     frozenset({"Water", "Ground", "Rock"}),
    "Water":    frozenset({"Electric", "Grass"}),
    "Electric": frozenset({"Ground"}),
    "Grass":    frozenset({"Fire", "Ice", "Poison", "Flying", "Bug"}),
    "Ice":      frozenset({"Fire", "Fighting", "Rock", "Steel"}),
    "Fighting": frozenset({"Flying", "Psychic"}),
    "Poison":   frozenset({"Ground", "Psychic"}),
    "Ground":   frozenset({"Water", "Grass", "Ice"}),
    "Flying":   frozenset({"Electric", "Ice", "Rock"}),
    "Psychic":  frozenset({"Bug", "Ghost", "Dark"}),
    "Bug":      frozenset({"Fire", "Flying", "Rock"}),
    "Rock":     frozenset({"Water", "Grass", "Fighting", "Ground", "Steel"}),
    "Ghost":    frozenset({"Ghost", "Dark"}),
    "Dragon":   frozenset({"Ice", "Dragon"}),
    "Dark":     frozenset({"Fighting", "Bug"}),
    "Steel":    frozenset({"Fire", "Fighting", "Ground"}),
}


def move_type(move_id: int) -> str | None:
    """Return type name for move_id, or None if not in the offline table."""
    return MOVE_TYPES.get(move_id)


def is_super_effective(atk_type: str, defender_types: list[str]) -> bool:
    """True if atk_type hits super-effectively against any of defender_types."""
    return any(atk_type in SUPER_EFFECTIVE.get(d, frozenset()) for d in defender_types)


@dataclass(frozen=True)
class GymInfo:
    index: int
    name: str
    leader: str
    types: tuple[str, ...]
    weak_to: tuple[str, ...]
    recommended_level: int
    training_routes: tuple[str, ...]


# First 4 Kanto gyms (Brock to Erika). Coordinate-based — not badge state.
GYM_SEQUENCE: tuple[GymInfo, ...] = (
    GymInfo(
        1, "Pewter Gym", "Brock",
        ("Rock", "Ground"),
        ("Water", "Grass"),
        14,
        ("Route 1", "Route 2", "Viridian Forest"),
    ),
    GymInfo(
        2, "Cerulean Gym", "Misty",
        ("Water",),
        ("Electric", "Grass"),
        21,
        ("Route 3", "Mt Moon"),
    ),
    GymInfo(
        3, "Vermilion Gym", "Lt Surge",
        ("Electric",),
        ("Ground",),
        24,
        ("Route 5", "Route 6"),
    ),
    GymInfo(
        4, "Celadon Gym", "Erika",
        ("Grass", "Poison"),
        ("Fire", "Flying", "Psychic", "Ice"),
        32,
        ("Route 7", "Route 8"),
    ),
)

# (map_group, map_num) -> index into GYM_SEQUENCE
# IDs sourced from pokefirered/include/constants/map_groups.h
# Format: MAP_<NAME> = (map_num | (map_group << 8))
PROGRESS_MAP: dict[tuple[int, int], int] = {
    # Pre-Brock — Pallet Town, Route 1, Viridian City, Route 2, Viridian Forest, Pewter City
    (3, 0): 0,   # MAP_PALLET_TOWN
    (3, 1): 0,   # MAP_VIRIDIAN_CITY
    (3, 2): 0,   # MAP_PEWTER_CITY
    (3, 19): 0,  # MAP_ROUTE1
    (3, 20): 0,  # MAP_ROUTE2
    (1, 0): 0,   # MAP_VIRIDIAN_FOREST
    # Pallet Town interiors (player always starts here, pre-Brock context)
    (4, 0): 0,   # MAP_PALLET_TOWN_PLAYERS_HOUSE_1F
    (4, 1): 0,   # MAP_PALLET_TOWN_PLAYERS_HOUSE_2F
    (4, 2): 0,   # MAP_PALLET_TOWN_RIVALS_HOUSE
    (4, 3): 0,   # MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB

    # Pre-Misty — Route 3, Mt Moon, Route 4, Cerulean City, Routes 24/25
    (3, 21): 1,  # MAP_ROUTE3
    (1, 1): 1,   # MAP_MT_MOON_1F
    (1, 2): 1,   # MAP_MT_MOON_B1F
    (1, 3): 1,   # MAP_MT_MOON_B2F
    (3, 22): 1,  # MAP_ROUTE4
    (3, 3): 1,   # MAP_CERULEAN_CITY
    (3, 43): 1,  # MAP_ROUTE24
    (3, 44): 1,  # MAP_ROUTE25

    # Pre-Lt Surge — Routes 5/6, Vermilion City
    (3, 23): 2,  # MAP_ROUTE5
    (3, 24): 2,  # MAP_ROUTE6
    (3, 5): 2,   # MAP_VERMILION_CITY

    # Pre-Erika — Routes 7/8, Celadon City
    (3, 25): 3,  # MAP_ROUTE7
    (3, 26): 3,  # MAP_ROUTE8
    (3, 6): 3,   # MAP_CELADON_CITY
}


def gym_for_location(map_group: int, map_num: int) -> GymInfo:
    """Return next expected gym based on map coordinates (not badge state).

    Unknown coordinates default to Brock (first gym) — safe fallback for any
    interior building or post-Erika location not in PROGRESS_MAP.
    """
    idx = PROGRESS_MAP.get((map_group, map_num), 0)
    return GYM_SEQUENCE[min(idx, len(GYM_SEQUENCE) - 1)]
