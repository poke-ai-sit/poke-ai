# PokéLive — AI Hackathon Demo

Turn Pokémon FireRed into a live AI experience. Talk to **Professor GPT 5.5** inside the game and get real GPT-powered responses directly in the textbox.

---

## What This Is

- A patched GBA ROM running in the mGBA emulator
- A Lua script inside mGBA that relays the player's question to a local FastAPI server
- A FastAPI bridge that calls OpenAI and returns the response encoded in FireRed's character set
- The in-game textbox displays GPT's answer as if it's coming from Professor Oak

---

## Prerequisites

### Everyone needs

| Tool | Download | Notes |
|------|---------|-------|
| **mGBA emulator** | https://mgba.io/builds/ | Use the latest **development build** |
| **Pokémon FireRed ROM** | https://www.romsgames.net/gameboy-advance-rom-pokemon---fire-red-version-a1/ | FireRed v1.0 USA — needed as the base for the custom ROM |
| **OpenAI API key** | https://platform.openai.com/api-keys | |
| **uv** (Python package manager) | https://docs.astral.sh/uv/getting-started/installation/ | |
| **Git** | https://git-scm.com/downloads | |

> **Why development build?** The development build of mGBA has the most complete Lua scripting API (`socket`, `console`, `callbacks`) that the bridge script depends on. The stable release may be missing some socket methods.

---

## macOS Setup

### 1. Install mGBA (development build)

Go to https://mgba.io/builds/ and download the latest macOS `.dmg` from the **development builds** section. Open it and drag mGBA into Applications.

### 2. Get the base ROM

Download the FireRed v1.0 USA ROM from https://www.romsgames.net/gameboy-advance-rom-pokemon---fire-red-version-a1/ — save it somewhere safe (e.g. `~/Downloads/fire-red.gba`). You will need it to load the game via the battery save.

### 3. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal so `uv` is on your PATH.

### 4. Clone this repo

```bash
git clone <repo-url>
cd poke-ai
```

### 5. Configure your API key

```bash
cp bridge/.env.example bridge/.env
# Open bridge/.env and replace sk-... with your real OpenAI key
```

Edit `bridge/.env`:
```
OPENAI_API_KEY=sk-your-real-key-here
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_MAX_COMPLETION_TOKENS=4096
```

### 6. Install Python dependencies

```bash
cd bridge
uv sync
cd ..
```

### 7. Get the patched ROM

The patched ROM (`pokefirered.gba`) is built from the pret/pokefirered source + our patches. Get the pre-built binary from a teammate or the shared drive and place it at:

```
poke-ai/pokefirered/pokefirered.gba
```

> **Need to build it yourself?** See the **Building the ROM** section at the bottom. You will need devkitPro installed first.

---

## Windows Setup

### 1. Install mGBA (development build)

Go to https://mgba.io/builds/ and download the latest Windows `.7z` or `.exe` from the **development builds** section. Extract or install it.

### 2. Get the base ROM

Download the FireRed v1.0 USA ROM from https://www.romsgames.net/gameboy-advance-rom-pokemon---fire-red-version-a1/ — save it somewhere safe.

### 3. Install uv

Open PowerShell and run:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart PowerShell so `uv` is on your PATH.

### 4. Install Git for Windows

Download from https://git-scm.com/download/win — use all default options.

### 5. Clone this repo

Open Git Bash or PowerShell:
```bash
git clone <repo-url>
cd poke-ai
```

### 6. Configure your API key

```cmd
copy bridge\.env.example bridge\.env
```

Then open `bridge\.env` in Notepad and fill in your key:
```
OPENAI_API_KEY=sk-your-real-key-here
OPENAI_CHAT_MODEL=gpt-4o
OPENAI_MAX_COMPLETION_TOKENS=4096
```

### 7. Install Python dependencies

```cmd
cd bridge
uv sync
cd ..
```

### 8. Get the patched ROM

Place the pre-built `pokefirered.gba` at:
```
poke-ai\pokefirered\pokefirered.gba
```

> **Need to build it yourself?** See the **Building the ROM** section at the bottom.

---

## Running the Demo

You need **two things running at the same time**: the FastAPI bridge and mGBA with the Lua script loaded.

### Step 1 — Start the FastAPI bridge

**macOS:**
```bash
cd poke-ai/bridge
bash run.sh
```

