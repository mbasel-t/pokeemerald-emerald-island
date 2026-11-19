# Adding an item

This is the workflow for adding a new item, including DLC key items, without
breaking vanilla saves. Items end up in saved data (the bag, the PC, held
items, the registered SELECT item), so the item ID you pick and the arrays you
leave alone matter more than the item data itself.

It follows the pret wiki's
[How To Add New Items](https://github.com/pret/pokeemerald/wiki/How-To-Add-New-Items),
adapted to this repo, where item IDs are an `enum` instead of `#define`s.

Rules this guide applies (see [CONTRIBUTING.md](../CONTRIBUTING.md) Part 1):
R2 (save layout), R6 (flags) and the AI policy (#2).

---

## 0. Before you start

From a human you need: the item's **name**, its **description** (three short
lines), its **icon** (24×24, 16 colors) and palette, and what it does.

Under the AI policy, Claude may wire an item in but must not write its name or
description or draw its icon. Until those exist, use `_("TODO_TEXT")` for the
text and `{gItemIcon_QuestionMark, gItemIconPalette_QuestionMark}` for the
icon.

Open (or find) an issue for the item and say which slot it takes.

---

## 1. Choose an item ID

Item IDs are stored as `u16` everywhere in the save (`struct ItemSlot`, held
items, `registeredItem`), so any ID below `ITEMS_COUNT` fits. **Never add a
new entry to the enum in `include/constants/items.h`, and never remove or
reorder one.** An item's ID is its position in the enum, so inserting a line
shifts every later item, and every saved bag would change meaning. Instead,
rename an unused entry in place.

### 1a. Unused placeholder slots

None of these are referenced anywhere outside the item tables (checked with
`git grep`), so no vanilla save can contain them:

| Slots | Count | Inside `ITEM_HAS_EFFECT` range? |
|---|---|---|
| `ITEM_034`…`ITEM_03E`, `ITEM_048`, `ITEM_052`, `ITEM_057`…`ITEM_05C`, `ITEM_063`…`ITEM_066`, `ITEM_069`, `ITEM_070`…`ITEM_078` | 33 | Yes |
| `ITEM_0E2`…`ITEM_0FD` | 28 | No |
| `ITEM_10B`, `ITEM_15B`, `ITEM_15C` | 3 | No |

That's 64 in all.

Exact names are in `include/constants/items.h`. Pick by what the item does:

- **Can be used on a Pokémon** (medicine, vitamins, evolution-style items):
  use a slot in the first group. `ITEM_HAS_EFFECT()` only lets items between
  `ITEM_POTION` and `ITEM_UNUSED_BERRY_3` be used on a Pokémon, and
  `gItemEffectTable` (`src/data/pokemon/item_effects.h`) is indexed by
  `item - ITEM_POTION`.
- **Anything else** (held items, general items, key items): either group.
  Prefer `ITEM_0E2` onward, to keep the first group free for medicine.

### 1b. FireRed/LeafGreen items

`ITEM_OAKS_PARCEL` to `ITEM_TEA`, plus `ITEM_RUBY` and `ITEM_SAPPHIRE`, are
FR/LG key items that Emerald defines but never gives out (23 items). Their
names, icons and descriptions are already in the tables, so reusing one means
replacing those too.

Don't reuse `ITEM_MYSTIC_TICKET`, `ITEM_AURORA_TICKET` or `ITEM_POWDER_JAR`.
Emerald uses all three.

Use FR/LG slots **only for key items**. Emerald links with FireRed and
LeafGreen, and an item ID sent over a link (for example a held item on a
traded Pokémon) keeps its FR/LG meaning on the other side. A key item can't be
held, so it never travels.

### 1c. Ranges that can't be extended

Some item categories are contiguous ranges with code that depends on them.
Adding to them is a separate issue, not this guide:

- **Poké Balls**: must stay first and contiguous (see the comment at the top
  of the enum; `MON_DATA_POKEBALL` is 4 bits in the save).
- **TMs/HMs**: `ITEM_TM01`…`ITEM_HM08` are contiguous, and each species'
  TM/HM compatibility is a bitfield.
- **Berries**: `FIRST_BERRY_INDEX`…`LAST_BERRY_INDEX` map to berry tree data,
  and saved berry trees store the berry ID.
- **Mail**: the mail range maps to mail designs stored in the save.

---

## 2. Every file to touch

The example renames `ITEM_0E2` to `ITEM_ISLAND_PASS` (a key item).

| File | Change |
|---|---|
| `include/constants/items.h` | Rename the enum entry in place: `ITEM_ISLAND_PASS, // was ITEM_0E2`. |
| `src/data/items.h` | Replace the slot's entry with the item's data (see 2a). |
| `src/data/text/item_descriptions.h` | `static const u8 sIslandPassDesc[] = _("...");`. Three lines of about 18 characters each, separated by `\n`. Human-written. |
| `graphics/items/icons/island_pass.png`, `graphics/items/icon_palettes/island_pass.pal` | The icon (24×24, 16 colors) and its palette. Human-made. |
| `include/graphics.h` | `extern const u32 gItemIcon_IslandPass[];` and `gItemIconPalette_IslandPass[]`. |
| `src/data/graphics/items.h` | `INCGFX_U32("graphics/items/icons/island_pass.png", ".4bpp.lz")` and the `.pal` → `.gbapal.lz` line, as the other items do. |
| `src/data/item_icon_table.h` | `[ITEM_ISLAND_PASS] = {gItemIcon_IslandPass, gItemIconPalette_IslandPass},`. |

When reusing an FR/LG item, also delete or comment out its old icon,
palette and description, so nothing is left pointing at the old item.

### 2a. The `src/data/items.h` entry

```c
[ITEM_ISLAND_PASS] =
{
    .name = _("TODO_TEXT"),          // up to 13 characters (ITEM_NAME_LENGTH is 14 with the terminator)
    .itemId = ITEM_ISLAND_PASS,      // the placeholder had ITEM_NONE here; set it
    .price = 0,                      // buy price; selling gives half
    .description = sIslandPassDesc,
    .importance = 1,                 // nonzero: can't be sold, tossed, given or stored in the PC
    .pocket = POCKET_KEY_ITEMS,
    .type = ITEM_USE_BAG_MENU,       // what happens after field use
    .fieldUseFunc = ItemUseOutOfBattle_CannotUse,
},
```

The other fields:

| Field | Meaning |
|---|---|
| `.holdEffect`, `.holdEffectParam` | Effect when held (`include/constants/hold_effects.h`). A new hold effect is handled in `ItemBattleEffects()` in `src/battle_util.c`. |
| `.pocket` | `POCKET_ITEMS`, `POCKET_KEY_ITEMS`, `POCKET_POKE_BALLS`, `POCKET_TM_HM` or `POCKET_BERRIES`. Don't put an item in the Balls, TM/HM or Berries pocket unless it's in that range (1c). |
| `.type` | `ITEM_USE_PARTY_MENU` (opens the party), `ITEM_USE_FIELD` (closes the bag and runs in the field), `ITEM_USE_BAG_MENU` (stays in the bag), `ITEM_USE_MAIL`, `ITEM_USE_PBLOCK_CASE`. |
| `.fieldUseFunc` | Overworld use. Existing ones are in `include/item_use.h` (`ItemUseOutOfBattle_Medicine`, `_Repel`, `_EvolutionStone`, `_CannotUse`, …). A new one goes in `src/item_use.c`. |
| `.battleUsage`, `.battleUseFunc` | Use from the bag in battle (`ITEM_B_USE_MEDICINE` / `ITEM_B_USE_OTHER`, and an `ItemUseInBattle_*` function). |
| `.secondaryId` | Extra data some functions read (rod type, bike type, mail index). |

### 2b. Getting it into the game

| How | Where |
|---|---|
| Shop | Add `.2byte ITEM_*` to a `pokemart` list in that map's `scripts.inc` (before `pokemartlistend`). The price comes from `.price`. |
| Item ball | An `OBJ_EVENT_GFX_ITEM_BALL` object in the map's `map.json` whose script is `finditem ITEM_*`, plus a **flag** (see section 4). |
| Hidden item | A `hidden_item` bg event in `map.json` with `"item"` and a **flag** (section 4). |
| Script gift | `giveitem ITEM_*`, usually guarded by a flag so it's given once. Check `checkitemspace` first if the pocket might be full. |
| Pickup | `sPickupItems` / `sRarePickupItems` in `src/battle_script_commands.c` (and the Battle Pyramid's own lists in `src/battle_pyramid.c`). Changing them changes vanilla Pickup odds, so only do it on purpose. |
| Held by wild Pokémon | `.itemCommon` / `.itemRare` in `src/data/pokemon/species_info.h`. |

---

## 3. Key items

- **Pocket space.** The key items pocket has 30 slots (`BAG_KEYITEMS_COUNT`),
  and that can't grow (R2). Vanilla Emerald already has more than 30 key items
  in total, though several are taken away after use (Devon Goods, Letter,
  Meteorite, the Abandoned Ship room keys). Before adding DLC key items, count
  the worst case a player could be holding at that point of the story. Prefer
  taking a DLC key item away (`removeitem`) once its job is done.
- **Registering.** Every key item shows USE and REGISTER
  (`sContextMenuItems_KeyItemsPocket` in `src/item_menu.c`), and the
  registered item is saved as `u16 registeredItem`. If the item does nothing
  in the field, use `ItemUseOutOfBattle_CannotUse` for now. Once #31 lands,
  follow its rule to hide USE and REGISTER for such items.
- **Importance.** Set `.importance = 1` so it can't be sold, tossed, given or stored in the PC.
- **Price.** Use `0`, which also means it can never be sold.

---

## 4. Flags for item balls, hidden items and gifts

Every item ball, hidden item and one-time gift needs a flag, so the item
doesn't come back after it's picked up. That's R6:

- Use only an unused vanilla flag, rename it in `include/constants/flags.h`
  to its new purpose with the original name in a comment, and check with
  `git grep` that vanilla never reads or writes it.
- **Hidden items** need a flag at or above `FLAG_HIDDEN_ITEMS_START` (0x1F4).
  The `bg_hidden_item_event` macro stores `flag - FLAG_HIDDEN_ITEMS_START`
  and stops the build if the flag is lower.
- Good places to look: `FLAG_UNUSED_0x264`…`FLAG_UNUSED_0x2BB`, right after
  the vanilla hidden-item flags, and `FLAG_UNUSED_0x493`…`FLAG_UNUSED_0x4EF`.
- Don't use `0x000`…`0x01F` (temporary flags, cleared on every map change) or
  `0x920`…`0x95F` (daily flags, cleared every day).
- List the flags you claim in the PR.

---

## 5. Save rules, summarized

- New item IDs are fine: all item fields in the save are `u16`.
- **Never** change pocket sizes (`BAG_*_COUNT`), PC item storage
  (`PC_ITEMS_COUNT`), the Battle Pyramid bag (`PYRAMID_BAG_ITEMS_COUNT`), or the
  layout of `struct ItemSlot`.
- **Never** add an `ITEMS_COUNT`-sized array to the save. Today there are none.
- Battle Pyramid bag quantities are `u8`. An item usable in the Pyramid must
  not need a stack above 255.
- Don't insert, remove or reorder item enum entries (section 1).

---

## 6. Verification checklist

Copy this into the PR and tick what you actually did.

- [ ] `make` builds.
- [ ] Bag: right pocket, name, icon, description; menu shows the right
  actions (USE, GIVE, TOSS, REGISTER).
- [ ] Buy it in the shop it's added to, at the right price; sell it for half,
  or confirm it can't be sold.
- [ ] Use it in the field and, if it has a battle use, in battle.
- [ ] Give it to a Pokémon and check the hold effect in battle (if any).
- [ ] Deposit it in the PC and withdraw it (or, for an important item, confirm the PC refuses it).
- [ ] Register it on SELECT (key items) and press SELECT in the field.
- [ ] Receive it from its item ball, hidden item or script; leave the map and
  come back to confirm it's gone (the flag works).
- [ ] Vanilla save loads, saves and reloads intact (CI's save-load test).
