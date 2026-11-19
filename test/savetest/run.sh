#!/bin/sh
# Run the save-load test for every save in test/saves/ (issue #11).
#
# Usage: test/savetest/run.sh [rom.gba] [rom.sym]
# Needs libmgba-dev, a C compiler, cpp and python3. Build the ROM first with
# `make all syms`. Per-save results, memory dumps and a screenshot of the last
# frame are written to build/savetest/<save name>/.
set -eu

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
ROM=${1:-$ROOT/pokeemerald.gba}
SYM=${2:-$ROOT/pokeemerald.sym}
OUT=$ROOT/build/savetest

mkdir -p "$OUT"
cc -O2 -Wall -o "$OUT/boot_save" "$ROOT/test/savetest/boot_save.c" -lmgba

status=0
for dir in "$ROOT"/test/saves/*/; do
    name=$(basename "$dir")
    save="$dir$name.sav"
    if [ ! -f "$save" ]; then
        echo "== $name: no $name.sav, skipping"
        continue
    fi
    echo "== $name"
    mkdir -p "$OUT/$name"
    if ! "$OUT/boot_save" "$ROM" "$SYM" "$save" "$OUT/$name"; then
        status=1
    fi
    if [ -f "$dir/expected.json" ]; then
        python3 "$ROOT/test/savetest/check_save.py" "$OUT/$name" "$dir/expected.json" --repo "$ROOT" || status=1
    else
        echo "No expected.json for $name: only checked that it loads"
    fi
done
exit $status
