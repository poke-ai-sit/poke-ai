# PokéLive — Implementation Plan

**Target:** AI Engineer Hackathon, Singapore, May 9 2026

---

## Completed Work

| Phase | Description | Files | Status |
|-------|-------------|-------|--------|
| 1 | ASK fix: move publish to C callback | `codex_npc.c`, `specials.inc`, `scripts.inc` | ✅ Done |
| 2 | ROM party data export struct (`gPokelivePartyData`) | `codex_npc.c`, `specials.inc`, `scripts.inc` | ✅ Done |
| 3 | Lua party reader + JSON extension (`request_kind`, `party[]`) | `codex_mailbox_bridge.lua` | ✅ Done |
| 4 | Bridge: Pydantic models, prompt split, PokéAPI name lookups | `pokemon_data.py`, `main.py`, `prompts.py`, `openai_client.py` | ✅ Done |
| 5 | Tests: pokemon_data (11 tests), api (8 tests), prompts (10 tests) | `tests/` | ✅ Done |
| 6 | Merge `pokefirered/` source into poke-ai monorepo | git | ✅ Done |
| 7 | ROM rebuild + address verification | `pokefirered.gba`, `.map` | ✅ Done |

---

## Remaining Tasks — Feature 1 (Prof GPT 5.5)

### P0 — Must do before hackathon demo (May 9)

- [x] **Rebuild the ROM** — ROM rebuilt at 23:49, 13 min after C/script changes (23:36). ✅

- [x] **Verify EWRAM addresses after rebuild** — Map file confirms addresses unchanged:
  - `gPokeliveCodexMailbox = 0x0203f48c` ✅
  - `gPokelivePartyData    = 0x0203f5bc` ✅
  Lua script already has correct values on lines 8–9. ✅

- [ ] **End-to-end ADVICE test with real party data** — Load rebuilt ROM + `fire-red.sav`, pick a starter, start bridge, walk to Prof GPT 5.5 → ADVICE. Confirm bridge stdout shows `party` array with species/moves/stats, and GPT response references the actual Pokémon.

- [ ] **End-to-end ASK test with typed input** — From Oak's Lab, select ASK → type a question → verify GPT answers the specific question (not the default ADVICE prompt).

### P1 — Nice to have for demo polish

- [ ] **ADVICE response length** — GPT may exceed 45 chars when given party context. Test and tune system prompt constraint if needed.

- [ ] **Starter-not-yet-chosen edge case** — ADVICE before picking a starter sends an empty `party[]`. Verify bridge handles `party=[]` and GPT gives a useful generic response.

- [ ] **PokéAPI latency on cold start** — First ADVICE after bridge restart hits PokéAPI for every move/species. Consider pre-warming Gen1 species cache at bridge startup.

---

## Feature 2 — AI Rival

### Overview
Dynamic rival that: (1) analyzes player's party, (2) picks a counter Pokémon from the existing 3 trained options, (3) delivers an AI-generated taunt referencing the player's team, (4) uses pre-computed move scores to influence actual battle AI, and (5) remembers win/loss history across interactions.

**Demo sequence:**
1. Player picks starter → rival enters Oak's Lab for battle
2. Rival "thinks" (wait loop) → AI-generated taunt mentioning player's Pokémon
3. Rival uses counter Pokémon chosen by AI (Squirtle/Charmander/Bulbasaur)
4. Rival's battle AI uses pre-computed move priorities from bridge
5. After battle → win/loss stored server-side
6. After catching 2nd Pokémon → rival returns, references battle history

### P0 — Hackathon demo requirements

#### ROM Changes

- [ ] **`gRivalAIBuffer` EWRAM struct (8 bytes)**
  ```c
  struct PokeliveRivalAIBuffer {
      u8 active;          // 1 = move plan loaded (consume on first AI turn)
      s8 moveScore[4];    // score additive per move slot; applied after AI scripts
      u8 counterChoice;   // 0=Squirtle, 1=Charmander, 2=Bulbasaur (AI-chosen)
      u8 resultPending;   // 1=player_won, 2=rival_won; Lua polls and clears
      u8 pad;
  };
  EWRAM_DATA struct PokeliveRivalAIBuffer gRivalAIBuffer = {0};
  ```
  Add to `codex_npc.c`. Verify ROM still links (budget: ~588 bytes remaining, struct is 8 bytes).

