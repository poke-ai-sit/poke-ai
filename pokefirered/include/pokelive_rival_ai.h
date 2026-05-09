#ifndef GUARD_POKELIVE_RIVAL_AI_H
#define GUARD_POKELIVE_RIVAL_AI_H

#define POKELIVE_RIVAL_AI_BUFFER_MAGIC 0x52414942  /* "RAIB" */

struct PokeliveRivalAIBuffer
{
    u32 magic;
    u8  active;
    s8  moveScore[4];
    u8  counterChoice;
    u8  resultPending;
    u8  pad;
};

extern struct PokeliveRivalAIBuffer gRivalAIBuffer;

#endif // GUARD_POKELIVE_RIVAL_AI_H
