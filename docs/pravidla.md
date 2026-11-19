# Podklady pro bodování LAN 11/2026

Kontrola z 19. listopadu 2026 vychází z místního souboru `Vyhodnocení LAN 11_2026.xlsx` a jeho stejnojmenné kopie v Google Sheets. List vyhodnocení uvádí 12 účastníků a čtyři hry. Age of Empires II mezi nimi uvedena není. Vstupní čísla v sešitu slouží jako kontrolní příklady. Doklad o odehrání listopadového zápasu k nim chybí.

| Disciplína | Co lze spočítat | Co vyžaduje další podklad |
|---|---|---|
| Half-Life | Na mapách Crossfire a Stalkyard platí `200 × kills − 100 × deaths`. Po obou mapách se skóre sčítá a následuje sestupný Excel RANK. Hráči se stejným součtem sdílejí místo. | Přepočet umístění na celkové body LAN. |
| Counter Strike 1.6 | Každá ze dvou map má části A a B. Pátou částí je fy_poolparty. Na všech pěti platí `200 × kills − 100 × deaths`. C48:C59 sčítá dílčí skóre, D48:D59 řadí sestupně. | Q1 a Q16 uvádějí bonus 1 000 za mapu. Buňky bonusu jsou prázdné a vzorec součtu sloupec Q vynechává. Před vyhlášením výsledku disciplíny musí pořadatel určit započtení a příjemce bonusu. Převod do bodů LAN chybí. |
| Warcraft 3 | Pro Divokou vodu, Tranquil Fury a Slalom je skóre součtem skóre za jednotky, suroviny a hrdiny, dále 100 za zničenou jednotku a 2 000 za zabitého hrdinu. C62:C73 sčítá **čtyři umístění**, včetně mapy UtherParty 4.0. | Umístění pro jednotlivá kola, vstupy pro UtherParty i pořadí disciplíny jsou ručně vyplněné. Sešit neurčuje algoritmus přidělení míst ani řešení shod. |
| Flatout 2 | C44:C55 sčítá tři umístění jednoho hráče z kombinované výsledkovky závodu K2:K13, společného závodu C22:C33 a destruction derby H22:H33. | Kvalifikace, přidělení finále A/B, převod finále do kombinované výsledkovky a konečné pořadí jsou ruční. Vzorec pro tyto převody, shody ani převod do bodů LAN nebyl nalezen. |

Na hlavním listu `Vyhodnocení` jsou C2:K13 prázdné. Vzorce L2:L13 porovnávají 12 řádků s devíti hodnotami K2:K10 a všech 12 uložených hodnot pořadí je `#N/A`. Pro vyhlášení celkového pořadí jsou potřeba ověřené převody bodů z her, pravidlo pro shody a opravený rozsah hráčů. Dílčí skóre různých her má rozdílné jednotky.

## Ověření proti sešitu

Porovnání všech 444 vzorců v pěti turnajových listech Excelu a Google Sheets vyšlo shodně po sjednocení oddělovačů argumentů. Nezávislý přepočet 432 číselných vzorců na čtyřech herních listech souhlasil s hodnotami uloženými v Excelu u všech 12 hráčů. Zbývajících 12 vzorců je na hlavním listu. List výdajů nebyl součástí kontroly bodování.

| List a buňky | Vstupy ze sešitu | Uložený výsledek |
|---|---|---:|
| Half-Life G2, G17, C33, D33 | 1 kill a 1 smrt na každé mapě | 100 a 100, součet 200, sdílené 1. místo |
| Counter Strike 1.6 G3, C49, D49 | 2 killy a 1 smrt v první části, 1 kill a 1 smrt v každé ze čtyř dalších | 300 v první části, celkem 700, 11. místo |
| Warcraft 3 J2, C62, D62 | Pět vstupů po 1, umístění 1 + 1 + 1 + 12 | Skóre mapy 2 103, součet umístění 15, ručně zadané pořadí 12 |
| Flatout 2 C44 | Tři umístění 1 + 1 + 1 | Součet 3 |

Kontrolní SHA-256 místního XLSX je `653e5ca96b538235deaac3615aa72fdf0c523f4872da6501ed8fea00b8e050f0`. Po změně sešitu je nutné kontrolu pravidel zopakovat.

## Dostupné screenshoty

V místních složkách her bylo vizuálně ověřeno sedm historických snímků. Šest pochází z FlatOutu 2 (čtyři z průběhu závodu a dva z výběru trati), jeden zachycuje začátek jiné mapy ve Warcraftu III. Žádný nedokládá konečný výsledek turnajového zápasu. Tyto snímky mohou ověřit odložení neúplných dat k ruční kontrole. Přesnost rozpoznávání výsledkovek na skutečných hrách vyžaduje fotografie nebo screenshoty ukončených zápasů.
