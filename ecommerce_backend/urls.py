from django.urls import path, include
from django.contrib import admin
from rest_framework import permissions

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/payments/', include('apps.payment.urls')),
    path('api/', include('apps.coupons.urls')),
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.cart.urls')),
    path('api/', include('apps.orders.urls')),
    path('api/', include('apps.addresses.urls')),
    path('api/', include('apps.reviews.urls')),
]