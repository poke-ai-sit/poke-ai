import logging
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from pokelive_bridge.battle_agent import (
    generate_taunt,
    plan_battle,
    summarize_battle,
)
from pokelive_bridge.openai_client import ask_codex
from pokelive_bridge.pokemon_text import format_dialog_hex, sanitize_dialog_text
from pokelive_bridge.rival_agent import reset_memory, rival_react


class HealthResponse(BaseModel):
    status: str
    service: str


class GameStateRequest(BaseModel):
    map_group: int
    map_num: int
    x: int
    y: int
    frame: int | None = None


class GameStateResponse(BaseModel):
    received: bool
    game_state: GameStateRequest


class LatestGameStateResponse(BaseModel):
    game_state: GameStateRequest


class PartyEntryRequest(BaseModel):
    species: int
    level: int
    hp: int
    max_hp: int
    moves: list[int]  # length 4, zeros = no move
    attack: int
    defense: int
    speed: int
    sp_attack: int
    sp_defense: int


class CodexChatRequest(BaseModel):
    message: str
    game_state: GameStateRequest | None = None
    party: list[PartyEntryRequest] | None = None
    request_kind: Literal["ADVICE", "ASK"] = "ASK"


class CodexChatResponse(BaseModel):
    speaker: str
    message: str
    message_hex: str
    game_state: GameStateRequest


class RivalEventRequest(BaseModel):
    trigger: Literal[
        "caught_pokemon",
        "won_battle",
        "lost_battle",
        "entered_new_area",
        "first_capture",
        "second_capture",
    ]
    game_state: GameStateRequest
    party: list[PartyEntryRequest] | None = None
    details: dict[str, Any] | None = None
    rival_name: str | None = None


class RivalEventResponse(BaseModel):
    speaker: str
    message: str
    message_hex: str
    action: Literal["approach", "idle"]
    game_state: GameStateRequest
    # Populated only for battle-setup triggers (first_capture / second_capture).
    # Lua writes this byte to gRivalAIBuffer.counterChoice so the C-side
    # battle script picks the right rival lead.
    counter_choice: int | None = None
    counter_label: str | None = None
    # Pokegear-style narration shown BEFORE the rival warps in. Three short
    # textboxes the player advances with A. Lua decodes each hex blob into
    # gRivalEncounterBuffer.callPages[i] so the ROM script can msgbox them
    # via BufferRivalCallNextPage. None for non-battle-setup triggers.
    call_pages: list[str] | None = None
    call_pages_hex: list[str] | None = None


# ---------------------------------------------------------------------------
# Smart Gary battle endpoints
# ---------------------------------------------------------------------------

BattleId = Literal["battle_1_oaks_lab", "battle_2_first_capture", "battle_3_second_capture"]


class BattleMonState(BaseModel):
    """Mid-battle snapshot of one Pokémon. Tighter than PartyEntryRequest —
    only the fields the GPT prompts and battle log need."""
    species: int
    level: int
    hp: int
    max_hp: int
    moves: list[int]  # length 4, zeros = no move
    status: str | None = None  # "burn"/"poison"/"sleep"/None


class BattleLogEntry(BaseModel):
    turn: int
    side: Literal["player", "rival"]
    actor_species: int
    move: str  # already resolved to a name on the Lua side, or "MOVE_X"
    result: str | None = None  # optional: "hit", "missed", "fainted", etc.


class RivalBattlePlanRequest(BaseModel):
    battle_id: BattleId
    player_party: list[BattleMonState]
    rival_party: list[BattleMonState] | None = None
    game_state: GameStateRequest | None = None
    rival_name: str | None = None


class RivalBattlePlanResponse(BaseModel):
    counter_choice: int  # 0-2 (party slot Gary should lead with)
    move_scores: list[int]  # length 4, clamped [-20, +20]
    opening_taunt: str
    opening_taunt_hex: str
    strategy_summary: str
    reasoning_trace: list[str] = []  # step-by-step reasoning shown to audience


class RivalTauntRequest(BaseModel):
    battle_id: BattleId
    turn: int
    rival_mon: BattleMonState
    player_mon: BattleMonState
    last_player_move: str | None = None
    last_rival_move: str | None = None
    rival_name: str | None = None


class RivalTauntResponse(BaseModel):
    taunt: str
    taunt_hex: str


class RivalBattleSummaryRequest(BaseModel):
    battle_id: BattleId
    outcome: Literal["won", "lost", "fled"]
    battle_log: list[BattleLogEntry]
    game_state: GameStateRequest | None = None
    rival_name: str | None = None


class RivalBattleSummaryResponse(BaseModel):
    summary: str
    lessons: str


app = FastAPI(title="PokéLive Bridge")
latest_game_state: GameStateRequest | None = None
latest_rival_plan: RivalBattlePlanResponse | None = None


@app.get("/health")
def get_health() -> HealthResponse:
    return HealthResponse(status="ok", service="pokelive-bridge")


@app.post("/game-state")
def post_game_state(game_state: GameStateRequest) -> GameStateResponse:
    global latest_game_state

    latest_game_state = game_state
    return GameStateResponse(received=True, game_state=game_state)


