"""Veřejný projekční web a oddělené místní ovládání."""
import argparse
import base64
import hmac
import json
import mimetypes
import os
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .scoring import CONFIG, ROOT, Review
from .store import Store, packed, snapshot
from .publish import publish

ASSETS={"index.html","app.js","style.css","arena.webp"}
def serve(store, host="127.0.0.1",port=8765, admin=True, remote="", token="", openai_key="", service=""):
    if admin and host not in {"127.0.0.1","localhost","::1"}:
        raise Review("Ovládání vyžaduje místní adresu.")
    auth=secrets.token_urlsafe(32)
    def sync():
        if not remote: return "Uloženo lokálně"
        try: return publish(store,remote,token,service)
        except Exception as e:
            store.log("Čeká na publikaci",str(e))
            return "Uloženo lokálně. Online přenos čeká: "+str(e)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,code,body,mime="application/json; charset=utf-8"):
            if not isinstance(body,bytes):body=packed(body).encode()
            self.send_response(code);self.send_header("Content-Type",mime);self.send_header("Cache-Control","no-store")
            self.send_header("X-Content-Type-Options","nosniff");self.send_header("Content-Length",str(len(body)));self.end_headers()
            self.wfile.write(body)
        def trusted(self):
            return admin and hmac.compare_digest(self.headers.get("X-LAN-Session",""),auth)
        def do_GET(self):
            path=urlsplit(self.path).path
            if path=="/session" and admin:
                if self.headers.get("Host","").split(":")[0] not in {"localhost","127.0.0.1"} or self.headers.get("Sec-Fetch-Site","same-origin")!="same-origin":
                    return self.send(403,{})
                return self.send(200,{"token":auth})
            if path=="/api":
                if not self.trusted():return self.send(403,{})
                rev,at,state=store.read()
                return self.send(200,{"config":CONFIG,"rev":rev,"state":state,"history":store.history(),"online":bool(remote),"openai":bool(openai_key)})
            if path=="/state.json":return self.send(200,snapshot(*store.read()))
            name=path.strip("/") or "index.html"
            if name in ASSETS: file=ROOT/"web"/name
            elif name in {"admin","admin.js"} and admin:file=ROOT/"admin"/("index.html" if name=="admin" else name)
            else:return self.send(404,{})
            self.send(200,file.read_bytes(),mimetypes.guess_type(file.name)[0]+("; charset=utf-8" if file.suffix in (".html",".js",".css") else ""))
        def do_POST(self):
            if urlsplit(self.path).path!="/api" or not self.trusted():return self.send(403,{})
            try:
                length=int(self.headers.get("Content-Length",0))
                if not 0<length<=35_000_000:return self.send(413,{})
                req=json.loads(self.rfile.read(length));action=req["action"];rev=req["rev"]
                if action=="player":store.player(rev,req.get("pid"),req["public"],req["aliases"])
                elif action=="match":
                    # Link retained evidence only if it is actually present in this private archive.
                    digests=req.get("digests",[])
                    import re
                    if any(not re.fullmatch("[0-9a-f]{64}",d) or not list((store.folder/"screenshots").glob(d+".*")) for d in digests):
                        raise Review("Původní snímek nenalezen.")
                    store.match(rev,req["game"],req["slot"],req["rows"],req["expected"],manual=True,replace=req["replace"],digests=digests)
                elif action=="process":
                    from .vision import process
                    upload=[base64.b64decode(s,validate=True) for s in req["files"]]
                    out=process(store,rev,req["game"],req["slot"],req["expected"],upload,req["engine"],openai_key)
                    if out["ok"]:out["publication"]=sync()
                    return self.send(200,out)
                elif action=="cancel":store.cancel(rev,req["key"])
                elif action=="restore":store.restore(rev,int(req["target"]))
                elif action=="award":store.award(rev,req["game"],req["points"],req["source"])
                elif action!="publish":raise Review("Neznámá akce.")
                self.send(200,{"ok":True,"publication":sync()})
            except Exception as e:self.send(400,{"ok":False,"reason":str(e)[:500]})
    server=ThreadingHTTPServer((host,port),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server,auth


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--state",default=os.getenv("LAN_STATE",".private"))
    parser.add_argument("--port",type=int,default=8765);parser.add_argument("--display-port",type=int)
    parser.add_argument("--open",action="store_true");args=parser.parse_args()
    store=Store(args.state)
    if args.open:
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/state.json",timeout=1) as response:
                if json.load(response).get("tournament")==CONFIG["id"]:
                    webbrowser.open(f"http://127.0.0.1:{args.port}/admin/")
                    return
        except (OSError,ValueError):pass
    profile={}
    if (store.folder/"publish.dpapi").exists():
        from .windows_secrets import protect
        profile=json.loads(protect((store.folder/"publish.dpapi").read_bytes(),decrypt=True))
    server,_=serve(store,port=args.port,token=os.getenv("LAN_PUBLISH_TOKEN") or profile.get("token",""),
                   remote=os.getenv("LAN_PUBLISH_URL") or profile.get("url",""),
                   openai_key=os.getenv("OPENAI_API_KEY",""),service=os.getenv("LAN_SITES_BEARER") or profile.get("service",""))
    if args.display_port:serve(store,"0.0.0.0",args.display_port,False)
    url=f"http://127.0.0.1:{server.server_port}/admin/"
    print("Ovládání organizátora: "+url,flush=True)
    if args.open:webbrowser.open(url)
    try:threading.Event().wait()
    except KeyboardInterrupt:server.shutdown()

if __name__=="__main__":main()
