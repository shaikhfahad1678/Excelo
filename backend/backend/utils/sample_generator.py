"""
Sample PDF Bank Statement Generator for Testing
Recreates the exact PDF statement shown in user's issue screenshot:
- Header: Savings Account Transactions
- Columns: #, Date, Description, Chq/Ref. No., Withdrawal (Dr.), Deposit (Cr.), Balance
- Multi-line descriptions and specific transaction rows.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

def create_exact_sample_pdf(filepath: str):
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()

    # Red Title Bar
    title_style = ParagraphStyle(
        'RedTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.white,
        alignment=1, # Center
        spaceAfter=0
    )

    title_table = Table([[Paragraph("Savings Account Transactions", title_style)]], colWidths=[550])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#DC2626')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    elements.append(title_table)
    elements.append(Spacer(1, 5))

    # Column Headers: #, Date, Description, Chq/Ref. No., Withdrawal (Dr.), Deposit (Cr.), Balance
    header_style = ParagraphStyle('HeaderStyle', parent=styles['Normal'], fontSize=9, textColor=colors.white, fontName='Helvetica-Bold')
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=8.5, leading=11, fontName='Helvetica')

    data = [
        [
            Paragraph("#", header_style),
            Paragraph("Date", header_style),
            Paragraph("Description", header_style),
            Paragraph("Chq/Ref. No.", header_style),
            Paragraph("Withdrawal (Dr.)", header_style),
            Paragraph("Deposit (Cr.)", header_style),
            Paragraph("Balance", header_style)
        ],
        ["-", "-", "Opening Balance", "-", "-", "-", "377.95"],
        ["1", "01 Jul 2026", "UPI/FAHAD MD\nAKBAR/KKBK/003137314529/Paid via Nav", "UPI-618220711177", "", "1.00", "378.95"],
        ["2", "01 Jul 2026", "UPI/FAHAD MD\nAKBAR/KKBK/618247507154/Paid via Sup", "UPI-618222744796", "", "1.00", "379.95"],
        ["3", "07 Jul 2026", "PCD/2958/AMAZON WEB\nSERVICES/224092000070726/15:41", "618810076819", "2.00", "", "377.95"],
        ["4", "09 Jul 2026", "VISA-REFUND/070726/070726/AMAZON WEB\nSERVICES", "FOS26190191456571", "", "2.00", "379.95"],
        ["5", "10 Jul 2026", "UPI/Jio Prepaid Re/YESB/619172895561/UPI", "UPI-619150172038", "79.00", "", "300.95"],
        ["6", "19 Jul 2026", "UPI/Yuvraj Parshur/SBIN/656645663694/UPI", "UPI-620058510729", "170.00", "", "130.95"],
        ["7", "23 Jul 2026", "UPI/FAHAD MD\nAKBAR/KKBK/657029382009/UPI", "UPI-620427591204", "", "500.00", "630.95"],
        ["8", "28 Jul 2026", "UPI/FAHAD MD\nAKBAR/KKBK/620917477800/UPI", "UPI-620937253421", "", "2,800.00", "3,430.95"],
        ["9", "28 Jul 2026", "UPI/FAHAD MD\nAKBAR/KKBK/620912675152/UPI", "UPI-620937642222", "", "200.00", "3,630.95"],
        ["10", "28 Jul 2026", "UPI/NAUMAN JUMMAN\n/UTIB/620960331206/UPI", "UPI-620939928759", "100.00", "", "3,530.95"],
        ["11", "28 Jul 2026", "UPI/FAHAD MD\nAKBAR/KKBK/620957959083/UPI", "UPI-620941476646", "2,900.00", "", "630.95"],
    ]

    table_data = []
    for row_idx, row in enumerate(data):
        formatted_row = []
        for col_idx, cell in enumerate(row):
            if row_idx == 0:
                formatted_row.append(cell)
            else:
                formatted_row.append(Paragraph(str(cell).replace('\n', '<br/>'), cell_style))
        table_data.append(formatted_row)

    t = Table(table_data, colWidths=[20, 65, 210, 110, 50, 50, 45])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#64748B')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#94A3B8')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
    ]))

    elements.append(t)
    doc.build(elements)

if __name__ == "__main__":
    os.makedirs("docs/sample_pdfs", exist_ok=True)
    create_exact_sample_pdf("docs/sample_pdfs/Sample_Bank_Statement.pdf")
    print("Generated exact sample PDF bank statement.")
