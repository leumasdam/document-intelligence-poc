"""Sample customer messages used by the classification demo."""

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
