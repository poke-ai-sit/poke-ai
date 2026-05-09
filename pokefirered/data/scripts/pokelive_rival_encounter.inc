@ PokeLive Smart Gary AI Rival — shared cinematic + trainer-battle dispatch.
@
@ Per-map MAP_SCRIPT_ON_FRAME_TABLE entries detect VAR_TEMP_0 == 1 (set by Lua
@ alongside the gRivalEncounterBuffer.message write) and run a small per-map
@ wrapper that places + spawns the rival sprite, walks it adjacent to the
@ player, then calls EventScript_AIRivalEncounterCinematic below to deliver
@ the GPT taunt and dispatch the correct trainer battle.
@
@ Battle 2 (Lua sets counterChoice 0..5) fires on Route 1 / Route 2.
@ Battle 3 (Lua sets counterChoice 6..11) fires inside Pewter City Gym.
@ Pallet Town keeps its original Phase-3 cinematic (no battle, just msgbox).

EventScript_AIRivalEncounterCinematic::
	special BufferRivalMessage
	msgbox PokeLive_Text_AIRivalProactive, MSGBOX_DEFAULT
	call EventScript_AIRivalDispatchTrainerBattle
	return

@ Hours 5-6 — Pokegear-style call narration that runs BEFORE the rival
@ warps in. Cycles three short pages through gStringVar1 (one msgbox label
@ reused, since gStringVar2/3 are only 20 bytes). Each page is its own
@ click-to-advance textbox. Lua writes the three page strings into
@ gRivalEncounterBuffer.callPages[0..2] alongside the in-person message
@ when the /rival-event response comes back.
EventScript_AIRivalPhoneCall::
	playse SE_PC_LOGIN
	special ResetRivalCallPageIndex
	special BufferRivalCallNextPage
	msgbox PokeLive_Text_AIRivalProactive, MSGBOX_DEFAULT
	special BufferRivalCallNextPage
	msgbox PokeLive_Text_AIRivalProactive, MSGBOX_DEFAULT
	special BufferRivalCallNextPage
	msgbox PokeLive_Text_AIRivalProactive, MSGBOX_DEFAULT
	return

@ Reads gRivalAIBuffer.counterChoice → VAR_RESULT (0..11) and runs the
@ matching trainer battle. Falls through to balanced variants on any
@ unexpected value so the cinematic never hangs.
EventScript_AIRivalDispatchTrainerBattle::
	special GetAIRivalCounterChoice
	switch VAR_RESULT
	case 0,  EventScript_AIRivalBattleB2AntiFire
	case 1,  EventScript_AIRivalBattleB2AntiWater
	case 2,  EventScript_AIRivalBattleB2AntiGrass
	case 3,  EventScript_AIRivalBattleB2AntiFlying
	case 4,  EventScript_AIRivalBattleB2AntiBug
	case 5,  EventScript_AIRivalBattleB2Balanced
	case 6,  EventScript_AIRivalBattleB3AntiFire
	case 7,  EventScript_AIRivalBattleB3AntiWater
	case 8,  EventScript_AIRivalBattleB3AntiGrass
	case 9,  EventScript_AIRivalBattleB3AntiFlying
	case 10, EventScript_AIRivalBattleB3AntiBug
	case 11, EventScript_AIRivalBattleB3Balanced
	@ Fallback for unexpected counterChoice — pick a sensible default per tier.
	goto EventScript_AIRivalBattleB2Balanced

EventScript_AIRivalBattleB2AntiFire::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_ANTI_FIRE, Text_RivalVictory
	return

EventScript_AIRivalBattleB2AntiWater::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_ANTI_WATER, Text_RivalVictory
	return

EventScript_AIRivalBattleB2AntiGrass::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_ANTI_GRASS, Text_RivalVictory
	return

EventScript_AIRivalBattleB2AntiFlying::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_ANTI_FLYING, Text_RivalVictory
	return

EventScript_AIRivalBattleB2AntiBug::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_ANTI_BUG, Text_RivalVictory
	return

EventScript_AIRivalBattleB2Balanced::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_BALANCED, Text_RivalVictory
	return

EventScript_AIRivalBattleB3AntiFire::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_ANTI_FIRE, Text_RivalVictory
	return

EventScript_AIRivalBattleB3AntiWater::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_ANTI_WATER, Text_RivalVictory
	return

EventScript_AIRivalBattleB3AntiGrass::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_ANTI_GRASS, Text_RivalVictory
	return

EventScript_AIRivalBattleB3AntiFlying::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_ANTI_FLYING, Text_RivalVictory
	return

EventScript_AIRivalBattleB3AntiBug::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_ANTI_BUG, Text_RivalVictory
	return

EventScript_AIRivalBattleB3Balanced::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_BALANCED, Text_RivalVictory
	return

PokeLive_Text_AIRivalProactive:
	.string "{STR_VAR_1}$"
