# LAN Tournament Manager · Pivní Burza

České ovládání výsledků LAN 11/2026. Turnaj obsahuje Half-Life, Counter-Strike 1.6, Warcraft III a FlatOut 2. Před prvním zápasem ukazuje veřejný přehled pouze program a počty. Individuální výsledky se objeví po zápisu pořadatelem. Přehled kontroluje data každých pět sekund a při výpadku ponechá poslední načtený stav.

## Začít na Windows

Otevřete **Spustit LAN.cmd**. V přenosné kopii spouštěč potřebuje Python 3.12 nebo 3.13 a při první instalaci přístup na internet. Před akcí ověřte OCR na přiloženém snímku v tréninkovém režimu notebooku. Na tomto počítači připravený spouštěč používá již nainstalované knihovny a turnajovou databázi. Dashboard je na `http://127.0.0.1:8765/`, ovládání na `http://127.0.0.1:8765/admin/`. Pro jiný počítač v LAN nabízí níže uvedený příkaz samostatný port pouze ke čtení.

```sh
python -m venv .venv
# Aktivujte virtuální prostředí podle systému.
python -m pip install -r requirements.txt
python -m lan.server --state .private --port 8765 --display-port 8766
```

Na druhém počítači otevřete adresu pořadatelského počítače na portu 8766. Ovládací port 8765 naslouchá na místní smyčce. Ubuntu a macOS vyžadují pro modely OCR podporovanou sestavu ONNX Runtime.

## Sedm úkonů pořadatele

1. **Promítání.** Otevřete dashboard, stiskněte **TV / Projektor** a případně **Celá obrazovka** nebo F11. Obrazovky se střídají po 14 sekundách. Střídání lze pozastavit.
2. **Screenshot.** V notebooku spusťte všechny buňky. Pro skutečnou akci zvolte režim **turnaj**. V poslední buňce otevřete ovládání pořadatele. Vyberte hru, konkrétní zápas a jeho účastníky, přidejte jeden až tři snímky a stiskněte **Přečíst snímky**. Stejný formulář je na PC. Původní soubory zůstávají v soukromé složce screenshots.
3. **Potvrzení.** Po úspěchu formulář vypíše stav a revizi. Stav „Uloženo lokálně“ potvrzuje zápis v místní databázi. Stav přenosu na GitHub potvrzuje commit. Vystavení na Pages proběhne až po dokončení nasazení. Na kartě hry přibude zápas.
4. **Oprava.** Zvolte uložený zápas, opravte statistiky, zaškrtněte **Opravuji již uložený zápas** a potvrďte. **Zrušit tento zápas** jej odebere z výsledků. V historii je možné obnovit dřívější stav jako novou revizi.
5. **Hráči.** V části **Hráči a přezdívky** upravte veřejnou přezdívku a soukromé herní aliasy. Položka **Nový hráč** registruje dalšího účastníka. Veřejnou přezdívku vyplňte podle přání hráče. Soukromé názvy se do veřejného exportu nepřenášejí.
6. **Další zápas.** Vyberte další připravený slot, zkontrolujte sestavu a zadejte výsledky. Čtrnáct slotů odpovídá agregaci v Excelu. Pro nový formát nebo změnu programu upravte konfiguraci a nechte zkontrolovat bodovací postup. Celkové LAN body lze po dokončení disciplíny zadat z pořadatelem schváleného vyhodnocení včetně jeho zdroje.
7. **Výpadek.** Nečitelný snímek přejde k ruční kontrole. Při výpadku internetu použijte místní formulář. Uložte nebo opravte zápas jako obvykle. Po návratu připojení zvolte **Znovu odeslat aktuální stav**. Během výpadku zůstává již otevřená projekce čitelná.

## Data a bodování

`config/tournament.json` popisuje disciplíny, zápasy, sloupce a důvody ruční kontroly. `lan/scoring.py` kontroluje jednotlivé statistiky, páruje aliasy a stanoví skóre. Doklady po buňkách a omezení jsou v [auditu vzorců](docs/pravidla.md).

Soutěže mají jiné jednotky skóre. Celkový žebříček vzniká až přidělením doložených LAN bodů. Ruční příděl se eviduje se zdrojem a při opravě výsledku disciplíny se zneplatní. Součet potvrzených LAN bodů používá sestupné sdílené pořadí; jde o provozní konvenci z principu RANK. Finální rozhodnutí o nerozhodném výsledku přísluší pořadateli. U Warcraftu a FlatOutu zobrazuje systém součet ručně zaznamenaných umístění. Konečné pořadí těchto disciplín se z Excelu jednoznačně odvodit nedá.

