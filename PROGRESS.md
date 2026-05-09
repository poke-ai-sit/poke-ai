# PokéLive — Team Progress Tracker

**Hackathon:** AI Engineer Hackathon, Singapore
**Demo Date:** May 9, 2026
**Team Size:** 3 members

---

## Team Assignments

| Member | Role | Primary Focus |
|--------|------|---------------|
| Member 1 | ROM / C | `codex_npc.c`, `battle_ai_script_commands.c`, `scripts.inc`, ROM builds |
| Member 2 | Python / AI | FastAPI bridge, OpenAI prompts, `/rival-plan`, `/rival-result` endpoints |
| Member 3 | Lua / QA | `codex_mailbox_bridge.lua`, E2E testing, demo dry-run |

> Update names above once assigned.

---

## Feature Status

| Feature | Status | Owner | Blocker |
|---------|--------|-------|---------|
| Feature 1: Prof GPT 5.5 (ADVICE) | 🟡 90% | — | E2E test pending |
| Feature 1: Prof GPT 5.5 (ASK) | 🟡 90% | — | E2E test pending |
| Feature 2: AI Rival (pre-battle dialogue) | 🔴 0% | Member 1+2+3 | Not started |
| Feature 2: AI Rival (counter pick) | 🔴 0% | Member 1+2 | Not started |
| Feature 2: AI Rival (move scoring) | 🔴 0% | Member 1+2 | Not started |
| Feature 2: AI Rival (battle history) | 🔴 0% | Member 2 | Not started |
| Feature 3: Custom Pokémon generator | ⚫ 0% | — | Deprioritised (stretch) |

---

## Pending Tasks — Priority Order

### 🔴 P0 — Must complete before demo

#### Feature 1 (Member 3)
- [ ] **E2E ADVICE test** — Load rebuilt ROM + `fire-red.sav`, pick starter, open bridge, walk to Prof GPT 5.5 → ADVICE. Confirm party data appears in bridge stdout and GPT names the Pokémon.
- [ ] **E2E ASK test** — Select ASK → type question → verify GPT answers the specific question.
- [ ] **Response length check** — If GPT exceeds 45 chars, tighten system prompt in `prompts.py`.

#### Feature 2 ROM (Member 1)
- [ ] Add `gRivalAIBuffer` struct (8 bytes) to `codex_npc.c`
  ```c
  EWRAM_DATA struct PokeliveRivalAIBuffer gRivalAIBuffer = {0};
  ```
- [ ] Implement `PublishRivalPlanPrompt()` — calls `UpdateCodexPartyData()`, sets mailbox PENDING with RIVAL_PLAN command
- [ ] Implement `GetRivalCounterChoice()` — reads `gRivalAIBuffer.counterChoice` → `gSpecialVar_Result`
- [ ] Implement `MarkRivalBattleResult()` — writes `gSpecialVar_Result` to `gRivalAIBuffer.resultPending`
- [ ] Register 3 new specials in `data/specials.inc`
- [ ] Edit `battle_ai_script_commands.c` — add 8-line hook after AI scripts loop (see CLAUDE.md)
- [ ] Edit `scripts.inc` — insert RIVAL_PLAN wait loop before `trainerbattle_earlyrival` for all 3 rival paths
- [ ] Add "IS THINKING" text string for rival wait box
- [ ] **Rebuild ROM** — `make -j$(sysctl -n hw.logicalcpu)` from `pokefirered/`
- [ ] **Verify `gRivalAIBuffer` address** — grep `.map`, add to Lua constants

#### Feature 2 Bridge (Member 2)
- [ ] Add `RivalPlanResult` Pydantic model (message, message_hex, move_scores[4], counter_choice)
- [ ] Add `RivalResultRequest` Pydantic model
- [ ] Implement `build_rival_plan_prompt()` in `prompts.py` — party + history context, JSON output instructions
- [ ] Implement `ask_rival()` in `openai_client.py` — JSON mode, clamped move_scores to [-20,+20]
- [ ] Add `POST /rival-plan` endpoint in `main.py`
- [ ] Add `POST /rival-result` endpoint in `main.py` — in-process history list
- [ ] Test `/rival-plan` with mock party data — verify JSON structure, move_scores in range

