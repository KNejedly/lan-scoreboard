import hashlib
import base64
import json
import os
import urllib.error
import urllib.request
from contextlib import closing
from .scoring import Review
from .store import packed, snapshot

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def github_write(url, token, payload, baseline):
    """Optimistic GitHub Contents update scoped to a single public Pages feed."""
    import re
    if not re.fullmatch(r"https://api\.github\.com/repos/[\w.-]+/[\w.-]+/contents/web/state\.json",url):
        raise Review("Adresa GitHub musí vést na contents/web/state.json.")
    opener=urllib.request.build_opener(NoRedirect())
    headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","User-Agent":"LAN-Tournament-Manager"}
    with opener.open(urllib.request.Request(url,headers=headers),timeout=20) as response:
        entry=json.load(response)
    current=base64.b64decode(entry["content"])
    if current==payload:return
    seed=json.loads(current)
    initial=(seed.get("revision")==0 and seed.get("tournament")==CONFIG_ID and not seed.get("recent") and not seed.get("hasAwards"))
    if hashlib.sha256(current).hexdigest()!=baseline and not (baseline=="empty" and initial):
        raise Review("Na GitHubu jsou novější výsledky. Sjednoťte zdrojovou databázi.")
    body={"message":"Aktualizace veřejných výsledků LAN","sha":entry["sha"],"content":base64.b64encode(payload).decode()}
    with opener.open(urllib.request.Request(url,headers=headers,data=packed(body).encode(),method="PUT"),timeout=20) as response:
        if not json.load(response).get("commit",{}).get("sha"):raise Review("GitHub nepotvrdil commit.")

from .scoring import CONFIG
CONFIG_ID=CONFIG["id"]

def publish(store, url, token, service=""):
    if not url.startswith("https://") or not token:
        raise Review("Pro online zápis nastavte HTTPS adresu a publikační klíč.")
    with closing(store.connect()) as db, db:
        db.execute("BEGIN IMMEDIATE")
        rev,at,body=db.execute("SELECT id,at,body FROM revisions ORDER BY id DESC LIMIT 1").fetchone()
        payload=packed(snapshot(rev,at,json.loads(body))).encode()
        fingerprint=hashlib.sha256(payload).hexdigest()
        key="remote:"+url
        row=db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        baseline=row[0] if row else "empty"
        req=urllib.request.Request(url, data=payload, method="PUT",headers={"Content-Type":"application/json","Authorization":"Bearer "+token,"If-Match":baseline})
        if service:
            req.add_header("OAI-Sites-Authorization","Bearer "+service)
        try:
            if url.startswith("https://api.github.com/"):
                github_write(url,token,payload,baseline)
            else:
                with urllib.request.build_opener(NoRedirect()).open(req,timeout=20) as response:
                    if not json.load(response).get("saved"):
                        raise Review("Server nepotvrdil zápis.")
        except urllib.error.HTTPError as e:
            raise Review(f"Publikace selhala (HTTP {e.code}). Lokální zápis je uložen.") from None
        db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)",(key,fingerprint))
    return "Zapsáno na GitHub · čeká na nasazení Pages" if url.startswith("https://api.github.com/") else "Zveřejněno"
