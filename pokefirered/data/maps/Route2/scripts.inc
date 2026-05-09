Route2_MapScripts::
	map_script MAP_SCRIPT_ON_LOAD, Route2_OnLoad
	map_script MAP_SCRIPT_ON_FRAME_TABLE, Route2_OnFrame
	.byte 0

Route2_OnLoad::
	setflag FLAG_HIDE_ROUTE2_AI_RIVAL
	end

Route2_OnFrame::
	map_script_2 VAR_TEMP_0, 1, Route2_EventScript_AIRivalEncounter
	.2byte 0

@ PokeLive Smart Gary AI Rival — Battle 2 cinematic on Route 2.
Route2_EventScript_AIRivalEncounter::
	lockall
	getplayerxy VAR_0x8004, VAR_0x8005
	addvar VAR_0x8004, 2
	setobjectxyperm LOCALID_ROUTE2_AI_RIVAL, VAR_0x8004, VAR_0x8005
	setobjectmovementtype LOCALID_ROUTE2_AI_RIVAL, MOVEMENT_TYPE_FACE_LEFT
	playse SE_WARP_IN
	addobject LOCALID_ROUTE2_AI_RIVAL
	applymovement LOCALID_ROUTE2_AI_RIVAL, Route2_Movement_AIRivalApproach
	waitmovement 0
	call EventScript_AIRivalEncounterCinematic
	removeobject LOCALID_ROUTE2_AI_RIVAL
	setflag FLAG_HIDE_ROUTE2_AI_RIVAL
	setvar VAR_TEMP_0, 0
	releaseall
	end

Route2_Movement_AIRivalApproach::
	walk_left
	step_end

Route2_EventScript_RouteSign::
	msgbox Route2_Text_RouteSign, MSGBOX_SIGN
	end

Route2_EventScript_DiglettsCaveSign::
	msgbox Route2_Text_DiglettsCave, MSGBOX_SIGN
	end