- [ ] **3 new specials in `codex_npc.c`**
  1. `PublishRivalPlanPrompt()` — calls `UpdateCodexPartyData()`, then sets mailbox PENDING with `request_kind=RIVAL_PLAN` command string.
  2. `GetRivalCounterChoice()` — reads `gRivalAIBuffer.counterChoice` → `gSpecialVar_Result`.
  3. `MarkRivalBattleResult(u8 result)` — writes `result` (1=win, 2=loss) to `gRivalAIBuffer.resultPending`, clears `gRivalAIBuffer.active`.

- [ ] **Register specials in `specials.inc`**
  Add `def_special PublishRivalPlanPrompt`, `def_special GetRivalCounterChoice`, `def_special MarkRivalBattleResult`.

- [ ] **Battle AI hook in `battle_ai_script_commands.c`**
  In `BattleAI_ChooseMoveOrAction()`, after the `while (aiFlags != 0)` loop and before the score comparison block (line ~382), insert:
  ```c
  /* Guard: only apply for rival trainer battles, not wild or other trainers */
  if (gRivalAIBuffer.active
      && (gTrainerBattleOpponent_A == TRAINER_RIVAL_OAKS_LAB_SQUIRTLE
       || gTrainerBattleOpponent_A == TRAINER_RIVAL_OAKS_LAB_CHARMANDER
       || gTrainerBattleOpponent_A == TRAINER_RIVAL_OAKS_LAB_BULBASAUR))
  {
      for (i = 0; i < MAX_MON_MOVES; i++)
      {
          s32 newScore = (s32)AI_THINKING_STRUCT->score[i] + gRivalAIBuffer.moveScore[i];
          if (newScore > 127) newScore = 127;
          if (newScore < -128) newScore = -128;
          AI_THINKING_STRUCT->score[i] = (s8)newScore;
      }
      gRivalAIBuffer.active = 0;
  }
  ```
  Add `extern struct PokeliveRivalAIBuffer gRivalAIBuffer;` at top of file.
  NOTE: s8 clamp applied explicitly (s32 intermediate prevents overflow). Bridge also pre-clamps move_scores to [-20, +20] as a first line of defence.

- [ ] **`scripts.inc` — rival battle pre-battle flow**
  Before each `trainerbattle_earlyrival` call, insert (reusing existing wait-loop pattern):
  ```
  @ PublishRivalPlanPrompt called ONCE before the loop label (not inside the loop)
  special UpdateCodexPartyData
  special PublishRivalPlanPrompt
  PalletTown_ProfessorOaksLab_EventScript_RivalWait::
      msgbox PalletTown_ProfessorOaksLab_Text_RivalThinking, MSGBOX_DEFAULT
  PalletTown_ProfessorOaksLab_EventScript_RivalWaitLoop::
      delay 15
      special IsCodexResponseReady
      goto_if_eq VAR_RESULT, FALSE, PalletTown_ProfessorOaksLab_EventScript_RivalWaitLoop
  special BufferCodexResponse         @ rival taunt → gStringVar1
  special GetRivalCounterChoice       @ gSpecialVar_Result = 0/1/2 (reads gRivalAIBuffer.counterChoice)
  msgbox gStringVar1, MSGBOX_DEFAULT  @ rival speaks AI taunt
  @ Branch on counter choice to existing rival battle paths
  goto_if_eq VAR_RESULT, 0, EventScript_RivalBattleSquirtle
  goto_if_eq VAR_RESULT, 1, EventScript_RivalBattleCharmander
  goto_if_eq VAR_RESULT, 2, EventScript_RivalBattleBulbasaur
  goto EventScript_RivalBattleSquirtle  @ fallback
  ```
  After each battle path's win text, call `MarkRivalBattleResult(1)`. After loss text, call `MarkRivalBattleResult(2)`.
  NOTE: `PublishRivalPlanPrompt` is called OUTSIDE the wait loop — same as existing ADVICE/ASK pattern.

