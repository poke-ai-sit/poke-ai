local buffer = console:createBuffer("PokéLive Codex Mailbox Bridge")

local HOST = "127.0.0.1"
local PORT = 8000
local SAVE_BLOCK_1_PTR = 0x03005008

-- EWRAM addresses from pokefirered.map (build 2026-05-07)
local CODEX_MAILBOX_ADDR = 0x0203f4ac  -- gPokeliveCodexMailbox
local PARTY_DATA_ADDR    = 0x0203f5dc  -- gPokelivePartyData

-- gPokelivePartyData struct constants
local POKELIVE_PARTY_MAGIC = 0x50415254  -- "PART"
local PARTY_ENTRY_MAGIC   = 0x5054       -- "PT"
local PARTY_HEADER_SIZE   = 8            -- u32 magic + u8 count + u8 pad[3]
local PARTY_ENTRY_SIZE    = 28           -- 14 × u16
local PARTY_MAX           = 6

-- Offsets within each PokelivePartyEntry (u16 each)
local PE_MAGIC    = 0
local PE_SPECIES  = 2
local PE_LEVEL    = 4
local PE_HP       = 6
local PE_MAXHP    = 8
local PE_MOVE1    = 10
local PE_MOVE2    = 12
local PE_MOVE3    = 14
local PE_MOVE4    = 16
local PE_ATTACK   = 18
local PE_DEFENSE  = 20
local PE_SPEED    = 22
local PE_SPATTACK  = 24
local PE_SPDEFENSE = 26

local POKELIVE_CODEX_MAILBOX_MAGIC = 0x58454443
local MAILBOX_STATUS_IDLE = 0
local MAILBOX_STATUS_PENDING = 1
local MAILBOX_STATUS_RESPONSE_READY = 2
local MAILBOX_STATUS_ERROR = 3

local OFFSET_MAGIC = 0
local OFFSET_SEQ = 4
local OFFSET_ACK = 6
local OFFSET_STATUS = 8
local OFFSET_COMMAND_LENGTH = 10
local OFFSET_RESPONSE_LENGTH = 12
local OFFSET_COMMAND = 14
local CODEX_INPUT_LENGTH = 32
local OFFSET_RESPONSE = OFFSET_COMMAND + CODEX_INPUT_LENGTH + 1
local CODEX_RESPONSE_LENGTH = 256

local RESPONSE_TIMEOUT_SECONDS = 90

-- "Try again." encoded in FireRed charset + EOS
local TIMEOUT_RESPONSE_HEX = "CEE6ED00D5DBD5DDE2ADFF"

