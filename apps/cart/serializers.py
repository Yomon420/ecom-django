from rest_framework import serializers
from .models import CartItem

class CartItemSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'user', 'user_email', 'product', 'product_name', 'product_price', 'quantity', 'created_at']
        read_only_fields = ['id', 'user', 'user_email', 'created_at', 'product_name', 'product_price']