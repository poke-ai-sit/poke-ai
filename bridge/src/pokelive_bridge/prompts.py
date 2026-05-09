from typing import Any

CODEX_ADVICE_PROMPT = "What should I do next."

_BASE_PERSONA_ADVICE = (
    "You are Professor GPT 5.5, an NPC researcher inside Pokemon FireRed. "
    "STRICT RULES: Reply with EXACTLY ONE sentence under 40 characters total. "
    "Use ONLY letters numbers and spaces. "
    "No punctuation of any kind."
)

_BASE_PERSONA_ASK = (
    "You are Professor GPT 5.5, an NPC researcher inside Pokemon FireRed. "
    "STRICT RULES: Reply with ONE or TWO sentences under 60 characters total. "
    "Use ONLY letters numbers and spaces. "
    "No punctuation of any kind."
)

# Backward-compatible alias used by tests that check persona content
_BASE_PERSONA = _BASE_PERSONA_ASK

ADVICE_HINT = (
    "Give the most useful advice based on the gym context and party data. "
    "Always name the specific Pokemon from the party that needs to act. "
    "If coverage is MISSING name that Pokemon and the exact move it should learn. "
    "If level warning is shown name that Pokemon and its level target. "
    "Example: Train PRATA to L13 Metal Claw. "
    "Keep reply under 40 chars."
)


def _gym_context_block(game_state: Any, party: list[Any] | None) -> str:
    from pokelive_bridge.gym_data import gym_for_location, is_super_effective, move_type

    gym = gym_for_location(game_state.map_group, game_state.map_num)
    lines = [
        f"Next gym (estimated from location): {gym.name} ({gym.leader})",
        f"Leader types: {', '.join(gym.types)}",
        f"Weak to: {', '.join(gym.weak_to)}",
        f"Recommended level: {gym.recommended_level}",
        f"Training routes: {', '.join(gym.training_routes[:2])}",
    ]
    if party:
        has_coverage = any(
            is_super_effective(mt, list(gym.types))
            for p in party
            for m in p.moves
            if m != 0 and (mt := move_type(m)) is not None
        )
        lines.append(
            "Party coverage: OK" if has_coverage
            else f"Party coverage: MISSING vs {'/'.join(gym.types)}"
        )
        max_level = max(p.level for p in party)
        if max_level < gym.recommended_level:
            lines.append(
                f"Level warning: top L{max_level} needs L{gym.recommended_level}"
            )
        else:
            lines.append(f"Level status: L{max_level} ready")
    return "\n".join(lines)


def _party_block(party: list[Any] | None) -> str:
    if not party:
        return ""
    from pokelive_bridge.pokemon_data import move_name, species_name

    lines = [f"Party ({len(party)} Pokemon):"]
    for p in party:
        moves = " ".join(move_name(m) for m in p.moves if m != 0) or "none"
        lines.append(
            f"  {species_name(p.species)} L{p.level} "
            f"HP {p.hp}/{p.max_hp} "
            f"ATK {p.attack} DEF {p.defense} SPD {p.speed} "
            f"moves: {moves}"
        )
    return "\n".join(lines)


def build_codex_system_prompt_advice(
    game_state: Any, party: list[Any] | None = None
) -> str:
    state_block = (
        f"Map group: {game_state.map_group}, map number: {game_state.map_num}\n"
        f"Player position: ({game_state.x}, {game_state.y})"
    )
    party_block = _party_block(party)
    gym_block = _gym_context_block(game_state, party)
    context = f"<game_state>\n{state_block}\n</game_state>"
    context += f"\n\n<gym>\n{gym_block}\n</gym>"
    if party_block:
        context += f"\n\n<party>\n{party_block}\n</party>"
    return f"{_BASE_PERSONA_ADVICE}\n\n{context}\n\n{ADVICE_HINT}"


def build_codex_system_prompt_ask(
    game_state: Any, party: list[Any] | None = None
) -> str:
    state_block = (
        f"Map group: {game_state.map_group}, map number: {game_state.map_num}\n"
        f"Player position: ({game_state.x}, {game_state.y})"
    )
    party_block = _party_block(party)
    context = f"<game_state>\n{state_block}\n</game_state>"
    if party_block:
        context += f"\n\n<party>\n{party_block}\n</party>"
    return f"{_BASE_PERSONA_ASK}\n\n{context}"


# Backward-compatible alias (used by existing tests and openai_client)
def build_codex_system_prompt(
    game_state: Any, party: list[Any] | None = None
) -> str:
    return build_codex_system_prompt_ask(game_state, party)


def build_codex_advice_prompt(game_state: Any) -> str:
    return (
        f"{CODEX_ADVICE_PROMPT} "
        f"I am on map {game_state.map_group}:{game_state.map_num} "
        f"at position {game_state.x},{game_state.y}. "
        "Give short context aware guidance about my next route, healing, "
        "Brock readiness, party level, and type weaknesses when relevant."
    )
