# PokéLive — Sprint Tracker

## Team

| Name | Focus Area |
|---|---|
| Shaun Liew Xin Hong | Professor GPT — AI Advice NPC |
| Desmond Chye Zhi Hao | Personalization — AI Pokémon Creator |
| Edmund Lin Zhenming | AI NPC — Autonomous, Memory-Driven NPCs |

---

## Sprint Format

```
### SPRINT-NNN — Sprint Title
**Owner:** Name
**Status:** [ ] Not Started | [~] In Progress | [x] Done | [!] Blocked
**Branch:** feat/NNN-short-description
**Started:** YYYY-MM-DD
**Closed:** YYYY-MM-DD

#### Goal
One sentence on what done looks like.

#### Tasks
- [ ] task one
- [ ] task two

#### Notes
Any blockers, decisions, or gotchas worth recording.
```

---

## Sprints

### SPRINT-001 — Repo Setup & ROM Compilation
**Owner:** All
**Status:** [x] Done
**Branch:** main
**Started:** —
**Closed:** 2026-05-07

#### Goal
Monorepo in place, patched ROM builds cleanly, bridge runs, Lua script loads in mGBA.

#### Tasks
- [x] Merge pokefirered decompilation source into monorepo
- [x] Apply 3 git-format patches to pokefirered
- [x] Compile pokefirered.gba with devkitPro + agbcc
- [x] FastAPI bridge runs via `bridge/run.sh`
- [x] Lua script loads in mGBA dev build
- [x] Confirm mailbox address `0x0203F48C`

---

### SPRINT-002 — End-to-End Codex NPC (ADVICE + ASK)
**Owner:** All
**Status:** [x] Done
**Branch:** main
**Started:** —
**Closed:** 2026-05-07

#### Goal
Player can talk to Prof GPT 5.5, select ADVICE or ASK, and see a GPT response in the in-game textbox with no crash.

#### Tasks
- [x] `src/codex_npc.c` — mailbox struct + special functions
- [x] `data/specials.inc` — register specials in gSpecials table
- [x] NPC script in Oak's Lab (`scripts.inc` ~line 950)
- [x] NPC placement in `map.json` (scientist at x=2, y=3)
- [x] ASK uses naming screen with title "ASK GPT5.5"
- [x] Bridge `/codex-chat` returns ≤45-char flat-encoded response
- [x] Infinite wait loop (no game-side timeout race)
- [x] Lua wall-clock 90s timeout writes "Try again."
- [x] Fix `0xFB` page-break crash (`chars_per_line=200, lines_per_page=1`)
- [x] Fix lazy OpenAI client init
- [x] Fix `.env` path for FastAPI reloader CWD issue

---

## Hackathon Day Sprints — May 9, 2026

> These run in parallel. Each person owns their track. Coordinate on shared files (Lua bridge, main.py) before touching them.

---

### SPRINT-003 — Professor GPT: Party-Aware & Gym-Context Advice
**Owner:** Shaun Liew Xin Hong
**Status:** [x] Done
**Branch:** feat/003-party-context
**Started:** 2026-05-07
**Closed:** 2026-05-08

#### Goal
ADVICE prompt includes the player's live party and next-gym context so GPT gives specific, actionable advice (e.g. "Train RATTATA on Route 2 for Brock").

#### Tasks — Party Data Pipeline
- [x] Lua: read party data from `gPokelivePartyData` (EWRAM `0x0203F5BC`), populated by `UpdateCodexPartyData()`
- [x] Fix Lua `PARTY_ENTRY_SIZE` stride bug: `24` → `28` (struct is 14 × u16, not 12)
- [x] Fix `sp_attack` / `sp_defense` hardcoded to 0 — now reads `PE_SPATTACK=24`, `PE_SPDEFENSE=26`
- [x] Include party JSON in `/codex-chat` POST body
- [x] `main.py`: `PartyEntryRequest` Pydantic model; `CodexChatRequest` accepts optional `party` list
- [x] `main.py`: add `logger.debug` line logging `party_count` and `request_kind` per request

