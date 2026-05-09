# PokéLive — Team Instructions

---

## FOR CLAUDE CODE — Run This On Every Session Start

*This section is your initialization script. Execute it top to bottom before doing anything else.*

### Step 1 — Identify who you are working with

Hackathon-day team and shipping focus:

| Name | Focus | Sprint |
|---|---|---|
| Shaun Liew Xin Hong | Professor GPT — AI Advice NPC | SPRINT-003 (done) |
| Edmund Lin Zhenming | AI Rival — autonomous walk-up + Smart Gary battles | SPRINT-005 (in progress) |

Sprint-006 (multi-feature polish) was folded into Sprint-005 Hour 7 dry-run. Sprint-004 (Pokémon sprite generator website) shipped on 2026-05-09 and is merged to dev. See `docs/BUILD.md`.

Ask the user who you are working with if they haven't said. Then introduce yourself in this format:

> "Hi [Name]. I'm your Claude Code for PokéLive. You own [focus area]. Let me get up to speed on the project and your current sprint."

### Step 2 — Read these files in order

1. `docs/CONTEXT.md` — understand what we're building and why
2. `docs/BUILD.md` — find the sprint(s) owned by this person, check their current status

Do not ask the user to summarise anything. Read the files yourself.

### Step 3 — Open a working discussion

After reading, give the user a short briefing (3–5 lines max):

- What their sprint goal is
- Which tasks are done, in progress, or not started
- What you recommend tackling right now, and why

Then ask: **"Does this look right, or do you want to change direction?"**

Wait for their answer before writing any code.

### Step 4 — Work on tasks

As you complete each task:

- Check it off in `docs/BUILD.md` immediately
- Update the sprint status to `[~] In Progress` if it was `[ ] Not Started`
- Commit the work with a clear message before moving to the next task

### Step 5 — End of session — merge back to dev

When the user says they're done, or you reach a natural stopping point:

1. Check `docs/BUILD.md` — mark completed tasks, update sprint status
2. Commit any uncommitted changes with a `wip:` prefix if incomplete
3. Push the feature branch: `git push origin feat/NNN-...`
4. **Merge back to `dev`** following this exact sequence:
   ```bash
   git checkout dev
   git pull origin dev                       # always pull before merging
   git merge --no-ff feat/NNN-... -m "Merge branch 'feat/NNN-...' — <one-line summary>"
   # if conflicts: resolve them, git add, git commit
   git push origin dev
   git checkout feat/NNN-...                 # leave the user back on their branch
   ```
5. Tell the user what was completed, that it's merged into dev, and what's left for next session

**Do not push to `main` ever.** `main` is the release branch — only humans merge `dev → main`, and only when explicitly approved. `dev` is the integration branch where all feature work lands.

Do not end the session without merging back to dev. Unsaved local work is invisible to teammates.

---

## FOR CLAUDE CODE — Rules You Must Never Break

- Never commit `.gba`, `.sav`, `.ss0`, or `.env` files
- Never call OpenAI directly from Lua — all AI calls go through the FastAPI bridge
- Never use `0xFB` (PAGE_BREAK) in response encoding — crashes the textbox engine inside `{STR_VAR_1}` substitution
- Never use `0xFE` (NEWLINE) in response encoding — also corrupts `{STR_VAR_1}` substitution and causes invalid-address jumps; keep `chars_per_line=200, lines_per_page=1` (flat encoding)
- Never raise the GPT response limit above 45 chars without fixing ROM-side textbox display — flat text overflows visually beyond ~45 chars and longer responses cannot be line-wrapped safely
- **Never push directly to `main`.** `main` is the release branch — only humans promote `dev → main`. Always merge feature branches into `dev`.
- **Always pull `dev` before merging into it.** If conflicts arise, resolve them in the editor — never `git push --force`, never discard a teammate's changes.
- The Lua bridge and `main.py` are no longer hot-contested (Sprint-003 done, Sprint-004 dropped). Edit freely; mention significant changes if Shaun re-opens Professor GPT work.
- Always rebuild the ROM after any change to `pokefirered/src/` or `pokefirered/data/`

---

## FOR HUMANS — Team Contract

> The rest of this file is for people, not Claude. Read it once at project start.

### Branch Model

```
main      ← release branch. Only humans promote dev → main.
  └─ dev  ← integration branch. All feature work merges here.
       └─ feat/NNN-...  ← one sprint = one feature branch, off dev
```

| Rule | Detail |
|---|---|
| Branch naming | `feat/NNN-short-description` matching the sprint ID in `BUILD.md` |
| Branch off | Always branch off the latest `dev` (pull first) |
| Merge into | Always merge back into `dev` (pull `dev` first to avoid conflicts) |
| One sprint = one branch | Do not mix sprint work on the same branch |
| `main` is sacred | Claude never pushes to `main`. Humans promote `dev → main` when ready |
| Keep branches short-lived | Merge into `dev` within the sprint; don't let branches drift |

**Active branches as of 2026-05-09:**

| Branch | Owner | Status |
|---|---|---|
| `feat/003-party-context` | Shaun | ✅ Done, merged to dev, deleted |
| `feat/004-pokemon-creator` | Shaun | ✅ Done, merged to dev, deleted |
| `feat/005-ai-npc` / `feat/005c-rival-rom-mvp` | Edmund | ✅ Done, merged to dev |
| `feat/006-demo-polish` | All | ✅ Done, folded into Sprint-005 dry-run, merged to dev |

