#include "global.h"
#include "characters.h"
#include "constants/pokemon.h"
#include "event_data.h"
#include "naming_screen.h"
#include "overworld.h"
#include "pokemon.h"
#include "pokelive_rival_ai.h"
#include "script.h"
#include "string_util.h"

#define POKELIVE_CODEX_MAILBOX_MAGIC 0x58454443
#define CODEX_RESPONSE_LENGTH 256

enum
{
    CODEX_MAILBOX_STATUS_IDLE,
    CODEX_MAILBOX_STATUS_PENDING,
    CODEX_MAILBOX_STATUS_RESPONSE_READY,
    CODEX_MAILBOX_STATUS_ERROR,
};

struct PokeliveCodexMailbox
{
    u32 magic;
    u16 seq;
    u16 ack;
    u8 status;
    u8 reserved;
    u16 commandLength;
    u16 responseLength;
    u8 command[CODEX_INPUT_LENGTH + 1];
    u8 response[CODEX_RESPONSE_LENGTH + 1];
};

#define POKELIVE_PARTY_MAGIC    0x50415254  /* "PART" */
#define POKELIVE_ENTRY_MAGIC    0x5054      /* "PT" */
#define POKELIVE_PARTY_MOVES    4

/* Proactive rival encounter (separate from codex mailbox / battle AI rival).
 * Lua writes a GPT-generated message into this buffer and flips status to
 * APPROACH_PENDING; a per-map MAP_SCRIPT_ON_FRAME_TABLE entry detects
 * VAR_TEMP_0 == 1 (set by Lua alongside the buffer write) and runs the
 * encounter script. The encounter script copies the buffered message into
 * gStringVar1 via BufferRivalMessage, displays it, and clears state.
 */
#define POKELIVE_RIVAL_ENCOUNTER_MAGIC 0x52454E43  /* "RENC" */
#define RIVAL_ENCOUNTER_MESSAGE_LENGTH 200

enum
{
    RIVAL_ENCOUNTER_STATUS_IDLE,
    RIVAL_ENCOUNTER_STATUS_APPROACH_PENDING,
};

struct PokeliveRivalEncounter
{
    u32 magic;
    u8  status;
    u8  messageLength;
    u8  pad[2];
    u8  message[RIVAL_ENCOUNTER_MESSAGE_LENGTH];
};

struct PokelivePartyEntry
{
    u16 magic;
    u16 species;
    u16 level;
    u16 hp;
    u16 maxHP;
    u16 moves[POKELIVE_PARTY_MOVES];
    u16 attack;
    u16 defense;
    u16 speed;
    u16 spAttack;
    u16 spDefense;
};

struct PokelivePartyData
{
    u32 magic;
    u8  count;
    u8  pad[3];
    struct PokelivePartyEntry entries[PARTY_SIZE];
};

static EWRAM_DATA u8 sCodexPromptBuffer[CODEX_INPUT_LENGTH + 1] = {0};
EWRAM_DATA struct PokeliveCodexMailbox gPokeliveCodexMailbox = {0};
EWRAM_DATA struct PokelivePartyData gPokelivePartyData = {0};
EWRAM_DATA struct PokeliveRivalEncounter gRivalEncounterBuffer = {0};
EWRAM_DATA struct PokeliveRivalAIBuffer gRivalAIBuffer = {0};

static const u8 sCodexAdvicePrompt[] = _("What should I do next.");
static const u8 sCodexEvolvePrompt[] = _("Evolve my custom Pokemon.");

/* Forward declarations */
void PublishCodexPrompt(void);

void UpdateCodexPartyData(void)
{
    u8 i;
    u8 count = gPlayerPartyCount;

    if (count > PARTY_SIZE)
        count = PARTY_SIZE;

    gPokelivePartyData.magic = POKELIVE_PARTY_MAGIC;
    gPokelivePartyData.count = count;

    for (i = 0; i < PARTY_SIZE; i++)
    {
        struct PokelivePartyEntry *e = &gPokelivePartyData.entries[i];

        if (i < count)
        {
            e->magic    = POKELIVE_ENTRY_MAGIC;
            e->species  = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_SPECIES);
            e->level    = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_LEVEL);
            e->hp       = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_HP);
            e->maxHP    = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_MAX_HP);
            e->moves[0] = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_MOVE1);
            e->moves[1] = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_MOVE2);
            e->moves[2] = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_MOVE3);
            e->moves[3] = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_MOVE4);
            e->attack   = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_ATK);
            e->defense  = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_DEF);
            e->speed    = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_SPEED);
            e->spAttack = (u16)GetMonData2(&gPlayerParty[i], MON_DATA_SPATK);
            e->spDefense= (u16)GetMonData2(&gPlayerParty[i], MON_DATA_SPDEF);
        }
        else
        {
            u8 j;
            u8 *p = (u8 *)e;
            for (j = 0; j < sizeof(struct PokelivePartyEntry); j++)
                p[j] = 0;
        }
    }
}