`lan/store.py` uchovává transakční revize v SQLite, historii zpracování, kontrolní součty obrázků a stav přenosu. Dashboard vzniká vždy novým výpočtem z platných zápasů. Zdrojová evidence je soukromá. Git i nasazení Pages vylučují databáze a screenshoty. Pro obnovu celého turnaje zastavte zapisující proces a zálohujte celou složku uvedenou v **--state**, včetně databáze a obrázků. Při přechodu mezi PC a Colabem zkopírujte poslední archiv a pokračujte v jedné zapisující relaci.

## Rozpoznávání a rozpočet

Výchozí RapidOCR používá místní neuronové modely. Automaticky přijímá úplnou a jasně označenou konečnou tabulku s doloženou hrou, mapou, podporovanými hlavičkami a sestavou. Ostatní rozvržení vyžadují ověření. Pro čtení složitějších výsledkovek je připraven OpenAI Responses API s obrazovým vstupem, modelem **gpt-5.4-nano** a striktním JSON schématem. Původní snímky se archivují soukromě; do API se při této volbě předává převzorkovaný obrázek bez původních metadat. Nastavte `OPENAI_API_KEY` v Colab Secrets nebo v prostředí lokálního serveru. V tréninkovém režimu se placená větev nepoužívá.

Na jeden placený pokus se v databázi rezervuje 5 Kč, po 20 pokusech placený režim přestane odesílat. Rezerva se počítá i při timeoutu. Je to konzervativní provozní limit pro jedinou turnajovou databázi. Skutečnou fakturaci spravuje poskytovatel; kopie databáze mají samostatný limit. Ověřený ceník modelu činil 0,20 USD za milion vstupních a 1,25 USD za milion výstupních tokenů. [Model a ceny](https://developers.openai.com/api/docs/models/gpt-5.4-nano) · [Obrazové vstupy](https://developers.openai.com/api/docs/guides/images-vision)

## Online publikace

GitHub Pages vystavuje jen složku **web**. Zdroj nasazení je možné nastavit na **GitHub Actions**. Workflow nejprve spustí testy. Pokud je nastavená proměnná repozitáře `LAN_PUBLIC_FEED`, stránka čte veřejný HTTPS JSON z této adresy (vyžaduje CORS). Výchozí relativní `state.json` funguje na Pages i v lokální síti.

Pro průběžnou aktualizaci souboru na GitHubu nastavte v Colab Secrets nebo prostředí zapisující aplikace:

- `LAN_PUBLISH_URL` na `https://api.github.com/repos/KNejedly/lan-scoreboard/contents/web/state.json`.
- `LAN_PUBLISH_TOKEN` na časově omezený fine-grained token pro jediný repozitář s oprávněním Contents: read and write. Do formuláře nadpisů, buněk nebo zdrojových souborů klíč nepatří.

Po validním zápisu procesor odešle pouze veřejný přehled. API před změnou kontroluje blob SHA a otisk posledního potvrzeného obsahu. Při souběhu nebo výpadku zůstane místní zápis zachován. První připojení akceptuje prázdný startovní stav; později vyžaduje databázi odpovídající poslednímu přenosu. Publikace Pages může mít zpoždění při čekání na GitHub Actions či CDN.

Alternativní server v **cloud/worker.js** umí přijímat stejný přehled pod HTTPS, atomicky jej zapisuje do R2 a kontroluje oprávnění a předchozí otisk. Nasazení používá ověřovací SHA-256 publikačního klíče; samotný klíč do zdrojů nepatří. U soukromé instance vyžaduje platforma také `LAN_SITES_BEARER`. Složka **cloud** obsahuje reprodukovatelný sestavovací skript. Tento projekt pro normální provoz nevyžaduje Firebase ani trvale spuštěný Colab.

## Testování

```sh
python -m unittest discover -s tests -v
```

Pro test skutečného OCR přidejte proměnnou prostředí **LAN_TEST_OCR=1**. **tests/synthetic-scoreboard.png** je umělá izolovaná výsledkovka pro trénink. Shoda s ní nedokládá přesnost pro libovolný herní HUD. **notebooks/build_notebook.py** vloží aktuální moduly a referenční snímek do přenosného notebooku. Testovací data nevkládejte do ostré databáze.
