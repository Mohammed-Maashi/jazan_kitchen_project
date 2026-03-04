from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # ✅ Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:pk>/', views.cart_add, name='cart_add'),
    path('cart/decrease/<int:pk>/', views.cart_decrease, name='cart_decrease'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart_remove'),
    path('cart/clear/', views.cart_clear, name='cart_clear'),

    # ✅ Pages
    path('contact/', views.contact, name='contact'),
    path('profile/', views.profile, name='profile'),

    # ✅ Checkout + Invoice
    path('checkout/', views.checkout, name='checkout'),
    path('invoice/<int:order_id>/', views.invoice, name='invoice'),
    path('invoice/<int:order_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]