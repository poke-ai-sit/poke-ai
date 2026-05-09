from pokelive_bridge.pokemon_text import format_dialog_hex, sanitize_dialog_text


def test_format_dialog_hex_encodes_firered_characters() -> None:
    assert format_dialog_hex("Hello!") == "C2D9E0E0E3ADFF"


def test_format_dialog_hex_wraps_lines_and_pages() -> None:
    assert (
        format_dialog_hex("Hello from Professor Codex", chars_per_line=10)
        == "C2D9E0E0E300DAE6E3E1FECAE6E3DAD9E7E7E3E6FBBDE3D8D9ECFF"
    )


def test_format_dialog_hex_sanitizes_unknown_characters() -> None:
    assert format_dialog_hex("PokéLive!") == "CAE3DF00C6DDEAD9ADFF"


def test_sanitize_dialog_text_keeps_only_letters_numbers_spaces_and_periods() -> None:
    assert (
        sanitize_dialog_text("Ah, you're in Oak's Lab! Choose wisely.")
        == "Ah youre in Oaks Lab. Choose wisely."
    )


def test_format_dialog_hex_uses_wider_default_line_length() -> None:
    assert format_dialog_hex("Professor Codex is online.") == (
        "CAE6E3DAD9E7E7E3E600BDE3D8D9EC00DDE700E3E2E0DDE2D9ADFF"
    )
