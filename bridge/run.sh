#!/usr/bin/env bash
# Clears any stale VIRTUAL_ENV from other projects before starting
unset VIRTUAL_ENV
cd "$(dirname "$0")"
exec uv run fastapi dev src/pokelive_bridge/main.py
