import logging
from typing import Any, Literal

import openai

from pokelive_bridge.config import (
    OPENAI_API_KEY,
    OPENAI_CHAT_MODEL,
    OPENAI_MAX_COMPLETION_TOKENS,
)
from pokelive_bridge.prompts import (
    build_codex_system_prompt_advice,
    build_codex_system_prompt_ask,
)

FALLBACK_RESPONSE = (
    "My data scanner is fuzzy right now. Try again in a moment, researcher."
)

_client: openai.OpenAI | None = None


def _get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(api_key=OPENAI_API_KEY)
    return _client


def ask_codex(
    message: str,
    game_state: Any,
    party: list[Any] | None = None,
    request_kind: Literal["ADVICE", "ASK"] = "ASK",
) -> str:
    if request_kind == "ADVICE":
        system_prompt = build_codex_system_prompt_advice(game_state, party)
    else:
        system_prompt = build_codex_system_prompt_ask(game_state, party)

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            max_completion_tokens=OPENAI_MAX_COMPLETION_TOKENS,
        )
        content = response.choices[0].message.content
        return content.strip() if content else FALLBACK_RESPONSE
    except Exception as e:
        logging.exception("OpenAI API call failed: %s", e)
        return FALLBACK_RESPONSE
