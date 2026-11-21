# Adding a Pokémon

This is the step-by-step workflow for adding a new species (or a new form of
an existing species) to Emerald Island. Follow it every time, so that every
new Pokémon is added the same way and none of them breaks vanilla saves.

It is adapted from the pret wiki's
[How to add a new Pokémon species](https://github.com/pret/pokeemerald/wiki/How-to-add-a-new-Pok%C3%A9mon-species).
**Do not follow that tutorial's numbering.** It appends the species after
Chimecho and bumps `SPECIES_EGG`, which grows `NUM_SPECIES`, and through it
the Pokédex flag arrays in the save. That breaks R4. This guide reuses
the slots that vanilla already reserves instead.

Rules this guide applies (see [CONTRIBUTING.md](../CONTRIBUTING.md) Part 1):
R2 (save layout), R4 (52 Dex flag bytes), R5 (species and Dex budget),
R6 (flags) and the AI policy (#2).

---

## 0. Before you start

You need, from a human:

- **The design**: name, types, base stats, abilities, learnset, evolution,
  where it is found.
- **The art**: front sprite (two frames), back sprite, normal and shiny
  palettes, party icon (two frames) and footprint.
- **The cry**.
- **The Pokédex text**: category name and entry text.

Under the AI policy, everything a player sees, hears or reads is made by a
human. Claude may wire the files in (constants, tables, build rules), but it
must not draw sprites, make cries, or write the name, category or Pokédex
text. Until the real text exists, use an obvious placeholder such as
`_("TODO_TEXT")`, and keep the vanilla `?` graphics until the real art exists.

Open (or find) an issue for the species with the `species` label. The issue
holds the design and the budget tally for that species.

---

## 1. Choose a species ID

A species ID is the number stored in every saved Pokémon (`species` in
`struct BoxPokemon`, a `u16`). Choosing it is the step most likely to break
something, so follow this order.

### 1a. First: the 25 "old Unown" slots (IDs 252 to 276)

Between Celebi (251) and Treecko (277), vanilla has 25 placeholder species,
`SPECIES_OLD_UNOWN_B` to `SPECIES_OLD_UNOWN_Z`. They are leftovers from
Gold/Silver-era Unown. They already have an entry in every species table, so
reusing one changes no array sizes. Vanilla never creates them, so no vanilla
save contains one.

They are already wired to their own Dex numbers:

| Species ID | Constant | National Dex | Hoenn Dex (unused) |
|---|---|---|---|
| 252 | `SPECIES_OLD_UNOWN_B` | 387 (`NATIONAL_DEX_OLD_UNOWN_B`) | 203 |
| 253 | `SPECIES_OLD_UNOWN_C` | 388 | 204 |
| ... | ... | ... | ... |
| 276 | `SPECIES_OLD_UNOWN_Z` | 411 (`NATIONAL_DEX_OLD_UNOWN_Z`) | 227 |

So slot *n* (B = 0 … Z = 24) has species ID `252 + n` and national Dex number
`387 + n`. Take slots in order, starting from `OLD_UNOWN_B`.

Another reason to use these slots first: if a mon with one of these IDs ever
reaches a vanilla game (trade, record mixing), vanilla shows a harmless `?`
species. A higher ID would read past the end of vanilla's tables.

### 1b. Later: IDs 412 to 511 (blocked)

Once the 25 slots run out, new species need IDs above Chimecho (411). **Don't
use them yet.** They need their own task first, because:

- `SPECIES_EGG` is 412 and `NUM_SPECIES` is defined as `SPECIES_EGG`.
  `NUM_DEX_FLAG_BYTES` is still `ROUND_BITS_TO_BYTES(NUM_SPECIES)` in
  `include/global.h`. Moving the egg grows the save's `owned`/`seen` arrays
  (R4) until that define is hard-coded to `52`.
- The Unown letter forms are defined as `NUM_SPECIES + 1` onward
  (413 to 439), so moving `SPECIES_EGG` moves them too.
- The Hall of Fame stores `species:9` (`src/hall_of_fame.c`), and an Egg in
  the party is recorded as `SPECIES_EGG`. Moving the egg to 512 or above
  doesn't fit in 9 bits, and vanilla Hall of Fame records that contain an Egg
  (412) would then show the new species at 412.
- Every `[NUM_SPECIES]`-sized table grows, and every table that lists species
  in order needs new rows.

So that task has to hard-code `NUM_DEX_FLAG_BYTES`, decide where the egg goes,
and handle the Hall of Fame. Until it's merged, the limit is 25 new species.

### 1c. The Hall of Fame limit

Any species that can be in the party when the player enters the Hall of Fame
must have an ID of **511 or lower**. All IDs above are off limits for
catchable species.

---

## 2. Choose a National Dex number (or none, for a form)

R4 gives 52 bytes of Dex flags = 416 bits, so national Dex numbers stop at
**#416**. That leaves **30** new numbers: #387 to #416.

- A **new Pokémon** gets the next free Dex number. With the old-Unown slots,
  that is the slot's own number (387 + n), so the two counts move together.
- A **form** (an alternate species ID that is the same Pokémon, for example a
  regional form) gets a species ID but **no** new Dex number. It points at its
  base species' Dex number instead. See section 5.
- #412 to #416 have no constants yet. They will only be reachable once IDs
  above 411 are available (1b), or by giving a form's unused old-Unown Dex
  number to another species. Add `NATIONAL_DEX_*` constants for them when
  they're first used.

### Running tally

Update this table in the PR that adds a species, and repeat the totals in the
PR template's R5 line.

| Species ID | Constant | Dex # | Form of | Issue / PR |
|---|---|---|---|---|
| 252 | `SPECIES_STARLY` (was `OLD_UNOWN_B`) | 387 | — | #58 |

**Used: Dex 1 / 30, species IDs 1 / 125** (of which 1 / 25 old-Unown slots).

---

## 3. Every file to touch

The fastest way to find every place a slot appears is to search for it:

```sh
git grep -n "OLD_UNOWN_B\b"
```

Rename `OLD_UNOWN_B` to your species' name (for example `NEWMON`) in each
place the steps below list, then fill the rows in. Two old-Unown tables are
shared or unused and can stay as they are: `unused_anims.h` and
`unknown_table.h`.

The examples below use `NEWMON` / `Newmon` in slot B (species 252, Dex 387).
Copy the shape of an existing species' rows (Chimecho is a good model, since
it's the last one in most tables).

### 3.1 Constants

| File | Change |
|---|---|
| `include/constants/species.h` | `#define SPECIES_OLD_UNOWN_B 252` → `#define SPECIES_NEWMON 252 // was SPECIES_OLD_UNOWN_B`. **Keep the number.** Don't touch `SPECIES_EGG` or `NUM_SPECIES`. |
| `include/constants/pokedex.h` | Rename `NATIONAL_DEX_OLD_UNOWN_B` → `NATIONAL_DEX_NEWMON` and `HOENN_DEX_OLD_UNOWN_B` → `HOENN_DEX_NEWMON`. Keep their positions in the enums. Raise `NATIONAL_DEX_COUNT` (see 3.4). |

### 3.2 Name

| File | Change |
|---|---|
| `src/data/text/species_names.h` | `[SPECIES_NEWMON] = _("NEWMON"),`. Up to 10 characters (`POKEMON_NAME_LENGTH`). Human-written. |
| `src/data/easy_chat/easy_chat_group_pokemon.h` (Hoenn) or `easy_chat_group_pokemon2.h` (national), and `easy_chat_words_by_letter.h` | Optional: makes the name selectable in Easy Chat. |

### 3.3 Species data

| File | Change |
|---|---|
| `src/data/pokemon/species_info.h` | Replace `[SPECIES_OLD_UNOWN_B] = OLD_UNOWN_SPECIES_INFO,` with a full entry: base stats, types, catch rate, EXP and EV yield, held items, gender ratio, egg cycles, friendship, growth rate, egg groups, two abilities, Safari flee rate, body color, `noFlip` (set `TRUE` if the sprite must not be mirrored). Leave `OLD_UNOWN_SPECIES_INFO` for the other slots. |
| `src/data/pokemon/level_up_learnsets.h` | Rename `sSpecies252LevelUpLearnset` to `sNewmonLevelUpLearnset` and fill it with `LEVEL_UP_MOVE(level, MOVE_*)` rows ending in `LEVEL_UP_END`. Each row packs the move into 9 bits, so move IDs must be ≤ 511. |
| `src/data/pokemon/level_up_learnset_pointers.h` | Point `[SPECIES_NEWMON]` at the renamed learnset. |
| `src/data/pokemon/tmhm_learnsets.h` | Replace the slot's (empty) entry with the TMs/HMs it can learn. |
| `src/data/pokemon/tutor_learnsets.h` | Add `[SPECIES_NEWMON] = (TUTOR(MOVE_*) \| ...)`. There is no old-Unown row, so this is a new row. |
| `src/data/pokemon/egg_moves.h` | Only for the base stage of a species that can breed: `egg_moves(NEWMON, MOVE_*, ...)`. |
| `src/data/pokemon/evolution.h` | `[SPECIES_NEWMON] = {{EVO_LEVEL, 30, SPECIES_NEWMON2}},` if it evolves. See section 4. |

### 3.4 Pokédex

| File | Change |
|---|---|
| `src/pokemon.c` | Rename the slot in `sSpeciesToHoennPokedexNum` (`SPECIES_TO_HOENN`), `sSpeciesToNationalPokedexNum` (`SPECIES_TO_NATIONAL`) and `sHoennToNationalOrder` (`HOENN_TO_NATIONAL`). |
| `include/constants/pokedex.h` | Raise `NATIONAL_DEX_COUNT` to the highest Dex number in use (for example `NATIONAL_DEX_NEWMON`). The Pokédex lists exactly `NATIONAL_DEX_COUNT` entries, so a species above it is never shown. |
| `src/pokedex.c` | `HasAllMons()` (the national Dex diploma) skips "the last two" entries assuming they are Jirachi and Deoxys (`NATIONAL_DEX_COUNT - 2`). Once the count is raised, change that bound to `NATIONAL_DEX_DEOXYS - 2`, or the diploma will require Jirachi. Whether DLC species count toward the diploma is a design decision; record it in the issue. |
| `src/data/pokemon/pokedex_entries.h` | Add `[NATIONAL_DEX_NEWMON] = { .categoryName, .height, .weight, .description, .pokemonScale, .pokemonOffset, .trainerScale, .trainerOffset }`. Height is in decimetres, weight in hectograms. Copy the scale/offset values from a species of similar size and adjust them on the size-comparison screen. |
| `src/data/pokemon/pokedex_text.h` | `const u8 gNewmonPokedexText[] = _("...");` Four lines, human-written. |
| `src/data/pokemon/pokedex_orders.h` | `gPokedexOrder_Alphabetical`: move the slot's line out of the old-Unown block at the top into alphabetical position (the array length stays the same). `gPokedexOrder_Weight` and `gPokedexOrder_Height`: **insert** the new Dex number in sorted position. These two have exactly `NATIONAL_DEX_COUNT` entries and are read up to that count, so forgetting one reads past the end. |

**Emerald Island Dex (decided).** DLC species go in their own regional Pokédex,
the **Emerald Island Dex**, which the player is given when the DLC starts, the
way the National Dex is given after the Hall of Fame. They are **not** added
to the Hoenn Dex, so Birch's rating, the Hoenn diploma (`HasAllHoennMons()`)
and Hoenn-only trade checks (`IsSpeciesInHoennDex()`) stay exactly as in
vanilla.

The Island Dex itself is a separate task (not built yet). Until it exists, a
DLC species caught before the National Dex won't appear in the Pokédex, and
the summary screen shows no number for it. When it's built, it should:

- be a third Pokédex mode next to `DEX_MODE_HOENN` and `DEX_MODE_NATIONAL`
  (`include/pokedex.h`, `sPokedexModes` in `src/pokedex.c`). The selected
  mode is already saved in `gSaveBlock2Ptr->pokedex.mode`, a `u8`, so a new
  value needs no layout change (R2);
- be unlocked by one unused vanilla flag (R6), set when the DLC starts;
- keep using the existing seen/caught flags, which are indexed by **national**
  Dex number. The Island Dex is only a list and an order in ROM (like
  `sHoennToNationalOrder`), so R4's 52-byte limit and the #387–#416 budget
  still apply;
- give the summary screen an Island Dex number for DLC species when the
  National Dex isn't unlocked (`SpeciesToPokedexNum()` in `src/pokemon.c`).

When adding a species, also add it to the Island Dex list once that exists.

### 3.5 Graphics

Graphics go in a new folder, `graphics/pokemon/newmon/`, using the same files
as every other species (copy `graphics/pokemon/chimecho/` as a template for
sizes, then replace every image with the human-made art):

| File | What |
|---|---|
| `anim_front.png` | 64×128: two 64×64 frames stacked, 16 colors |
| `front.png` | 64×64, first frame |
| `back.png` | 64×64 |
| `normal.pal`, `shiny.pal` | JASC palettes, 16 colors each |
| `icon.png` | 32×64: two 32×32 frames, using one of the 3 shared icon palettes |
| `footprint.png` | 16×16, 2 colors |

Then register them:

| File | Change |
|---|---|
| `include/graphics.h` | `extern` declarations: `gMonFrontPic_Newmon`, `gMonPalette_Newmon`, `gMonBackPic_Newmon`, `gMonShinyPalette_Newmon`, `gMonStillFrontPic_Newmon`, `gMonIcon_Newmon`, `gMonFootprint_Newmon`. |
| `src/anim_mon_front_pics.c` | `gMonFrontPic_Newmon` from `anim_front.png`. |
| `src/data/graphics/pokemon.h` | The other six, from their files (`INCGFX_U32` / `INCGFX_U8`, as Chimecho does). |
| `src/data/pokemon_graphics/front_pic_table.h`, `still_front_pic_table.h`, `back_pic_table.h` | Point the slot's `SPECIES_SPRITE(...)` at the new pics instead of `DoubleQuestionMark`. |
| `palette_table.h`, `shiny_palette_table.h` | Same, for `SPECIES_PAL` / `SPECIES_SHINY_PAL`. |
| `front_pic_coordinates.h`, `back_pic_coordinates.h` | Size and `y_offset` of the visible sprite, so it sits on the ground in battle. |
| `footprint_table.h` | `gMonFootprint_Newmon`. |
| `src/pokemon_icon.c` | `gMonIconTable` → `gMonIcon_Newmon`; `gMonIconPaletteIndices` → 0, 1 or 2. |
| `enemy_mon_elevation.h` | Optional: pixels to raise a floating or flying mon in battle. |

### 3.6 Animation

| File | Change |
|---|---|
| `src/data/pokemon_graphics/front_pic_anims.h` | Add an `sAnim_Newmon_1[]` frame list and `SINGLE_ANIMATION(Newmon);` (copy Chimecho's), then point `[SPECIES_NEWMON]` at `sAnims_Newmon` instead of the shared `sAnims_OldUnownB`. |
| `src/pokemon.c` `sMonFrontAnimIdsTable` | `[SPECIES_NEWMON - 1] = ANIM_*`, the front animation played on the summary screen and in battle. The list of animations is in the pret tutorial's appendix. |
| `src/pokemon.c` `sMonAnimationDelayTable` | Optional delay before the animation starts. |
| `src/pokemon_animation.c` `sSpeciesToBackAnimSet` | `[SPECIES_NEWMON] = BACK_ANIM_*`. |

The old-Unown slots have no rows in the last three tables (they default to 0),
so these are new rows.

### 3.7 Cry

Cries are made by a human (AI policy). To wire one in:

| File | Change |
|---|---|
| `sound/direct_sound_samples/cries/newmon.wav` | The cry sample (the build turns it into `newmon.bin`). |
| `sound/direct_sound_data.inc` | `Cry_Newmon::` with an `.incbin` of the built `.bin`, next to `Cry_Chimecho`. |
| `sound/cry_tables.inc` | Append `cry Cry_Newmon` to `gCryTable` **and** `cry_reverse Cry_Newmon` to `gCryTable_Reverse` (Growl and others play it reversed). Its cry ID is its position, starting from 388 for the first new one. |
| `src/pokemon.c` `SpeciesToCryId()` | Today every species from 252 to 276 is sent to Unown's cry. Add a lookup for the old-Unown range that returns the new cry ID (`src/sound.c` supports cry IDs up to 511). |

Until the cry exists, leave it on Unown's cry.

### 3.8 Make it appear

- Wild: `src/data/wild_encounters.json`.
- Trainers: `src/data/trainer_parties.h`.
- Gifts / static encounters: scripts using `givemon` / `setwildbattle`. Any
  "already received" state is a flag, so follow R6.
- Optional: `src/data/bard_music/pokemon.h` (Mauville bard sounds); copy an
  existing entry.

---

## 4. Evolutions

### 4a. Vanilla methods

`include/constants/pokemon.h` has 15 methods (`EVO_FRIENDSHIP` …
`EVO_BEAUTY`), and each species has up to `EVOS_PER_MON` (5) entries in
`gEvolutionTable` (`src/data/pokemon/evolution.h`). The table is ROM data, so
raising `EVOS_PER_MON` doesn't touch the save.

How `GetEvolutionTargetSpecies()` in `src/pokemon.c` picks a target:

- Level-up and trade checks go through **every** entry, and **the last match
  wins**. Put the most specific condition last.
- Item (stone) checks stop at the first match.
- An Everstone blocks everything except the party menu's "can this stone be
  used" check.

### 4b. New evolution methods

The pret wiki's
[New Evolution Methods](https://github.com/pret/pokeemerald/wiki/New-Evolution-Methods)
adds methods from later games (time of day, gender, held item, known move or
move type, party member, location, rain, nature, item count, Dark type in
party). To add one:

1. Add `#define EVO_<NAME> <next number>` in `include/constants/pokemon.h`.
   Take the next free number in **this** repo, not the wiki's numbering.
2. Add its `case` in the right `mode` of `GetEvolutionTargetSpecies()`.
3. If it uses an item or a held item, the item must exist (see the item guide).
4. Port only the methods a species actually needs, one per PR, and credit the
   source (R3).

Time-of-day methods use the RTC (`RtcCalcLocalTime()`). Keep their hours
consistent with the day/night cycle (#41).

### 4c. Blocking evolution

The wiki's "block evolution" snippet makes `GetEvolutionTargetSpecies()`
return `SPECIES_NONE` while a flag is set. It needs one flag: claim an unused
vanilla flag (R6), rename it in `include/constants/flags.h` with the original
name in a comment, and confirm with `git grep` that vanilla never touches it.
Don't pick one between `0x920` and `0x95F`, because those are daily flags and
get cleared every day.

### 4d. Branched / regional evolutions

The pattern from
[Branched Alolan Evolution](https://github.com/pret/pokeemerald/wiki/Branched-Alolan-Evolution)
is: one species has two entries in `gEvolutionTable`, the normal one and one
with an extra condition that leads to the regional form. The original uses a
held item (Strange Souvenir). For Emerald Island, the location version from
New Evolution Methods fits better:

```c
// include/constants/pokemon.h
#define EVO_LEVEL_ISLAND 16 // reach level `param` inside the DLC region (example)

// src/data/pokemon/evolution.h
[SPECIES_FOO] = {{EVO_LEVEL, 30, SPECIES_FOO2},
                 {EVO_LEVEL_ISLAND, 30, SPECIES_FOO2_ISLAND}}, // more specific entry last
```

`param` is a `u16`, so a method that needs both a level and a place must
hard-code one of them (for example, the region as a set of `MAPSEC_*`
values checked with `GetCurrentRegionMapSectionId()`). Write that in the
method's comment.

The regional form is a form (section 5): it spends a species ID but no Dex
number.

---

## 5. Forms

Vanilla has no general form system. Unown and Deoxys use special cases, and
the HGSS-style "Forms" Pokédex page is a separate port (R3). On this project a
form is **a separate species ID that shares its base species' Dex number**.

Use a form when it's the same Pokémon in-universe (regional variant, an
alternate look, Indeedee-style male/female). Use a new Dex number when it's a
new Pokémon.

What a form costs and how it behaves:

- It takes one species ID (an old-Unown slot) and **no** Dex number.
- In `sSpeciesToNationalPokedexNum`, map it to the base species
  (`[SPECIES_FOO_ISLAND - 1] = NATIONAL_DEX_FOO`). Don't map it with
  `SPECIES_TO_NATIONAL(FOO_ISLAND)`, which needs a constant of its own.
- That leaves the slot's old-Unown Dex number unused. Rename it
  `NATIONAL_DEX_UNUSED_<n>` so a later species can take it.
- Seeing or catching the form sets the **base species'** Dex flags, and the
  Pokédex shows the base species' entry and sprite.
- It needs its own name, stats, learnsets, graphics and cry rows like any
  species, but no Pokédex entry, text or order rows.
- Its name in `species_names.h` is what the player sees. Pick something that
  reads well in battle ("FOO" with a different look, or a distinct name).

---

## 6. Verification checklist

Copy this into the PR and tick what you actually did.

- [ ] `make` builds, and `NUM_DEX_FLAG_BYTES` is still 52
  (`NUM_SPECIES` didn't change).
- [ ] Summary screen: name, Dex number, types, ability, stats, moves, sprite,
  shiny sprite, animation.
- [ ] Pokédex: appears in numerical, alphabetical, height and weight order;
  entry text, category, height, weight, size comparison, footprint, cry.
- [ ] Battle: front and back sprites on the ground (or floating as intended),
  cry, a move from each learnset, catching it, EXP gain.
- [ ] Evolution: by its method, and blocked by an Everstone; for a branched
  evolution, both branches.
- [ ] PC: box icon, moving it, depositing and withdrawing.
- [ ] Hall of Fame: entering with it in the party, then viewing the record
  from the PC.
- [ ] Breeding (if it can breed): egg hatches into the right species with
  its egg moves.
- [ ] Trade/link: decide whether it may be traded to a vanilla game. Mew and
  Deoxys are already blocked in `src/trade.c`, and new species should
  probably be blocked the same way (separate issue). Record the decision.
- [ ] National Dex diploma still requires exactly the vanilla set (or the
  set the issue decided).
- [ ] Vanilla save loads, saves and reloads intact (CI's save-load test, plus
  the manual check if the PR touches save-related files).
- [ ] The tally in section 2 and the PR template's R5 line are updated.