- [ ] **Rebuild ROM + re-verify EWRAM addresses**
  After all ROM changes: `make -j$(sysctl -n hw.logicalcpu)`, grep `.map` for `gRivalAIBuffer`. Update Lua constants.

#### Lua Changes (`codex_mailbox_bridge.lua`)

- [ ] **Add `RIVAL_AI_BUFFER_ADDR` constant** — value from `.map` after rebuild.

- [ ] **Extend `json_codex_chat()`** to detect `request_kind=RIVAL_PLAN` and include party data (same as ADVICE).

- [ ] **Parse RIVAL_PLAN response fields**: after `extract_json_field(response, "message_hex")`, also extract:
  - `move_scores` (JSON array of 4 ints → write to `gRivalAIBuffer.moveScore[0..3]` via `emu:write8`)
  - `counter_choice` (int 0-2 → write to `gRivalAIBuffer.counterChoice` via `emu:write8`)
  - Write `gRivalAIBuffer.active = 1` last (after scores are written).
  - NOTE: `move_scores`/`counter_choice` go directly to EWRAM via Lua — they do NOT go through the 256-byte mailbox response buffer. Only `message_hex` (rival taunt) uses the mailbox buffer.

- [ ] **Poll `gRivalAIBuffer.resultPending`** each frame. When non-zero: clear the byte FIRST (`emu:write8(RIVAL_AI_BUFFER_ADDR+6, 0)`), then POST `/rival-result`. Clearing before POST prevents duplicate sends if the POST is slow and the loop fires again next frame.

#### Bridge Changes (FastAPI Python)

- [ ] **New `request_kind="RIVAL_PLAN"` in `openai_client.py`**
  Dispatch to `ask_rival()` function that uses `response_format={"type": "json_object"}` to return structured output.

- [ ] **New `ask_rival()` in `openai_client.py`**
  Calls OpenAI with JSON mode. Parses response into `RivalPlanResult`. Falls back to defaults on error.

- [ ] **New Pydantic models in `main.py`**:
  ```python
  class RivalPlanResult(BaseModel):
      message: str
      message_hex: str
      move_scores: list[int]    # [s0, s1, s2, s3], each -20 to +20 (NOT +30: s8 max=127, 100+20=120 safe)
      counter_choice: int       # 0=Squirtle, 1=Charmander, 2=Bulbasaur
  
  class RivalResultRequest(BaseModel):
      winner: Literal["player", "rival"]
      frame: int | None = None
  ```

- [ ] **New `POST /rival-result` endpoint** — appends `{winner, timestamp}` to in-process `rival_history: list[dict]`.

- [ ] **`build_rival_plan_prompt()` in `prompts.py`** — system prompt that instructs GPT to:
  - Output strict JSON with keys: `message` (taunt ≤45 chars, letters+numbers+spaces only), `move_scores` (array of 4 ints, each -20 to +30, higher = prefer), `counter_choice` (0, 1, or 2).
  - Include player party summary + battle history.

- [ ] **New `POST /rival-plan` endpoint** — separate from `/codex-chat` to avoid polluting existing dispatch. Lua calls `/rival-plan` when mailbox command contains RIVAL_PLAN sentinel. Returns `RivalPlanResult` with `message_hex` + `move_scores` + `counter_choice`.

### P1 — Post-hackathon polish

- [ ] **Second rival encounter trigger** — After catching 2nd Pokémon (`setflag FLAG_CAUGHT_2ND_POKEMON`), trigger rival reappearance script. Rival references battle history in taunt.

- [ ] **Battle history in prompt** — Pass `rival_history[-3:]` to `build_rival_plan_prompt()` for multi-battle memory.

- [ ] **Response length for taunts** — Monitor GPT taunt length. Tighten system prompt or add post-truncation to `message` field.

---

## Architecture Reference

