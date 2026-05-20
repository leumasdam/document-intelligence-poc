"""Sample customer messages used by the classification & summarization demos."""

SAMPLE_CASES: dict[str, dict[str, str]] = {
    "accident": {
        "title": "Car accident report",
        "body": """Dobrý deň,

dnes ráno (14.5.2026) o 7:40 sa mi stala dopravná nehoda na križovatke Einsteinova / Petržalská v Bratislave. Druhé vozidlo mi nedalo prednosť pri odbočovaní vľavo a poškodilo mi pravý predný blatník, svetlo a nárazník. Druhý vodič odmieta priznať vinu, ale máme záznam z palubnej kamery aj zápisnicu od polície.

Moja zmluva: HV-99 88 77 66 55, havarijné poistenie (KASKO).
Auto: Škoda Octavia, EČV BA-123XY.

Prosím o čo najrýchlejšie spracovanie — bez auta sa neviem dostať do práce. K dispozícii mám fotky, policajný záznam aj kontakt na druhého vodiča. Auto je odtiahnuté v servise Auto Palace Bratislava.

S pozdravom,
Ján Novák
+421 905 123 456""",
    },
    "complaint": {
        "title": "Payment delay complaint",
        "body": """Dobrý deň,

už druhý mesiac čakám na výplatu poistného plnenia za škodovú udalosť ŠU-2026-02-1102 (poškodenie strechy búrkou z februára 2026). Likvidácia bola ukončená 28.3.2026 s priznanou sumou 3 200 EUR, no na účet mi stále nič neprišlo. Volal som 3× na infolinku, vždy mi povedia "už to spracovávame".

Toto je posledné upozornenie pred tým, ako sa obrátim na Slovenskú obchodnú inšpekciu a Národnú banku Slovenska. Žiadam okamžité vysvetlenie a vyplatenie do 5 pracovných dní, inak budem konať právnou cestou.

S pozdravom,
Pavol Horváth
pavol.horvath@example.sk""",
    },
    "address": {
        "title": "Address change request",
        "body": """Dobrý deň,

oznamujem zmenu trvalej adresy.
Stará: Hlavná 12, 851 01 Bratislava
Nová: Vajnorská 89, 831 04 Bratislava
Platí od 1.6.2026.

Týka sa nasledujúcich aktívnych zmlúv:
- Povinné zmluvné poistenie: PZP-22 33 44 55
- Životné poistenie: ZP-12 12 12 12

Prosím o aktualizáciu kontaktných údajov a zaslanie dodatkov k zmluvám na novú adresu (alebo elektronicky).

Ďakujem,
Eva Kováčová""",
    },
    "policy_question": {
        "title": "Pre-sales question about travel cover",
        "body": """Dobrý deň,

uvažujem o uzavretí cestovného poistenia na 10-dňovú dovolenku do Chorvátska v júni 2026. Mám aktívne havarijné poistenie (HV-44 55 66 77) — zahŕňa cestovanie autom do zahraničia aj liečebné náklady, alebo musím dokupovať samostatné cestovné poistenie?

Tiež by ma zaujímalo, či sa dá pripoistiť aj batožina a koľko by stálo pripoistenie pre dve deti (5 a 8 rokov).

Vopred ďakujem za informácie,
Mária Tóthová""",
    },
}


SAMPLE_NARRATIVES: dict[str, dict[str, str]] = {
    "property": {
        "title": "Long property-damage narrative",
        "body": """Dobrý deň,

obraciam sa na Vás vo veci poistnej udalosti na našom rodinnom dome na adrese Záhradnícka 47, 902 01 Pezinok. Dom je poistený zmluvou č. MAJ-55 44 33 22 11, poistenie nehnuteľnosti aj domácnosti.

V noci z 11. na 12. mája 2026 sa nad Pezinkom prehnala silná búrka s krupobitím. Ráno 12.5.2026 sme zistili rozsiahle škody. Na streche je poškodených odhadom 30 až 40 škridiel, dve strešné okná majú prasknuté sklo a do podkrovia začalo zatekať. Voda stiekla po stene a poškodila sadrokartónový strop v jednej z detských izieb, ktorý bude treba kompletne vymeniť. Zároveň nám krupobitie dorezalo plastovú fasádu na južnej strane domu a rozbilo sklo na skleníku v záhrade, ten ale asi nie je súčasťou poistenia, to mi nie je jasné.

Hneď ráno 12.5. som volal na infolinku, kde mi povedali, že mám spísať škodu a poslať fotky, čo robím teraz. Fotky prikladám v prílohe — je ich 24, snažil som sa zachytiť všetko. Provizórne sme strechu prekryli plachtou, aby ďalej nezatekalo, faktúru za plachtu a prácu suseda, ktorý mi pomáhal, vo výške 180 eur tiež prikladám.

Volal som aj pokrývačovi, ten príde obhliadnuť strechu až 19.5.2026 a predbežne odhaduje opravu strechy na 2 800 až 3 500 eur podľa toho, koľko latovania bude treba meniť. Výmena dvoch strešných okien je podľa neho ďalších cca 900 eur. Sadrokartón a maľovanie detskej izby neviem odhadnúť, hľadám firmu.

Chcem sa spýtať na niekoľko vecí. Po prvé, je toto krytá udalosť? Po druhé, mám čakať na Vašu obhliadku, alebo môžem dať opravovať hneď ako príde pokrývač, lebo sa bojím ďalšieho dažďa? Po tretie, ako je to s tým skleníkom. A po štvrté, dokedy zhruba môžem očakávať vyriešenie, lebo s malými deťmi v dome, kde jedna izba nie je obývateľná, je to dosť nepríjemné.

Vopred ďakujem za odpoveď a budem rád za čo najrýchlejšie riešenie.

S pozdravom,
Martin Belko
tel. 0907 445 221""",
    },
    "dispute": {
        "title": "Disputed claim — email thread",
        "body": """--- Pôvodná správa, 28.4.2026 ---
Dobrý deň, posielam vyúčtovanie škody na vozidle po nehode z 14.4.2026, škodová udalosť ŠU-2026-04-2031. Servis Auto Centrum vyčíslil opravu na 4 120 eur. Faktúru prikladám. Žiadam o preplatenie. J. Hraško

--- Odpoveď poisťovne, 6.5.2026 ---
Dobrý deň, na základe obhliadky nášho technika uznávame škodu vo výške 2 950 eur. Rozdiel oproti faktúre servisu je v tom, že časť poškodení (zadný nárazník, ľavé dvere) podľa nášho technika nesúvisí s nahlásenou nehodou a javí sa ako staršie poškodenie. Plnenie 2 950 eur Vám bude vyplatené do 10 dní.

--- Reakcia klienta, 7.5.2026 ---
Dobrý deň, s týmto zásadne nesúhlasím. Zadné dvere aj nárazník boli poškodené PRESNE pri tejto nehode, žiadne staršie poškodenie auto nemalo, kúpil som ho pred 8 mesiacmi a mám servisnú knihu. Váš technik bol pri aute 4 minúty, ledva sa naň pozrel. Mám fotky z miesta nehody hneď po náraze, kde je jasne vidno poškodené dvere. Tie fotky som Vám už raz posielal. Žiadam o nové, poriadne posúdenie alebo mi vysvetlite, na základe čoho tvrdíte, že ide o staršie poškodenie. Takto sa so zákazníkmi nejedná. Ak sa to nevyrieši, obrátim sa na ombudsmana aj na Národnú banku Slovenska a tiež zvážim právne kroky. Čakám na vašu odpoveď do konca týždňa.

J. Hraško""",
    },
}
