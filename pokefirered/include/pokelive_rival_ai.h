#ifndef GUARD_POKELIVE_RIVAL_AI_H
#define GUARD_POKELIVE_RIVAL_AI_H

#define POKELIVE_RIVAL_AI_BUFFER_MAGIC 0x52414942  /* "RAIB" */

#define POKELIVE_RIVAL_OVERRIDE_MAX 6

/* One slot in the runtime-constructed rival party. The bridge picks the
 * species + level + moves at /rival-event time based on the player's
 * current party; Lua writes this struct into gRivalAIBuffer.partyOverride
 * before flipping VAR_TEMP_0 to fire the encounter script. The C-side hook
 * in CreateNPCTrainerParty then materialises gEnemyParty[i] from these
 * fields, replacing whatever the base trainer's static party contained. */
struct PokeliveRivalPartySlot
{
    u16 species;
    u8  level;
    u8  pad;
    u16 moves[4];
};

/* Layout-locked. The Lua bridge writes into this struct by absolute
 * offset, so the offsets here must match the constants in
 * codex_mailbox_bridge.lua. We force partyOverride to start at a 4-byte
 * aligned offset (16) by inserting a u32 sentinel at offset 12. Lua
 * reads partyMagic before writing slots; if it sees anything other
 * than POKELIVE_PARTY_MAGIC, the struct shifted under it (e.g. someone
 * reordered fields without updating the Lua offsets) and we surface a
 * loud "STRUCT MISMATCH" error instead of writing into the wrong byte. */
#define POKELIVE_RIVAL_PARTY_SENTINEL 0xCAFEBABE

struct PokeliveRivalAIBuffer
{
    u32 magic;                    /* offset  0..3  — buffer-init marker  */
    u8  active;                   /* offset  4     — battle-AI move plan */
    s8  moveScore[4];             /* offset  5..8  */
    u8  counterChoice;            /* offset  9     */
    u8  resultPending;            /* offset 10     */
    u8  partyOverrideCount;       /* offset 11     — 0=no override; 1..6=use partyOverride[] */
    u32 partyMagic;               /* offset 12..15 — alignment + sentinel for Lua verify */
    /* offset 16: struct partyOverride[6], 12 bytes per slot, 72 bytes total */
    struct PokeliveRivalPartySlot partyOverride[POKELIVE_RIVAL_OVERRIDE_MAX];
};

extern struct PokeliveRivalAIBuffer gRivalAIBuffer;

/* Battle-engine hook (battle_main.c CreateNPCTrainerParty): if
 * partyOverrideCount > 0, wipe gEnemyParty and reconstruct from the
 * override slots. Consumes the override so a follow-up battle doesn't
 * reuse stale data. */
void ApplyPokeliveRivalPartyOverride(struct Pokemon *party);

/* Refreshes gPokelivePartyData (the EWRAM buffer Lua reads via
 * read_party_data) from the live gPlayerParty[]. Hooked into
 * GiveMonToPlayer so the bridge sees the player's just-caught mon
 * the first time Lua POSTs /rival-event after a catch — without it,
 * the buffer is whatever the last `special` left and the picker falls
 * to defaults. */
void UpdateCodexPartyData(void);

#endif // GUARD_POKELIVE_RIVAL_AI_H
