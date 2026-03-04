import re
import hashlib
import requests
from django.core.files.base import ContentFile
from .models import Category, Product


JAZAN_FOODS = [
    ("المغش", "لحم مطهو في قدر حجري مع خضار وتتبيلة جنوبية.", 45, 30, "maghash saudi food"),
    ("الحنيذ", "لحم حنيذ على الطريقة الجنوبية بطعم مدخن مميز.", 85, 18, "haneeth saudi traditional"),
    ("المندي", "رز مندي بنكهة مدخنة مع لحم أو دجاج على الطريقة الجنوبية.", 95, 12, "saudi mandi rice"),
    ("المرسة", "طبق جازاني شعبي يُحضّر من الموز والتمر مع خبز الميفا ويُهرس مع السمن أو العسل.", 25, 40, "saudi banana dates dessert"),
    ("العريكة", "حلا/فطور جنوبي مكوّن من دقيق القمح مع تمر وسمن وعسل.", 22, 45, "areekah saudi dessert"),
    ("العصيدة", "طبق شعبي دافئ من الدقيق يُقدّم مع العسل أو السمن.", 18, 50, "aseedah arabic porridge"),
    ("خبز الميفا", "خبز جنوبي تقليدي يُخبز في تنور الميفا.", 8, 80, "arabic flatbread tandoor"),
    ("سمك مشوي", "سمك طازج مشوي بتتبيلة بحرية جنوبية.", 55, 20, "grilled fish arabic food"),
    ("المطبق", "فطيرة شعبية محشية باللحم أو الخضار على الطريقة الجنوبية.", 15, 60, "mutabbaq saudi"),
]


def safe_filename(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    if not s:
        s = hashlib.md5(name.encode("utf-8")).hexdigest()[:12]
    return f"{s}.jpg"


def fetch_image(query: str, name: str):
    """
    ✅ نسخة قوية بدون API:
    - Unsplash Source غالبًا يرجع Redirect
    - نأخذ الرابط النهائي (response.url) ثم ننزل الصورة منه
    - نتحقق من حجم المحتوى لتجنب HTML/ردود صغيرة
    """
    sig = int(hashlib.md5(name.encode("utf-8")).hexdigest(), 16) % 10000
    base_url = f"https://source.unsplash.com/900x600/?{requests.utils.quote(query)},food&sig={sig}"

    try:
        # 1) اتبع التحويلات للحصول على الرابط النهائي للصورة
        r1 = requests.get(base_url, timeout=25, allow_redirects=True)
        final_url = r1.url

        # 2) تنزيل الصورة من الرابط النهائي
        r2 = requests.get(final_url, timeout=25)
        if r2.status_code == 200 and r2.content and len(r2.content) > 8000:
            return r2.content
    except Exception:
        pass

    return None


def run(refresh_images: bool = False) -> int:
    """
    refresh_images=False:
      يجلب صورة فقط إذا المنتج ما عنده صورة.
    refresh_images=True:
      يعيد تحميل الصور بالقوة (مفيد إذا كانت الصور مكسورة).
    """
    category, _ = Category.objects.get_or_create(
        name="مأكولات شعبية جازانية",
        slug="jazan-kitchen"
    )

    created = 0
    food_names = [food[0] for food in JAZAN_FOODS]

    # ✅ حذف المنتجات القديمة غير الموجودة في القائمة (مثل Apple/المفطح)
    Product.objects.exclude(name__in=food_names).delete()

    for name, desc, price, stock, img_query in JAZAN_FOODS:
        product, was_created = Product.objects.get_or_create(
            category=category,
            name=name,
            defaults={
                "description": desc,
                "price": price,
                "stock": stock,
                "available": True,
            }
        )

        # ✅ تحديث بيانات المنتج إذا كان موجود
        if not was_created:
            product.description = desc
            product.price = price
            product.stock = stock
            product.available = True
            product.save()

        if was_created:
            created += 1

        # ✅ إعادة تحميل الصور بالقوة إذا طلبت
        if refresh_images and product.image:
            try:
                product.image.delete(save=False)
            except Exception:
                pass
            product.image = None
            product.save(update_fields=["image"])

        # ✅ تحميل صورة إذا لا توجد صورة
        if not product.image:
            img = fetch_image(img_query, name)
            if img:
                product.image.save(
                    safe_filename(name),
                    ContentFile(img),
                    save=True
                )

    return created