```
ROM (C + scripts)
  └─ codex_npc.c
       ├─ CB2_PublishCodexPromptAndReturn   ← publish after naming screen closes (ASK)
       ├─ gPokelivePartyData  0x0203f5bc    ← EWRAM: 152-byte party struct
       ├─ gRivalAIBuffer      TBD           ← EWRAM: 8-byte rival plan buffer
       ├─ UpdateCodexPartyData()            ← fills via GetMonData
       ├─ PublishRivalPlanPrompt()          ← NEW: RIVAL_PLAN request
       ├─ GetRivalCounterChoice()           ← NEW: reads counterChoice → gSpecialVar_Result
       └─ MarkRivalBattleResult()           ← NEW: sets resultPending for Lua
  └─ battle_ai_script_commands.c
       └─ BattleAI_ChooseMoveOrAction()     ← +8 lines: apply gRivalAIBuffer.moveScore[] after AI scripts
  └─ scripts.inc (PalletTown_ProfessorOaksLab)
       ├─ ADVICE: UpdateCodexPartyData → PublishCodexAdvicePrompt → ProfessorCodexWait
       ├─ ASK:    StartCodexPrompt → ProfessorCodexWait
       └─ RIVAL:  UpdateCodexPartyData → PublishRivalPlanPrompt → RivalWait → GetRivalCounterChoice → trainerbattle_earlyrival

Lua bridge (codex_mailbox_bridge.lua)
  └─ CODEX_MAILBOX_ADDR   0x0203f48c
  └─ PARTY_DATA_ADDR      0x0203f5bc
  └─ RIVAL_AI_BUFFER_ADDR TBD              ← re-verify after rebuild
  └─ json_codex_chat()    ← adds request_kind=RIVAL_PLAN + party[] when applicable
  └─ (RIVAL_PLAN response) → writes moveScore[] + counterChoice + active to EWRAM
  └─ (frame poll) → detects resultPending → POST /rival-result

FastAPI bridge (Python)
  └─ pokemon_data.py  ← PokéAPI lookups with @lru_cache
  └─ prompts.py       ← build_codex_system_prompt_advice / _ask / build_rival_plan_prompt (NEW)
  └─ openai_client.py ← ask_codex() / ask_rival() (NEW, JSON mode)
  └─ main.py          ← /codex-chat / /rival-plan (NEW) / /rival-result (NEW)
```

---

## gPokelivePartyData Struct Layout

```c
struct PokelivePartyEntry {  // 24 bytes
    u16 magic;       // 0x5054 "PT"
    u16 species;     u16 level;  u16 hp;  u16 maxHP;
    u16 moves[4];    u16 attack; u16 defense;
    u16 speed;       u16 spAttack; u16 spDefense;
};

struct PokelivePartyData {   // 152 bytes
    u32 magic;   // 0x50415254 "PART"
    u8  count;   u8 pad[3];
    struct PokelivePartyEntry entries[6];
};
```

## gRivalAIBuffer Struct Layout

```c
struct PokeliveRivalAIBuffer {   // 8 bytes
    u8 active;          // 1 = plan loaded, consume on first AI turn
    s8 moveScore[4];    // additive score boost per move slot (range: -20 to +30)
    u8 counterChoice;   // 0=Squirtle, 1=Charmander, 2=Bulbasaur
    u8 resultPending;   // 1=player_won, 2=rival_won; cleared by Lua after POST
    u8 pad;
};
```

---

## Key Risks

| Risk | Mitigation |
|------|-----------|
| EWRAM linker failure after adding 8 bytes | Check `.map` total before merge; 8 bytes << 588 remaining |
| EWRAM addresses shift after rebuild | Re-grep `.map`; magic bytes detect mismatches at runtime |
| GPT JSON mode returns invalid structure | Pydantic validation + fallback defaults in `ask_rival()` |
| GPT taunt exceeds 45 chars | `sanitize_dialog_text` post-truncates; tighten system prompt |
| Battle AI score overflow (s8) | Bridge clamps `move_scores` to [-20, +30]; base score is 100 |
| resultPending not cleared → spam | Lua clears immediately after HTTP send (before response) |
| PokéAPI timeout during demo (network issue) | Falls back to `#<id>` — GPT still receives numeric IDs |
| trainerbattle_earlyrival ignores VAR_RESULT | Script uses GetRivalCounterChoice BEFORE trainerbattle cmd |
