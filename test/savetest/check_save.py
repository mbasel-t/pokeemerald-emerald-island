#!/usr/bin/env python3
"""Compare a loaded save against its expected values (issue #11).

Reads the result and memory dumps written by boot_save, decodes the player,
party, badges, money, Pokedex and location, and compares them against the
save's expected.json.

Usage: check_save.py <boot_save out_dir> <expected.json> [--repo <repo root>]
Exit codes: 0 all checks passed, 1 a check failed.
"""

import argparse
import json
import os
import re
import struct
import subprocess
import sys

# Offsets pinned to vanilla pokeemerald (include/global.h, include/pokemon.h).
SB2_PLAYER_NAME = 0x00
SB2_GENDER = 0x08
SB2_TRAINER_ID = 0x0A
SB2_PLAY_HOURS = 0x0E
SB2_PLAY_MINUTES = 0x10
SB2_POKEDEX = 0x18
POKEDEX_OWNED = 0x10
POKEDEX_SEEN = 0x44
SB2_ENCRYPTION_KEY = 0xAC
SB1_LOCATION = 0x04
SB1_PARTY_COUNT = 0x234
SB1_PARTY = 0x238
SB1_MONEY = 0x490
SB1_FLAGS = 0x1270

MON_SIZE = 100
MON_LEVEL = 0x54
NATIONAL_DEX_COUNT = 386
NUM_BADGES = 8

# Order of the Growth/Attacks/EVs/Misc substructs, indexed by personality % 24.
SUBSTRUCT_ORDERS = [
    "GAEM", "GAME", "GEAM", "GEMA", "GMAE", "GMEA",
    "AGEM", "AGME", "AEGM", "AEMG", "AMGE", "AMEG",
    "EGAM", "EGMA", "EAGM", "EAMG", "EMGA", "EMAG",
    "MGAE", "MGEA", "MAGE", "MAEG", "MEGA", "MEAG",
]


def decode_text(data):
    """Decode a Gen 3 string (letters, digits and space only)."""
    out = []
    for b in data:
        if b == 0xFF:
            break
        if 0xBB <= b <= 0xD4:
            out.append(chr(ord("A") + b - 0xBB))
        elif 0xD5 <= b <= 0xEE:
            out.append(chr(ord("a") + b - 0xD5))
        elif 0xA1 <= b <= 0xAA:
            out.append(chr(ord("0") + b - 0xA1))
        elif b == 0x00:
            out.append(" ")
        else:
            out.append("?")
    return "".join(out)


def read_defines(path, pattern):
    """Map value -> name for '#define NAME value' lines matching pattern."""
    names = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"#define\s+(%s)\s+(\d+)\s*$" % pattern, line)
            if m and int(m.group(2)) not in names:
                names[int(m.group(2))] = m.group(1)
    return names


def read_maps(path):
    """Map (group, num) -> MAP_ name from the generated map_groups.h."""
    maps = {}
    with open(path) as f:
        for line in f:
            m = re.match(r"\s*(MAP_\w+)\s*=\s*\((\d+)\s*\|\s*\((\d+)\s*<<\s*8\)\)", line)
            if m:
                maps[(int(m.group(3)), int(m.group(2)))] = m.group(1)
    return maps


