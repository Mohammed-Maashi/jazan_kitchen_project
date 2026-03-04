import base64
import io

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

import qrcode

from .models import Product, ContactMessage, Order, OrderItem
from .utils.invoice_pdf import build_invoice_pdf


def _get_cart(request):
    return request.session.get("cart", {})  # {product_id(str): qty(int)}


def _save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def home(request):
    products = Product.objects.filter(available=True).order_by("-id")

    return render(request, "shop/home.html", {
        "products": products,
        "store_name": settings.STORE_NAME
    })


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    return render(request, "shop/detail.html", {
        "product": product,
        "store_name": settings.STORE_NAME
    })


# =========================
# ✅ CART (عرض/إضافة/حذف/تقليل/تفريغ)
# =========================
def cart_view(request):
    cart = _get_cart(request)
    ids = [int(k) for k in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=ids)

    items = []
    total = 0
    for p in products:
        qty = int(cart.get(str(p.id), 0))
        if qty <= 0:
            continue
        line_total = p.price * qty
        total += line_total
        items.append({"product": p, "qty": qty, "line_total": line_total})

    return render(request, "shop/cart.html", {
        "items": items,
        "total": total,
        "store_name": settings.STORE_NAME
    })


def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    cart = _get_cart(request)
    key = str(product.id)
    cart[key] = int(cart.get(key, 0)) + 1
    _save_cart(request, cart)
    return redirect("cart")  # ✅ بدل checkout


def cart_decrease(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    cart = _get_cart(request)
    key = str(product.id)

    if key in cart:
        cart[key] = int(cart.get(key, 0)) - 1
        if cart[key] <= 0:
            cart.pop(key, None)
        _save_cart(request, cart)

    return redirect("cart")


def cart_remove(request, pk):
    product = get_object_or_404(Product, pk=pk, available=True)
    cart = _get_cart(request)
    key = str(product.id)

    if key in cart:
        cart.pop(key, None)
        _save_cart(request, cart)

    return redirect("cart")


def cart_clear(request):
    _save_cart(request, {})
    return redirect("cart")


# =========================
# ✅ CONTACT
# =========================
def contact(request):
    sent = False

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        message = (request.POST.get("message") or "").strip()

        ContactMessage.objects.create(
            name=name, email=email, subject=subject, message=message
        )

        html = f"""
        <div style="font-family:Arial;line-height:1.8">
          <h2 style="margin:0;color:#0b2e4a">{settings.STORE_NAME}</h2>
          <p>مرحباً <b>{name}</b> 👋</p>
          <p>تم استلام رسالتك بنجاح بعنوان:</p>
          <div style="padding:12px;border:1px solid #eee;border-radius:10px;background:#fafafa">
            <b>{subject}</b>
            <div style="color:#555;margin-top:8px">{message}</div>
          </div>
          <p style="margin-top:16px;color:#555">سيتم الرد عليك في أقرب وقت.</p>
          <hr style="border:none;border-top:1px solid #eee;margin:18px 0">
          <small style="color:#888">هذا البريد مرسل تلقائياً من {settings.STORE_NAME}</small>
        </div>
        """

        msg = EmailMultiAlternatives(
            subject=f"{settings.STORE_NAME} - تم استلام رسالتك",
            body=f"مرحباً {name}، تم استلام رسالتك وسيتم الرد عليك قريباً.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
        )
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)

        sent = True

    return render(request, "shop/contact.html", {
        "sent": sent,
        "store_name": settings.STORE_NAME
    })


@login_required
def profile(request):
    u = request.user
    return render(request, "shop/profile.html", {
        "u": u,
        "store_name": settings.STORE_NAME
    })


