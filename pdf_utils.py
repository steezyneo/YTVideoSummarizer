from fpdf import FPDF

def export_pdf(summary, filename="summary.pdf"):
    pdf = FPDF()
    pdf.add_page()
    # Add a Unicode font (DejaVuSans)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)
    for line in summary.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename 