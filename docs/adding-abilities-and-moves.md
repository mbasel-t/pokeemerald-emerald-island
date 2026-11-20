# Adding abilities and moves

This is the workflow for adding a new ability or a new move to Emerald Island.
New species (#7), the Fairy type (#4) and Rock Climb (#40) all need new moves,
and probably new abilities. Both touch battle scripts, the AI and animations,
and move IDs end up in saved Pokémon.

Sources:

- Abilities: pret wiki
  [How to add a new ability](https://github.com/pret/pokeemerald/wiki/How-to-add-a-new-ability)
  (worked example: Snow Warning).
- Moves: the pret wiki links to PokeCommunity's
  [Adding a New Move](https://www.pokecommunity.com/showthread.php?t=445273).
  That page couldn't be read while this guide was written, so the move
  section below is built from this repo's code. Compare it with the tutorial
  the first time you follow it, and fix this guide where they differ.

Rules this guide applies (see [CONTRIBUTING.md](../CONTRIBUTING.md) Part 1):
R2 (save layout), R3 (ported code), R6 (flags) and the AI policy (#2).

---

## 0. Before you start

From a human you need: the **name** and **description** (for a move, also its
contest description if it gets a new contest effect), and any new **animation
graphics** or **sound effects**.

Under the AI policy, Claude may write the battle code, data, battle scripts,
AI and the animation *script* that reuses existing graphics and sounds. It
must not write the name or description text, or draw new animation graphics
or make new sounds. Until the text exists, use `_("TODO_TEXT")`.

Open (or find) an issue for each move or ability.

---

## 1. Save rules

| Data | Where it lives | Limit |
|---|---|---|
| A Pokémon's moves | `u16 moves[4]` in `struct BoxPokemon` (and in Battle Frontier records) | No layout change. Any ID fits. |
| Level-up learnsets | `LEVEL_UP_MOVE(level, move)` packs the move into 9 bits (`LEVEL_UP_MOVE_ID = 0x01FF`) | **Move IDs ≤ 511** |
| Easy Chat words | A move word stores the move in 9 bits (saved in mail, TV shows, profiles) | Move IDs ≤ 511 |
| Metronome | `Cmd_metronome` assumes `MOVES_COUNT < 512` | Move IDs ≤ 511 |
| A Pokémon's ability | `abilityNum:1` in the save: **slot 0 or 1**, not the ability ID | The ability ID comes from `.abilities[2]` in the species' ROM data. |
| Ability IDs | `u8` in `struct SpeciesInfo` and `struct BattlePokemon` | **Ability IDs ≤ 255** |
| Battle effects | `u8 effect` in `struct BattleMove` | **Effect IDs ≤ 255** |

Vanilla has 354 moves (`MOVES_COUNT` = 355), 77 abilities
(`ABILITIES_COUNT` = 78) and 214 move effects, so there's room for 157 more
moves, 178 more abilities and 42 more effects.

None of the `MOVES_COUNT`- or `ABILITIES_COUNT`-sized arrays are in the save,
so growing those counts doesn't change the save layout. Keep it that way:
never add such an array to saved data.

### Compatibility with vanilla games

A Pokémon that knows a new move, or a new species with a new ability, will
show garbage (or worse) in a vanilla game. Vanilla reads `gMoveNames[]` and
`gBattleMoves[]` past their ends for move IDs of 355 and up. That covers
trades, link battles, and record mixing (Battle Tower records carry moves).
Blocking such Pokémon from links to vanilla games is a separate issue,
together with the same question for new species. Until it's done, say so in
each PR that adds a move.

Changing an **existing** ability on an existing species changes it for every
saved Pokémon of that species. That's ROM data, so it's allowed, but call it
out in the PR.

---

## 2. Adding an ability

### 2a. Constant, name and description

| File | Change |
|---|---|
| `include/constants/abilities.h` | `#define ABILITY_NEW_ABILITY 78` (the next number) and raise `ABILITIES_COUNT` by one. |
| `src/data/text/abilities.h` | `static const u8 sNewAbilityDescription[] = _("...");` (one short line, like the others), then `[ABILITY_NEW_ABILITY] = _("NEW ABILITY"),` in `gAbilityNames` (up to 12 characters, `ABILITY_NAME_LENGTH`) and `[ABILITY_NEW_ABILITY] = sNewAbilityDescription,` in `gAbilityDescriptionPointers`. Human-written. |
| `src/data/pokemon/species_info.h` | Put it in a species' `.abilities = {first, second}`. Slot 0 or 1 is what the save remembers. |

At this point the ability shows on the summary screen but does nothing.

### 2b. Battle effect

Find the closest existing ability and copy how it works. Most abilities are
handled in `AbilityBattleEffects()` in `src/battle_util.c`, under one of its
cases:

| Case | When it runs | Examples |
|---|---|---|
| `ABILITYEFFECT_ON_SWITCHIN` | Entering battle | Drizzle, Intimidate, Trace |
| `ABILITYEFFECT_ENDTURN` | End of each turn | Speed Boost, Rain Dish |
| `ABILITYEFFECT_MOVES_BLOCK` | A move is about to hit | Soundproof |
| `ABILITYEFFECT_ABSORBING` | A move of a type hits | Volt Absorb, Flash Fire |
| `ABILITYEFFECT_ON_DAMAGE` | After being hit | Static, Rough Skin |
| `ABILITYEFFECT_IMMUNITY` | Status checks | Limber, Insomnia |

Others are checked where they matter: damage in `CalculateBaseDamage()` in
`src/pokemon.c` (Huge Power, Thick Fat), accuracy and type effectiveness in
`src/battle_script_commands.c` (Levitate, Wonder Guard), and some outside
battle in `src/wild_encounter.c` (Intimidate, Keen Eye and others change
encounter rates).

If the ability shows a message, it needs:

1. a battle script in `data/battle_scripts_1.s`, exposed in
   `include/battle_scripts.h`;
2. a string ID in `include/constants/battle_string_ids.h` (raise
   `BATTLESTRINGS_COUNT`);
3. the text in `src/battle_message.c` (`gBattleStringsTable`). Human-written.

The Snow Warning tutorial walks through all three, plus adding a new weather
bit (`gBattleWeather` is battle-only state, not saved).

### 2c. AI awareness

The AI is scripted in `data/battle_ai_scripts.s`. It checks the target's
ability by ID, for example `if_equal ABILITY_VOLT_ABSORB,
CheckIfVoltAbsorbCancelsElectric` in `AI_CheckBadMove`. If the new ability
makes a move fail or backfire (an absorb or immunity ability), add a matching
check there, or the AI will keep using that move into it. Switching logic in
`src/battle_ai_switch_items.c` has similar checks (Wonder Guard, absorbing
abilities).

---

## 3. Adding a move

Moves are `#define`s in `include/constants/moves.h`, from `MOVE_POUND` (1) to
`MOVE_PSYCHO_BOOST` (354). Add a new move as the next number and raise
`MOVES_COUNT`. Several tables are **positional lists** (entry N is move N), so
add every new move at the end, in the same order everywhere.

### 3a. Every file to touch

| File | Change |
|---|---|
| `include/constants/moves.h` | `#define MOVE_NEW_MOVE 355` and `MOVES_COUNT 356`. |
| `src/data/battle_moves.h` | `[MOVE_NEW_MOVE] = { .effect, .power, .type, .accuracy, .pp, .secondaryEffectChance, .target, .priority, .flags }` (see 3b). |
| `src/data/text/move_names.h` | `[MOVE_NEW_MOVE] = _("NEW MOVE"),`. Up to 12 characters (`MOVE_NAME_LENGTH`). Human-written. |
| `src/data/text/move_descriptions.h` | `static const u8 sNewMoveDescription[] = _("...");` (lines broken with `\n`, like the others), and `[MOVE_NEW_MOVE - 1] = sNewMoveDescription,` in `gMoveDescriptionPointers`. Note the `- 1`. Human-written. |
| `data/battle_anim_scripts.s` | Add `.4byte Move_NEW_MOVE` to `gBattleAnims_Moves` **after `Move_PSYCHO_BOOST` and before `Move_COUNT`**, and write the `Move_NEW_MOVE:` animation script (see 3d). |
| `src/data/contest_moves.h` | `[MOVE_NEW_MOVE] = { .effect = CONTEST_EFFECT_*, .contestCategory = CONTEST_CATEGORY_*, .comboStarterId, .comboMoves }`. |
| Learnsets | Level-up, TM/HM, tutor and egg moves (see 3e). |

Optional, but check each one:

| File | Why |
|---|---|
| `src/battle_script_commands.c` `sMovesForbiddenToCopy` | Metronome picks any move below `MOVES_COUNT`, so new moves join automatically. Add a move to the right section of this list if Mimic, Metronome or Assist mustn't use it. |
| `src/data/easy_chat/easy_chat_group_move_1.h` / `_move_2.h` | Lets players use the move name in Easy Chat. |
| `src/battle_message.c` `sGrammarMoveUsedTable` | Changes the "used X!" wording for some moves. |
| Battle Frontier tables: `sMindRatings` (`src/battle_arena.c`), `sBattleStyleMovePoints` (`src/battle_dome.c`), `sValidApprenticeMoves` (`src/data/battle_frontier/apprentice.h`), the move-style lists in `src/battle_factory.c` | Sized by `MOVES_COUNT`, so a new move gets zeros. Fill them in if the move should matter there. |
| `src/data/bard_music/moves.h` | Mauville bard sounds for the word; an empty entry is silent. Copy an existing one. |

### 3b. Battle data

| Field | Notes |
|---|---|
| `.effect` | An existing `EFFECT_*` from `include/constants/battle_move_effects.h`, or a new one (3c). `EFFECT_HIT` is a plain damaging move. |
| `.power`, `.accuracy`, `.pp` | `u8`. Accuracy 0 means it never misses. |
| `.type` | `TYPE_*`. Until a full physical/special split exists, **the category comes from the type**: `IS_TYPE_PHYSICAL(type)` is `type < TYPE_MYSTERY` (`include/battle.h`). #3 moves Ghost to special and Dark to physical, and #4 adds Fairy as special. Pick the type knowing which stat it will use. |
| `.secondaryEffectChance` | Percent chance of the effect's side effect. |
| `.target` | `MOVE_TARGET_SELECTED`, `_USER`, `_USER_OR_SELECTED`, `_BOTH` (both foes), `_FOES_AND_ALLY`, `_OPPONENTS_FIELD`, `_RANDOM`, `_DEPENDS` (in `include/battle.h`). |
| `.priority` | `s8`; Quick Attack is 1. |
| `.flags` | `FLAG_MAKES_CONTACT`, `FLAG_PROTECT_AFFECTED`, `FLAG_MAGIC_COAT_AFFECTED`, `FLAG_SNATCH_AFFECTED`, `FLAG_MIRROR_MOVE_AFFECTED`, `FLAG_KINGS_ROCK_AFFECTED` (`include/constants/pokemon.h`). Only 2 of the 8 bits are still free. |

### 3c. A new move effect

Only add one when no existing effect does the job.

1. `include/constants/battle_move_effects.h`: `#define EFFECT_NEW 214` and
   raise `NUM_BATTLE_MOVE_EFFECTS` to 215.
2. `data/battle_scripts_1.s`: append `.4byte BattleScript_EffectNew @
   EFFECT_NEW` at the **end** of `gBattleScriptsForMoveEffects` (it's
   positional, after `EFFECT_CAMOUFLAGE`), and write `BattleScript_EffectNew:`
   using the existing battle script macros. Copy the closest existing effect's
   script.
3. If the script needs logic the macros can't express, add a battle script
   command or a `callnative`-style helper in `src/battle_script_commands.c`.
4. **AI:** `data/battle_ai_scripts.s` scores moves by effect
   (`if_effect EFFECT_*, ...` in `AI_CheckBadMove`, `AI_CheckViability` and
   others). Add the new effect wherever the AI should avoid it (for example
   when it would fail) or prefer it. Also check `sIgnoredPowerfulMoveEffects`
   in `src/battle_ai_script_commands.c` for moves that shouldn't count as
   "most powerful".

### 3d. Animation

`gBattleAnims_Moves` points every move at an animation script in
`data/battle_anim_scripts.s`. A new move can:

- reuse an existing move's script (`.4byte Move_TACKLE` in its slot), or
- get a new `Move_NEW_MOVE:` script that combines **existing** sprites,
  particles, palettes and sound effects (`loadspritegfx`, `createsprite`,
  `playsewithpan`, `delay`, `waitforvisualfinish`, `end`).

Writing the script is code. New particle graphics or new sound effects are
art and sound, so a human makes them (AI policy). Check the animation in a
single and a double battle, and from both sides of the field.

### 3e. Learnsets, TMs, HMs and tutors

| What | Where | Notes |
|---|---|---|
| Level-up | `src/data/pokemon/level_up_learnsets.h` | `LEVEL_UP_MOVE(level, MOVE_*)`. Level up to 100, move ID ≤ 511. |
| Egg moves | `src/data/pokemon/egg_moves.h` | `egg_moves(SPECIES, MOVE_*, ...)`. |
| TMs/HMs | `include/constants/tms_hms.h` (`FOREACH_TM` / `FOREACH_HM`), plus each species' row in `src/data/pokemon/tmhm_learnsets.h` | There are exactly 50 TMs and 8 HMs, all items. Changing which move a TM teaches changes it for TMs already in players' bags (allowed, but call it out). Adding TMs means new items and a wider bitfield, so that needs its own issue. A new HM (Rock Climb, #40) replaces an HM slot or needs that issue. |
| Tutors | `gTutorMoves` and `TUTOR_MOVE_COUNT` (30) in `src/data/pokemon/tutor_learnsets.h` / `include/constants/party_menu.h`, plus each species' `TUTOR(...)` mask | The per-species mask is a `u32`, so only 2 more tutor moves fit before it has to grow. A one-time tutor uses a `FLAG_MOVE_TUTOR_TAUGHT_*` style flag (R6). |

---

## 4. Verification checklist

Copy this into the PR and tick what you actually did.

**Moves**

- [ ] `make` builds, and `MOVES_COUNT` is still ≤ 511.
- [ ] Single battle: the move hits, deals sensible damage for its category
  (check which attack stat it used), and applies its effect at the right
  chance.
- [ ] Double battle: it hits the right targets (`.target`), and its
  animation plays correctly from both sides.
- [ ] Interactions its flags imply: Protect, Magic Coat, Snatch, Mirror Move,
  King's Rock, contact abilities (Static, Rough Skin).
- [ ] The AI uses it sensibly, and doesn't use it when it would fail.
- [ ] Summary screen: name, type, power, accuracy, PP, description; contest
  view: category, appeal, jam, contest description.
- [ ] A contest with the move: appeal, combo, effect.
- [ ] Learned by level-up, TM/HM or tutor as intended; the Move Relearner
  offers it.
- [ ] Metronome can (or can't) call it, as intended.

**Abilities**

- [ ] `make` builds, and `ABILITIES_COUNT` is still ≤ 255.
- [ ] Summary screen: name and description, for both ability slots.
- [ ] It triggers when it should (switch-in, end of turn, on hit, …), shows
  its message, and doesn't trigger when it shouldn't.
- [ ] Interactions: Trace, Skill Swap and Role Play copy it (or fail) as
  intended.
- [ ] The AI doesn't walk into it (immunities and absorbs).
- [ ] Outside battle, if it has a field effect.

**Both**

- [ ] Vanilla save loads, saves and reloads intact (CI's save-load test).
- [ ] The PR states the vanilla trade/link caveat from section 1.
