"""Generates the fictitious handbook in English: two pages with selectable text."""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

DESTINO = Path(__file__).resolve().parent / "documentos" / "manual_empresa.pdf"

PAGINAS = [
    [
        ("Employee Handbook", "Lumina Services | Edition DEMO-2026-10 | Page 1"),
        ("Fictitious company", "Lumina Services is a fictitious consulting firm with 48 employees. "
         "All names, contacts and policies in this document are made up. "
         "This handbook is effective from 1 October 2026 and applies to full-time employees."),
        ("1. Vacation", "Each employee is entitled to <b>24 working days of vacation per year</b>. "
         "Weekends and public holidays do not count as vacation days. Employees who join during the year "
         "receive a prorated amount: two days for each full month worked."),
        ("Requesting vacation", "Vacation is requested in the internal People portal at least "
         "<b>15 calendar days in advance</b>. The team manager must approve the request. "
         "Up to four days may be carried over to the following year and must be used before 31 March."),
        ("2. Remote work", "Employees may work remotely <b>two days per week</b>, with prior approval "
         "from their manager. On Wednesdays, the whole team works on site. "
         "Common availability hours are from 10:00 to 14:00."),
        ("Remote work conditions", "Using the company laptop and the VPN is mandatory. "
         "Changes of remote day must be requested 48 hours in advance. "
         "Working from another country is not allowed without explicit authorization from Human Resources."),
    ],
    [
        ("Expenses, training and contact", "Lumina Services | Edition DEMO-2026-10 | Page 2"),
        ("3. Expenses and travel", "Business trips require approval from the manager "
         "before making any bookings. Train travel is booked in economy class "
         "and hotels are limited to <b>120 euros per night</b>, taxes included."),
        ("How to request reimbursement", "The employee submits form <b>GV-17</b> in the Expenses "
         "portal, attaching invoices and receipts, within a maximum of <b>10 calendar days</b> "
         "after returning. The finance department reviews the request and pays approved expenses "
         "in the next payroll run."),
        ("Expense limits", "Meals are limited to 28 euros per person per day. "
         "Authorized trips in a private vehicle are reimbursed at 0.26 euros per kilometre. "
         "Fines and personal expenses are not reimbursable."),
        ("4. Training", "Each employee has <b>600 euros and 20 hours of training per year</b>. "
         "The company offers courses in artificial intelligence, cybersecurity and communication. "
         "Enrolment is requested by email to Human Resources, with the manager's approval. "
         "Unused budget does not carry over to the following year."),
        ("5. Human Resources contact", "Fictitious contact person: Elena Robles. Email: "
         "<b>people@lumina.example</b>. Internal extension: 241. "
         "Opening hours: Monday to Friday, from 09:00 to 16:00. "
         "The usual response time is two working days."),
    ],
]


def main():
    DESTINO.parent.mkdir(exist_ok=True)
    estilos = getSampleStyleSheet()
    estilos["BodyText"].fontSize = 11
    estilos["BodyText"].leading = 16
    elementos = []
    for numero, secciones in enumerate(PAGINAS):
        if numero:
            elementos.append(PageBreak())
        for indice, (titulo, texto) in enumerate(secciones):
            elementos.append(Paragraph(titulo, estilos["Title" if indice == 0 else "Heading2"]))
            elementos.append(Paragraph(texto, estilos["BodyText"]))
            elementos.append(Spacer(1, 10))

    paginas_generadas = []

    def pie_pagina(lienzo, documento):
        paginas_generadas.append(documento.page)
        lienzo.setFillColor(colors.HexColor("#555555"))
        lienzo.setFont("Helvetica", 9)
        lienzo.drawString(48, 28, "Fictitious document for demos. No real data.")
        lienzo.drawRightString(A4[0] - 48, 28, str(documento.page))

    # Deterministic PDF: regenerating the same content does not change its hash.
    pdf = SimpleDocTemplate(str(DESTINO), pagesize=A4, topMargin=42, bottomMargin=48,
                            invariant=1)
    pdf.build(elementos, onFirstPage=pie_pagina, onLaterPages=pie_pagina)
    if paginas_generadas != [1, 2]:
        raise ValueError(f"Expected two pages; generated: {paginas_generadas}")
    print(f"PDF created: {DESTINO}\nPages: 2")


if __name__ == "__main__":
    main()