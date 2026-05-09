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

struct PokeliveRivalAIBuffer
{
    u32 magic;
    u8  active;
    s8  moveScore[4];
    u8  counterChoice;       /* legacy field, still readable by GetAIRivalCounterChoice */
    u8  resultPending;
    u8  partyOverrideCount;  /* 0 = no override, 1..6 = use partyOverride[] */
    u8  pad[2];
    struct PokeliveRivalPartySlot partyOverride[POKELIVE_RIVAL_OVERRIDE_MAX];
};

extern struct PokeliveRivalAIBuffer gRivalAIBuffer;

/* Battle-engine hook (battle_main.c CreateNPCTrainerParty): if
 * partyOverrideCount > 0, wipe gEnemyParty and reconstruct from the
 * override slots. Consumes the override so a follow-up battle doesn't
 * reuse stale data. */
void ApplyPokeliveRivalPartyOverride(struct Pokemon *party);

#endif // GUARD_POKELIVE_RIVAL_AI_H