#### Tasks — Prompt Engineering (Party Focus)
- [x] `prompts.py`: `_party_block()` — sorts party ascending by level, marks weakest with `FOCUS:` prefix
- [x] `prompts.py`: promote `advice_hint` to module-level `ADVICE_HINT` constant (testable, swappable)
- [x] `prompts.py`: `build_codex_system_prompt_advice()` wraps party in `<party>` XML block
- [x] `test_prompts.py`: 4 regression tests — FOCUS placement, ascending order, single-member, hint content

#### Tasks — Gym Context Block
- [x] New `bridge/src/pokelive_bridge/gym_data.py`:
  - `GymInfo` frozen dataclass (index, name, leader, types, weak_to, recommended_level, training_routes)
  - `GYM_SEQUENCE` — first 4 Kanto gyms (Brock → Erika) with full metadata
  - `PROGRESS_MAP` — 30 `(map_group, map_num)` entries from `pokefirered/include/constants/map_groups.h`
  - `MOVE_TYPES` — 55 early-game move IDs → type strings (including Fighting moves: Karate Chop, Low Kick, etc.)
  - `SUPER_EFFECTIVE` — Gen III 17-type chart as `dict[str, frozenset[str]]` (defender → super-effective attackers)
  - `move_type(move_id)` → `str | None` (returns `None` for unknown IDs — never falsely contributes to coverage)
  - `is_super_effective(atk_type, defender_types)` → `bool`
  - `gym_for_location(map_group, map_num)` → `GymInfo` (coordinate lookup, defaults to Brock for unknowns)
- [x] `prompts.py`: `_gym_context_block()` — builds `<gym>` block with gym info, coverage status, level warning
- [x] `prompts.py`: `build_codex_system_prompt_advice()` includes `<gym>` block between `<game_state>` and `<party>`
- [x] `ADVICE_HINT` updated to reference FOCUS, coverage MISSING, and level warning signals
- [x] `test_gym_data.py` (new): 28 tests covering gym lookup, move_type, is_super_effective
- [x] `test_prompts.py`: 11 new gym context tests (block presence, coverage OK/MISSING, level warning, all 4 gym leaders)
- [x] 78/78 tests pass
- [x] E2E validated in-game: caught second Pokémon, ADVICE response correctly references the lower-level party member

#### Tasks — ROM Additions
- [x] `script_menu.c`: added `BALLS` as 5th multichoice option in Prof GPT 5.5 menu
- [x] `scripts.inc`: `ProfessorCodexBalls` handler uses `giveitem_msg ITEM_POKE_BALL 5` — gives 5 Poké Balls
- [x] ROM rebuilt after menu changes

#### Tasks — E2E Bug Fixes (May 8 continued)
- [x] Fix root cause: `PublishCodexAdvicePrompt()` never called `UpdateCodexPartyData()` — party magic stayed 0x00000000, Lua returned nil, no party JSON sent; GPT gave generic advice
- [x] Lua: add `[DEBUG]` log for POST body and party read result so party data is visible in mGBA console
- [x] Bridge: add `logging.info("SYSTEM PROMPT:")` in `openai_client.py` so full prompt is visible in bridge terminal
- [x] Investigated `0xFE` (NEWLINE) in `{STR_VAR_1}` substitution — confirmed unsafe (crash `D5E8D5E8`); reverted to flat encoding `chars_per_line=200, lines_per_page=1`
- [x] `gym_data.py`: add `SPECIES_NAMES` — offline Gen 1 species table (151 entries, national dex IDs matching FireRed constants)
- [x] `gym_data.py`: add `MOVE_NAMES` — offline move name table (~160 entries, covers all Gen 1 moves)
- [x] `pokemon_data.py`: offline-first lookup — checks `SPECIES_NAMES`/`MOVE_NAMES` before PokéAPI; custom Pokémon fall back to `CUSTOM#<id>` (ready for Sprint-004 injection)
- [x] `string_util.c`: expand `gStringVar1` from 32 → 64 bytes; prevents silent EWRAM overflow on 33-64 char responses
- [x] Update Lua EWRAM addresses after `gStringVar1` expansion: `gPokeliveCodexMailbox` `0x0203F48C` → `0x0203F4AC`, `gPokelivePartyData` `0x0203F5BC` → `0x0203F5DC`
- [x] `prompts.py`: split `_BASE_PERSONA` into `_BASE_PERSONA_ADVICE` (40 chars, terse) and `_BASE_PERSONA_ASK` (60 chars, conversational)
- [x] `ADVICE_HINT`: instruct GPT to always name the specific party member, give exact move and level target
- [x] ROM rebuilt twice (party data fix + `gStringVar1` expansion); 91/91 tests pass

