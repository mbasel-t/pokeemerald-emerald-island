# Emerald Island: DLC design overview

This is the living design doc for what the DLC is. Rules about *how* it's
built (save compatibility, species budget, flags) are in
[CONTRIBUTING.md](../../CONTRIBUTING.md); this file covers *what* it adds.
Ideas here aren't commitments until they have an issue.

## Start trigger

- The DLC storyline begins when the player **talks to Mr. Briney after
  beating Wattson** (third badge, Dynamo Badge).
- Starting at the third badge lets players reach the new story early in a
  vanilla playthrough instead of only after the Elite Four.
- Existing saves that are already past this point must also be able to
  start the DLC the next time they talk to Briney.
- The trigger's "DLC started" state must use an unused vanilla flag or var
  (R6).

## Badge-based level curve

- Levels in DLC battles (trainers, and possibly wild Pokémon) scale with the
  number of badges the player has, so the DLC stays challenging whether it's
  played at 3 badges or 8.
- The curve tops out once the player becomes Champion.
- Open questions: exact level bands per badge count, whether wild encounters
  scale too, and whether scaling applies only to DLC areas or also to
  vanilla ones.

## Badge-gated story beats

- Story beats are locked behind badge counts so players can't get powerful
  Pokémon (including legendaries) too early.
- Gates read the vanilla badge flags (`FLAG_BADGE01_GET`..`FLAG_BADGE08_GET`)
  and, for post-game content, `FLAG_SYS_GAME_CLEAR`; DLC progress itself uses
  unused flags/vars (R6).
- Open questions: which beats and Pokémon sit behind which badge.

## Testing

- The playtest save for this start point is made after the third badge
  (#8) and is also the fixture for the automated save-compatibility test
  (#11).
