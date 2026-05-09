from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PATCH_DIR = REPO_ROOT / "patches" / "pokefirered-commits"
MAILBOX_LUA = REPO_ROOT / "emulator" / "lua" / "codex_mailbox_bridge.lua"


def test_pokefirered_patch_series_exists_in_order() -> None:
    patch_names = [path.name for path in sorted(PATCH_DIR.glob("*.patch"))]

    assert patch_names == [
        "0001-add-professor-codex-prompt-ui.patch",
        "0002-add-professor-codex-mailbox.patch",
        "0003-route-professor-oak-to-codex.patch",
    ]


def test_patch_series_ports_native_prompt_menu_and_mailbox() -> None:
    combined = "\n".join(path.read_text() for path in sorted(PATCH_DIR.glob("*.patch")))

    assert "NAMING_SCREEN_CODEX" in combined
    assert "CODEX_INPUT_LENGTH 32" in combined
    assert "StartCodexPrompt" in combined
    assert "BufferCodexPrompt" in combined
    assert "MULTICHOICE_POKELIVE_CODEX" in combined
    assert "sMultichoiceList_PokeliveCodex" in combined
    assert "PublishCodexAdvicePrompt" in combined
    assert "PublishCodexPrompt" in combined
    assert "IsCodexResponseReady" in combined
    assert "BufferCodexResponse" in combined
    assert "gPokeliveCodexMailbox" in combined
    assert "PalletTown_ProfessorOaksLab_EventScript_ProfessorCodex" in combined
    assert "FLAG_BEAT_RIVAL_IN_OAKS_LAB" in combined


def test_mailbox_lua_bridge_is_transport_only() -> None:
    source = MAILBOX_LUA.read_text()

    assert "CODEX_MAILBOX_ADDR" in source
    assert "POKELIVE_CODEX_MAILBOX_MAGIC" in source
    assert "MAILBOX_STATUS_PENDING" in source
    assert "MAILBOX_STATUS_RESPONSE_READY" in source
    assert "POST /codex-chat" in source
    assert 'callbacks:add("frame"' in source
    assert "emu:getKeys" not in source
    assert "TEXT_BUF" not in source
    assert "write_native" not in source