# =========================
# ✅ CHECKOUT
# =========================
def checkout(request):
    cart = _get_cart(request)
    ids = [int(k) for k in cart.keys()] if cart else []
    products = Product.objects.filter(id__in=ids)

    items = []
    total = 0
    for p in products:
        qty = int(cart.get(str(p.id), 0))
        if qty <= 0:
            continue
        line_total = p.price * qty
        total += line_total
        items.append({"product": p, "qty": qty, "line_total": line_total})

    # ✅ لو السلة فاضية
    if not items and request.method == "POST":
        return redirect("checkout")

    if request.method == "POST":
        customer_name = (request.POST.get("customer_name") or "").strip()
        customer_email = (request.POST.get("customer_email") or "").strip()

        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            total=total
        )

        for it in items:
            p = it["product"]
            OrderItem.objects.create(
                order=order,
                product_name=p.name,
                price=p.price,
                qty=it["qty"],
            )

        invoice_url = request.build_absolute_uri(f"/invoice/{order.id}/")
        pdf_bytes = build_invoice_pdf(order, invoice_url=invoice_url, store_name=settings.STORE_NAME)

        rows = ""
        for it in order.items.all():
            rows += f"""
              <tr>
                <td style="padding:10px;border-bottom:1px solid #eee">{it.product_name}</td>
                <td style="padding:10px;border-bottom:1px solid #eee;text-align:center">{it.qty}</td>
                <td style="padding:10px;border-bottom:1px solid #eee;text-align:right">{it.price} SAR</td>
              </tr>
            """

        html = f"""
        <div style="font-family:Arial;line-height:1.8">
          <h2 style="margin:0;color:#0b2e4a">{settings.STORE_NAME}</h2>
          <p>مرحباً <b>{customer_name}</b> 🌟</p>
          <p>تم تأكيد طلبك بنجاح.</p>

          <div style="padding:14px;border:1px solid #e9eef5;border-radius:12px;background:#f7fbff">
            <b>رقم الطلب:</b> #{order.id}<br>
            <b>الإجمالي:</b> {order.total} SAR<br>
            <b>رابط الفاتورة:</b> <a href="{invoice_url}">{invoice_url}</a>
          </div>

          <h3 style="margin:18px 0 8px">تفاصيل المنتجات</h3>
          <table style="border-collapse:collapse;width:100%;border:1px solid #eee;border-radius:10px;overflow:hidden">
            <thead>
              <tr style="background:#0b2e4a;color:#fff">
                <th style="padding:10px;text-align:right">المنتج</th>
                <th style="padding:10px;text-align:center">الكمية</th>
                <th style="padding:10px;text-align:right">السعر</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>

          <p style="margin-top:16px;color:#555">
            تم إرفاق ملف PDF للفاتورة في هذا البريد.
          </p>

          <hr style="border:none;border-top:1px solid #eee;margin:18px 0">
          <small style="color:#888">هذا البريد مرسل تلقائياً من {settings.STORE_NAME}</small>
        </div>
        """

        msg = EmailMultiAlternatives(
            subject=f"{settings.STORE_NAME} - تأكيد الطلب #{order.id}",
            body=f"تم تأكيد طلبك. رقم الطلب: {order.id} - الإجمالي: {order.total} SAR",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer_email],
        )
        msg.attach_alternative(html, "text/html")
        msg.attach(filename=f"invoice_{order.id}.pdf", content=pdf_bytes, mimetype="application/pdf")
        msg.send(fail_silently=False)

        _save_cart(request, {})
        return redirect("invoice", order_id=order.id)

    return render(request, "shop/checkout.html", {
        "items": items,
        "total": total,
        "store_name": settings.STORE_NAME
    })


def invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    invoice_url = request.build_absolute_uri(f"/invoice/{order.id}/")

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(invoice_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render(request, "shop/invoice.html", {
        "order": order,
        "invoice_url": invoice_url,
        "qr_b64": qr_b64,
        "store_name": settings.STORE_NAME
    })


def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    invoice_url = request.build_absolute_uri(f"/invoice/{order.id}/")
    pdf_bytes = build_invoice_pdf(order, invoice_url=invoice_url, store_name=settings.STORE_NAME)

    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="invoice_{order.id}.pdf"'
    return resp