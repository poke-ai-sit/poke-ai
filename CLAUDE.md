# PokéLive — CLAUDE.md

## Project Overview

PokéLive turns Pokémon FireRed into a live AI experience inside the mGBA emulator.
Three features: (1) AI-powered NPC (Professor GPT 5.5), (2) AI Rival (dynamic rival with AI battle planning), (3) custom Pokémon generator (stretch goal).
Target: AI Engineer Hackathon, Singapore, May 9 2026.

## Repository Layout

```
poke-ai/                              ← this repo (current working directory)
  CLAUDE.md                           ← this file
  pokefirered/                        ← cloned + patched pret/pokefirered decompilation
    pokefirered.gba                   ← compiled patched ROM
    pokefirered.map                   ← linker map — grep for gPokeliveCodexMailbox
    src/codex_npc.c                   ← mailbox struct + special functions
    data/specials.inc                 ← registers codex specials in gSpecials table
    data/maps/PalletTown_ProfessorOaksLab/
      scripts.inc                     ← Prof GPT 5.5 NPC script (line ~950)
      map.json                        ← NPC placement (GPT5.5 = scientist at x=2,y=3)
    src/naming_screen.c               ← ASK title: "ASK GPT5.5"

  bridge/                             ← FastAPI Python bridge (uv project)
    run.sh                            ← start bridge (unsets stale VIRTUAL_ENV)
    .env                              ← OPENAI_API_KEY, OPENAI_CHAT_MODEL (not committed)
    src/pokelive_bridge/
      main.py                         ← FastAPI app: /health, /game-state, /codex-chat
      openai_client.py                ← OpenAI client (lazy init per-call)
      prompts.py                      ← GPT5.5 system prompt + game state injection
      pokemon_text.py                 ← FireRed text encoder (encode/format/sanitize)
      config.py                       ← .env loader (path-relative, not CWD-dependent)

  emulator/lua/
    codex_mailbox_bridge.lua          ← mGBA Lua bridge

pokelive/                             ← sibling dir with original assets
  fire-red.gba                        ← original unpatched ROM (DO NOT COMMIT)
  fire-red.sav                        ← battery save (portable across ROM rebuilds)
  patches/pokefirered-commits/        ← 3 git-format patches for pokefirered
  bridge/server/                      ← original bridge (superseded by poke-ai/bridge)
  emulator/lua/                       ← original Lua (superseded by poke-ai/emulator/lua)
```

## Architecture

```
mGBA emulator
  └─ Lua script (codex_mailbox_bridge.lua)
       ├─ polls  gPokeliveCodexMailbox (EWRAM 0x0203F4AC) every frame
       ├─ ADVICE/ASK: when status=PENDING → POST /codex-chat → write message_hex → READY
       ├─ RIVAL_PLAN: when status=PENDING → POST /rival-plan → write message_hex to mailbox
       │              + write move_scores/counter_choice directly to gRivalAIBuffer EWRAM
       └─ frame poll: if gRivalAIBuffer.resultPending → POST /rival-result → clear byte

FastAPI bridge (localhost:8000)
  └─ POST /codex-chat      → OpenAI (ADVICE/ASK) → 1 sentence ≤45 chars → hex-encoded
  └─ POST /rival-plan      → OpenAI JSON mode → {message_hex, move_scores[4], counter_choice}
  └─ POST /rival-result    → store {winner, timestamp} in-process list (no response needed)

Patched ROM (pokefirered.gba)
  └─ Prof GPT 5.5 NPC in Oak's Lab (scientist sprite at x=2,y=3)
       → requires FLAG_BEAT_RIVAL_IN_OAKS_LAB to be set
       → multichoice: ADVICE / ASK / EVOLVE / EXIT
       → ADVICE: PublishCodexAdvicePrompt → ProfessorCodexWait (infinite loop until response)
       → ASK: naming screen → PublishCodexPrompt → ProfessorCodexWait
       → waits for IsCodexResponseReady (polls every 15 frames, NO game-side timeout)
       → BufferCodexResponse → copies response to gStringVar1 → msgbox {STR_VAR_1}
  └─ AI Rival (Oak's Lab rival battle)
       → UpdateCodexPartyData → PublishRivalPlanPrompt → RivalWait loop
       → BufferCodexResponse (rival taunt) → GetRivalCounterChoice → msgbox taunt
       → goto rival battle path 0/1/2 (Squirtle/Charmander/Bulbasaur) based on AI choice
       → battle uses gRivalAIBuffer.moveScore[4] boosts in BattleAI_ChooseMoveOrAction
       → post-battle: MarkRivalBattleResult → Lua fires /rival-result
```

