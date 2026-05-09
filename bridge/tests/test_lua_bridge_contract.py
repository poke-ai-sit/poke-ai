from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
LUA_BRIDGE = REPO_ROOT / "emulator" / "lua" / "bridge_game_state_test.lua"


def test_codex_menu_uses_dpad_confirm_controls_with_key_swallowing() -> None:
    source = LUA_BRIDGE.read_text()

    assert 'callbacks:add("keysRead"' in source
    assert "local CODEX_CONFIRM_KEY = C.GBA_KEY.A" in source
    assert "local CODEX_CANCEL_KEY = C.GBA_KEY.B" in source
    assert "local CODEX_MENU_LEFT_KEY = C.GBA_KEY.LEFT" in source
    assert "local CODEX_MENU_RIGHT_KEY = C.GBA_KEY.RIGHT" in source
    assert "local CODEX_MENU_UP_KEY = C.GBA_KEY.UP" in source
    assert "local CODEX_MENU_DOWN_KEY = C.GBA_KEY.DOWN" in source
    assert "local CODEX_MENU_KEY_MASK" in source
    assert "clear_codex_menu_key" in source
    assert "clear_codex_menu_keys" in source
    assert "codex_menu_keys_are_idle" in source
    assert "codex_menu_input_armed" in source
    assert "START Advice" not in source
    assert "SELECT Evolve" not in source


def test_codex_menu_handles_input_before_swallowing_fire_red_keys() -> None:
    source = LUA_BRIDGE.read_text()
    keys_read_start = source.index('callbacks:add("keysRead"')
    handle_input_at = source.index("handle_codex_menu_input(keys, previous_codex_menu_keys)", keys_read_start)
    clear_keys_at = source.index("clear_codex_menu_keys()", keys_read_start)

    assert handle_input_at < clear_keys_at
    assert 'codex_ui_state == "menu" or codex_ui_state == "confirm_evolve"' in source
    assert 'CODEX_MENU_OPTIONS = {"Advice", "Evolve", "Exit"}' in source


def test_codex_menu_uses_start_menu_style_textbox_bar() -> None:
    source = LUA_BRIDGE.read_text()

    assert 'return "CODEX MENU\\n" .. table.concat(option_text, "  ")' in source
    assert "string.upper(option)" in source
    assert 'return "What do you need.\\n"' not in source
