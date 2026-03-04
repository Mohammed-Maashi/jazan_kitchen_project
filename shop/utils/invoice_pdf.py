import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

import qrcode


def make_qr_image(data: str):
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def build_invoice_pdf(order, invoice_url: str, store_name: str) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, h - 2*cm, store_name)

    c.setFont("Helvetica", 11)
    c.drawString(2*cm, h - 2.8*cm, f"Invoice / فاتورة")
    c.drawString(2*cm, h - 3.4*cm, f"Order ID: {order.id}")
    c.drawString(2*cm, h - 4.0*cm, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Customer
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, h - 5.0*cm, "Customer / الزبون")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, h - 5.7*cm, f"Name: {order.customer_name}")
    c.drawString(2*cm, h - 6.3*cm, f"Email: {order.customer_email}")

    # Items table header
    y = h - 7.5*cm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, "Item")
    c.drawString(11*cm, y, "Qty")
    c.drawString(13*cm, y, "Price")
    c.drawString(16*cm, y, "Total")

    c.setFont("Helvetica", 11)
    y -= 0.6*cm
    c.line(2*cm, y, w - 2*cm, y)
    y -= 0.6*cm

    for it in order.items.all():
        line_total = it.line_total()
        c.drawString(2*cm, y, it.product_name[:40])
        c.drawString(11*cm, y, str(it.qty))
        c.drawString(13*cm, y, f"{it.price}")
        c.drawString(16*cm, y, f"{line_total}")
        y -= 0.7*cm
        if y < 4*cm:
            c.showPage()
            y = h - 3*cm

    # Total
    y -= 0.4*cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(13*cm, y, "Grand Total:")
    c.drawString(16*cm, y, f"{order.total} SAR")

    # QR
    qr_img = make_qr_image(invoice_url)
    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format="PNG")
    qr_buf.seek(0)

    c.setFont("Helvetica", 10)
    c.drawString(2*cm, 3.0*cm, "Scan QR to open invoice page / امسح QR لفتح صفحة الفاتورة")
    c.drawImage(ImageReader(qr_buf), 2*cm, 1.0*cm, width=3.2*cm, height=3.2*cm, mask='auto')

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    return pdf