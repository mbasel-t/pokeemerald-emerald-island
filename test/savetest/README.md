# Save-load test

Checks that real save files still load on the current build (CONTRIBUTING.md
R2, issue #11). CI runs it on every PR right after the agbcc build.

```sh
make all syms
test/savetest/run.sh
```

For each folder in [`test/saves/`](../saves/):

1. **`boot_save.c`** boots the ROM in libmgba with the save, presses A to skip
   the intro and pick CONTINUE, and passes once the game is in the overworld
   (`gMain.callback2 == CB2_Overworld`) and stays there for 10 seconds. It
   fails if the save doesn't load (CONTINUE is never offered), the game
   crashes or freezes, or the overworld isn't reached within 90 seconds of
   game time. It works on a copy of the save, never the original.
2. **`check_save.py`** reads the loaded save blocks from memory and compares
   them to the save's `expected.json`: player name, gender, trainer ID,
   money, badges, play time (may be up to a minute later), Pokédex counts,
   map, and each party Pokémon's species, nickname and level.

Results go to `build/savetest/<save>/`: `result.txt`, the memory dumps, and
`screenshot.ppm` (the last frame). On a CI failure the result and screenshot
are uploaded as the `savetest-output` artifact.

Needs `libmgba-dev` (Ubuntu/Debian), a C compiler, `cpp` and Python 3.
