# PokéLive — Project Context

## The Big Idea

Games have always been limited by hardcoded logic. Every NPC says the same thing on loop. Every opponent follows the same script. The world doesn't react to you — it just plays out its routine.

We want to change that, starting with Pokémon.

**PokéLive uses AI to make a classic game feel genuinely alive.** Not an overlay, not a chatbot bolted on — real in-game behaviour driven by real intelligence, running inside the game engine itself.

Target event: **AI Engineer Hackathon, Singapore — May 9, 2026. 7 hours.**

---

## Two Directions

### 1. AI for Advice — Professor GPT

An AI-powered NPC (Professor GPT 5.5) who actually knows your situation. He reads your current party, considers your past encounters, and gives you real, contextual advice — not a wiki page.

- Talk to him in Oak's Lab → select **ADVICE** → he analyses your team and tells you what to do
- Select **ASK** → type any question via the in-game naming screen → he answers it live
- The response appears in an authentic FireRed textbox. No overlay. No break in immersion.

The wow moment: the professor says something specific to *your* team, *your* situation, right now.

---

### 2. AI NPCs — Living, Thinking Creatures *(Most Interesting)*

This is the big one. Instead of NPCs that follow hardcoded patrol routes and say the same line on repeat, AI NPCs have:

- **Thought process** — they reason about what to do next, not just execute a script
- **Memory** — they remember past encounters with the player and adapt
- **Autonomous behaviour** — they can walk up to you, challenge you, or ignore you based on their own state — not because a trigger condition fired
- **Battle intelligence** — they learn from losing; they get better at beating you over time
- **Spectator mode** — AI NPCs can battle *each other* while the player watches

The wow moment: an NPC walks across the map to find you, challenges you unprompted, and opens with the exact counter to the team it saw you use last time.

---

## Why Pokémon

Pokémon FireRed has a full open decompilation (pret/pokefirered). We own every byte of the ROM. That means we can add real C code, real special functions, and real memory structures — not hacks, not overlays.

The mGBA emulator exposes a Lua scripting API with direct memory read/write. That's our real-time bridge between the game and the AI.

The result is AI behaviour that runs *inside* the game, not alongside it.

---

## System Architecture

```
mGBA Emulator
  └─ Lua bridge (codex_mailbox_bridge.lua)
       ├─ polls EWRAM mailbox (0x0203F4AC) every frame
       ├─ reads game state (party, map, encounters, battle)
       ├─ on PENDING / triggers → POST to FastAPI bridge
       └─ writes response + AI plan back → game picks it up

FastAPI Bridge (localhost:8000)
  └─ routes: /codex-chat, /rival-event,
              /rival-battle-plan, /rival-taunt, /rival-battle-summary
       └─ OpenAI GPT → response → FireRed-encoded → hex
       └─ rival memory persisted to agents/rival/memory.md

Patched ROM (pokefirered.gba)
  └─ Prof GPT 5.5 NPC, rival encounter buffer, gRivalAIBuffer + AI hook
       → all real C code, compiled into the ROM
       → responses appear in native FireRed textboxes
```

---

## What Makes This Different

| Approach | What most people do | What we do |
|---|---|---|
| AI in games | Chatbot overlay on top of the game | Response rendered inside the game's own textbox engine |
| NPC behaviour | Scripted trigger → scripted response | GPT reasons about state, generates behaviour dynamically |
| Battle AI | Fixed move-priority table | GPT biases the AI's move-score array based on memory of prior fights |
| NPC memory | Stateless per-interaction | Persistent memory across encounters, informs future behaviour |

---

## Implementation Status

| Phase | Feature | Status |
|---|---|---|
| 0 | ROM compiled, mailbox address confirmed | Done |
| 1 | Professor GPT end-to-end (ADVICE + ASK → textbox) | Done |
| 2 | Party-aware ADVICE + gym-context coverage prompts | Done |
| 3 | AI Rival proactive walk-up cinematic + memory.md | Done |
| 4a | Smart Gary battle endpoints + EWRAM hook (gRivalAIBuffer) | Done |
| 4b | `/rival-battle-plan` POST at battle entry → Gary's first move shifts | In progress |
| 4c | Battle 2 (Route 1) and Battle 3 (Pewter) cinematic + trainer | Pending |
| S4a | Custom sprites: Prata / Prata Pro / Frankson (front + back, 64×64) | Done |
| S4b | Custom icons: Pokédex icon replacement for Charmander/Charmeleon/Squirtle | In progress |
| 5 | AI NPC vs AI NPC battle spectator mode | Stretch |

---

## Key Constraints

- Response must be **≤ 45 characters, 1 sentence, ASCII only** — FireRed textbox limit
- Encoding must be **flat** (no `0xFB`/`0xFE`) — these bytes crash the textbox engine
- All OpenAI calls go through the FastAPI bridge — never directly from Lua
- Never commit ROMs, save files, or `.env` files
