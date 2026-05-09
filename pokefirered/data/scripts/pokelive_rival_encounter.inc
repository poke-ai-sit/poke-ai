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
@ counter_choice encoding (0..17):
@   counter_choice = starter_idx (0..2) * 3 + caught_idx (0..2)
@   starter_idx: 0=rival CHAR (player Bulba), 1=rival SQUIRT (player Char), 2=rival BULBA (player Squirt)
@   caught_idx:  0=anti-Flying, 1=anti-Normal, 2=Default (mixed)
@   B2 = 0..8, B3 = 9..17
EventScript_AIRivalDispatchTrainerBattle::
	special GetAIRivalCounterChoice
	switch VAR_RESULT
	case 0,  EventScript_AIRivalBattleB2_Char_F
	case 1,  EventScript_AIRivalBattleB2_Char_N
	case 2,  EventScript_AIRivalBattleB2_Char_X
	case 3,  EventScript_AIRivalBattleB2_Squirt_F
	case 4,  EventScript_AIRivalBattleB2_Squirt_N
	case 5,  EventScript_AIRivalBattleB2_Squirt_X
	case 6,  EventScript_AIRivalBattleB2_Bulba_F
	case 7,  EventScript_AIRivalBattleB2_Bulba_N
	case 8,  EventScript_AIRivalBattleB2_Bulba_X
	case 9,  EventScript_AIRivalBattleB3_Char_F
	case 10, EventScript_AIRivalBattleB3_Char_N
	case 11, EventScript_AIRivalBattleB3_Char_X
	case 12, EventScript_AIRivalBattleB3_Squirt_F
	case 13, EventScript_AIRivalBattleB3_Squirt_N
	case 14, EventScript_AIRivalBattleB3_Squirt_X
	case 15, EventScript_AIRivalBattleB3_Bulba_F
	case 16, EventScript_AIRivalBattleB3_Bulba_N
	case 17, EventScript_AIRivalBattleB3_Bulba_X
	@ Fallback for unexpected counterChoice — default to Battle 2 Bulba_X.
	goto EventScript_AIRivalBattleB2_Bulba_X

EventScript_AIRivalBattleB2_Char_F::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_CHAR_F, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Char_N::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_CHAR_N, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Char_X::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_CHAR_X, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Squirt_F::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_SQUIRT_F, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Squirt_N::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_SQUIRT_N, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Squirt_X::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_SQUIRT_X, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Bulba_F::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_BULBA_F, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Bulba_N::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_BULBA_N, Text_RivalVictory
	return
EventScript_AIRivalBattleB2_Bulba_X::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B2_BULBA_X, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Char_F::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_CHAR_F, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Char_N::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_CHAR_N, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Char_X::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_CHAR_X, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Squirt_F::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_SQUIRT_F, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Squirt_N::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_SQUIRT_N, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Squirt_X::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_SQUIRT_X, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Bulba_F::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_BULBA_F, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Bulba_N::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_BULBA_N, Text_RivalVictory
	return
EventScript_AIRivalBattleB3_Bulba_X::
	trainerbattle_no_intro TRAINER_AI_RIVAL_B3_BULBA_X, Text_RivalVictory
	return

PokeLive_Text_AIRivalProactive:
	.string "{STR_VAR_1}$"
