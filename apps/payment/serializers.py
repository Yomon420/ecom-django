# apps/payment/serializers.py
from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'order', 'stripe_payment_intent_id', 'amount', 'status', 'created_at']
        read_only_fields = ['id', 'stripe_payment_intent_id', 'amount', 'status', 'created_at']

class PaymentIntentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    client_secret = serializers.CharField(read_only=True)

    def validate_order_id(self, value):
        # Check if order exists
        from apps.orders.models import Order
        try:
            Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order does not exist")
        return value