@app.get("/game-state")
def get_game_state() -> LatestGameStateResponse:
    if latest_game_state is None:
        raise HTTPException(
            status_code=404,
            detail="No game state has been received yet.",
        )

    return LatestGameStateResponse(game_state=latest_game_state)


@app.post("/codex-chat")
def post_codex_chat(chat: CodexChatRequest) -> CodexChatResponse:
    global latest_game_state

    if chat.game_state is not None:
        latest_game_state = chat.game_state

    if latest_game_state is None:
        raise HTTPException(
            status_code=404,
            detail="No game state has been received yet.",
        )

    logger.debug(
        "codex-chat received party_count=%d kind=%s",
        len(chat.party) if chat.party else 0,
        chat.request_kind,
    )
    message = sanitize_dialog_text(
        ask_codex(chat.message, latest_game_state, chat.party, chat.request_kind)
    )

    return CodexChatResponse(
        speaker="Professor GPT 5.5",
        message=message,
        message_hex=format_dialog_hex(message, chars_per_line=200, lines_per_page=1),
        game_state=latest_game_state,
    )


class RivalMemoryResetResponse(BaseModel):
    reset: bool


@app.post("/rival-memory-reset")
def post_rival_memory_reset() -> RivalMemoryResetResponse:
    """Wipe agents/rival/memory.md back to template state.

    Called by Lua once on script load so every demo run starts with a clean
    rival memory — prevents GPT from anchoring on stale party data and
    inverting the actual battle parties in its opening line.
    """
    reset_memory()
    return RivalMemoryResetResponse(reset=True)


@app.post("/rival-event")
def post_rival_event(event: RivalEventRequest) -> RivalEventResponse:
    global latest_game_state

    latest_game_state = event.game_state

    result = rival_react(
        trigger=event.trigger,
        game_state=event.game_state,
        party=event.party,
        details=event.details,
        rival_name=event.rival_name,
    )
    message = result["message"]
    call_pages = result.get("call_pages")
    call_pages_hex: list[str] | None = None
    if call_pages:
        call_pages_hex = [
            format_dialog_hex(p, chars_per_line=200, lines_per_page=1)
            for p in call_pages
        ]

    return RivalEventResponse(
        speaker=event.rival_name or "Rival",
        message=message,
        message_hex=format_dialog_hex(message, chars_per_line=200, lines_per_page=1),
        action="approach",
        game_state=event.game_state,
        counter_choice=result.get("counter_choice"),
        counter_label=result.get("counter_label"),
        call_pages=call_pages,
        call_pages_hex=call_pages_hex,
    )


@app.get("/rival-latest-plan")
def get_rival_latest_plan() -> RivalBattlePlanResponse:
    """Return the most recent battle plan (for the website thinking panel)."""
    if latest_rival_plan is None:
        raise HTTPException(status_code=404, detail="No battle plan has been generated yet.")
    return latest_rival_plan


@app.post("/rival-battle-plan")
def post_rival_battle_plan(req: RivalBattlePlanRequest) -> RivalBattlePlanResponse:
    """Pre-battle: GPT reads memory + opponent + outputs counter + score boosts + opening line."""
    global latest_game_state, latest_rival_plan
    if req.game_state is not None:
        latest_game_state = req.game_state

    plan = plan_battle(
        battle_id=req.battle_id,
        player_party=req.player_party,
        rival_party=req.rival_party,
        game_state=req.game_state,
        rival_name=req.rival_name,
    )

    opening = plan["opening_taunt"]
    response = RivalBattlePlanResponse(
        counter_choice=plan["counter_choice"],
        move_scores=plan["move_scores"],
        opening_taunt=opening,
        opening_taunt_hex=format_dialog_hex(opening, chars_per_line=200, lines_per_page=1),
        strategy_summary=plan["strategy_summary"],
        reasoning_trace=plan.get("reasoning_steps", []),
    )
    latest_rival_plan = response
    return response


@app.post("/rival-taunt")
def post_rival_taunt(req: RivalTauntRequest) -> RivalTauntResponse:
    """Per-turn one-liner. Non-blocking from Lua's POV; if it arrives in time
    it displays, otherwise the next turn proceeds without it."""
    taunt = generate_taunt(
        battle_id=req.battle_id,
        turn=req.turn,
        rival_mon=req.rival_mon,
        player_mon=req.player_mon,
        last_player_move=req.last_player_move,
        last_rival_move=req.last_rival_move,
        rival_name=req.rival_name,
    )
    return RivalTauntResponse(
        taunt=taunt,
        taunt_hex=format_dialog_hex(taunt, chars_per_line=200, lines_per_page=1),
    )


@app.post("/rival-battle-summary")
def post_rival_battle_summary(
    req: RivalBattleSummaryRequest,
) -> RivalBattleSummaryResponse:
    """Post-battle: GPT writes a summary + lessons, appends entry to memory.md."""
    global latest_game_state
    if req.game_state is not None:
        latest_game_state = req.game_state

    result = summarize_battle(
        battle_id=req.battle_id,
        outcome=req.outcome,
        battle_log=req.battle_log,
        game_state=req.game_state,
        rival_name=req.rival_name,
    )
    return RivalBattleSummaryResponse(
        summary=result["summary"],
        lessons=result["lessons"],
    )
