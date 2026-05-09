-- give_pokeballs.lua
-- Writes 10 Poke Balls to bag slot 0 of the Poke Balls pocket in SaveBlock1.
-- Load once from mGBA scripting console (Tools -> Scripting).
-- Safe: only writes to known offsets, does not affect party or ROM.

local SAVE_BLOCK_1_PTR     = 0x03005008
local POKEBALLS_PKT_OFFSET = 0x3B8   -- bagPocket_PokeBalls in SaveBlock1 (FireRed USA v1.0)
local ITEM_POKE_BALL       = 4       -- ITEM_POKE_BALL id in FireRed item table
local QTY                  = 10

local sb1 = emu:read32(SAVE_BLOCK_1_PTR)

if sb1 == 0 or sb1 == 0xFFFFFFFF then
    console:log("SaveBlock1 not ready — load your save first.")
    return
end

-- Slot 0 of Poke Balls pocket: 2 bytes item ID + 2 bytes quantity
emu:write16(sb1 + POKEBALLS_PKT_OFFSET,     ITEM_POKE_BALL)
emu:write16(sb1 + POKEBALLS_PKT_OFFSET + 2, QTY)

-- Read back to verify
local check_id  = emu:read16(sb1 + POKEBALLS_PKT_OFFSET)
local check_qty = emu:read16(sb1 + POKEBALLS_PKT_OFFSET + 2)

if check_id == ITEM_POKE_BALL and check_qty == QTY then
    console:log(string.format("Done: Poke Ball x%d written to bag (SaveBlock1=0x%08X + 0x%03X).", QTY, sb1, POKEBALLS_PKT_OFFSET))
    console:log("Open your bag in-game to confirm. If nothing shows, the offset needs adjustment.")
else
    console:log(string.format("Write mismatch — read back id=%d qty=%d. Offset may be wrong.", check_id, check_qty))
end