#### Notes
- `PARTY_ENTRY_SIZE = 28` — the C struct `PokelivePartyEntry` has 14 × u16 fields. Using 24 caused misaligned reads for party slots 2–6. Fixed in `codex_mailbox_bridge.lua`.
- Gym context is **coordinate-based, not badge-based** — clearly labelled "estimated from location" in the prompt. Acceptable for demo purposes.
- Offline species/move tables in `gym_data.py`; PokéAPI is fallback only. Custom Pokémon (Sprint-004) use `CUSTOM#<id>` until a name is registered.
- `0xFE` (NEWLINE) is **also unsafe** inside `{STR_VAR_1}` substitution — corrupts the text renderer state machine and causes invalid-address jumps. Both `0xFE` and `0xFB` are forbidden. Flat encoding only.
- EWRAM addresses shift whenever any `EWRAM_DATA` symbol before them in the link order grows. Always re-grep `pokefirered.map` after any size change and update Lua lines 8–9.
- `gStringVar1` is now 64 bytes (was 32). EWRAM usage: 261588/262144 (99.79%). No headroom for further expansion.
- ADVICE: 40-char limit, names specific party member + move. ASK: 60-char limit, conversational.
- Codex plan reviews: 8.5/10 (party FOCUS fix), 7.5/10 (gym context). Code reviews: 8.0/10, 7.5/10.

---

### SPRINT-004 — Pokémon Sprite Generator Website (PokéLive Creator)
**Owner:** Shaun Liew Xin Hong
**Status:** [x] Done
**Branch:** feat/004-pokemon-creator (merged to dev, deleted 2026-05-09)
**Started:** 2026-05-09
**Closed:** 2026-05-09

#### Goal
Standalone Next.js 14 website where users describe a custom Pokémon concept, click Generate, and get a GBA-style pixel art sprite (front + back) and a 40×40 party icon — all powered by OpenAI `gpt-image-2`.

#### Tasks
- [x] Scaffold `website/` with Next.js 14 App Router + TypeScript + TailwindCSS
- [x] Press Start 2P font + authentic FireRed colour system (red-dominant palette)
- [x] `lib/openai-image.ts` — `generateSprite()` and `editSpriteWithReference()` (lazy OpenAI client)
- [x] `lib/prompts.ts` — `SYSTEM_SPRITE_PROMPT` + `buildFinalPrompt()`
- [x] `lib/icon-extract.ts` — `sharp` nearest-neighbor crop to 40×40 party icon
- [x] `lib/validation.ts` — Zod schemas for request/response
- [x] `app/api/generate-sprite/route.ts` — POST handler, `runtime="nodejs"`, `maxDuration=120`
- [x] `components/HomeClient.tsx` — `useReducer` state machine (idle → loading → success/error)
- [x] `components/SpriteGeneratorForm.tsx` — textarea, quick-example chips (Rusty Car, Ferrari, Smooth Criminal), ImageUpload
- [x] `components/SpritePreview.tsx` + `components/IconPreview.tsx` — pixelated upscale + download
- [x] `components/LoadingDialog.tsx` + `components/ErrorDialog.tsx` — HP-bar loading animation, red error panel
- [x] `components/ImageUpload.tsx` — drag-drop + file picker + client-side canvas resize
- [x] Fix `quality: "high"` → `quality: "low"` (high=90s+ timeout, low=16-32s) — root cause of generation timeout
- [x] `npm run build` passes with zero TypeScript errors
- [x] E2E smoke test: Rusty Car prompt → sprite returned in ~23s

#### Notes
- `quality: "low"` is correct for GBA pixel art — no perceptible quality loss at 64×64 sprite resolution.
- `gpt-image-2` does NOT accept `response_format` parameter (returns 400); `b64_json` is the default response — do not pass it explicitly.
- API key is the same `OPENAI_API_KEY` used by the FastAPI bridge — copy from `bridge/.env` into `website/.env.local`.
- Dev server runs on `PORT=3001` to avoid conflict with bridge on `8000`; or just use `3000` if bridge is off.
- `<img>` is used (not Next.js `<Image>`) intentionally — `image-rendering: pixelated` on base64 data URLs requires native `<img>`.

