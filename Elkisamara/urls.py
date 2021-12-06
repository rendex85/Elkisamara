from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from main.views import (
    BaseView,
    ProductDetailView,
    CategoryDetailView,
    CartView,
    AddToCartView,
    DeleteFromCartView,
    ChangeQTYView,
    CheckoutView, LoginUserView, RegisterUserView, OrderListView, OrderDetailView,
    # MakeOrderView
)

urlpatterns = [

                  path('admin/', admin.site.urls),
                  path('', BaseView.as_view(), name='base'),
                  path('products/<str:ct_model>/<str:slug>/', ProductDetailView.as_view(), name='product_detail'),
                  path('category/<str:ct_model>/<str:slug>/', CategoryDetailView.as_view(), name='category_detail'),
                  path('category/<str:ct_model>/', CategoryDetailView.as_view(), name='category_detail'),
                  path('cart/', CartView.as_view(), name='cart'),
                  path('add-to-cart/<str:ct_model>/<str:slug>/', AddToCartView.as_view(), name='add_to_cart'),
                  path('remove-from-cart/<str:ct_model>/<str:slug>/', DeleteFromCartView.as_view(),
                       name='delete_from_cart'),
                  path('change-qty/<str:ct_model>/<str:slug>/', ChangeQTYView.as_view(), name='change_qty'),
                  path('checkout/', CheckoutView.as_view(), name='checkout'),
                  path('login/', LoginUserView.as_view(), name='login'),
                  path('register/', RegisterUserView.as_view(), name='register'),
                  path('orders/', OrderListView.as_view(), name='list_orders'),
                  path('order/<int:pk>', OrderDetailView.as_view(), name='list_orders')
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
