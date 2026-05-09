"""Battle-aware GPT agent for the Smart Gary system.

Three flows:
- plan_battle: pre-battle, reads memory.md + player party + rival party,
  outputs counter choice, per-move score boosts (for gRivalAIBuffer.moveScore),
  and an opening taunt.
- generate_taunt: per-turn one-liner. Non-blocking from Lua's perspective —
  if the response arrives before next turn it displays, otherwise skipped.
- summarize_battle: post-battle, takes the full chess log + outcome and writes
  a structured memory entry that future plan_battle calls will see.

All three share the rival persona file with rival_agent.py. Battle entries
are appended to the same memory.md so the rival has one continuous memory
across both casual encounters and battles.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal

import openai

from pokelive_bridge.config import (
    OPENAI_API_KEY,
    OPENAI_CHAT_MODEL,
    OPENAI_MAX_COMPLETION_TOKENS,
)
from pokelive_bridge.pokemon_text import sanitize_dialog_text
from pokelive_bridge.rival_agent import (
    _append_memory,
    _read_persona,
    _read_recent_memory,
    FALLBACK_MESSAGE,
)


# Per-turn taunt may exceed 45 chars at battle moments per the design spec.
# Pre/post-battle speeches can use up to ~120 chars, paginated client-side.
_TAUNT_MAX_CHARS = 45
_BATTLE_SPEECH_MAX_CHARS = 120
_SUMMARY_MAX_CHARS = 400  # written to memory only, not displayed in textbox

FALLBACK_TAUNT = "You wont win this time."
FALLBACK_OPENING = "Time to show you who is really the best."
FALLBACK_SUMMARY = "Battle ended. Memory append failed."

BATTLE_ID_LABELS: dict[str, str] = {
    "battle_1_oaks_lab": "Battle 1 — Oak's Lab",
    "battle_2_first_capture": "Battle 2 — after first capture",
    "battle_3_second_capture": "Battle 3 — after second capture",
}


_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _client


def _resolve_species(species_id: int) -> str:
    from pokelive_bridge.pokemon_data import species_name
    return species_name(species_id)


def _resolve_move(move_id: int) -> str:
    from pokelive_bridge.pokemon_data import move_name
    return move_name(move_id)


def _format_party(party: list[Any] | None, label: str) -> str:
    if not party:
        return f"{label}: unknown"
    lines = [f"{label}:"]
    for entry in party:
        species = _resolve_species(entry.species)
        moves = " / ".join(
            _resolve_move(m) for m in entry.moves if m and m != 0
        ) or "no moves"
        status = f" [{entry.status}]" if getattr(entry, "status", None) else ""
        lines.append(
            f"  {species} L{entry.level} HP {entry.hp}/{entry.max_hp}{status}"
            f"  moves: {moves}"
        )
    return "\n".join(lines)


def _format_battle_log(log: list[Any]) -> str:
    if not log:
        return "(empty log)"
    lines = []
    for entry in log:
        actor = _resolve_species(entry.actor_species)
        side = entry.side.upper()
        result = f" → {entry.result}" if getattr(entry, "result", None) else ""
        lines.append(f"  T{entry.turn} {side} {actor} used {entry.move}{result}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# /rival-battle-plan
# ---------------------------------------------------------------------------


def plan_battle(
    battle_id: str,
    player_party: list[Any],
    rival_party: list[Any] | None = None,
    game_state: Any = None,
    rival_name: str | None = None,
) -> dict[str, Any]:
    """Pre-battle: pick a counter, output move-score boosts, write opening line.

    Returns:
      {
        "counter_choice": int,         # 0-based party slot Gary leads with
        "move_scores": list[int],      # length 4, clamped [-20, +20]
        "opening_taunt": str,          # ≤120 chars (paginatable)
        "strategy_summary": str,       # written into memory afterwards
      }
    """
    persona = _read_persona(rival_name)
    memory = _read_recent_memory()
    label = BATTLE_ID_LABELS.get(battle_id, battle_id)
    player_block = _format_party(player_party, "Player party (CURRENT, ground truth)")
    rival_block = _format_party(rival_party, "Your party (CURRENT, ground truth)")
    location = ""
    if game_state is not None:
        from pokelive_bridge.map_data import map_name
        location = (
            f"Location: {map_name(game_state.map_group, game_state.map_num)}\n"
        )

    system_prompt = (
        f"{persona}\n\n"
        f"---\n"
        f"## Pre-Battle Strategy ({label})\n"
        f"{location}"
        f"{player_block}\n\n"
        f"{rival_block}\n\n"
        f"## Your Memory of Past Encounters\n"
        f"{memory}\n\n"
        f"## CRITICAL — Ground Truth Anchoring\n"
        f"The Player party and Your party blocks above are the LIVE state.\n"
        f"If memory mentions different species (e.g. an old battle where the\n"
        f"player had Charmander), trust the LIVE state, not memory.\n"
        f"NEVER invert the parties — the rival's species is in 'Your party',\n"
        f"the player's is in 'Player party'.\n\n"
        f"## Output\n"
        f"You must output ONE JSON object with exactly these keys:\n"
        f"  reasoning_steps: array of 2-4 short strings (under 60 chars each)\n"
        f"                   showing your step-by-step thinking BEFORE deciding.\n"
        f"                   E.g. [\"Player leads Charmander (Fire type)\",\n"
        f"                         \"Squirtle has type advantage\",\n"
        f"                         \"Boost Water Gun slot +15\"].\n"
        f"                   This is shown to the audience — be specific.\n"
        f"  counter_choice: integer 0-2 — which of your party slots leads.\n"
        f"  move_scores: array of 4 integers in range [-20, 20] — additive\n"
        f"               boosts to your lead's move scoring. Index 0 is move 1.\n"
        f"               Higher = more likely to use. Use -20 to suppress.\n"
        f"  opening_taunt: string under 120 characters, ASCII letters numbers\n"
        f"                 spaces and periods only, no exclamation or question\n"
        f"                 marks, in character, said when battle starts.\n"
        f"  strategy_summary: string under 300 chars summarizing your plan and\n"
        f"                    why memory shaped it. Reference live species only.\n"
        f"Do not include any other keys. Do not wrap in markdown.\n"
    )

    client = _get_client()
    raw: dict[str, Any]
    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Plan {label}."},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=OPENAI_MAX_COMPLETION_TOKENS,
        )
        content = response.choices[0].message.content or "{}"
        raw = json.loads(content)
    except Exception as e:
        logging.exception("plan_battle GPT call failed: %s", e)
        raw = {}

    raw_steps = raw.get("reasoning_steps", [])
    reasoning_steps: list[str] = (
        [str(s)[:80] for s in raw_steps[:4]]
        if isinstance(raw_steps, list)
        else []
    )

    counter_choice = int(raw.get("counter_choice", 0))
    counter_choice = max(0, min(2, counter_choice))

    raw_scores = raw.get("move_scores", [0, 0, 0, 0])
    move_scores: list[int] = []
    for i in range(4):
        try:
            score = int(raw_scores[i]) if i < len(raw_scores) else 0
        except (TypeError, ValueError):
            score = 0
        move_scores.append(max(-20, min(20, score)))

    opening_taunt = sanitize_dialog_text(
        str(raw.get("opening_taunt", FALLBACK_OPENING))
    )[:_BATTLE_SPEECH_MAX_CHARS].rstrip()

    strategy_summary = str(raw.get("strategy_summary", "")).strip()[:_SUMMARY_MAX_CHARS]

    # Persist the strategy decision so future plan_battle calls can see it.
    _record_battle_plan(battle_id, counter_choice, move_scores, strategy_summary, reasoning_steps)

    return {
        "counter_choice": counter_choice,
        "move_scores": move_scores,
        "opening_taunt": opening_taunt,
        "strategy_summary": strategy_summary,
        "reasoning_steps": reasoning_steps,
    }


def _record_battle_plan(
    battle_id: str,
    counter_choice: int,
    move_scores: list[int],
    strategy: str,
    reasoning_steps: list[str] | None = None,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    label = BATTLE_ID_LABELS.get(battle_id, battle_id)
    lines = [
        f"\n## {timestamp} — {label} (PLAN)",
        f"Counter choice: party slot {counter_choice}",
        f"Move score boosts: {move_scores}",
    ]
    if reasoning_steps:
        lines.append("Reasoning: " + " → ".join(reasoning_steps))
    if strategy:
        lines.append(f"Strategy: {strategy}")
    _append_memory("\n".join(lines))


# ---------------------------------------------------------------------------
# /rival-taunt
# ---------------------------------------------------------------------------


def generate_taunt(
    battle_id: str,
    turn: int,
    rival_mon: Any,
    player_mon: Any,
    last_player_move: str | None = None,
    last_rival_move: str | None = None,
    rival_name: str | None = None,
) -> str:
    """Per-turn one-liner. ≤45 chars."""
    persona = _read_persona(rival_name)
    label = BATTLE_ID_LABELS.get(battle_id, battle_id)

    rival_species = _resolve_species(rival_mon.species)
    player_species = _resolve_species(player_mon.species)

    state_block = (
        f"Turn {turn} of {label}.\n"
        f"Your {rival_species}: HP {rival_mon.hp}/{rival_mon.max_hp}\n"
        f"Player's {player_species}: HP {player_mon.hp}/{player_mon.max_hp}\n"
    )
    if last_rival_move:
        state_block += f"Your last move: {last_rival_move}\n"
    if last_player_move:
        state_block += f"Player's last move: {last_player_move}\n"

    system_prompt = (
        f"{persona}\n\n"
        f"---\n\n"
        f"## Mid-Battle Taunt\n"
        f"{state_block}\n"
        f"## Instructions\n"
        f"Reply with ONE punchy line under 45 characters. Be in character.\n"
        f"React to the current matchup or recent moves. No exclamation marks\n"
        f"no question marks no quotes. Letters numbers spaces and periods only.\n"
    )

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Taunt the player on turn {turn}."},
            ],
            max_completion_tokens=OPENAI_MAX_COMPLETION_TOKENS,
        )
        content = response.choices[0].message.content
        text = content.strip() if content else FALLBACK_TAUNT
    except Exception as e:
        logging.exception("generate_taunt GPT call failed: %s", e)
        text = FALLBACK_TAUNT

    sanitized = sanitize_dialog_text(text)
    if len(sanitized) > _TAUNT_MAX_CHARS:
        sanitized = sanitized[:_TAUNT_MAX_CHARS].rstrip()
    return sanitized


# ---------------------------------------------------------------------------
# /rival-battle-summary
# ---------------------------------------------------------------------------


def summarize_battle(
    battle_id: str,
    outcome: str,
    battle_log: list[Any],
    game_state: Any = None,
    rival_name: str | None = None,
) -> dict[str, str]:
    """Post-battle: GPT summary + lessons appended to memory.md.

    Returns: {"summary": str, "lessons": str}
    """
    persona = _read_persona(rival_name)
    memory = _read_recent_memory()
    label = BATTLE_ID_LABELS.get(battle_id, battle_id)
    log_block = _format_battle_log(battle_log)

    # Extract the actual species each side used so the prompt can anchor
    # GPT's summary on ground-truth instead of memory hallucinations. The
    # battle_log entries already have actor_species resolved by name in the
    # log_block above, but spelling them out explicitly here is the cheapest
    # way to stop GPT from inverting parties.
    rival_species_seen = sorted({
        _resolve_species(e.actor_species)
        for e in battle_log if e.side == "rival"
    })
    player_species_seen = sorted({
        _resolve_species(e.actor_species)
        for e in battle_log if e.side == "player"
    })
    rival_species_str = ", ".join(rival_species_seen) or "unknown"
    player_species_str = ", ".join(player_species_seen) or "unknown"

    system_prompt = (
        f"{persona}\n\n"
        f"---\n"
        f"## Battle Just Finished — {label}\n"
        f"Outcome: {outcome.upper()}\n\n"
        f"### CRITICAL — Ground Truth (do not contradict this)\n"
        f"Your species (rival side): {rival_species_str}\n"
        f"Player's species: {player_species_str}\n\n"
        f"### Move Log (chronological)\n"
        f"{log_block}\n\n"
        f"## Your Earlier Memory\n"
        f"{memory}\n\n"
        f"## Output\n"
        f"You must output ONE JSON object with exactly these keys:\n"
        f"  summary: string under 200 chars — what happened in this battle.\n"
        f"           Stay in character thinking back on the fight. ONLY name\n"
        f"           species from the Ground Truth block above. NEVER invert\n"
        f"           the parties — your side used {rival_species_str}, the\n"
        f"           player used {player_species_str}.\n"
        f"  lessons: string under 200 chars — what you learned about the\n"
        f"           player's preferences and what counter you should pick\n"
        f"           next time. Concrete and actionable, no fluff.\n"
        f"Do not include other keys. Do not wrap in markdown.\n"
    )

    client = _get_client()
    raw: dict[str, Any]
    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Reflect on {label}."},
            ],
            response_format={"type": "json_object"},
            max_completion_tokens=OPENAI_MAX_COMPLETION_TOKENS,
        )
        content = response.choices[0].message.content or "{}"
        raw = json.loads(content)
    except Exception as e:
        logging.exception("summarize_battle GPT call failed: %s", e)
        raw = {}

    summary = str(raw.get("summary", FALLBACK_SUMMARY)).strip()[:_SUMMARY_MAX_CHARS]
    lessons = str(raw.get("lessons", "")).strip()[:_SUMMARY_MAX_CHARS]

    _record_battle_summary(battle_id, outcome, battle_log, summary, lessons)

    return {"summary": summary, "lessons": lessons}


def _record_battle_summary(
    battle_id: str,
    outcome: str,
    battle_log: list[Any],
    summary: str,
    lessons: str,
) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    label = BATTLE_ID_LABELS.get(battle_id, battle_id)
    lines = [
        f"\n## {timestamp} — {label} (RESULT)",
        f"Outcome: {outcome.upper()}",
        f"Turns: {len(battle_log)}",
    ]
    if battle_log:
        lines.append("Move log:")
        for entry in battle_log:
            actor = _resolve_species(entry.actor_species)
            side = entry.side.upper()
            result = f" → {entry.result}" if getattr(entry, "result", None) else ""
            lines.append(f"  T{entry.turn} {side} {actor} used {entry.move}{result}")
    if summary:
        lines.append(f"Summary: {summary}")
    if lessons:
        lines.append(f"Lessons: {lessons}")
    _append_memory("\n".join(lines))
