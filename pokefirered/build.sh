#!/usr/bin/env bash
# Build the patched FireRed ROM with the devkitPro toolchain.
#
# Usage:
#   ./build.sh             — parallel build of pokefirered.gba
#   ./build.sh clean       — wipe build/ and pokefirered.{elf,gba,map,sym}
#   ./build.sh -j1         — pass any flag straight to make (single-threaded here)
set -euo pipefail

cd "$(dirname "$0")"

export DEVKITPRO="${DEVKITPRO:-/opt/devkitpro}"
export DEVKITARM="${DEVKITARM:-$DEVKITPRO/devkitARM}"
export PATH="$DEVKITARM/bin:$DEVKITPRO/tools/bin:$PATH"

if ! command -v arm-none-eabi-as >/dev/null; then
  echo "error: arm-none-eabi-as not found under $DEVKITARM/bin" >&2
  echo "install devkitPro: https://devkitpro.org/wiki/Getting_Started" >&2
  exit 1
fi

if [ "$#" -eq 0 ]; then
  exec make -j"$(sysctl -n hw.logicalcpu)"
else
  exec make "$@"
fi