#### Run the Website
```bash
cd website
cp .env.example .env.local   # then fill in OPENAI_API_KEY
npm install
npm run dev                  # → http://localhost:3000 (or PORT=3001 if bridge is running)
npm run build                # production build check
```

---

### SPRINT-004b — In-Game Sprite & Icon Injection (PokéLive ROM)
**Owner:** Desmond Chye Zhi Hao
**Status:** [~] In Progress — icon bug fixes applied, pending in-game verify
**Branch:** feat/004-AI-Pokémon-Creator
**Started:** 2026-05-09
**Closed:** —

#### Goal
Replace Charmander → Prata, Charmeleon → Prata Pro, Squirtle → Frankson inside the ROM: front sprite, back sprite, and Pokédex icon all show the custom pixel art.

#### Custom Pokémon Mapping

| Original | Custom Name | Asset source |
|---|---|---|
| Charmander | Prata | `sprite_gen/assets/prata_generated.png` (front/back), `prata_icon.png` (icon) |
| Charmeleon | Prata Pro | `sprite_gen/assets/prata_pro_generated.png`, `prata_pro_icon.png` |
| Squirtle | Frankson | `sprite_gen/assets/frankson_generated.png`, `frankson_icon.png` |

#### Tasks — Front/Back Sprites
- [x] `sprite_gen/process.py` — `process_sprite()`: crop → resize 64×64 → joint 16-color quantize → save indexed PNG + JASC-PAL
- [x] `sprite_gen/main.py` — CLI: `python main.py <source> <pokemon_name>`
- [x] Front + back sprites generated and copied to `pokefirered/graphics/pokemon/{charmander,charmeleon,squirtle}/`

#### Tasks — Icon Pipeline
- [x] `process_icon()` in `process.py`: resize → magenta sentinel → quantize 16 colors → stack 2 frames → 32×64
- [x] `--icon --icon-pal-slot N` flags in `main.py`
- [x] Icons generated; per-Pokémon palette slots assigned (Charmander=0, Charmeleon=1, Squirtle=2) in `pokemon_icon.c`
- [x] Fix: transparency sentinel switched white→magenta so car windows don't become transparent holes
- [x] Fix: `_snap_sentinel()` collapses LANCZOS edge blends; `_apply_palette()` clamps indices to 0–15
- [x] ROM rebuilt: `pokefirered_modern.gba` (MODERN=1, arm-none-eabi-gcc 15.2.0, EWRAM 259950/262144)
- [x] Lua EWRAM addresses updated for MODERN build (all 4 symbols)
- [ ] **Verify in-game** — load `pokefirered_modern.gba`; confirm icon + sprite render correctly

#### Notes
- ROM is `pokefirered_modern.gba` (MODERN=1 build). All Lua EWRAM addresses target this build.
- Magenta `#FF00FF` is the GBA transparency sentinel at palette index 0 — do not use white.
- Each of the 3 custom Pokémon has its own icon palette slot so colors don't bleed across species.

---

### SPRINT-005 — AI Rival: Autonomous Behaviour, Memory & Smart Gary
**Owner:** Edmund Lin Zhenming
**Status:** [~] In Progress — Phases 1–3 done, Phase 4 (Smart Gary) Hours 2–3 done
**Branch:** dev (merged & deleted: feat/005a–005f)
**Started:** 2026-05-08
**Closed:** —

#### Goal
The rival reasons about game state, remembers past player encounters, walks toward the player unprompted, and adapts its battle moves over a sequence of staged fights. Memory persists across battles in `agents/rival/memory.md`.

#### Phase 1 — Bridge (event-driven, .md memory) ✅
- [x] `agents/rival/persona.md` — hand-authored Gary personality
- [x] `agents/rival/memory.md` — template + log header (auto-appended by bridge)
- [x] `bridge/src/pokelive_bridge/rival_agent.py` — read persona+memory, call GPT, append memory
- [x] `POST /rival-event` — trigger + game_state + party + details → message_hex + action

