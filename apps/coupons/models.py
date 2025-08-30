from django.db import models
from django.utils import timezone

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[
            ('percent', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ],
        default='percent'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    min_cart_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        help_text="Minimum cart value required to use this coupon"
    )
    active = models.BooleanField(default=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)

    def is_valid(self, cart_total=None):
        """Check if coupon is valid, optionally with cart total validation"""
        now = timezone.now()
        is_valid = (
            self.active
            and self.valid_from <= now <= self.valid_to
            and (self.usage_limit is None or self.used_count < self.usage_limit)
        )
        
        # Additional validation for minimum cart value if provided
        if cart_total is not None:
            is_valid = is_valid and (cart_total >= self.min_cart_value)
            
        return is_valid

    def __str__(self):
        return f"{self.code} ({self.discount_type} - {self.discount_value})"