#### Feature 2 Lua (Member 3)
- [ ] Add `RIVAL_AI_BUFFER_ADDR` constant (value from `.map` after rebuild)
- [ ] Detect `RIVAL_PLAN` request_kind in `json_codex_chat()` — route to `/rival-plan` instead of `/codex-chat`
- [ ] Parse `move_scores[4]` from response → `emu:write8` to `gRivalAIBuffer`
- [ ] Parse `counter_choice` from response → `emu:write8` to `gRivalAIBuffer.counterChoice`
- [ ] Write `gRivalAIBuffer.active = 1` LAST (after scores written)
- [ ] Poll `gRivalAIBuffer.resultPending` each frame → POST `/rival-result` → clear byte

### 🟡 P1 — Nice to have (if time allows)

- [ ] Rival second encounter after catching 2nd Pokémon
- [ ] Pass battle history to `/rival-plan` prompt (multi-battle memory)
- [ ] Pre-warm PokéAPI Gen1 cache at bridge startup
- [ ] Tune ADVICE response length with real party

### ⚫ P2 — Stretch (after demo)

- [ ] Custom Pokémon generator (inject custom species into party slot)

---

## Completed Work

| Date | What | Who |
|------|------|-----|
| May 7 | ASK fix + party-aware ADVICE + PokéAPI lookups + tests | — |
| May 7 | ROM rebuilt (23:49), EWRAM addresses verified unchanged | — |
| May 7 | Merge pokefirered/ into poke-ai monorepo | — |
| May 8 | AI Rival plan written to PLAN.md + CLAUDE.md | — |

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| EWRAM linker fail after adding 8 bytes | Low | High | Only 8 bytes added; 580 remaining |
| `s8 move_scores` overflow (100+boost>127) | Medium | Medium | Bridge clamps scores to [-20,+20] |
| AI Rival not complete in time | High | Medium | Feature 1 alone is demoable; Rival is bonus |
| GPT JSON mode returns malformed response | Medium | Medium | Pydantic validation + fallback defaults |
| ROM rebuild fails (compiler error) | Low | High | Test compile immediately after each C change |
| Bridge / network down during demo | Low | High | Pre-cache one ADVICE response; restart bridge |
| Demo save state incompatible with rebuilt ROM | Low | Medium | Use `.sav` battery save, never `.ss0` |

---

## Demo Script (for judges)

**Setup (before demo starts):**
1. Start bridge: `cd bridge && ./run.sh`
2. Load mGBA dev build → ROM: `pokefirered/pokefirered.gba` → Save: `fire-red.sav`
3. Load Lua: `Tools → Scripting → emulator/lua/codex_mailbox_bridge.lua`

**Demo flow:**
1. Walk to Oak's Lab → talk to Prof GPT 5.5 (scientist at left side)
2. Select **ADVICE** → wait ~3-5s → GPT response names your starter → show judges
3. Select **ASK** → type "what type beats Brock?" → wait → answer appears → show judges
4. *(If AI Rival complete)* Select starter → rival enters → "RIVAL IS THINKING" box → rival taunts you by name → battle with AI-chosen counter

**Fallback if something breaks:**
- Bridge down: restart `./run.sh`, retry
- Mailbox stuck: reload Lua script in mGBA
- ROM crash: reload game from `.sav` (not `.ss0`)
- Rival feature broken: demo Feature 1 only (still fully demoable)

---

## Stand-up Notes

> Use this section for daily updates. Add a new entry each session.

### May 8, 2026
- AI Rival plan finalized, written to PLAN.md + CLAUDE.md + PROGRESS.md
- ROM rebuilt and addresses verified (from May 7)
- Feature 1 E2E test pending
- Feature 2 implementation not yet started

---

## Architecture Quick Reference

```
poke-ai/
  pokefirered/pokefirered.gba   ← patched ROM (rebuild after every C/script change)
  pokefirered/pokefirered.map   ← grep for EWRAM addresses after each rebuild
  pokefirered/src/codex_npc.c   ← mailbox specials + gRivalAIBuffer
  bridge/src/pokelive_bridge/
    main.py                     ← /codex-chat, /rival-plan, /rival-result
    prompts.py                  ← system prompts (advice, ask, rival)
    openai_client.py            ← ask_codex(), ask_rival()
  emulator/lua/codex_mailbox_bridge.lua  ← mGBA Lua bridge
```
