import io
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from inventory.models import Product, Transaction

def generate_pdf_report(data, title, filename):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    styles = getSampleStyleSheet()
    elements = []
    
    # Add title
    elements.append(Paragraph(title, styles['Title']))
    
    # Prepare data for table
    if hasattr(data, 'model'):
        if data.model == Product:
            table_data = [["ID", "Name", "Category", "Quantity", "Price"]]
            for item in data:
                table_data.append([
                    str(item.id),
                    item.name,
                    item.get_category_display(),
                    str(item.quantity),
                    f"${item.price:.2f}"
                ])
        elif data.model == Transaction:
            table_data = [["ID", "Product", "Type", "Quantity", "Price", "Total", "Date"]]
            for item in data:
                table_data.append([
                    str(item.id),
                    item.product.name,
                    item.get_transaction_type_display(),
                    str(item.quantity),
                    f"${item.price:.2f}",
                    f"${item.total_amount:.2f}",
                    item.transaction_date.strftime('%Y-%m-%d %H:%M')
                ])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response