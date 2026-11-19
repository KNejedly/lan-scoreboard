import copy
import hashlib
import json
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from .scoring import CONFIG, GAMES, Review, normalized, ranks, resolve_rows, score, slot_for


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def packed(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class Store:
    def __init__(self, folder):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.file = self.folder / "turnaj.sqlite"
        with closing(self.connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS revisions(id INTEGER PRIMARY KEY, at TEXT, action TEXT, body TEXT);
                CREATE TABLE IF NOT EXISTS log(id INTEGER PRIMARY KEY, at TEXT, status TEXT, detail TEXT);
                CREATE TABLE IF NOT EXISTS receipts(digest TEXT PRIMARY KEY, slot TEXT);
                CREATE TABLE IF NOT EXISTS budget(id INTEGER PRIMARY KEY, at TEXT, reserve INTEGER);
                CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
            """)
            roster_file = self.folder / "roster.json"
            aliases = json.loads(roster_file.read_text(encoding="utf-8")) if roster_file.exists() else {}
            players = {f"p{i:02}": {"public": f"Hráč {i:02}", "aliases": aliases.get(f"p{i:02}", [])} for i in range(1,13)}
            seed = {"players": players, "matches": {}, "awards": {}, "previous": {}}
            db.execute("INSERT OR IGNORE INTO revisions VALUES(0,?,?,?)", (None, "Založení turnaje", packed(seed)))

    def connect(self):
        return sqlite3.connect(self.file, timeout=15)

    def read(self, rev=None):
        with closing(self.connect()) as db:
            row = db.execute("SELECT id,at,body FROM revisions ORDER BY id DESC LIMIT 1" if rev is None
                             else "SELECT id,at,body FROM revisions WHERE id=?", () if rev is None else (rev,)).fetchone()
        if not row:
            raise Review("Revize nenalezena.")
        return row[0], row[1], json.loads(row[2])

    def log(self, status, detail):
        with closing(self.connect()) as db, db:
            db.execute("INSERT INTO log(at,status,detail) VALUES(?,?,?)", (now(), status, str(detail)[:2000]))

    def mutate(self, rev, action, update, digests=(), slot=""):
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            current, body = db.execute("SELECT id,body FROM revisions ORDER BY id DESC LIMIT 1").fetchone()
            if current != rev:
                raise Review("Data se mezitím změnila. Obnovte formulář.")
            state = json.loads(body)
            for digest in digests:
                prior = db.execute("SELECT slot FROM receipts WHERE digest=?", (digest,)).fetchone()
                if prior and prior[0] != slot:
                    raise Review("Stejný snímek je již přiřazen jinému zápasu.")
                db.execute("INSERT OR IGNORE INTO receipts VALUES(?,?)", (digest, slot))
            update(state)
            if packed(state) == body:
                return current
            db.execute("INSERT INTO revisions VALUES(?,?,?,?)", (rev+1, now(), action, packed(state)))
            return rev+1

    def player(self, rev, pid, public, aliases):
        public = public.strip()
        if not re.fullmatch(r"[\w .’'-]{1,30}", public):
            raise Review("Veřejná přezdívka má mít 1–30 znaků.")
        def update(state):
            players = state["players"]
            if not pid:
                new_id = f"p{max(int(k[1:]) for k in players)+1:02}"
            elif pid in players:
                new_id = pid
            else:
                raise Review("Neznámý hráč.")
            existing = {normalized(a) for k,p in players.items() if k != new_id for a in [p["public"], *p["aliases"]]}
            if any(normalized(a) in existing for a in [public,*aliases]):
                raise Review("Přezdívku již používá jiný hráč.")
            players[new_id] = {"public": public, "aliases": [a.strip() for a in aliases if a.strip()]}
        return self.mutate(rev, "Registrace / úprava hráče", update)

    def match(self, rev, game, slot, rows, expected, *, manual=False, replace=False, digests=()):
        spec = slot_for(game, slot)
        if spec["review"] and not manual:
            raise Review(spec["review"])
        key = game + "/" + slot
        def update(s):
            mapped = resolve_rows(s["players"], spec["fields"], rows, expected)
            result = {p: {"stats": stats, "score": score(game,slot,stats)} for p,stats in mapped.items()}
            if any(r["stats"].get("place", 1) > len(s["players"]) for r in result.values()):
                raise Review("Umístění přesahuje počet registrovaných hráčů.")
            previous = s["matches"].get(key)
            if previous and previous["rows"] == result:
                return
            if previous and not replace:
                raise Review("Zápas má jiný výsledek. Použijte výslovnou opravu.")
            s["matches"][key] = {"rows": result, "at": now(), "sequence": previous["sequence"] if previous else rev+1}
            if game in s["awards"]:
                s["previous"] = overall(s)[0]
                del s["awards"][game]
        return self.mutate(rev, "Oprava zápasu " + key if replace else "Zápis zápasu " + key, update, digests, key)

    def cancel(self, rev, key):
        def update(s):
            if key not in s["matches"]:
                raise Review("Zápas nenalezen.")
            del s["matches"][key]
            s["previous"] = overall(s)[0]
            s["awards"].pop(key.split("/")[0], None)
        return self.mutate(rev, "Zrušení zápasu " + key, update)

    def award(self, rev, game, points, source):
        if not source.strip() or game not in GAMES:
            raise Review("Uveďte schválený zdroj bodů.")
        def update(s):
            if not all(game+"/"+m["id"] in s["matches"] for m in GAMES[game]["slots"]):
                raise Review("Nejprve dokončete všechny zápasy disciplíny.")
            participants = {p for key,m in s["matches"].items() if key.split("/")[0]==game for p in m["rows"]}
            if set(points) != participants or any(type(v) is not int or abs(v)>10000000 for v in points.values()):
                raise Review("Schválené body musí být zadány pro všechny účastníky disciplíny.")
            s["previous"] = overall(s)[0]
            s["awards"][game] = {"points":points,"source":source.strip()}
        return self.mutate(rev, "Schválené LAN body · "+game, update)

    def restore(self, rev, target):
        if type(target) is not int or not 0 <= target < rev:
            raise Review("Vyberte starší revizi.")
        old = self.read(target)[2]
        return self.mutate(rev, f"Obnova revize {target}", lambda s:(s.clear(), s.update(old)))

    def history(self):
        with closing(self.connect()) as db:
            return {"changes":db.execute("SELECT id,at,action FROM revisions ORDER BY id DESC LIMIT 100").fetchall(),
                    "processing":db.execute("SELECT at,status,detail FROM log ORDER BY id DESC LIMIT 60").fetchall()}


def overall(s):
    points = {}
    for award in s["awards"].values():
        for p,n in award["points"].items():
            points[p] = points.get(p,0) + n
    return ranks(points), points


def snapshot(rev, at, s):
    nick = lambda p: s["players"][p]["public"]
    places, points = overall(s)
    board = [{"name":nick(p),"rank":places.get(p),"points":points.get(p),
              "delta":s["previous"][p]-places[p] if p in places and p in s["previous"] else None} for p in s["players"]]
    board.sort(key=lambda v: (v["rank"] or 999, v["name"]))
    games, recent = [], []
    for g in CONFIG["games"]:
        totals,counts,history = {},{},[]
        for slot in g["slots"]:
            match = s["matches"].get(g["id"]+"/"+slot["id"])
            if not match:
                continue
            rows = []
            for p,r in match["rows"].items():
                value = r["stats"]["place"] if g["sort"]=="low" else r["score"]
                totals[p] = totals.get(p,0)+value
                counts[p] = counts.get(p,0)+1
                rows.append({"name":nick(p),"value":value,"score":r["score"],"stats":{CONFIG["labels"][k]:v for k,v in r["stats"].items()}})
            rr = ranks({r["name"]:r["value"] for r in rows}, g["sort"]=="low")
            for r in rows:
                r["rank"] = r["value"] if g["sort"]=="low" else rr[r["name"]]
            rows.sort(key=lambda r:r["rank"])
            history.append({"title":slot["title"],"game":g["name"],"at":match["at"],"seq":match["sequence"],"rows":rows})
        # Sums of placements across unequal starts would reward absences.
        comparable = {p:n for p,n in totals.items() if g["sort"]!="low" or counts[p]==len(history)}
        positions = ranks(comparable) if g["sort"]=="high" else {}
        standings = sorted([{"name":nick(p),"value":v,"rank":positions.get(p)} for p,v in totals.items()],
                           key=lambda r:(r["value"] if g["sort"]=="low" else -r["value"],r["name"]))
        history.sort(key=lambda r:r["seq"],reverse=True)
        recent.extend(history)
        games.append({**{k:g[k] for k in ("id","name","genre","color","mark","metric","sort")},
                      "planned":len(g["slots"]),"count":len(history),"standings":standings,"history":history,
                      "provisional":g["id"] in ("cs","fo","wc"),"awarded":g["id"] in s["awards"]})
    return {"schema":1,"tournament":CONFIG["id"],"revision":rev,"updated":at,"players":len(board),
            "board":board,"games":games,"recent":sorted(recent,key=lambda r:r["seq"],reverse=True),
            "hasAwards":bool(points)}
