"""Build a Sites Worker in the selected checkout. Only a SHA-256 verifier enters the artifact."""
import base64
import json
from pathlib import Path
import sys

def build(root, out, verifier):
    web=root/"web"
    assets={name:[mime,base64.b64encode((web/name).read_bytes()).decode()] for name,mime in
            [("index.html","text/html; charset=utf-8"),("app.js","text/javascript; charset=utf-8"),
             ("style.css","text/css; charset=utf-8"),("arena.webp","image/webp")]}
    dest=out/"dist/server"; dest.mkdir(parents=True,exist_ok=True)
    source="const ASSETS="+json.dumps(assets)+";\nconst WRITE_VERIFIER="+json.dumps(verifier)+";\nconst INITIAL="+json.dumps((web/"state.json").read_text(encoding="utf-8"))+";\n"
    (dest/"index.js").write_text(source+(root/"cloud/worker.js").read_text(encoding="utf-8"),encoding="utf-8")
    manifest=out/".openai/hosting.json"
    m=json.loads(manifest.read_text(encoding="utf-8"));m.update(r2="BUCKET",d1=None)
    manifest.write_text(json.dumps(m,indent=2),encoding="utf-8")
    copy=out/"dist/.openai/hosting.json";copy.parent.mkdir(exist_ok=True);copy.write_bytes(manifest.read_bytes())

if __name__=="__main__":
    build(Path(__file__).resolve().parents[1],Path(sys.argv[1]),sys.argv[2])