static void EnsureCodexMailboxInitialized(void)
{
    if (gPokeliveCodexMailbox.magic == POKELIVE_CODEX_MAILBOX_MAGIC)
        return;

    gPokeliveCodexMailbox.magic = POKELIVE_CODEX_MAILBOX_MAGIC;
    gPokeliveCodexMailbox.seq = 0;
    gPokeliveCodexMailbox.ack = 0;
    gPokeliveCodexMailbox.status = CODEX_MAILBOX_STATUS_IDLE;
    gPokeliveCodexMailbox.commandLength = 0;
    gPokeliveCodexMailbox.responseLength = 0;
}

static void CB2_PublishCodexPromptAndReturn(void)
{
    PublishCodexPrompt();
    SetMainCallback2(CB2_ReturnToFieldContinueScript);
}

void StartCodexPrompt(void)
{
    sCodexPromptBuffer[0] = EOS;
    DoNamingScreen(NAMING_SCREEN_CODEX, sCodexPromptBuffer, 0, 0, 0, CB2_PublishCodexPromptAndReturn);
    ScriptContext_Stop();
}

void BufferCodexPrompt(void)
{
    if (sCodexPromptBuffer[0] == EOS)
        gStringVar1[0] = EOS;
    else
        StringCopy(gStringVar1, sCodexPromptBuffer);
}

static u16 CopyCodexString(u8 *dest, const u8 *src, u16 maxLen)
{
    u16 i;

    for (i = 0; i < maxLen && src[i] != EOS; i++)
        dest[i] = src[i];

    dest[i] = EOS;
    return i;
}

static void PublishCodexCommand(const u8 *command)
{
    EnsureCodexMailboxInitialized();
    gPokeliveCodexMailbox.commandLength = CopyCodexString(
        gPokeliveCodexMailbox.command,
        command,
        CODEX_INPUT_LENGTH);
    gPokeliveCodexMailbox.responseLength = 0;
    gPokeliveCodexMailbox.response[0] = EOS;
    gPokeliveCodexMailbox.seq++;
    gPokeliveCodexMailbox.status = CODEX_MAILBOX_STATUS_PENDING;
}

void PublishCodexAdvicePrompt(void)
{
    UpdateCodexPartyData();
    PublishCodexCommand(sCodexAdvicePrompt);
}

void PublishCodexPrompt(void)
{
    if (sCodexPromptBuffer[0] == EOS)
        PublishCodexCommand(sCodexAdvicePrompt);
    else
        PublishCodexCommand(sCodexPromptBuffer);
}

void PublishCodexEvolvePrompt(void)
{
    PublishCodexCommand(sCodexEvolvePrompt);
}

void IsCodexResponseReady(void)
{
    EnsureCodexMailboxInitialized();
    gSpecialVar_Result =
        gPokeliveCodexMailbox.status == CODEX_MAILBOX_STATUS_RESPONSE_READY
     && gPokeliveCodexMailbox.ack == gPokeliveCodexMailbox.seq;
}

void BufferCodexResponse(void)
{
    EnsureCodexMailboxInitialized();
    if (gPokeliveCodexMailbox.response[0] == EOS)
        gStringVar1[0] = EOS;
    else
        StringCopy(gStringVar1, gPokeliveCodexMailbox.response);
    gPokeliveCodexMailbox.status = CODEX_MAILBOX_STATUS_IDLE;
}

static void EnsureRivalEncounterInitialized(void)
{
    if (gRivalEncounterBuffer.magic == POKELIVE_RIVAL_ENCOUNTER_MAGIC)
        return;

    gRivalEncounterBuffer.magic = POKELIVE_RIVAL_ENCOUNTER_MAGIC;
    gRivalEncounterBuffer.status = RIVAL_ENCOUNTER_STATUS_IDLE;
    gRivalEncounterBuffer.messageLength = 0;
    gRivalEncounterBuffer.message[0] = EOS;
}

void IsRivalEncounterPending(void)
{
    EnsureRivalEncounterInitialized();
    gSpecialVar_Result =
        gRivalEncounterBuffer.status == RIVAL_ENCOUNTER_STATUS_APPROACH_PENDING;
}

void BufferRivalMessage(void)
{
    EnsureRivalEncounterInitialized();
    if (gRivalEncounterBuffer.message[0] == EOS)
        gStringVar1[0] = EOS;
    else
        StringCopy(gStringVar1, gRivalEncounterBuffer.message);
    gRivalEncounterBuffer.status = RIVAL_ENCOUNTER_STATUS_IDLE;
}

void EvolveCustomPokemon(void)
{
    u16 species;
    u16 newSpecies;
    int i;

    for (i = 0; i < gPlayerPartyCount; i++)
    {
        species = GetMonData(&gPlayerParty[i], MON_DATA_SPECIES, NULL);
        if (species == SPECIES_CHARMANDER)
        {
            newSpecies = SPECIES_CHARMELEON;
            SetMonData(&gPlayerParty[i], MON_DATA_SPECIES, &newSpecies);
            CalculateMonStats(&gPlayerParty[i]);
            gSpecialVar_Result = TRUE;
            return;
        }
    }
    gSpecialVar_Result = FALSE;
}
