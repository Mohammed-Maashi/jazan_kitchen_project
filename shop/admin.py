from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ContactMessage, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("thumb", "name", "category", "price", "stock", "available")
    list_filter = ("category", "available")
    search_fields = ("name", "description")
    list_editable = ("price", "stock", "available")

    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:52px;height:52px;object-fit:cover;border-radius:10px;">', obj.image.url)
        return "—"
    thumb.short_description = "صورة"

admin.site.register(ContactMessage)
admin.site.register(Order)
admin.site.register(OrderItem)