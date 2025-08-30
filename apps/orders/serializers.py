# apps/orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.models import Product
from .services import OrderService

class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product"
    )
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_id", "product_name", "product_price", "quantity", "price_per_unit", "status", "status_display"]
        read_only_fields = ["id", "price_per_unit", "product_name", "product_price", "status_display"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    coupon = serializers.CharField(required=False, allow_null=True, write_only=True)  # Accept string for write
    coupon_details = serializers.SerializerMethodField(read_only=True)  # For read operations

    class Meta:
        model = Order
        fields = [
            "id", "user", "user_email", "total_amount", "status", "status_display",
            "created_at", "updated_at", "coupon", "coupon_details", "shipping_address", "items"
        ]
        read_only_fields = [
            "id", "total_amount", "status", "created_at", "updated_at", 
            "user", "user_email", "status_display", "coupon_details"
        ]

    def get_coupon_details(self, obj):
        """Return coupon details for read operations"""
        if obj.coupon:
            return {
                "code": obj.coupon.code,
                "discount_type": obj.coupon.discount_type,
                "discount_value": str(obj.coupon.discount_value),
                "min_cart_value": str(obj.coupon.min_cart_value)
            }
        return None

    def validate_coupon(self, value):
        """Validate coupon code format"""
        if value is None or value == "":
            return None
            
        if not isinstance(value, str):
            raise serializers.ValidationError("Coupon must be a string code")
            
        # Optional: validate coupon code format (alphanumeric, etc.)
        if not value.strip():
            raise serializers.ValidationError("Coupon code cannot be empty")
            
        return value.strip().upper()  # Normalize to uppercase

    def validate(self, data):
        """Additional validation for the entire order"""
        # Ensure items are provided
        if 'items' not in data or not data['items']:
            raise serializers.ValidationError({"items": "At least one item is required"})
            
        # Ensure shipping address is provided
        if 'shipping_address' not in data:
            raise serializers.ValidationError({"shipping_address": "Shipping address is required"})
            
        return data

    def create(self, validated_data):
        user = self.context["request"].user
        return OrderService.create_order(user, validated_data)

    def update(self, instance, validated_data):
        return OrderService.update_order(instance, validated_data)