ENCODE_TABLE: dict[str, int] = {
    " ": 0x00,
    "!": 0xAB,
    "?": 0xAC,
    ".": 0xAD,
    "-": 0xAE,
    ",": 0xB8,
    "/": 0xBA,
    ":": 0xF0,
}

ENCODE_TABLE.update({str(index): 0xA1 + index for index in range(10)})
ENCODE_TABLE.update({chr(ord("A") + index): 0xBB + index for index in range(26)})
ENCODE_TABLE.update({chr(ord("a") + index): 0xD5 + index for index in range(26)})

NEWLINE = 0xFE
PAGE_BREAK = 0xFB
EOS = 0xFF
DEFAULT_CHARS_PER_LINE = 32


def sanitize_dialog_text(text: str) -> str:
    sanitized: list[str] = []

    for char in text:
        if char.isascii() and (char.isalnum() or char == " "):
            sanitized.append(char)
        elif char == ".":
            sanitized.append(char)
        elif char in {"!", "?", ",", ":", ";"}:
            sanitized.append("." if char in {"!", "?"} else " ")
        elif char in {"\n", "\r", "\t", "-", "/", "_"}:
            sanitized.append(" ")
        elif char in {"'", '"', "`"}:
            continue
        else:
            sanitized.append(" ")

    return " ".join("".join(sanitized).split())


def encode_text(text: str) -> bytes:
    encoded: list[int] = []

    for char in text:
        if char == "\n":
            encoded.append(NEWLINE)
            continue

        value = ENCODE_TABLE.get(char)
        if value is None:
            value = ENCODE_TABLE["?"]
        encoded.append(value)

    return bytes(encoded)


def format_dialog(
    text: str,
    *,
    chars_per_line: int = DEFAULT_CHARS_PER_LINE,
    lines_per_page: int = 2,
) -> bytes:
    encoded: list[int] = []
    line_count = 0
    text = sanitize_dialog_text(text)

    for paragraph_index, paragraph in enumerate(text.split("\n")):
        if paragraph_index > 0:
            encoded.append(NEWLINE)
            line_count += 1

        words = paragraph.split()
        current_line = ""

        for word in words:
            candidate = word if not current_line else f"{current_line} {word}"
            if len(candidate) <= chars_per_line:
                current_line = candidate
                continue

            if current_line:
                encoded.extend(encode_text(current_line))
                line_count += 1

            if line_count >= lines_per_page:
                encoded.append(PAGE_BREAK)
                line_count = 0
            else:
                encoded.append(NEWLINE)

            current_line = word

        if current_line:
            encoded.extend(encode_text(current_line))

    encoded.append(EOS)
    return bytes(encoded)


def format_dialog_hex(
    text: str,
    *,
    chars_per_line: int = DEFAULT_CHARS_PER_LINE,
    lines_per_page: int = 2,
) -> str:
    return format_dialog(
        text,
        chars_per_line=chars_per_line,
        lines_per_page=lines_per_page,
    ).hex().upper()
