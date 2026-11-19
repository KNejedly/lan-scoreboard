"""Regenerace samostatného notebooku z verzovaných modulů projektu."""
import base64,hashlib,io,json,textwrap,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
buffer=io.BytesIO()
with zipfile.ZipFile(buffer,"w",zipfile.ZIP_DEFLATED) as bundle:
    for folder in ("lan","config","web","admin"):
        for f in sorted((root/folder).glob("*")):
            if f.is_file():bundle.write(f,f.relative_to(root).as_posix())
    bundle.write(root/"tests/ocr_fixture.py","ocr_fixture.py")
    bundle.write(root/"tests/synthetic-scoreboard.png","synthetic-scoreboard.png")
raw=buffer.getvalue()
cells=[]
def cell(kind,text,meta=None):
    c={"cell_type":kind,"id":"lan-"+str(len(cells)),"metadata":meta or {},"source":textwrap.dedent(text).strip().splitlines(True)}
    if kind=="code":c.update(outputs=[],execution_count=None)
    cells.append(c)
cell("markdown","""# LAN 11/2026 · zpracování výsledků
Spusťte **Prostředí → Spustit vše**. První spuštění použije tréninkovou databázi a skutečné bezplatné OCR na syntetickém snímku. Skóre 1 700 a 800 je očekávaný výsledek testu.

Pro zápis turnaje změňte v první buňce režim na **turnaj**, spusťte znovu všechny buňky a povolte připojení Disku. Jeden zapisující notebook na turnaj. Obrazovka pořadatele na konci nabízí výběr hráčů a zápasu, nahrání až tří snímků, kontrolu přepisu, změnu pořadí i ruční opravy.""")
cell("code",'''# @title Režim turnaje
REZIM = "trenink" # @param ["trenink", "turnaj"]
import sys, os, subprocess, tempfile
from pathlib import Path
from importlib.util import find_spec
if any(find_spec(m) is None for m in ("PIL","jsonschema","rapidocr","onnxruntime")):
    subprocess.check_call([sys.executable,"-m","pip","-q","install","Pillow>=10,<14","jsonschema>=4.18,<5","rapidocr>=3.3,<4","onnxruntime>=1.20,<2"])
print("Knihovny připraveny ·", REZIM)''')
cell("markdown","""### Společný procesor
Notebook má kopii stejného bodovacího modulu, formuláře a testu jako místní aplikace. Balíček se před rozbalením kontroluje pomocí SHA-256. Tato buňka může zůstat sbalená.""")
cell("code",'''# @title Načíst ověřený balíček aplikace
import base64, hashlib, io, zipfile
bundle = base64.b64decode("'''+base64.b64encode(raw).decode()+'''")
assert hashlib.sha256(bundle).hexdigest() == "'''+hashlib.sha256(raw).hexdigest()+'''"
APP = Path(tempfile.mkdtemp(prefix="lan-app-"))
with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
    archive.extractall(APP)
sys.path.insert(0,str(APP))
for name in list(sys.modules):
    if name=="lan" or name.startswith("lan.") or name=="ocr_fixture":
        del sys.modules[name]
from lan.store import Store,snapshot
from lan.vision import process
from lan.server import serve
from ocr_fixture import fixture
print("Procesor připraven.")''',{"cellView":"form"})
cell("code",'''# @title Ověřit obrázek, aliasy, přepočet a ochranu proti duplicitě
training = Store(tempfile.mkdtemp(prefix="lan-training-"))
training.player(0,"p01","ALFA",[])
training.player(1,"p02","BETA",[])
sample = (APP/"synthetic-scoreboard.png").read_bytes()
result = process(training,2,"hl","crossfire",["p01","p02"],[sample])
if not result["ok"]:
    from lan.vision import reader
    observed=reader()(sample)
    print("Kontrolní snímek:", observed.txts, observed.scores)
    raise AssertionError(str(result))
test_board = snapshot(*training.read())
assert [r["value"] for r in test_board["games"][0]["standings"]] == [1700,800]
assert not process(training,3,"hl","crossfire",["p01","p02"],[sample])["ok"]
print("TRÉNINK · ALFA 1 700 · BETA 800 · duplicitní zápis odmítnut")''')
cell("markdown","""### Úložiště a volitelné klíče
V turnajovém režimu se soukromá databáze, historie a původní obrázky ukládají do složky projektu na Disku. V Colab Secrets můžete povolit `OPENAI_API_KEY` pro placený model, `LAN_PUBLISH_URL` a `LAN_PUBLISH_TOKEN` pro aktualizace hostované stránky. Soukromý hosting navíc vyžaduje `LAN_SITES_BEARER`. Výchozí OCR pracuje bez API klíče. Po výpadku zůstane lokální zápis připravený k opětovnému odeslání.""")
cell("code",'''# @title Připojit turnajový archiv a připravit ovládání
try:
    from google.colab import drive, userdata, output
    COLAB=True
except ImportError:
    COLAB=False
def secret(name):
    if not COLAB: return os.environ.get(name,"")
    try: return userdata.get(name) or ""
    except Exception: return ""
remote=token=api=service=""
if REZIM=="turnaj":
    if COLAB:
        drive.mount("/content/drive")
        folder=Path("/content/drive/MyDrive/LAN Tournament Manager – listopad 2026")
    else:
        folder=Path(os.environ.get("LAN_STATE",".private"))
    if not folder.exists(): raise ValueError("Projektová složka nebyla nalezena. Ověřte připojený Google účet.")
    active=Store(folder)
    remote,token,api,service=(secret(n) for n in ("LAN_PUBLISH_URL","LAN_PUBLISH_TOKEN","OPENAI_API_KEY","LAN_SITES_BEARER"))
else:
    active=training
if "server" in globals():
    server.shutdown()
    server.server_close()
server,access=serve(active,port=0,remote=remote,token=token,openai_key=api,service=service)
print("Připraveno ·",REZIM,"· revize",active.read()[0])''')
cell("code",'''# @title Otevřít formulář pořadatele
from IPython.display import HTML,display
from html import escape
if COLAB:
    origin=output.eval_js("google.colab.kernel.proxyPort("+str(server.server_port)+")").rstrip("/")
else:
    origin="http://127.0.0.1:"+str(server.server_port)
# Odkaz obsahuje pouze krátkodobý přístup do tohoto běžícího notebooku.
display(HTML('<a target="_blank" rel="noopener noreferrer" href="'+escape(origin+'/admin/#'+access,quote=True)+'">Otevřít ovládání pořadatele</a>'))
print("Vyberte disciplínu, zápas a účastníky, přidejte snímek a stiskněte Přečíst snímky.")''')
cell("markdown","""**Při potížích** zkontrolujte přepis a doplňte prázdné buňky. Potvrdit ruční výsledek uloží opravu. Při změně už zapsaného výsledku zaškrtněte **Opravuji již uložený zápas**. Když Colab ukončí relaci, spusťte notebook znovu v režimu turnaj. Pro přenos práce mezi PC a Diskem nejprve zastavte zapisující relaci a přeneste aktuální soukromou databázi a složku screenshots. Před sdílením notebooku odstraňte výstupy buněk.""")
notebook={"nbformat":4,"nbformat_minor":5,"metadata":{"colab":{"name":"LAN_Tournament_AI_Processor.ipynb","provenance":[]},"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python"}},"cells":cells}
(root/"notebooks/LAN_Tournament_AI_Processor.ipynb").write_text(json.dumps(notebook,ensure_ascii=False,indent=1),encoding="utf-8")