def flag_set(flags, flag):
    return bool(flags[flag // 8] & (1 << (flag % 8)))


def read_dex_orders(path):
    """National Dex numbers of the Hoenn Dex entries, from constants/pokedex.h."""
    text = open(path).read()
    national_enum, hoenn_enum = re.findall(r"enum\s*\{(.*?)\};", text, re.S)[:2]
    national = {name: i for i, name in enumerate(re.findall(r"NATIONAL_DEX_(\w+)", national_enum))}
    hoenn = re.findall(r"HOENN_DEX_(\w+)", hoenn_enum)
    count = hoenn.index("DEOXYS")  # HOENN_DEX_COUNT
    return [national[name] for name in hoenn[1:count + 1]]


def count_dex(data, dex_numbers):
    """How many of the given National Dex numbers have their flag set."""
    return sum(1 for n in dex_numbers if data[(n - 1) // 8] & (1 << ((n - 1) % 8)))


def decode_mon(mon, species_names):
    personality, ot_id = struct.unpack_from("<II", mon, 0)
    order = SUBSTRUCT_ORDERS[personality % 24]
    growth = 0x20 + order.index("G") * 12
    key = personality ^ ot_id
    word0 = struct.unpack_from("<I", mon, growth)[0] ^ key
    species = word0 & 0xFFFF
    return {
        "species": species_names.get(species, str(species)),
        "nickname": decode_text(mon[8:18]),
        "level": mon[MON_LEVEL],
    }


def badge_flag_base(repo):
    """FLAG_BADGE01_GET, evaluated by running the C preprocessor on flags.h."""
    src = '#include "constants/flags.h"\nFLAG_BADGE01_GET\n'
    out = subprocess.run(["cpp", "-P", "-I", os.path.join(repo, "include"), "-"],
                         input=src, capture_output=True, text=True, check=True).stdout
    expr = out.strip().splitlines()[-1]
    if not re.fullmatch(r"[0-9a-fA-Fx+\-*() ]+", expr):
        raise ValueError("Unexpected FLAG_BADGE01_GET expansion: %r" % expr)
    return eval(expr)


def read_actual(out_dir, repo):
    result = {}
    with open(os.path.join(out_dir, "result.txt")) as f:
        for line in f:
            k, _, v = line.strip().partition("=")
            result[k] = v

    actual = {"save_status": int(result["save_status"]),
              "reached_overworld": result["reached_overworld"] == "1"}
    if not actual["reached_overworld"]:
        return actual

    sb1 = open(os.path.join(out_dir, "saveblock1.bin"), "rb").read()
    sb2 = open(os.path.join(out_dir, "saveblock2.bin"), "rb").read()
    species_names = read_defines(os.path.join(repo, "include/constants/species.h"), r"SPECIES_\w+")
    maps = read_maps(os.path.join(repo, "include/constants/map_groups.h"))
    badge01 = badge_flag_base(repo)
    hoenn_dex = read_dex_orders(os.path.join(repo, "include/constants/pokedex.h"))
    national_dex = range(1, NATIONAL_DEX_COUNT + 1)

    key = struct.unpack_from("<I", sb2, SB2_ENCRYPTION_KEY)[0]
    flags = sb1[SB1_FLAGS:]
    group, num = struct.unpack_from("<bb", sb1, SB1_LOCATION)
    party_count = sb1[SB1_PARTY_COUNT]

    actual.update({
        "player_name": decode_text(sb2[SB2_PLAYER_NAME:SB2_PLAYER_NAME + 8]),
        "gender": "female" if sb2[SB2_GENDER] else "male",
        "trainer_id": struct.unpack_from("<H", sb2, SB2_TRAINER_ID)[0],
        "money": struct.unpack_from("<I", sb1, SB1_MONEY)[0] ^ key,
        "badges": sum(flag_set(flags, badge01 + i) for i in range(NUM_BADGES)),
        "play_time": "%02d:%02d" % (struct.unpack_from("<H", sb2, SB2_PLAY_HOURS)[0], sb2[SB2_PLAY_MINUTES]),
        # The Pokedex screen shows Hoenn counts until the National Dex is unlocked.
        "pokedex_seen": count_dex(sb2[SB2_POKEDEX + POKEDEX_SEEN:], hoenn_dex),
        "pokedex_owned": count_dex(sb2[SB2_POKEDEX + POKEDEX_OWNED:], hoenn_dex),
        "national_dex_seen": count_dex(sb2[SB2_POKEDEX + POKEDEX_SEEN:], national_dex),
        "national_dex_owned": count_dex(sb2[SB2_POKEDEX + POKEDEX_OWNED:], national_dex),
        "map": maps.get((group, num), "%d.%d" % (group, num)),
        "party": [decode_mon(sb1[SB1_PARTY + i * MON_SIZE:SB1_PARTY + (i + 1) * MON_SIZE], species_names)
                  for i in range(min(party_count, 6))],
    })
    return actual


def minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir")
    parser.add_argument("expected")
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()

    expected = json.load(open(args.expected))
    actual = read_actual(args.out_dir, args.repo)
    failures = []

    def check(name, ok, exp, act):
        print("%-4s %-16s expected %-30s got %s" % ("ok" if ok else "FAIL", name, exp, act))
        if not ok:
            failures.append(name)

    check("save_status", actual["save_status"] == 1, "1 (SAVE_STATUS_OK)", actual["save_status"])
    check("reached_overworld", actual["reached_overworld"], True, actual["reached_overworld"])

    if actual["reached_overworld"]:
        for key, exp in expected.items():
            act = actual.get(key)
            if key == "play_time":
                # The clock keeps running after the save loads.
                ok = 0 <= minutes(act) - minutes(exp) <= 1
            else:
                ok = act == exp
            check(key, ok, exp, act)

    if failures:
        print("\n%d check(s) failed: %s" % (len(failures), ", ".join(failures)))
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