#### Phase 2 — Lua trigger detection ✅
- [x] Party-size delta (catch detection) via `SaveBlock1+0x34`
- [x] Map-ID delta (entered new area), in-scope maps only
- [x] Wall-clock cooldown (≥60s between rival reactions)
- [x] On trigger: POST `/rival-event`, log response, respect single-pending guard

#### Phase 3 — ROM cinematic walk-up ✅
- [x] `gRivalEncounterBuffer` EWRAM struct (status + 200-byte message)
- [x] Encounter script (lockall → showobject → applymovement → msgbox → hideobject → releaseall)
- [x] Pallet Town frame script + hidden rival object — pattern proven, can be cloned to Route 1 / Viridian / Pewter
- [x] Lua writes message_hex to `gRivalEncounterBuffer` and sets `VAR_TEMP_0=1` to fire the frame script

#### Phase 4 — Smart Gary (battle-aware AI rival)

**Bridge — done**
- [x] `POST /rival-battle-plan` — pre-battle JSON-mode GPT call → `counter_choice` + `move_scores[4]` + `opening_taunt` + `strategy_summary`; appends PLAN entry to memory.md
- [x] `POST /rival-taunt` — per-turn one-liner ≤45 chars, fire-and-forget
- [x] `POST /rival-battle-summary` — post-battle GPT call → `summary` + `lessons`; appends RESULT entry with full chess move log
- [x] `battle_agent.py` shares persona + memory with `rival_agent.py`

**ROM — done (Hour 3)**
- [x] `pokefirered/include/pokelive_rival_ai.h` — shared header for struct + magic
- [x] `gRivalAIBuffer` (8 bytes EWRAM at `0x0203F75C`)
- [x] AI hook in `BattleAI_ChooseMoveOrAction` (defensive ±20 clamp on `score[i] += moveScore[i]`, then clears `active`)
- [x] EWRAM after rebuild: 261808 / 262144 bytes (99.87%) — fits

**Lua — done (Hours 2 + 3)**
- [x] `BATTLE_POLLING_ENABLED = true`, `check_battle_transitions()` wired into the frame callback
- [x] Battle log accumulator + map-signature → battle_id lookup (`4:3`, `3:19`, `3:2`)
- [x] `extract_json_int_array` / `extract_json_int` helpers
- [x] `write_rival_ai_plan(move_scores, counter_choice)` — writes magic + scores + counter, then arms `active=1` LAST
- [x] `poll_pending_response` handles `rival-battle-plan` and `rival-battle-summary` labels
- [x] **Validated in mGBA:** addresses correct (Charmander/Scratch, Squirtle/Tackle read out of `gBattleMons` / `gCurrentMove`); Battle 1 in Oak's Lab logged 6 turns and produced a RESULT entry in `agents/rival/memory.md`

