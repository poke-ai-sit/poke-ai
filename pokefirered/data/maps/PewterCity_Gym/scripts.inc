PewterCity_Gym_MapScripts::
	map_script MAP_SCRIPT_ON_LOAD, PewterCity_Gym_OnLoad
	map_script MAP_SCRIPT_ON_FRAME_TABLE, PewterCity_Gym_OnFrame
	.byte 0

PewterCity_Gym_OnLoad::
	setflag FLAG_HIDE_PEWTER_GYM_AI_RIVAL
	end

PewterCity_Gym_OnFrame::
	map_script_2 VAR_TEMP_0, 1, PewterCity_Gym_EventScript_AIRivalEncounter
	.2byte 0

@ PokeLive Smart Gary AI Rival — Battle 3 cinematic.
@ Lua sets VAR_TEMP_0=1 after the player has taken 3 steps inside the gym.
@ Rival warps in 2 tiles below+right of the player, walks 2 tiles toward them,
@ delivers the GPT taunt, and battles using the Lua-selected counter team.
@ Brock is untouched — the player continues to the gym leader normally.
PewterCity_Gym_EventScript_AIRivalEncounter::
	lockall
	call EventScript_AIRivalPhoneCall
	getplayerxy VAR_0x8004, VAR_0x8005
	addvar VAR_0x8005, 2
	setobjectxyperm LOCALID_PEWTER_GYM_AI_RIVAL, VAR_0x8004, VAR_0x8005
	setobjectmovementtype LOCALID_PEWTER_GYM_AI_RIVAL, MOVEMENT_TYPE_FACE_UP
	playse SE_WARP_IN
	addobject LOCALID_PEWTER_GYM_AI_RIVAL
	applymovement LOCALID_PEWTER_GYM_AI_RIVAL, PewterCity_Gym_Movement_AIRivalApproach
	waitmovement 0
	call EventScript_AIRivalEncounterCinematic
	removeobject LOCALID_PEWTER_GYM_AI_RIVAL
	setflag FLAG_HIDE_PEWTER_GYM_AI_RIVAL
	setvar VAR_TEMP_0, 0
	releaseall
	end

PewterCity_Gym_Movement_AIRivalApproach::
	walk_up
	step_end

PewterCity_Gym_EventScript_Brock::
	famechecker FAMECHECKER_BROCK, FCPICKSTATE_COLORED, UpdatePickStateFromSpecialVar8005
	trainerbattle_single TRAINER_LEADER_BROCK, PewterCity_Gym_Text_BrockIntro, PewterCity_Gym_Text_BrockDefeat, PewterCity_Gym_EventScript_DefeatedBrock, NO_MUSIC
	goto_if_unset FLAG_GOT_TM39_FROM_BROCK, PewterCity_Gym_EventScript_GiveTM39
	msgbox PewterCity_Gym_Text_BrockPostBattle
	release
	end

PewterCity_Gym_EventScript_DefeatedBrock::
	famechecker FAMECHECKER_BROCK, 1
	setflag FLAG_DEFEATED_BROCK
	setflag FLAG_BADGE01_GET
	setvar VAR_MAP_SCENE_PEWTER_CITY, 1
	setflag FLAG_HIDE_PEWTER_CITY_GYM_GUIDE
	clearflag FLAG_HIDE_PEWTER_CITY_RUNNING_SHOES_GUY
	set_gym_trainers 1
	goto PewterCity_Gym_EventScript_GiveTM39
	end

PewterCity_Gym_EventScript_GiveTM39::
	msgbox PewterCity_Gym_Text_TakeThisWithYou
	checkitemspace ITEM_TM39
	goto_if_eq VAR_RESULT, FALSE, PewterCity_Gym_EventScript_NoRoomForTM39
	giveitem_msg PewterCity_Gym_Text_ReceivedTM39FromBrock, ITEM_TM39
	setflag FLAG_GOT_TM39_FROM_BROCK
	msgbox PewterCity_Gym_Text_ExplainTM39
	release
	end

PewterCity_Gym_EventScript_NoRoomForTM39::
	msgbox PewterCity_Gym_Text_DontHaveRoomForThis
	release
	end

PewterCity_Gym_EventScript_Liam::
	trainerbattle_single TRAINER_CAMPER_LIAM, PewterCity_Gym_Text_LiamIntro, PewterCity_Gym_Text_LiamDefeat
	msgbox PewterCity_Gym_Text_LiamPostBattle, MSGBOX_AUTOCLOSE
	end

PewterCity_Gym_EventScript_GymGuy::
	lock
	faceplayer
	goto_if_set FLAG_DEFEATED_BROCK, PewterCity_Gym_EventScript_GymGuyPostVictory
	msgbox PewterCity_Gym_Text_LetMeTakeYouToTheTop, MSGBOX_YESNO
	goto_if_eq VAR_RESULT, YES, PewterCity_Gym_EventScript_GymGuyTakeMeToTop
	goto_if_eq VAR_RESULT, NO, PewterCity_Gym_EventScript_GymGuyDontTakeMeToTop
	end

PewterCity_Gym_EventScript_GymGuyPostVictory::
	msgbox PewterCity_Gym_Text_YoureChampMaterial
	release
	end

PewterCity_Gym_EventScript_GymGuyTakeMeToTop::
	msgbox PewterCity_Gym_Text_LetsGetHappening
	goto PewterCity_Gym_EventScript_GymGuyAdvice
	end

PewterCity_Gym_EventScript_GymGuyDontTakeMeToTop::
	msgbox PewterCity_Gym_Text_ItsFreeLetsGetHappening
	goto PewterCity_Gym_EventScript_GymGuyAdvice
	end

PewterCity_Gym_EventScript_GymGuyAdvice::
	msgbox PewterCity_Gym_Text_TryDifferentPartyOrders
	release
	end

PewterCity_Gym_EventScript_GymStatue::
	lockall
	goto_if_set FLAG_BADGE01_GET, PewterCity_Gym_EventScript_GymStatuePostVictory
	msgbox PewterCity_Gym_Text_GymStatue
	releaseall
	end

PewterCity_Gym_EventScript_GymStatuePostVictory::
	msgbox PewterCity_Gym_Text_GymStatuePlayerWon
	releaseall
	end
