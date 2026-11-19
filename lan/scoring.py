"""Ověřené dílčí výpočty. Turnajové body se zadávají podle schváleného podkladu."""
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config/tournament.json").read_text(encoding="utf-8"))
GAMES = {g["id"]: g for g in CONFIG["games"]}


class Review(ValueError):
    """Konkrétní důvod k zásahu pořadatele."""


def normalized(name):
    return unicodedata.normalize("NFKC", str(name)).strip().casefold()


def slot_for(game, slot):
    for spec in GAMES.get(game, {}).get("slots", []):
        if spec["id"] == slot:
            return spec
    raise Review("Neznámá hra nebo zápas.")


def score(game, slot, stats):
    spec = slot_for(game, slot)
    if set(stats) != set(spec["fields"]):
        raise Review("Chybějící nebo nadbytečná statistika.")
    for field, value in stats.items():
        if type(value) is not int or not (int(field == "place") <= value <= 10_000_000):
            raise Review("Neplatná hodnota: " + CONFIG["labels"][field])
    if game in {"hl", "cs"}:
        return 200 * stats["kills"] - 100 * stats["deaths"]
    if game == "wc" and slot != "uther":
        return (stats["unit_score"] + stats["resource_score"] + stats["hero_score"]
                + 100 * stats["units_killed"] + 2000 * stats["heroes_killed"])
    return None


def ranks(values, low=False):
    ordered = sorted(values.values(), reverse=not low)
    return {p: ordered.index(v) + 1 for p, v in values.items()}


def resolve_rows(players, fields, rows, expected):
    if not expected or len(set(expected)) != len(expected) or not set(expected) <= players.keys():
        raise Review("Vyberte skutečné účastníky zápasu.")
    aliases = {normalized(a): key for key, p in players.items() for a in [p["public"], *p["aliases"]]}
    out = {}
    for row in rows:
        pid = aliases.get(normalized(row["nick"]))
        if pid is None or pid in out:
            raise Review("Neznámá nebo opakovaná přezdívka: " + str(row["nick"]))
        stats = row["stats"]
        if set(stats) != set(fields):
            raise Review("Sloupce se neshodují se zápasem.")
        out[pid] = stats
    if set(out) != set(expected):
        raise Review("Hráči na snímku neodpovídají zvolené sestavě.")
    return out