```bash
# Start a new sprint (always branch from latest dev)
git fetch origin
git checkout origin/dev -b feat/NNN-short-description

# End of sprint — merge back into dev
git push origin feat/003-party-context
git checkout dev && git pull origin dev
git merge --no-ff feat/003-party-context -m "Merge branch 'feat/003-...' — short summary"
# resolve conflicts if any, commit, then:
git push origin dev
```

### Daily Workflow

**Start of session:**
1. `git checkout dev && git pull origin dev`
2. Rebase your branch on dev if it has moved: `git rebase dev` (on your feature branch)
3. Say "read docs/INSTRUCTIONS.md and introduce yourself" to Claude Code — it handles the rest

**During session:**
- Commit small and often — at minimum one commit per logical change
- Write clear commit messages: `feat: read party data from EWRAM` not `update lua`
- If you hit a blocker, tell Claude to update the sprint entry in `BUILD.md` with `[!] Blocked` and a note

**End of session:**
- Tell Claude "we're done for today" — it will commit, push the feature branch, **merge back into `dev` (pull-then-merge-then-push)**, and update BUILD.md

### Shared File Coordination

With Sprint-003 already merged, the Smart Gary track is the only active editor of `codex_mailbox_bridge.lua` and `main.py`. Coordination is mostly a courtesy now — if Shaun re-opens Professor GPT work, mention any in-flight Lua or `main.py` edits before pushing.

| Area | Files |
|---|---|
| Lua bridge | `emulator/lua/codex_mailbox_bridge.lua` |
| FastAPI bridge | `bridge/src/pokelive_bridge/main.py`, `bridge/src/pokelive_bridge/battle_agent.py`, `bridge/src/pokelive_bridge/rival_agent.py` |
| ROM / C code | `pokefirered/src/`, `pokefirered/data/`, `pokefirered/include/` |
| Docs | `docs/` |

### ROM Build Rules

- Always rebuild after any change to `pokefirered/src/` or `pokefirered/data/`
- Committed ROM (`pokefirered.gba`) must stay in sync with source
- Never overwrite `pokelive/fire-red.gba` — that is the unpatched original
- Test with the battery save (`fire-red.sav`), not `.ss0` save states

```bash
cd pokefirered
DEVKITPRO=/opt/devkitpro \
DEVKITARM=/opt/devkitpro/devkitARM \
PATH="/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH" \
make -j$(sysctl -n hw.logicalcpu)
```

### Coding Standards

**Python (bridge)**
- PEP 8, type hints, Pydantic models for all request/response shapes
- `uv` for package management — never `pip` directly
- Lazy-init clients that need env vars (see `openai_client.py`)
- Load `.env` with explicit path, never CWD-relative (see `config.py`)
- Keep offline tables (type chart, gym data, move IDs) in `gym_data.py` — `pokemon_data.py` is for network-only PokéAPI lookups
- `move_type()` returns `None` for unknown move IDs — callers must skip `None` before coverage checks

**Lua (mGBA bridge)**
- Lua 5.4 — `emu:read32` / `emu:write32` for all memory access
- HTTP via mGBA's `socket` API — no external libraries
- Side effects (HTTP calls) only on state transitions, not every frame

**C (ROM patches)**
- Match pret/pokefirered style — 4-space indent, GBA types (`u8`, `u16`, `u32`)
- No `#include "strings.h"` — use `characters.h`
- Response encoding always flat: `chars_per_line=200, lines_per_page=1`

**Commit messages**
```
feat: add party data to /codex-chat POST body
fix: lazy-init OpenAI client to avoid empty-key crash
wip: EWRAM party read, name resolution pending
chore: rebuild ROM after codex_npc.c fix
docs: update BUILD.md sprint-003 tasks
```

### Resolving Conflicts

Conflicts will happen during the hackathon — three people, one Lua bridge, one `main.py`. Claude is expected to resolve them, not abandon the merge.

1. **Always `git pull origin dev` before merging your feature branch into dev.** This catches conflicts early.
2. **Prefer `git rebase dev`** on your feature branch over `git merge dev` — keeps history linear.
3. **`BUILD.md` conflicts:** keep both sides of the diff. Every team member's task updates are valid. Never delete someone else's checkmarks.
4. **Lua or C file conflicts:** if intent is unclear, ask the user. Don't guess and silently delete a teammate's logic.
5. **`main.py` conflicts (new endpoints):** both endpoints belong; merge them side-by-side.
6. **Never `--force` push** a branch someone else has checked out, and never `--force` push to `main` or `dev`.
7. **If you can't resolve a conflict cleanly,** stop and ask the user — better to pause than corrupt shared state.

### Definition of Done (per sprint)

- [ ] All tasks in `BUILD.md` checked off
- [ ] Feature branch pushed AND merged into `dev` (`dev` pushed too)
- [ ] ROM rebuilt if any C/data files changed
- [ ] Feature works end-to-end in mGBA
- [ ] `BUILD.md` sprint status updated to `[x] Done` with closed date