## AI Rival — Key Implementation Details

### gRivalAIBuffer Struct (8 bytes, EWRAM)
```c
struct PokeliveRivalAIBuffer {
    u8 active;          // 1 = move plan loaded, cleared after first AI turn
    s8 moveScore[4];    // score additive per move slot; MUST be clamped to [-20, +20]
                        // s8 max=127; base score=100; 100+20=120 safe; >+27 wraps negative
    u8 counterChoice;   // 0=Squirtle rival, 1=Charmander rival, 2=Bulbasaur rival
    u8 resultPending;   // 1=player_won, 2=rival_won; Lua polls → clears after POST
    u8 pad;
};
```

### Battle AI Hook (battle_ai_script_commands.c)
Insert after `while (aiFlags != 0)` loop in `BattleAI_ChooseMoveOrAction()`, before score comparison:
```c
extern struct PokeliveRivalAIBuffer gRivalAIBuffer;
if (gRivalAIBuffer.active)
{
    for (i = 0; i < MAX_MON_MOVES; i++)
        AI_THINKING_STRUCT->score[i] += gRivalAIBuffer.moveScore[i];
    gRivalAIBuffer.active = 0;
}
```

### New C Specials (codex_npc.c)
- `PublishRivalPlanPrompt()` — calls UpdateCodexPartyData(), sets mailbox PENDING with RIVAL_PLAN command
- `GetRivalCounterChoice()` — reads `gRivalAIBuffer.counterChoice` → `gSpecialVar_Result`
- `MarkRivalBattleResult()` — writes `gSpecialVar_Result` to `gRivalAIBuffer.resultPending`

### Lua Data Flow (RIVAL_PLAN response)
1. Lua receives HTTP response from `/rival-plan`
2. Extract `message_hex` → write to 256-byte mailbox response buffer (rival taunt text only)
3. Extract `move_scores[4]` → `emu:write8(RIVAL_AI_BUFFER_ADDR+1..4, score)`
4. Extract `counter_choice` → `emu:write8(RIVAL_AI_BUFFER_ADDR+5, choice)`
5. Write `active=1` → `emu:write8(RIVAL_AI_BUFFER_ADDR+0, 1)` — LAST, after scores are set
6. Mark mailbox READY (ack=seq, status=RESPONSE_READY)

### EWRAM Budget
- Before AI Rival: 261556/262144 bytes used (99.78%, ~588 bytes remaining)
- `gRivalAIBuffer`: 8 bytes → ~580 bytes remaining after addition
- Verify linker succeeds after adding struct; check `.map` total size

## Key Addresses (FireRed v1.0 USA, patched ROM)

| Symbol | Address | Notes |
|---|---|---|
| `gPokeliveCodexMailbox` | `0x0203F4AC` | Set in `codex_mailbox_bridge.lua` line 8 |
| `gPokelivePartyData` | `0x0203F5DC` | Set in `codex_mailbox_bridge.lua` line 9 |
| `gRivalAIBuffer` | TBD | Re-grep `.map` after AI Rival ROM rebuild |
| SaveBlock1 pointer | `0x03005008` | Party data at +0x238, each mon 100 bytes |

## Mailbox Struct Layout (offset from 0x0203F4AC)

