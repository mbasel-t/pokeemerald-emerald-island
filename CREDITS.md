# Credits

Emerald Island is built on other people's work. This file lists all of it:
the base project, ported code and tutorials, third-party graphics and sound,
and the people who contribute to the hack. Release notes and the in-game or
README credits are taken from here.

## Keeping this file up to date

- A pull request that adds or changes anything made by someone else
  (graphics, sound, code ported from another project, code adapted from a
  tutorial) adds its credit here **in the same PR**.
- A collaborator's first merged PR adds them under [Collaborators](#collaborators).
- Each entry says **who** made it, **what** it is, **where** it is used in
  this repository, the **source** link, and the **terms** of use (for
  example "free to use with credit"). If the source has no licence, say so.
- Only credit what is actually in the repository. Planned assets get their
  credit in the PR that adds them.
- Remove an entry only when the asset or code it credits is removed.

## Base project

| Who | What | Source |
|---|---|---|
| pret and the pokeemerald contributors | The Pokémon Emerald decompilation this hack is built on | [pret/pokeemerald](https://github.com/pret/pokeemerald) |

Pokémon is © Nintendo, Creatures Inc. and GAME FREAK inc. Emerald Island is a
non-commercial fan project distributed only as a patch.

## Code ported or adapted from tutorials and other projects

| Who | What | Used in | Source | Terms |
|---|---|---|---|---|
| meejle, with help from Anon822 | Save throbber code (spinner while saving) | `src/start_menu.c` | [pret wiki: Show a throbber animation while the game is saving](https://github.com/pret/pokeemerald/wiki/Show-a-throbber-animation-while-the-game-is-saving) | Shared as a tutorial; asks for credit |

## Graphics

| Who | What | Used in | Source | Terms |
|---|---|---|---|---|
| meejle | Save throbber animation (8 frames) | `graphics/text_window/throbber.png` | [meejle/rainbowamnesty](https://github.com/meejle/rainbowamnesty/blob/0.1/graphics/text_window/throbber.png), linked from the tutorial above | Offered for use in the tutorial with credit; the source repo has no licence file |
| 11bayerf1 and Chaos Rush (Sugimori Palettes DS-Style 64x64 resource), assembled by the pokeemerald-expansion contributors | Starly front, back, shiny palette, icon and footprint | `graphics/pokemon/starly/` (`front.png` is the first frame of `anim_front.png`) | [PokéCommunity thread](https://www.pokecommunity.com/threads/sugimori-palettes-the-ds-style-64x64-pok%C3%A9mon-sprite-resource.336945/), copied from [rh-hideout/pokeemerald-expansion `graphics/pokemon/starly/`](https://github.com/rh-hideout/pokeemerald-expansion/tree/master/graphics/pokemon/starly) | Free to use in hacks with credit; the expansion repo has no licence file |

## Sound and music

| Who | What | Used in | Source | Terms |
|---|---|---|---|---|
| GAME FREAK (original cry), converted to GBA format by the pokeemerald-expansion contributors | Starly's cry | `sound/direct_sound_samples/cries/starly.wav` | [rh-hideout/pokeemerald-expansion](https://github.com/rh-hideout/pokeemerald-expansion/blob/master/sound/direct_sound_samples/cries/starly.wav) | The expansion repo has no licence file |

## Text

| Who | What | Used in | Source | Terms |
|---|---|---|---|---|
| GAME FREAK (official English text), via the pokeemerald-expansion contributors | Starly's name, category and Pokédex entry | `src/data/text/species_names.h`, `src/data/pokemon/pokedex_entries.h`, `src/data/pokemon/pokedex_text.h` | [rh-hideout/pokeemerald-expansion `gen_4_families.h`](https://github.com/rh-hideout/pokeemerald-expansion/blob/master/src/data/pokemon/species_info/gen_4_families.h) | Only "Pokémon" was changed to "POKéMON" to match vanilla's spelling |

## Collaborators

| Who | Contribution |
|---|---|
| mbasel-t | Project owner |
