from django.utils import timezone
from .models import Coupon
from django.core.exceptions import ValidationError
from .serializers import CouponSerializer

def create_coupon(data):
    serializer = CouponSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.save()

def validate_coupon(code):
    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        raise ValidationError("Invalid coupon code.")

    if not coupon.is_valid():
        raise ValidationError("Coupon is not valid or expired.")

    return coupon