**Windows (PowerShell):**
```powershell
cd poke-ai\bridge
uv run fastapi dev src\pokelive_bridge\main.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Leave this terminal open.

### Step 2 — Load the game in mGBA

1. Open mGBA
2. **File → Load ROM** → select `poke-ai/pokefirered/pokefirered.gba` (the patched ROM)
3. **File → Load Game** → select `fire-red.sav` (battery save from a teammate or the shared drive)
4. **Tools → Scripting** → click **Load script** → select `poke-ai/emulator/lua/codex_mailbox_bridge.lua`

The scripting console should print:
```
PokeLive Codex mailbox bridge loaded.
```

### Step 3 — Talk to Professor GPT 5.5

1. Walk up to the scientist NPC in Professor Oak's lab
2. Press A to interact — you'll see the Codex menu: **ADVICE / ASK / EXIT**
3. **ADVICE** — GPT gives context-aware advice about your current map position
4. **ASK** — Type your own question using the naming screen (letters only, max 32 chars), then confirm

The game will show "..." while waiting, then display GPT's response in the textbox.

---

## Troubleshooting

**Bridge returns "My data scanner is fuzzy" (fallback message)**
- Check that `bridge/.env` exists and `OPENAI_API_KEY` is set correctly
- Make sure `OPENAI_MAX_COMPLETION_TOKENS` is at least `1024` (set to `4096` for gpt-5.x reasoning models)
- Restart the bridge after editing `.env`

**"Mailbox magic mismatch" in the Lua console**
- This is normal right after loading a save state — the game hasn't initialized the mailbox yet
- Walk to Prof Oak and talk to him; the magic check will pass once the game script runs

**No response appears in the game / game seems stuck**
- Verify the bridge is running and shows no errors
- The Lua script has a 90-second wall-clock timeout; if GPT takes longer it writes "Try again." into the mailbox
- Check the Lua console for HTTP errors

**mGBA scripting console is empty after loading the Lua script**
- Make sure you loaded the patched ROM (`pokefirered.gba`), not the original `fire-red.gba`
- Make sure you are using the mGBA **development build** — stable may not have full socket support

**Windows: `uv` not found after install**
- Close and reopen PowerShell; the installer adds uv to your user PATH

---

## Architecture Overview

```
mGBA emulator (development build)
  └─ codex_mailbox_bridge.lua
       ├─ reads  gPokeliveCodexMailbox (EWRAM 0x0203F48C) — status + command text
       ├─ POSTs  localhost:8000/codex-chat     — command + current map/position
       └─ writes gPokeliveCodexMailbox.response — GPT reply in FireRed encoding

FastAPI bridge  (bridge/src/pokelive_bridge/)
  └─ POST /codex-chat → OpenAI gpt-4o → sanitized → FireRed hex encoded → returned

Patched ROM  (pokefirered/)
  └─ Oak's lab script: ADVICE / ASK multichoice
       → writes question to mailbox
       → polls IsCodexResponseReady every 15 frames
       → displays response in textbox via BufferCodexResponse
```

---

## Building the ROM (Advanced)

Only needed if you need to build the patched ROM yourself rather than getting the pre-built binary from a teammate.

### Step 0 — Install devkitPro

devkitPro provides the ARM cross-compiler and GBA toolchain required to build GBA ROMs.
Main site: https://devkitpro.org | Getting started guide: https://devkitpro.org/wiki/Getting_Started

**macOS / Linux:**
```bash
# Download and run the devkitPro pacman installer
curl -sSL https://apt.devkitpro.org/install-devkitpro-pacman | sudo bash

# Then install the GBA development group
sudo dkp-pacman -Sy --noconfirm gba-dev
```

After install, devkitPro lives at `/opt/devkitpro`. Add to your shell profile:
```bash
export DEVKITPRO=/opt/devkitpro
export DEVKITARM=/opt/devkitpro/devkitARM
export PATH="$DEVKITPRO/devkitARM/bin:$DEVKITPRO/tools/bin:$PATH"
```

**Windows:**

Download the Windows installer from https://github.com/devkitPro/installer/releases — get `devkitProUpdater-X.X.X.exe`, run it, and select **GBA Development** when prompted. The installer sets `DEVKITPRO` and `DEVKITARM` environment variables automatically.

> After install, verify with `arm-none-eabi-gcc --version` in a new terminal.

### Step 1 — Clone pret/pokefirered and apply patches

The base decompilation is at https://github.com/pret/pokefirered.

```bash
# Clone the pret decompilation (place it inside poke-ai/ or alongside it)
git clone https://github.com/pret/pokefirered
cd pokefirered

# Apply the three PokéLive patches from this repo
git am ../patches/0001-add-professor-codex-prompt-ui.patch
git am ../patches/0002-add-professor-codex-mailbox.patch
git am ../patches/0003-route-professor-oak-to-codex.patch
```

### Step 2 — Install agbcc (GBA-specific C compiler)

pokefirered uses `agbcc` (a patched GCC for GBA) rather than standard devkitARM gcc for the game C code.

```bash
cd /tmp
git clone --depth=1 https://github.com/pret/agbcc
cd agbcc
chmod +x build.sh install.sh
./build.sh
./install.sh /path/to/pokefirered   # absolute path to your pokefirered clone
```

### Step 3 — Build the ROM

```bash
cd /path/to/pokefirered

# macOS/Linux
DEVKITPRO=/opt/devkitpro \
DEVKITARM=/opt/devkitpro/devkitARM \
PATH="/opt/devkitpro/devkitARM/bin:/opt/devkitpro/tools/bin:$PATH" \
make -j$(sysctl -n hw.logicalcpu)

# Windows (Git Bash, with DEVKITPRO set by installer)
make -j4
```

Output: `pokefirered.gba` and `pokefirered.map` in the pokefirered directory.

**Docker alternative (no local toolchain needed):**
```bash
cd /path/to/pokefirered
docker run --rm \
  -v "$(pwd)":/pokefirered \
  devkitpro/devkitarm:latest \
  bash -c "
    apt-get update -qq && apt-get install -y -qq libpng-dev git 2>/dev/null &&
    cd /tmp && git clone --depth=1 https://github.com/pret/agbcc agbcc &&
    cd agbcc && chmod +x build.sh install.sh && ./build.sh &&
    ./install.sh /pokefirered &&
    cd /pokefirered && make -j4
  "
```

### Step 4 — Verify mailbox address

```bash
grep "gPokeliveCodexMailbox" pokefirered.map
```

The address should be `0x0203F48C`. If it differs, update line 10 of `emulator/lua/codex_mailbox_bridge.lua`.

### Step 5 — Place the ROM

Copy the built `pokefirered.gba` to `poke-ai/pokefirered/pokefirered.gba`.