**What's next**
- [x] **Hour 4 — fire `/rival-battle-plan` at battle entry.** `check_battle_transitions()` now POSTs on the first observed `outcome == 0` bootstrap frame: full player party from `gPokelivePartyData` + active rival slots 1/3 from `gBattleMons`. Single-pending guard at the top of the function prevents double-fire. Lua-side mGBA validation pending (no graphical test environment available here).
- [x] **Hour 4 — display `opening_taunt`.** Routed to script panel only (Option B). The existing `gRivalEncounterBuffer` cinematic relies on a map_script_2 frame handler on the overworld, which does not fire mid-battle, so Option A wasn't viable for v1. Strategy summary also printed for narration.
- [x] **Hour 4b — fix Battle 1 silent skip.** First in-session battle (Oak's Lab `4:3`) was missing its `/rival-battle-plan` POST while Battle 2 (Route 1 `3:19`) worked. Two root causes in `check_battle_transitions()`: (a) the function early-returned on any in-flight `pending` HTTP request — a `/game-state` POST queued by the player's last walking step into the lab routinely landed in that window; (b) bootstrap fired on `outcome == 0` alone, which is also the value on the overworld, so the watcher was racing the actual battle-start frame. Fix: drop the `pending` early-return, gate bootstrap on `gBattleMons[1].species != 0` (rival lead loaded — only true mid-battle), and queue the plan POST into `deferred_battle_plan` if `pending` is busy at battle-start, retrying every frame until it lands. Also throttled `/game-state` chatter from per-step (every x/y change) to per-map-change with a 2s wall-clock floor — the bridge no longer gets spammed once per walking step.
- [~] **Hour 5 — Battle 2 (ROM side).** Added 6 new trainers (`TRAINER_AI_RIVAL_B2_ANTI_FIRE` … `TRAINER_AI_RIVAL_B2_BALANCED`) at level 7-9 with type-counter parties. Added shared cinematic primitive `EventScript_AIRivalEncounterCinematic` + dispatch ladder `EventScript_AIRivalDispatchTrainerBattle` (12-way `switch`/`case` on `gRivalAIBuffer.counterChoice` via new special `GetAIRivalCounterChoice`). Wired Route 1 + Route 2 `OnFrame` triggers on `VAR_TEMP_0 == 1`; rival NPC warps in adjacent (player x+2), single step + `SE_WARP_IN`, msgbox the GPT taunt, `trainerbattle_no_intro`, hide. Map.json adds hidden rival object event guarded by `FLAG_HIDE_ROUTE{1,2}_AI_RIVAL`. Viridian Forest punted (pathfinding edge-cases noted in Phase 3).
- [~] **Hour 6 — Battle 3 (ROM side).** Added 6 new trainers (`TRAINER_AI_RIVAL_B3_ANTI_FIRE` … `TRAINER_AI_RIVAL_B3_BALANCED`) at level 11-13 with 3-4 mon counter parties. Wired `MAP_PEWTER_CITY_GYM` `OnFrame` trigger on `VAR_TEMP_0 == 1`; rival warps in 2 tiles below player and walks up 1 tile (gym is narrow, vertical motion is safe). Brock untouched. Map.json adds hidden rival guarded by `FLAG_HIDE_PEWTER_GYM_AI_RIVAL`. New flags: `FLAG_HIDE_ROUTE1_AI_RIVAL=0x4A8`, `FLAG_HIDE_ROUTE2_AI_RIVAL=0x4A9`, `FLAG_HIDE_PEWTER_GYM_AI_RIVAL=0x4AA`. New LOCALIDs: `LOCALID_ROUTE1_AI_RIVAL=3`, `LOCALID_ROUTE2_AI_RIVAL=8`, `LOCALID_PEWTER_GYM_AI_RIVAL=4`. ROM rebuild + EWRAM verification still pending (sandbox blocks `make` from this agent).
- [ ] **Hour 7 — demo dry-run.** Full playthrough start → Battle 3, with `agents/rival/memory.md` tail visible to judges.

**Move-log dedup polish (low priority)**
- The watcher dedupes `current_move == last_logged_*`, suppressing *consecutive* same-move turns by the same battler. Functional for now; refine if it bites.

#### Notes
- Memory format is `.md`, not JSON — human-readable, git-trackable, GPT reads it natively.
- `persona.md` static (authored), `memory.md` dynamic (bridge appends).
- `0xFE` (NEWLINE) and `0xFB` (PAGE_BREAK) both unsafe inside `{STR_VAR_1}` — flat encoding only (`chars_per_line=200, lines_per_page=1`).
- `gRivalAIBuffer` layout matches `pokefirered/include/pokelive_rival_ai.h` — Lua offsets (`+4 active`, `+5..8 moveScore`, `+9 counterChoice`) must stay in sync with the C struct.
- Viridian Forest pathfinding remains the weak spot if we extend the cinematic — fallback to adjacent spawn rather than long walk through trees.

---

### SPRINT-006 — Hackathon Demo Polish
**Owner:** All
**Status:** [x] Closed — folded into Sprint-005 Hour 7 dry-run
**Branch:** —
**Closed:** 2026-05-09

Polish work (debug-log removal, single-feature stress test, demo script) is now part of the Sprint-005 Hour 7 dry-run since only the AI Rival track is shipping. The completed item — removing `[DEBUG]` Lua lines, raw HTTP response dumps, and the bridge SYSTEM PROMPT info log — has already shipped.

---

## Backlog (Unscheduled)

- EVOLVE multichoice option (currently placeholder in NPC script)
- Two AI NPCs battle each other; player can walk up and spectate
- Deeper battle memory — Gary tracks per-move success rates across many fights
- Frontend overlay on mGBA stream showing AI reasoning in real time