| Offset | Type | Field | Notes |
|---|---|---|---|
| 0 | u32 | magic | Must be 0x58454443 ("CDEX") or Lua skips it |
| 4 | u16 | seq | Incremented by game on each new request |
| 6 | u16 | ack | Written by Lua when response is ready |
| 8 | u8 | status | 0=IDLE 1=PENDING 2=READY 3=ERROR |
| 10 | u16 | commandLength | |
| 12 | u16 | responseLength | |
| 14 | u8[33] | command | FireRed-encoded input text |
| 47 | u8[257] | response | FireRed-encoded response (flat, NO 0xFB/0xFE) |

`IsCodexResponseReady` triggers when `status==READY && ack==seq`.

## Known Issues and Fixes Applied

### ROM / C patches
- `src/codex_npc.c` include: `"constants/characters.h"` → `"characters.h"`
- `src/codex_npc.c`: removed `#include "strings.h"`; replaced `gText_EmptyString2` with `gStringVar1[0] = EOS`
- `data/specials.inc`: removed `, waitstate=1` from `def_special StartCodexPrompt`

### Response encoding — CRITICAL
- `0xFB` (PAGE_BREAK) inside `{STR_VAR_1}` substitution crashes the textbox engine
- **Fix**: `format_dialog_hex(msg, chars_per_line=200, lines_per_page=1)` — flat encoding, NO 0xFB/0xFE
- Response must be 1 sentence ≤ 45 chars (enforced by system prompt)

### Bridge config
- `load_dotenv()` with no args fails when FastAPI reloader changes CWD
- **Fix**: explicit path `Path(__file__).resolve().parent.parent.parent / ".env"`

### OpenAI client
- Module-level `_client = openai.OpenAI(...)` uses empty key if `.env` not loaded at import time
- **Fix**: lazy init inside `ask_codex()` function

### gpt-5.5 token budget
- 512 tokens exhausted by reasoning phase → empty `content` → fallback response
- **Fix**: `OPENAI_MAX_COMPLETION_TOKENS` default raised to 4096

### Game wait loop
- Game-side counter timeout (40/120 × 15 frames) races against emulator speed and API latency
- **Fix**: infinite `delay 15` + `goto` loop; Lua wall-clock timeout (90s) writes "Try again." + marks READY

### Save state magic mismatch
- Loading `.ss0` saves with uninitialised EWRAM gives "magic mismatch" warnings — **cosmetic only**
- Game calls `EnsureCodexMailboxInitialized` when player first talks to Prof GPT 5.5
- Use battery save (`.sav`) for portability across ROM rebuilds; `.ss0` save states are ROM-specific

### Virtual env warning
- `VIRTUAL_ENV` pointing to old pokelive path causes warning in new terminal
- **Fix**: `bridge/run.sh` does `unset VIRTUAL_ENV` before `uv run fastapi dev`

## Key External References

| Resource | URL | Notes |
|---|---|---|
| mGBA development builds | https://mgba.io/builds/ | **Use dev build** — stable may lack socket API |
| FireRed base ROM | https://www.romsgames.net/gameboy-advance-rom-pokemon---fire-red-version-a1/ | v1.0 USA needed as base |
| pret/pokefirered decompilation | https://github.com/pret/pokefirered | Base repo — apply `patches/` on top |
| devkitPro (GBA toolchain) | https://devkitpro.org | ARM cross-compiler for building the ROM |
| devkitPro Getting Started | https://devkitpro.org/wiki/Getting_Started | Install guide |
| devkitPro Windows installer | https://github.com/devkitPro/installer/releases | Download `devkitProUpdater-X.X.X.exe` |
| agbcc (GBA C compiler) | https://github.com/pret/agbcc | pokefirered-specific patched GCC; must be installed into the pokefirered tree |

## Build Commands

```bash
# One-time: install devkitPro GBA toolchain (macOS/Linux)
# See https://devkitpro.org/wiki/Getting_Started for full guide
curl -sSL https://apt.devkitpro.org/install-devkitpro-pacman | sudo bash
sudo dkp-pacman -Sy --noconfirm gba-dev

# One-time: build + install agbcc into the pokefirered tree
cd /tmp && git clone --depth=1 https://github.com/pret/agbcc
cd agbcc && ./build.sh && ./install.sh /Users/shaunliew/Documents/poke-ai/pokefirered

# Every build — run from pokefirered directory
cd /Users/shaunliew/Documents/poke-ai/pokefirered
DEVKITPRO=/opt/devkitpro \
DEVKITARM=/opt/devkitpro/devkitARM \
PATH="/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH" \
make -j$(sysctl -n hw.logicalcpu)
```