-- ===========================================================================
-- AI Rival proactive encounters — SPRINT-005 Hours 5-6 (Lua side)
-- ===========================================================================
-- Two ONE-SHOT triggers fire the cinematic walk-up + Battle 2/Battle 3 setup:
--
--   first_capture:  party size goes 1 → 2 (off the canon Oak's Lab map)
--                   → wait until player walks ONE more tile → POST /rival-event
--                   → bridge picks counter_choice (anti-fire/water/grass/...)
--                   → Lua writes counterChoice to gRivalAIBuffer + arms cinematic
--
--   second_capture: party size goes 2 → 3 (any map). Same 1-tile delay.
--                   POSTs with battle 3 picker output.
--
-- Battle entry (any map_signature in BATTLE_ID_BY_MAP_SIGNATURE) keeps using
-- /rival-battle-plan to populate moveScore[].
--
-- gRivalEncounterBuffer EWRAM contract (lives in pokefirered/src/codex_npc.c):
--   struct PokeliveRivalEncounter {
--     u32 magic;          // offset 0   — 0x52454E43 ("RENC")
--     u8  status;         // offset 4   — 0=IDLE, 1=APPROACH_PENDING
--     u8  messageLength;  // offset 5   — bytes in message including EOS
--     u8  pad[2];         // offset 6
--     u8  message[200];   // offset 8   — FireRed-encoded, terminated by 0xFF
--   };  // total: 208 bytes
-- Lua transitions IDLE → APPROACH_PENDING by writing magic + message + length
-- + status, then flipping VAR_TEMP_0=1 in SaveBlock1.vars[0] to trigger the
-- map_script_2 entry that the ROM team adds for each cinematic map.
-- Address from pokefirered.map after build 2026-05-08 (post-merge with SPRINT-003).
local RIVAL_ENCOUNTER_BUFFER_ADDR    = 0x0203f68c  -- gRivalEncounterBuffer
local RIVAL_ENCOUNTER_MAGIC          = 0x52454E43  -- "RENC"
local RIVAL_ENCOUNTER_STATUS_PENDING = 1
local RIVAL_ENCOUNTER_MESSAGE_MAX    = 200
local RIVAL_ENCOUNTER_OFFSET_STATUS  = 4
local RIVAL_ENCOUNTER_OFFSET_LENGTH  = 5
local RIVAL_ENCOUNTER_OFFSET_MESSAGE = 8

-- VAR_TEMP_0 lives at SaveBlock1 + 0x1000 (vars[0], u16). The map_script_2
-- frame script triggers when VAR_TEMP_0 == 1; the encounter script resets
-- it back to 0 after running so it can fire again next time.
local VAR_TEMP_0_OFFSET = 0x1000

-- Map signatures we care about for the new triggers.
local OAKS_LAB_MAP_SIG     = "4:3"

-- Skip event detection during the first N frames after script load so the
-- baseline party-size read doesn't false-fire on hot-reload.
local RIVAL_GRACE_FRAMES = 60

-- Party-count byte lives at SaveBlock1 + 0x34 (verified in pokefirered global.h).
local SAVE_BLOCK_1_OFFSET_PARTY_COUNT = 0x34

-- ===========================================================================
-- Smart Gary battle-state polling — SPRINT-005 Phase 4 SCAFFOLDING
-- ===========================================================================
-- Constants and helpers below are mapped from pokefirered's battle.h /
-- battle_main.c via the build at 2026-05-09. The frame callback does NOT
-- yet invoke these — Edmund must verify addresses in mGBA before enabling.
--
-- TO ENABLE per-frame battle polling: set BATTLE_POLLING_ENABLED = true.
-- The integration steps are documented in docs/HANDOFF_smart_gary.md.

local BATTLE_POLLING_ENABLED = true  -- enabled 2026-05-09 for Hour 2 mGBA validation

-- EWRAM addresses (verified from pokefirered.map post-build 2026-05-09)
local BATTLE_OUTCOME_ADDR     = 0x02023EAA  -- u8: 0=in_battle, 1=won, 2=lost, ...
local CURRENT_MOVE_ADDR       = 0x02023D6A  -- u16: move ID currently animating
local BATTLER_ATTACKER_ADDR   = 0x02023D8B  -- u8: 0|2=player side, 1|3=opponent
local BATTLE_STRUCT_PTR       = 0x02024008  -- gBattleStruct base
local CHOSEN_MOVE_OFFSET      = 0x87        -- chosenMovePositions[battler] u8
local BATTLE_MONS_ADDR        = 0x02023C04  -- gBattleMons[0]
local BATTLE_MON_STRIDE       = 0x58        -- 88 bytes per BattlePokemon

-- gRivalAIBuffer (post-build 2026-05-09): Lua writes the AI move-score plan
-- here so the C-side BattleAI hook can apply boosts on Gary's first turn.
local RIVAL_AI_BUFFER_ADDR    = 0x0203F75C
local RIVAL_AI_BUFFER_MAGIC   = 0x52414942  -- "RAIB"

-- Field offsets within each gBattleMons[i] entry
local BMON_SPECIES   = 0x00  -- u16
local BMON_MOVES     = 0x0C  -- u16[4]
local BMON_HP        = 0x28  -- u16
local BMON_LEVEL     = 0x2A  -- u8
local BMON_MAX_HP    = 0x2C  -- u16
local BMON_STATUS1   = 0x4C  -- u32

-- Battle outcome enum (matches B_OUTCOME_* in include/constants/battle.h)
local BATTLE_OUTCOME_IN_PROGRESS = 0
local BATTLE_OUTCOME_WON         = 1
local BATTLE_OUTCOME_LOST        = 2
local BATTLE_OUTCOME_DREW        = 3
local BATTLE_OUTCOME_RAN         = 4
local BATTLE_OUTCOME_CAUGHT      = 7

-- Battler IDs: 0,2 = player side; 1,3 = opponent side
local function is_player_battler(battler_id)
  return battler_id == 0 or battler_id == 2
end

local function is_opponent_battler(battler_id)
  return battler_id == 1 or battler_id == 3
end

-- Battle 1 (Oak's Lab) is the only battle whose ID is determined purely by
-- map. Battle 2 and Battle 3 fire anywhere the player walks one tile after
-- their first / second wild capture, so they're keyed off the most recently
-- fired rival trigger (see `last_rival_trigger` below) instead of map sig.
local BATTLE_ID_BY_MAP_SIGNATURE = {
  ["4:3"]  = "battle_1_oaks_lab",   -- Professor Oak's Lab (canon)
}

-- Battle ID picked by which capture trigger fired most recently. Set by
-- fire_rival_event(); read at battle entry; cleared once consumed so it
-- doesn't bleed into a later battle.
local BATTLE_ID_BY_TRIGGER = {
  first_capture  = "battle_2_first_capture",
  second_capture = "battle_3_second_capture",
}

local frame_count = 0
local pending = nil
local last_seq = nil
local warned_unconfigured = false
local warned_magic_mismatch = false

-- Rival trigger state
local last_party_count = nil
local last_map_signature = nil

-- Position tracker — used by the post-capture 1-tile delay logic for both
-- first_capture and second_capture triggers. Format: "map_group:map_num:x:y".
-- When this string changes between frames, the player has moved one tile.
local last_position_signature = nil

-- first_capture state machine.
--   "idle"        : nothing armed
--   "post_catch"  : party size just went 1 → 2 off Oak's Lab. Waiting for the
--                   first tile of player movement before firing.
--   "fired"       : POST sent. One-shot per session — never re-arms.
local first_capture_state = "idle"
local first_capture_anchor_position = nil  -- position sig at the moment of catch

-- second_capture state machine. Same shape as first_capture; fires on the
-- 2 → 3 party-size transition (player's second wild catch — total mons = 3).
local second_capture_state = "idle"
local second_capture_anchor_position = nil

-- The trigger string from the most-recently-fired rival_event. Read by the
-- battle-entry watcher to pick battle_id (battle_2_first_capture vs.
-- battle_3_second_capture). Cleared once consumed so it doesn't bleed.
local last_rival_trigger = nil

-- Smart Gary battle log accumulator. Cleared at battle start, sent to
-- /rival-battle-summary at battle end.
local in_battle = false
local current_battle_id = nil
local current_turn = 0
local battle_log = {}              -- list of {turn, side, actor_species, move, result?}
local last_logged_player_move = -1
local last_logged_rival_move = -1
local last_outcome_seen = 0

-- Hour 4b — deferred battle-plan POST.
-- check_battle_transitions() used to early-return when `pending` was set, which
-- caused Battle 1 (Oak's Lab) to silently miss its /rival-battle-plan POST: a
-- /game-state POST queued by the player's last walking step into the lab was
-- still in flight during the narrow window where the watcher would otherwise
-- bootstrap. We now ALWAYS run the state machine; if the POST can't fire this
-- frame because another request is in flight, we stash the payload here and
-- retry next frame from the frame callback.
local deferred_battle_plan = nil   -- { battle_id, player_party, rival_party, state }

local decode_table = {
  [0x00] = " ",
  [0xAB] = ".",
  [0xAC] = ".",
  [0xAD] = ".",
  [0xAE] = " ",
  [0xB8] = " ",
  [0xBA] = " ",
  [0xF0] = " ",
}

for index = 0, 9 do
  decode_table[0xA1 + index] = tostring(index)
end

for index = 0, 25 do
  decode_table[0xBB + index] = string.char(string.byte("A") + index)
  decode_table[0xD5 + index] = string.char(string.byte("a") + index)
end

local function write_line(text)
  console:log(text)
  buffer:print(text .. "\n")
end

local function is_temporary_socket_error(err)
  local s = tostring(err)
  return err == socket.ERRORS.AGAIN
      or s == "temporary failure"
      or s == "unsupported"
end

local function json_escape(text)
  return text
    :gsub("\\", "\\\\")
    :gsub('"', '\\"')
    :gsub("\n", "\\n")
    :gsub("\r", "\\r")
end

local function json_game_state(state)
  if state.frame then
    return string.format(
      '{"map_group":%d,"map_num":%d,"x":%d,"y":%d,"frame":%d}',
      state.map_group,
      state.map_num,
      state.x,
      state.y,
      state.frame
    )
  end

  return string.format(
    '{"map_group":%d,"map_num":%d,"x":%d,"y":%d}',
    state.map_group,
    state.map_num,
    state.x,
    state.y
  )
end

local function read_party_data()
  local magic = emu:read32(PARTY_DATA_ADDR)
  if magic ~= POKELIVE_PARTY_MAGIC then
    return nil
  end

  local count = emu:read8(PARTY_DATA_ADDR + 4)
  if count == 0 or count > PARTY_MAX then
    return nil
  end

  local entries = {}
  for i = 0, count - 1 do
    local base = PARTY_DATA_ADDR + PARTY_HEADER_SIZE + i * PARTY_ENTRY_SIZE
    if emu:read16(base + PE_MAGIC) ~= PARTY_ENTRY_MAGIC then
      break
    end
    entries[#entries + 1] = {
      species   = emu:read16(base + PE_SPECIES),
      level     = emu:read16(base + PE_LEVEL),
      hp        = emu:read16(base + PE_HP),
      max_hp    = emu:read16(base + PE_MAXHP),
      moves     = {
        emu:read16(base + PE_MOVE1),
        emu:read16(base + PE_MOVE2),
        emu:read16(base + PE_MOVE3),
        emu:read16(base + PE_MOVE4),
      },
      attack    = emu:read16(base + PE_ATTACK),
      defense   = emu:read16(base + PE_DEFENSE),
      speed     = emu:read16(base + PE_SPEED),
      sp_attack  = emu:read16(base + PE_SPATTACK),
      sp_defense = emu:read16(base + PE_SPDEFENSE),
    }
  end

  return #entries > 0 and entries or nil
end

local function json_party_entry(e)
  return string.format(
    '{"species":%d,"level":%d,"hp":%d,"max_hp":%d,' ..
    '"moves":[%d,%d,%d,%d],' ..
    '"attack":%d,"defense":%d,"speed":%d,"sp_attack":%d,"sp_defense":%d}',
    e.species, e.level, e.hp, e.max_hp,
    e.moves[1], e.moves[2], e.moves[3], e.moves[4],
    e.attack, e.defense, e.speed, e.sp_attack, e.sp_defense
  )
end

local ADVICE_COMMAND_PREFIX = "What should I do next"

local function json_codex_chat(message, state)
  local is_advice = message:find(ADVICE_COMMAND_PREFIX, 1, true) ~= nil
  local request_kind = is_advice and "ADVICE" or "ASK"

  local party_json = ""
  if is_advice then
    local party = read_party_data()
    if party then
      local parts = {}
      for _, e in ipairs(party) do
        parts[#parts + 1] = json_party_entry(e)
      end
      party_json = ',"party":[' .. table.concat(parts, ",") .. ']'
    end
  end

  local body = string.format(
    '{"message":"%s","game_state":%s,"request_kind":"%s"%s}',
    json_escape(message),
    json_game_state(state),
    request_kind,
    party_json
  )
  return body
end

local function json_unescape(text)
  return text
    :gsub('\\"', '"')
    :gsub("\\n", "\n")
    :gsub("\\r", "\r")
    :gsub("\\\\", "\\")
end

local function extract_json_field(response, field_name)
  local pattern = '"' .. field_name .. '":"(.-)"'
  local value = response:match(pattern)
  if value then
    return json_unescape(value)
  end

  return nil
end

-- Extracts an integer-array JSON field (e.g. "move_scores":[1,-2,0,5]).
-- Returns a Lua table of numbers, or nil if not found / malformed.
local function extract_json_int_array(response, field_name)
  local pattern = '"' .. field_name .. '"%s*:%s*%[(.-)%]'
  local body = response:match(pattern)
  if not body then return nil end
  local out = {}
  for num in body:gmatch("-?%d+") do
    out[#out + 1] = tonumber(num)
  end
  return out
end

-- Extracts a numeric JSON field (e.g. "counter_choice":2). Returns number or nil.
local function extract_json_int(response, field_name)
  local pattern = '"' .. field_name .. '"%s*:%s*(-?%d+)'
  local raw = response:match(pattern)
  if raw then return tonumber(raw) end
  return nil
end

-- gRivalAIBuffer layout (matches struct in include/pokelive_rival_ai.h):
--   off 0..3  : u32 magic
--   off 4     : u8  active        (1 = plan loaded; C hook clears to 0 after first turn)
--   off 5..8  : s8  moveScore[4]
--   off 9     : u8  counterChoice
--   off 10    : u8  resultPending
--   off 11    : u8  pad
local RIVAL_AI_OFF_ACTIVE          = 4
local RIVAL_AI_OFF_MOVE_SCORE      = 5
local RIVAL_AI_OFF_COUNTER_CHOICE  = 9
local RIVAL_AI_OFF_RESULT_PENDING  = 10

-- Writes a Smart-Gary AI plan into gRivalAIBuffer. Order matters:
--   1. magic + counterChoice + moveScore[0..3]   (clamped, negatives → two's complement)
--   2. active = 1                                (LAST — C hook gates on this byte)
local function write_rival_ai_plan(move_scores, counter_choice)
  if RIVAL_AI_BUFFER_ADDR == 0 then return false, "RIVAL_AI_BUFFER_ADDR unset" end
  emu:write32(RIVAL_AI_BUFFER_ADDR, RIVAL_AI_BUFFER_MAGIC)
  emu:write8(RIVAL_AI_BUFFER_ADDR + RIVAL_AI_OFF_COUNTER_CHOICE, counter_choice or 0)
  for i = 1, 4 do
    local s = move_scores and move_scores[i] or 0
    if s > 20 then s = 20 end
    if s < -20 then s = -20 end
    if s < 0 then s = s + 256 end  -- s8 → byte
    emu:write8(RIVAL_AI_BUFFER_ADDR + RIVAL_AI_OFF_MOVE_SCORE + (i - 1), s)
  end
  emu:write8(RIVAL_AI_BUFFER_ADDR + RIVAL_AI_OFF_ACTIVE, 1)  -- arm LAST
  return true
end

local function read_game_state()
  local save_block_1 = emu:read32(SAVE_BLOCK_1_PTR)

  if save_block_1 == 0 or save_block_1 == 0xFFFFFFFF then
    return nil, "SaveBlock1 pointer not ready yet."
  end

  return {
    x = emu:read16(save_block_1),
    y = emu:read16(save_block_1 + 2),
    map_group = emu:read8(save_block_1 + 4),
    map_num = emu:read8(save_block_1 + 5),
    frame = emu:currentFrame(),
  }
end

local function mailbox_addr(offset)
  return CODEX_MAILBOX_ADDR + offset
end

local function mailbox_is_configured()
  if CODEX_MAILBOX_ADDR == 0 then
    if not warned_unconfigured then
      write_line("Set CODEX_MAILBOX_ADDR to gPokeliveCodexMailbox from the patched ROM map file.")
      warned_unconfigured = true
    end
    return false
  end

  local magic = emu:read32(mailbox_addr(OFFSET_MAGIC))
  if magic ~= POKELIVE_CODEX_MAILBOX_MAGIC then
    if not warned_magic_mismatch then
      write_line(string.format(
        "Mailbox magic mismatch at 0x%08X: 0x%08X (this is normal until you talk to Professor GPT — silencing further warnings)",
        CODEX_MAILBOX_ADDR, magic
      ))
      warned_magic_mismatch = true
    end
    return false
  end

  -- Magic matched at least once; allow re-warn if it ever desyncs again.
  warned_magic_mismatch = false
  return true
end

local function read_fire_red_string(addr, max_len)
  local chars = {}
  for offset = 0, max_len - 1 do
    local value = emu:read8(addr + offset)
    if value == 0xFF then
      break
    elseif value == 0xFE or value == 0xFB then
      chars[#chars + 1] = " "
    else
      chars[#chars + 1] = decode_table[value] or " "
    end
  end

  return table.concat(chars):gsub("%s+", " "):gsub("^%s+", ""):gsub("%s+$", "")
end

local function write_hex_to_mailbox_response(hex_text)
  if not hex_text or #hex_text < 2 or #hex_text % 2 ~= 0 or hex_text:match("[^0-9A-Fa-f]") then
    return false, "invalid message_hex"
  end

  local byte_count = math.min(#hex_text / 2, CODEX_RESPONSE_LENGTH)
  local addr = mailbox_addr(OFFSET_RESPONSE)
  local wrote_eos = false

  for index = 1, byte_count do
    local hex_index = index * 2 - 1
    local value = tonumber(hex_text:sub(hex_index, hex_index + 1), 16)
    emu:write8(addr + index - 1, value)
    if value == 0xFF then
      wrote_eos = true
      byte_count = index
      break
    end
  end

  if not wrote_eos and byte_count < CODEX_RESPONSE_LENGTH then
    emu:write8(addr + byte_count, 0xFF)
    byte_count = byte_count + 1
  end

  emu:write16(mailbox_addr(OFFSET_RESPONSE_LENGTH), byte_count)
  return true, "ok"
end

local function post_json(path, body, success_marker, label, seq)
  local request = table.concat({
    "POST " .. path .. " HTTP/1.1",
    "Host: " .. HOST .. ":" .. PORT,
    "Accept: application/json",
    "Content-Type: application/json",
    "Content-Length: " .. #body,
    "Connection: close",
    "",
    body,
  }, "\r\n")

  local client, connect_error = socket.connect(HOST, PORT)
  if not client then
    return nil, "connect failed: " .. tostring(connect_error)
  end

  local sent, send_error = client:send(request)
  if not sent then
    return nil, "send failed: " .. tostring(send_error)
  end

  pending = {
    client = client,
    chunks = {},
    label = label,
    seq = seq,
    started_at = os.time(),
    success_marker = success_marker,
  }

  return "request sent; waiting for response...", nil
end

local function post_codex_chat(message, state, seq)
  return post_json(
    "/codex-chat",
    json_codex_chat(message, state),
    '"message_hex"',
    "codex-chat",
    seq
  )
end

-- ---------------------------------------------------------------------------
-- Rival event POST
-- ---------------------------------------------------------------------------

local function json_kv_pairs(t)
  -- Minimal JSON serializer for a flat table of string/number values.
  local parts = {}
  for k, v in pairs(t) do
    local key = '"' .. json_escape(tostring(k)) .. '"'
    local val
    if type(v) == "number" then
      val = tostring(v)
    elseif type(v) == "boolean" then
      val = v and "true" or "false"
    else
      val = '"' .. json_escape(tostring(v)) .. '"'
    end
    parts[#parts + 1] = key .. ":" .. val
  end
  return "{" .. table.concat(parts, ",") .. "}"
end

local function json_rival_event(trigger, state, party, details)
  local party_json = ""
  if party then
    local parts = {}
    for _, e in ipairs(party) do
      parts[#parts + 1] = json_party_entry(e)
    end
    party_json = ',"party":[' .. table.concat(parts, ",") .. ']'
  end

  local details_json = ""
  if details then
    details_json = ',"details":' .. json_kv_pairs(details)
  end

  return string.format(
    '{"trigger":"%s","game_state":%s%s%s}',
    json_escape(trigger),
    json_game_state(state),
    party_json,
    details_json
  )
end

local function post_rival_event(trigger, state, party, details)
  return post_json(
    "/rival-event",
    json_rival_event(trigger, state, party, details),
    '"action"',
    "rival-event",
    nil
  )
end

local function write_hex_to_rival_buffer(hex_text)
  if not hex_text or #hex_text < 2 or #hex_text % 2 ~= 0 or hex_text:match("[^0-9A-Fa-f]") then
    return false, "invalid message_hex"
  end

  local base = RIVAL_ENCOUNTER_BUFFER_ADDR
  local msg_addr = base + RIVAL_ENCOUNTER_OFFSET_MESSAGE
  local byte_count = math.min(#hex_text / 2, RIVAL_ENCOUNTER_MESSAGE_MAX)
  local wrote_eos = false

  -- Set magic so EnsureRivalEncounterInitialized in C doesn't reset our write.
  emu:write32(base, RIVAL_ENCOUNTER_MAGIC)

  for i = 1, byte_count do
    local hex_index = i * 2 - 1
    local value = tonumber(hex_text:sub(hex_index, hex_index + 1), 16)
    emu:write8(msg_addr + i - 1, value)
    if value == 0xFF then
      wrote_eos = true
      byte_count = i
      break
    end
  end

  if not wrote_eos and byte_count < RIVAL_ENCOUNTER_MESSAGE_MAX then
    emu:write8(msg_addr + byte_count, 0xFF)
    byte_count = byte_count + 1
  end

  emu:write8(base + RIVAL_ENCOUNTER_OFFSET_LENGTH, byte_count)
  -- Status flips last in the struct so the frame script never sees a partial msg.
  emu:write8(base + RIVAL_ENCOUNTER_OFFSET_STATUS, RIVAL_ENCOUNTER_STATUS_PENDING)

  -- Flip VAR_TEMP_0 = 1 to trigger the map_script_2 entry.
  local save_block_1 = emu:read32(SAVE_BLOCK_1_PTR)
  if save_block_1 == 0 or save_block_1 == 0xFFFFFFFF then
    return false, "SaveBlock1 not ready; rival message buffered but VAR_TEMP_0 unset"
  end
  emu:write16(save_block_1 + VAR_TEMP_0_OFFSET, 1)

  return true, "armed"
end

local function read_party_count()
  local save_block_1 = emu:read32(SAVE_BLOCK_1_PTR)
  if save_block_1 == 0 or save_block_1 == 0xFFFFFFFF then
    return nil
  end
  return emu:read8(save_block_1 + SAVE_BLOCK_1_OFFSET_PARTY_COUNT)
end

local function fire_rival_event(trigger, state, party, details)
  write_line(string.format(
    "RIVAL EVENT trigger=%s map=%d:%d pos=(%d,%d)",
    trigger, state.map_group, state.map_num, state.x, state.y
  ))
  -- Remember which trigger fired so the battle-entry watcher can tag the
  -- log with the right battle_id when the cinematic transitions to combat.
  last_rival_trigger = trigger
  local response, err = post_rival_event(trigger, state, party, details)
  if err then
    write_line("rival-event POST failed: " .. tostring(err))
    return
  end
  if response and #response > 0 then
    write_line(response)
  end
end

-- Writes counter_choice to gRivalAIBuffer.counterChoice without arming the
-- moveScore plan. The /rival-battle-plan POST at battle entry is responsible
-- for filling moveScore[] and flipping `active`. By writing counterChoice
-- now (Hours 5-6), the rival trainer-load script (which reads the byte via
-- GetRivalCounterChoice when the cinematic ends and the battle starts)
-- picks the right team-slot bucket (0-11 contract, see rival_counter.py).
-- We deliberately leave `active` alone — no move plan to apply yet.
local function write_counter_choice_only(counter_choice)
  if RIVAL_AI_BUFFER_ADDR == 0 then return false, "RIVAL_AI_BUFFER_ADDR unset" end
  emu:write32(RIVAL_AI_BUFFER_ADDR, RIVAL_AI_BUFFER_MAGIC)
  emu:write8(RIVAL_AI_BUFFER_ADDR + RIVAL_AI_OFF_COUNTER_CHOICE, counter_choice or 0)
  return true
end

-- ---------------------------------------------------------------------------
-- Smart Gary battle-state helpers (Phase 4 — addresses verified, polling off
-- by default, Edmund enables after live mGBA validation)
-- ---------------------------------------------------------------------------

local function read_battle_outcome()
  return emu:read8(BATTLE_OUTCOME_ADDR)
end

local function read_battler_attacker()
  return emu:read8(BATTLER_ATTACKER_ADDR)
end

local function read_current_move()
  return emu:read16(CURRENT_MOVE_ADDR)
end

local function read_player_chosen_move()
  -- gBattleStruct is itself a pointer; deref then add CHOSEN_MOVE_OFFSET.
  -- For player battler 0: chosenMovePositions[0] at offset 0x87.
  local battle_struct = emu:read32(BATTLE_STRUCT_PTR)
  if battle_struct == 0 or battle_struct == 0xFFFFFFFF then
    return nil
  end
  return emu:read8(battle_struct + CHOSEN_MOVE_OFFSET)
end

local function read_battle_mon(battler_id)
  local base = BATTLE_MONS_ADDR + battler_id * BATTLE_MON_STRIDE
  return {
    species  = emu:read16(base + BMON_SPECIES),
    hp       = emu:read16(base + BMON_HP),
    max_hp   = emu:read16(base + BMON_MAX_HP),
    level    = emu:read8(base + BMON_LEVEL),
    moves    = {
      emu:read16(base + BMON_MOVES + 0),
      emu:read16(base + BMON_MOVES + 2),
      emu:read16(base + BMON_MOVES + 4),
      emu:read16(base + BMON_MOVES + 6),
    },
    status1  = emu:read32(base + BMON_STATUS1),
  }
end

-- ---------------------------------------------------------------------------
-- Battle bridge POSTs — JSON builders
-- ---------------------------------------------------------------------------

local function json_battle_mon_state(mon)
  return string.format(
    '{"species":%d,"level":%d,"hp":%d,"max_hp":%d,"moves":[%d,%d,%d,%d]}',
    mon.species, mon.level, mon.hp, mon.max_hp,
    mon.moves[1], mon.moves[2], mon.moves[3], mon.moves[4]
  )
end

local function json_battle_log_entries(entries)
  local parts = {}
  for _, e in ipairs(entries) do
    local result_field = ""
    if e.result then
      result_field = string.format(',"result":"%s"', json_escape(e.result))
    end
    parts[#parts + 1] = string.format(
      '{"turn":%d,"side":"%s","actor_species":%d,"move":"%s"%s}',
      e.turn, e.side, e.actor_species, json_escape(e.move), result_field
    )
  end
  return "[" .. table.concat(parts, ",") .. "]"
end

local function json_battle_plan_request(battle_id, player_party, rival_party, state)
  local pp_parts = {}
  for _, m in ipairs(player_party or {}) do
    pp_parts[#pp_parts + 1] = json_battle_mon_state(m)
  end
  local rp_field = ""
  if rival_party then
    local rp_parts = {}
    for _, m in ipairs(rival_party) do
      rp_parts[#rp_parts + 1] = json_battle_mon_state(m)
    end
    rp_field = ',"rival_party":[' .. table.concat(rp_parts, ",") .. ']'
  end
  local state_field = ""
  if state then
    state_field = ',"game_state":' .. json_game_state(state)
  end
  return string.format(
    '{"battle_id":"%s","player_party":[%s]%s%s}',
    json_escape(battle_id),
    table.concat(pp_parts, ","),
    rp_field,
    state_field
  )
end

local function post_rival_battle_plan(battle_id, player_party, rival_party, state)
  return post_json(
    "/rival-battle-plan",
    json_battle_plan_request(battle_id, player_party, rival_party, state),
    '"counter_choice"',
    "rival-battle-plan",
    nil
  )
end

local function post_rival_battle_summary(battle_id, outcome, log_entries, state)
  local state_field = ""
  if state then
    state_field = ',"game_state":' .. json_game_state(state)
  end
  local body = string.format(
    '{"battle_id":"%s","outcome":"%s","battle_log":%s%s}',
    json_escape(battle_id),
    json_escape(outcome),
    json_battle_log_entries(log_entries),
    state_field
  )
  return post_json(
    "/rival-battle-summary",
    body,
    '"summary"',
    "rival-battle-summary",
    nil
  )
end

-- ---------------------------------------------------------------------------
-- Battle log accumulator helpers
-- ---------------------------------------------------------------------------

local function append_battle_log(side, actor_species, move_name, result)
  battle_log[#battle_log + 1] = {
    turn = current_turn,
    side = side,
    actor_species = actor_species,
    move = move_name,
    result = result,
  }
  write_line(string.format(
    "  T%d %s species=%d move=%s%s",
    current_turn, side:upper(), actor_species, move_name,
    result and (" → " .. result) or ""
  ))
end

local function reset_battle_state()
  in_battle = false
  current_battle_id = nil
  current_turn = 0
  battle_log = {}
  last_logged_player_move = -1
  last_logged_rival_move = -1
  last_outcome_seen = 0
  -- Drop any battle-plan POST that was queued for a battle that just ended
  -- before its retry window came up — stale and would confuse the bridge.
  deferred_battle_plan = nil
end

-- ---------------------------------------------------------------------------
-- Battle-state transition watcher — FRAMEWORK ONLY
--
-- This function detects (a) battle entry: outcome flips from any to 0
-- mid-frame, (b) battle exit: outcome was 0, becomes non-zero. It accumulates
-- a chess-style move log between those transitions.
--
-- IT IS NOT INVOKED FROM THE FRAME CALLBACK YET. To enable, flip
-- BATTLE_POLLING_ENABLED to true at the top of this file AND add a call to
-- check_battle_transitions() inside the frame callback (after
-- check_rival_triggers). See docs/HANDOFF_smart_gary.md.
-- ---------------------------------------------------------------------------
-- Try to fire a battle-plan POST. If `pending` is busy, stash the payload in
-- `deferred_battle_plan` and the frame callback will retry next frame.
local function fire_or_defer_battle_plan(battle_id, player_party, rival_party, state)
  if pending then
    deferred_battle_plan = {
      battle_id = battle_id,
      player_party = player_party,
      rival_party = rival_party,
      state = state,
    }
    write_line(string.format(
      "POST /rival-battle-plan deferred (pending=%s) id=%s",
      tostring(pending and pending.label or "?"), battle_id
    ))
    return
  end
  write_line(string.format(
    "POST /rival-battle-plan id=%s player_party=%d rival_active=%d",
    battle_id, #player_party, rival_party and #rival_party or 0
  ))
  local _, err = post_rival_battle_plan(battle_id, player_party, rival_party, state)
  if err then
    write_line("rival-battle-plan POST failed: " .. tostring(err))
  end
end

local function flush_deferred_battle_plan()
  if not deferred_battle_plan or pending then return end
  local d = deferred_battle_plan
  deferred_battle_plan = nil
  write_line(string.format(
    "POST /rival-battle-plan (retry) id=%s player_party=%d rival_active=%d",
    d.battle_id, #d.player_party, d.rival_party and #d.rival_party or 0
  ))
  local _, err = post_rival_battle_plan(d.battle_id, d.player_party, d.rival_party, d.state)
  if err then
    write_line("rival-battle-plan POST (retry) failed: " .. tostring(err))
  end
end

-- Returns true iff the rival side of the battle struct shows a loaded mon —
-- the most reliable signal that an actual battle (not just a stale outcome=0
-- byte on the overworld) is currently active.
local function rival_battler_is_loaded()
  local rival_lead_species = emu:read16(BATTLE_MONS_ADDR + BATTLE_MON_STRIDE + BMON_SPECIES)
  return rival_lead_species ~= 0
end

local function check_battle_transitions()
  -- NOTE: we deliberately do NOT early-return on `pending`. Hour 4b regression:
  -- a /game-state POST in flight during the player's lab-entry frame caused
  -- Battle 1 to skip its plan POST. The watcher must always update its state
  -- machine; only the outbound POST is gated (and deferred via
  -- `deferred_battle_plan` when pending is busy).

  local outcome = read_battle_outcome()

  if outcome ~= BATTLE_OUTCOME_IN_PROGRESS then
    if in_battle then
      -- EXIT — fire summary
      local outcome_label = "lost"
      if outcome == BATTLE_OUTCOME_WON then outcome_label = "won"
      elseif outcome == BATTLE_OUTCOME_RAN then outcome_label = "fled"
      end
      write_line(string.format(
        "BATTLE END: outcome=%d label=%s log_entries=%d",
        outcome, outcome_label, #battle_log
      ))
      if current_battle_id and #battle_log > 0 then
        post_rival_battle_summary(current_battle_id, outcome_label, battle_log, nil)
      end
      reset_battle_state()
    end
    last_outcome_seen = outcome
    return
  end

  -- outcome == 0. Bootstrap if not already in_battle. Hour 4b: require a
  -- secondary signal (rival battler loaded in gBattleMons[1]) so we don't
  -- false-positive on the overworld where outcome can also read 0.
  if not in_battle then
    if not rival_battler_is_loaded() then
      -- Still on overworld (or in pre-battle cinematic) — wait for the rival
      -- battler to materialise. Don't touch in_battle yet.
      return
    end

    local state = read_game_state()
    local sig = nil
    if state then
      sig = string.format("%d:%d", state.map_group, state.map_num)
      -- Trigger flag wins over map sig — Battle 2/3 can fire on any map,
      -- only Battle 1 (Oak's Lab) is map-determined. Once consumed, clear
      -- the flag so a later battle doesn't inherit it.
      if last_rival_trigger and BATTLE_ID_BY_TRIGGER[last_rival_trigger] then
        current_battle_id = BATTLE_ID_BY_TRIGGER[last_rival_trigger]
        last_rival_trigger = nil
      else
        current_battle_id = BATTLE_ID_BY_MAP_SIGNATURE[sig]
      end
    end
    if not current_battle_id then
      -- Battle is real but on a map we don't track. Still mark in_battle so
      -- exit detection works, but skip plan + summary POSTs.
      in_battle = true
      current_turn = 1
      battle_log = {}
      write_line(string.format("BATTLE START: id=<untracked> map=%s", tostring(sig)))
      return
    end

    in_battle = true
    current_turn = 1
    battle_log = {}
    write_line(string.format("BATTLE START: id=%s map=%s", current_battle_id, sig))

    -- Hour 4: gather both parties + POST /rival-battle-plan so the AI hook
    -- in BattleAI_ChooseMoveOrAction picks up the score boosts on Gary's
    -- first move. Player party comes from the live gPokelivePartyData
    -- struct (already populated by UpdateCodexPartyData when the rival
    -- battle script ran). Rival party is reconstructed from gBattleMons
    -- slots 1 and 3 — only the active mon is fully visible mid-battle, so
    -- the bridge plan reasons mostly off the player party + battle_id
    -- archetype.
    local player_party_full = read_party_data()
    local player_party_for_plan = {}
    if player_party_full then
      for _, e in ipairs(player_party_full) do
        player_party_for_plan[#player_party_for_plan + 1] = {
          species = e.species,
          level = e.level,
          hp = e.hp,
          max_hp = e.max_hp,
          moves = e.moves,
        }
      end
    else
      -- Fallback: use player active slot 0 from gBattleMons (now populated).
      local pm = read_battle_mon(0)
      if pm.species ~= 0 then
        player_party_for_plan[1] = pm
      end
    end

    local rival_party_for_plan = {}
    for _, slot in ipairs({1, 3}) do
      local rm = read_battle_mon(slot)
      if rm.species ~= 0 then
        rival_party_for_plan[#rival_party_for_plan + 1] = rm
      end
    end

    if #player_party_for_plan > 0 then
      fire_or_defer_battle_plan(
        current_battle_id,
        player_party_for_plan,
        #rival_party_for_plan > 0 and rival_party_for_plan or nil,
        state
      )
    else
      write_line("rival-battle-plan skipped: no player party data available")
    end
    return
  end

  -- Mid-battle: detect new player and opponent move selections.
  local attacker = read_battler_attacker()
  local current_move = read_current_move()

  if current_move ~= 0 then
    if is_player_battler(attacker) and current_move ~= last_logged_player_move then
      local mon = read_battle_mon(attacker)
      append_battle_log("player", mon.species, string.format("MOVE_%d", current_move), nil)
      last_logged_player_move = current_move
    elseif is_opponent_battler(attacker) and current_move ~= last_logged_rival_move then
      local mon = read_battle_mon(attacker)
      append_battle_log("rival", mon.species, string.format("MOVE_%d", current_move), nil)
      last_logged_rival_move = current_move
      current_turn = current_turn + 1  -- crude turn counter; refine when verified
    end
  end
end

-- ---------------------------------------------------------------------------
-- Hours 5-6 trigger detection
--
-- Two ONE-SHOT triggers — neither re-arms after firing within a Lua session:
--   first_capture:  1 → 2 party transition off Oak's Lab, then wait one tile
--                   of player movement before POSTing /rival-event.
--   second_capture: 2 → 3 party transition (any map), same 1-tile delay.
-- ---------------------------------------------------------------------------

local function check_rival_triggers()
  -- Read state every frame so tracking stays current even when we early-out.
  local state = read_game_state()
  if not state then return end

  local map_sig = string.format("%d:%d", state.map_group, state.map_num)
  local position_sig = string.format("%d:%d:%d:%d",
    state.map_group, state.map_num, state.x, state.y)
  local party_count = read_party_count()

  local previous_party_count = last_party_count
  local previous_position_sig = last_position_signature
  local previous_map_sig = last_map_signature

  -- Update tracking state up front — we never want a stale value to leak
  -- into a later frame's delta calculation.
  if party_count then
    last_party_count = party_count
  end
  last_position_signature = position_sig
  last_map_signature = map_sig

  -- Grace window prevents the baseline party read from false-firing on hot
  -- reload (you typically already have 1 mon when the script attaches).
  if frame_count < RIVAL_GRACE_FRAMES then return end

  -- ----- first_capture detector ---------------------------------------------
  if first_capture_state == "idle"
     and party_count
     and previous_party_count
     and previous_party_count == 1
     and party_count == 2
     and map_sig ~= OAKS_LAB_MAP_SIG
  then
    first_capture_state = "post_catch"
    first_capture_anchor_position = position_sig
    write_line(string.format(
      "first_capture armed: caught at %s — waiting one tile of movement",
      position_sig
    ))
  end

  if first_capture_state == "post_catch"
     and first_capture_anchor_position
     and previous_position_sig
     and position_sig ~= first_capture_anchor_position
  then
    -- Player moved one tile after the catch. Fire the cinematic.
    if pending then
      -- Don't lose the trigger — leave state armed; we'll retry next frame.
      return
    end
    first_capture_state = "fired"
    local party = read_party_data()
    fire_rival_event("first_capture", state, party, {
      anchor = first_capture_anchor_position,
    })
    return
  end

  -- ----- second_capture detector --------------------------------------------
  -- Same shape as first_capture but for the 2 → 3 transition (player's
  -- second wild catch — party total reaches 3). Fires anywhere.
  if second_capture_state == "idle"
     and party_count
     and previous_party_count
     and previous_party_count == 2
     and party_count == 3
  then
    second_capture_state = "post_catch"
    second_capture_anchor_position = position_sig
    write_line(string.format(
      "second_capture armed: 3rd mon obtained at %s — waiting one tile",
      position_sig
    ))
  end

  if second_capture_state == "post_catch"
     and second_capture_anchor_position
     and previous_position_sig
     and position_sig ~= second_capture_anchor_position
  then
    if pending then return end  -- leave armed; retry next frame
    second_capture_state = "fired"
    local party = read_party_data()
    fire_rival_event("second_capture", state, party, {
      anchor = second_capture_anchor_position,
    })
    return
  end
end

local function mark_mailbox_error(seq)
  emu:write16(mailbox_addr(OFFSET_ACK), seq)
  emu:write8(mailbox_addr(OFFSET_STATUS), MAILBOX_STATUS_ERROR)
end

local function mark_mailbox_response_ready(seq)
  emu:write16(mailbox_addr(OFFSET_ACK), seq)
  emu:write8(mailbox_addr(OFFSET_STATUS), MAILBOX_STATUS_RESPONSE_READY)
end

local function write_timeout_response(seq)
  write_hex_to_mailbox_response(TIMEOUT_RESPONSE_HEX)
  mark_mailbox_response_ready(seq)
end

local function poll_pending_response()
  if not pending then
    return
  end

  pending.client:poll()

  while true do
    local chunk, receive_error = pending.client:receive(4096)

    if chunk and #chunk > 0 then
      table.insert(pending.chunks, chunk)
    elseif receive_error and not is_temporary_socket_error(receive_error) then
      local partial = table.concat(pending.chunks)
      if partial:find(pending.success_marker, 1, true) then
        break
      end
      write_line("receive failed: " .. tostring(receive_error))
      if pending.label == "codex-chat" then
        mark_mailbox_error(pending.seq)
      end
      pending = nil
      return
    else
      break
    end
  end

  local response = table.concat(pending.chunks)
  if response:find(pending.success_marker, 1, true) then
    if pending.label == "codex-chat" then
      local message_hex = extract_json_field(response, "message_hex")
      local ok, reason = write_hex_to_mailbox_response(message_hex)
      if ok then
        mark_mailbox_response_ready(pending.seq)
        write_line(string.format("Professor Codex response written to mailbox seq=%d.", pending.seq))
      else
        write_line("Codex mailbox write failed: " .. tostring(reason))
        mark_mailbox_error(pending.seq)
      end
    elseif pending.label == "rival-event" then
      local message_hex = extract_json_field(response, "message_hex")
      -- counter_choice is populated for first_capture / second_capture setup
      -- triggers; absent (or null) for the legacy event types. When present,
      -- write it to gRivalAIBuffer.counterChoice BEFORE arming the cinematic
      -- so the rival battle script reads the correct value if the player
      -- engages immediately.
      local counter_choice = extract_json_int(response, "counter_choice")
      if counter_choice then
        local ok_cc, reason_cc = write_counter_choice_only(counter_choice)
        if ok_cc then
          write_line(string.format(
            "Rival counter_choice=%d written to gRivalAIBuffer", counter_choice
          ))
        else
          write_line("counter_choice write failed: " .. tostring(reason_cc))
        end
      end
      local ok, reason = write_hex_to_rival_buffer(message_hex)
      if ok then
        write_line("Rival encounter armed: " .. tostring(reason))
      else
        write_line("Rival encounter arm failed: " .. tostring(reason))
      end
    elseif pending.label == "rival-battle-plan" then
      local move_scores = extract_json_int_array(response, "move_scores")
      local counter_choice = extract_json_int(response, "counter_choice")
      local opening_taunt = extract_json_field(response, "opening_taunt")
      local strategy_summary = extract_json_field(response, "strategy_summary")
      if move_scores and #move_scores >= 4 then
        local ok, reason = write_rival_ai_plan(move_scores, counter_choice)
        if ok then
          write_line(string.format(
            "Smart Gary plan armed: counter=%d scores=[%d,%d,%d,%d]",
            counter_choice or 0,
            move_scores[1], move_scores[2], move_scores[3], move_scores[4]
          ))
        else
          write_line("Smart Gary plan arm failed: " .. tostring(reason))
        end
      else
        write_line("rival-battle-plan: missing or short move_scores in response")
      end
      -- Hour 4 (Option B): print Gary's opening taunt to the script panel so
      -- the judge can see/narrate it. Routing through gRivalEncounterBuffer
      -- isn't viable mid-battle (the encounter cinematic only fires from a
      -- map_script_2 frame handler on the overworld, not inside a battle).
      if opening_taunt and #opening_taunt > 0 then
        write_line('Gary opening taunt: "' .. opening_taunt .. '"')
      end
      if strategy_summary and #strategy_summary > 0 then
        write_line("Gary strategy: " .. strategy_summary)
      end
    elseif pending.label == "rival-battle-summary" then
      write_line("Battle summary acknowledged by bridge.")
    end
    pending = nil
    return
  end

  if os.time() - pending.started_at > RESPONSE_TIMEOUT_SECONDS then
    if #response > 0 then
      write_line("partial response at timeout: " .. response)
    else
      write_line("response timed out after " .. RESPONSE_TIMEOUT_SECONDS .. "s. Is FastAPI still running?")
    end
    if pending.label == "codex-chat" then
      write_timeout_response(pending.seq)
    end
    pending = nil
  end
end

local function poll_codex_mailbox()
  if pending or not mailbox_is_configured() then
    return
  end

  local status = emu:read8(mailbox_addr(OFFSET_STATUS))
  if status ~= MAILBOX_STATUS_PENDING then
    return
  end

  local seq = emu:read16(mailbox_addr(OFFSET_SEQ))
  if last_seq == seq then
    return
  end

  local command = read_fire_red_string(mailbox_addr(OFFSET_COMMAND), CODEX_INPUT_LENGTH + 1)
  if command == "" then
    command = "What should I do next."
  end

  local state, read_error = read_game_state()
  if not state then
    write_line(read_error)
    return
  end

  write_line(string.format('POST /codex-chat mailbox_seq=%d message="%s"', seq, command))
  last_seq = seq

  local response, post_error = post_codex_chat(command, state, seq)
  if post_error then
    write_line(post_error)
    mark_mailbox_error(seq)
    return
  end

  if response and #response > 0 then
    write_line(response)
  end
end

write_line("PokeLive Codex mailbox bridge loaded.")
write_line("Start FastAPI first: cd bridge && ./run.sh")
write_line("Use this with the patched pret/pokefirered ROM, not the runtime textbox-injection demo.")

callbacks:add("frame", function()
  frame_count = frame_count + 1
  poll_pending_response()
  poll_codex_mailbox()
  check_rival_triggers()
  if BATTLE_POLLING_ENABLED then
    check_battle_transitions()
    -- Hour 4b: if a battle-plan POST got deferred because another request
    -- was in flight at battle-start time, retry as soon as `pending` clears.
    flush_deferred_battle_plan()
  end
end)
