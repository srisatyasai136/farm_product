from django.urls import path
from . import views
urlpatterns = [
path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
path('', views.cart_view, name='cart_view'),
path('delete/<int:item_id>/', views.delete_cart_item, name='delete_cart_item'),
 path('checkout/', views.checkout, name='checkout'),
]