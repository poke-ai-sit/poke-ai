Route1_MapScripts::
	map_script MAP_SCRIPT_ON_LOAD, Route1_OnLoad
	map_script MAP_SCRIPT_ON_FRAME_TABLE, Route1_OnFrame
	.byte 0

@ Always hide the proactive AI rival on map enter so existing battery saves
@ from before this feature was added still load cleanly.
Route1_OnLoad::
	setflag FLAG_HIDE_ROUTE1_AI_RIVAL
	end

Route1_OnFrame::
	map_script_2 VAR_TEMP_0, 1, Route1_EventScript_AIRivalEncounter
	.2byte 0

@ PokeLive Smart Gary AI Rival — Battle 2 cinematic.
@ Lua sets VAR_TEMP_0=1 after the player's first capture (anywhere).
@ The rival warps in adjacent to the player (right side), takes a single
@ step toward them, delivers the GPT taunt, and battles using the
@ Lua-selected counter team.
Route1_EventScript_AIRivalEncounter::
	lockall
	call EventScript_AIRivalPhoneCall
	getplayerxy VAR_0x8004, VAR_0x8005
	addvar VAR_0x8004, 2
	setobjectxyperm LOCALID_ROUTE1_AI_RIVAL, VAR_0x8004, VAR_0x8005
	setobjectmovementtype LOCALID_ROUTE1_AI_RIVAL, MOVEMENT_TYPE_FACE_LEFT
	playse SE_WARP_IN
	addobject LOCALID_ROUTE1_AI_RIVAL
	applymovement LOCALID_ROUTE1_AI_RIVAL, Route1_Movement_AIRivalApproach
	waitmovement 0
	call EventScript_AIRivalEncounterCinematic
	removeobject LOCALID_ROUTE1_AI_RIVAL
	setflag FLAG_HIDE_ROUTE1_AI_RIVAL
	setvar VAR_TEMP_0, 0
	releaseall
	end

Route1_Movement_AIRivalApproach::
	walk_left
	step_end

Route1_EventScript_MartClerk::
	lock
	faceplayer
	goto_if_set FLAG_GOT_POTION_ON_ROUTE_1, Route1_EventScript_AlreadyGotPotion
	msgbox Route1_Text_WorkAtPokeMartTakeSample
	textcolor NPC_TEXT_COLOR_NEUTRAL
	checkitemspace ITEM_POTION
	goto_if_eq VAR_RESULT, FALSE, EventScript_BagIsFull
	bufferitemname STR_VAR_2, ITEM_POTION
	playfanfare MUS_LEVEL_UP
	message Text_ObtainedTheX
	waitmessage
	waitfanfare
	additem ITEM_POTION
	msgbox Route1_Text_PutPotionAway
	call EventScript_RestorePrevTextColor
	setflag FLAG_GOT_POTION_ON_ROUTE_1
	release
	end

Route1_EventScript_AlreadyGotPotion::
	msgbox Route1_Text_ComeSeeUsIfYouNeedPokeBalls
	release
	end

Route1_EventScript_Boy::
	msgbox Route1_Text_CanJumpFromLedges, MSGBOX_NPC
	end

Route1_EventScript_RouteSign::
	msgbox Route1_Text_RouteSign, MSGBOX_SIGN
	end
