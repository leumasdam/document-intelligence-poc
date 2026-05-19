"""Generate a realistic Slovak car-insurance claim form PDF.

Run once to produce sample-data/claim-form.pdf. Output is committed to the repo
so consumers don't need fpdf2 installed.
"""
from pathlib import Path

from fpdf import FPDF


OUT = Path(__file__).resolve().parent.parent / "sample-data" / "claim-form.pdf"


def build() -> None:
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_margins(left=20, top=18, right=20)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Header — fake UNIQA-style banner
    pdf.set_fill_color(0, 47, 95)
    pdf.rect(0, 0, 210, 22, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(20, 6)
    pdf.cell(0, 10, "UNIQA", align="L")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(20, 15)
    pdf.cell(0, 4, "Poistovna a.s.   |   Lazaretska 15, 820 07 Bratislava", align="L")

    # Title
    pdf.set_text_color(0, 47, 95)
    pdf.set_xy(20, 32)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, "Oznamenie poistnej udalosti", align="L")
    pdf.set_xy(20, 41)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "Havarijne poistenie motoroveho vozidla", align="L")

    # Reference block (right side)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(130, 32)
    pdf.cell(0, 5, "Cislo skodovej udalosti:", align="L")
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(130, 37)
    pdf.cell(0, 5, "SU-2026-04-1882", align="L")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(130, 44)
    pdf.cell(0, 5, "Datum prijatia: 17.05.2026", align="L")
    pdf.set_xy(130, 49)
    pdf.cell(0, 5, "Likvidator: M. Kovacova", align="L")

    pdf.set_draw_color(220, 220, 220)
    pdf.line(20, 58, 190, 58)

    # Policy details
    y = 64
    pdf.set_text_color(0, 47, 95)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(20, y)
    pdf.cell(0, 5, "POISTNA ZMLUVA", align="L")
    y += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Cislo poistnej zmluvy:")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(65, y); pdf.cell(0, 5, "HV-99 88 77 66 55")

    y += 6
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Typ poistenia:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "Havarijne poistenie (KASKO)")

    y += 6
    pdf.set_xy(20, y); pdf.cell(45, 5, "Splatnost zmluvy:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "01.01.2026 - 31.12.2026")

    # Policyholder
    y += 12
    pdf.set_text_color(0, 47, 95)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(20, y); pdf.cell(0, 5, "POISTNIK")
    y += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Meno a priezvisko:")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(65, y); pdf.cell(0, 5, "Jan Novak")

    y += 6
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Adresa:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "Hlavna 12, 851 01 Bratislava")

    y += 6
    pdf.set_xy(20, y); pdf.cell(45, 5, "Rodne cislo:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "780304/1234")

    # Incident
    y += 12
    pdf.set_text_color(0, 47, 95)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(20, y); pdf.cell(0, 5, "UDAJE O SKODOVEJ UDALOSTI")
    y += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Datum udalosti:")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(65, y); pdf.cell(0, 5, "14.05.2026")

    y += 6
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Miesto:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "Krizovatka Einsteinova / Petrzalska, Bratislava")

    y += 6
    pdf.set_xy(20, y); pdf.cell(45, 5, "Typ skody:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "Dopravna nehoda - kolizia s inym vozidlom")

    y += 8
    pdf.set_xy(20, y); pdf.cell(45, 5, "Popis udalosti:")
    pdf.set_xy(65, y)
    pdf.multi_cell(
        125,
        5,
        "Pri odbocovani vlavo z hlavnej cesty doslo k boku kolizii s vozidlom, "
        "ktore neumoznilo vjazd. Skoda na pravej strane vozidla - naraznik, "
        "predne svetlo a blatnik.",
    )

    # Damage breakdown (looks like an invoice — extractor reuses the same schema)
    y = pdf.get_y() + 6
    pdf.set_text_color(0, 47, 95)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(20, y); pdf.cell(0, 5, "VYCISLENIE SKODY")
    y += 8

    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_xy(20, y); pdf.cell(95, 7, "  Polozka", border=0, fill=True)
    pdf.set_xy(115, y); pdf.cell(20, 7, "Mnozstvo", border=0, fill=True, align="C")
    pdf.set_xy(135, y); pdf.cell(25, 7, "Jedn. cena", border=0, fill=True, align="R")
    pdf.set_xy(160, y); pdf.cell(30, 7, "Celkom", border=0, fill=True, align="R")
    y += 7

    items = [
        ("Naraznik predny pravy - vymena", 1, 420.00, 420.00),
        ("Svetlo predne prave - vymena", 1, 280.00, 280.00),
        ("Blatnik predny pravy - oprava", 1, 175.00, 175.00),
        ("Praca lakovnika (3.5h)", 3.5, 50.00, 175.00),
    ]
    pdf.set_font("Helvetica", "", 10)
    for desc, qty, unit, total in items:
        pdf.set_xy(20, y); pdf.cell(95, 6, f"  {desc}")
        pdf.set_xy(115, y); pdf.cell(20, 6, f"{qty}", align="C")
        pdf.set_xy(135, y); pdf.cell(25, 6, f"{unit:.2f}", align="R")
        pdf.set_xy(160, y); pdf.cell(30, 6, f"$ {total:.2f}", align="R")
        y += 6

    y += 2
    pdf.line(20, y, 190, y)
    y += 3
    pdf.set_xy(135, y); pdf.cell(25, 5, "Subtotal", align="R")
    pdf.set_xy(160, y); pdf.cell(30, 5, "$ 1050.00", align="R")
    y += 5
    pdf.set_xy(135, y); pdf.cell(25, 5, "Tax 20%", align="R")
    pdf.set_xy(160, y); pdf.cell(30, 5, "$ 210.00", align="R")
    y += 5
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_xy(135, y); pdf.cell(25, 5, "TOTAL", align="R")
    pdf.set_xy(160, y); pdf.cell(30, 5, "$ 1260.00", align="R")

    # Payment details
    y += 14
    pdf.set_text_color(0, 47, 95)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_xy(20, y); pdf.cell(0, 5, "BANKOVE SPOJENIE PRE VYPLATENIE PLNENIA")
    y += 7
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(20, y); pdf.cell(45, 5, "Banka:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "Tatra banka")
    y += 6
    pdf.set_xy(20, y); pdf.cell(45, 5, "Account Name:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "Jan Novak")
    y += 6
    pdf.set_xy(20, y); pdf.cell(45, 5, "Account No.:")
    pdf.set_xy(65, y); pdf.cell(0, 5, "SK12 1100 0000 0026 1900 4488")

    # Footer
    pdf.set_y(-22)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 4, "UNIQA poistovna a.s. | ICO: 00 653 501 | IBAN: SK00 0000 0000 0000 0000 0000", align="C")
    pdf.ln(4)
    pdf.cell(0, 4, "Concept demo - not affiliated with UNIQA Insurance Group", align="C")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUT))
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