## Run the Demo

```bash
# Terminal 1: Start bridge
cd /Users/shaunliew/Documents/poke-ai/bridge
./run.sh
# → runs on http://localhost:8000

# mGBA (development build — https://mgba.io/builds/):
# 1. File → Load ROM → pokefirered/pokefirered.gba  (patched ROM)
# 2. File → Load Game → fire-red.sav  (battery save, NOT .ss0)
# 3. Tools → Scripting → emulator/lua/codex_mailbox_bridge.lua
# 4. Walk to Prof Oak's Lab → talk to the scientist (Prof GPT 5.5)
# 5. Select ADVICE or ASK — game will loop-wait; response appears in textbox
```

## Demo Script (Hackathon Judges)

1. **Professor GPT 5.5**: Walk into Oak's Lab → talk to the scientist NPC → select ADVICE → wait (game loops silently) → GPT response appears in textbox
2. **ASK**: Select ASK → type question in naming screen → press OK → same wait → answer appears

## Active Branch

| Branch | Purpose | Status |
|---|---|---|
| `feat/006-demo-polish` | **Current** — hackathon demo cleanup | 🔲 In progress |
| `feat/003-party-context` | Professor GPT party-aware advice (Sprint-003) | ✅ Done, merged to dev |
| `origin/dev` | Integration branch — all features merge here | — |
| `main` | Production — never push directly | — |

**To continue on demo polish:** you are already on `feat/006-demo-polish`.

**To start a new sprint after the hackathon:**
```bash
git fetch origin
git checkout origin/dev -b feat/NNN-your-feature
```

## Implementation Plan Status

| Phase | Description | Status |
|---|---|---|
| 0 | Compile patched ROM, get mailbox address | ✅ Done — ROM built, address `0x0203F4AC` |
| 1 | End-to-end Codex NPC: game → Lua → bridge → GPT → textbox | ✅ Done (response works, no crash) |
| 2 | ASK fix + party-aware ADVICE + PokéAPI name lookups | ✅ Done — code committed, tests pass |
| 2a | **Rebuild ROM** — recompile after C/script changes | ✅ Done — rebuilt May 7 23:49 |
| 2b | **Verify EWRAM addresses** — re-grep `.map`, update Lua lines 8–9 if shifted | ✅ Done — addresses unchanged (`0x0203F4AC`, `0x0203F5DC`) |
| 2c | **E2E test** — ADVICE with real party, ASK with typed input | ✅ Done — validated May 8, party data confirmed working |
| 3 | **AI Rival** — proactive encounters, Lua triggers, Pallet Town textbox cutscene | ✅ Done (Sprint-005, merged to dev May 8) |
| 3a | **Demo polish** — remove debug logging, stress test, demo script | 🔲 In progress (Sprint-006, `feat/006-demo-polish`) |
| 4 | Custom Pokémon generator (stretch goal) | 🔲 Pending (Sprint-004) |

## Coding Style

- Python: PEP 8, type hints, Pydantic models; `uv` for package management
- Lua: mGBA Lua 5.4 — `emu:read32`/`emu:write32` for memory, `socket` for HTTP
- C patches: match pret/pokefirered style — 4-space indent, GBA types (u8/u16/u32)
- Bridge response constraint: 1 sentence ≤ 45 chars, ASCII letters+numbers+spaces only

## Rules

- Never commit ROMs, save files, or .env files
- The patched ROM goes in `poke-ai/pokefirered/` — never overwrite `pokelive/fire-red.gba`
- All OpenAI calls go through the bridge — never directly from Lua
- Response encoding must be flat (no 0xFB/0xFE) — use `chars_per_line=200, lines_per_page=1`
