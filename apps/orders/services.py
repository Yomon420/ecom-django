# apps/orders/services.py
from django.db import transaction
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from .models import Order, OrderItem
from apps.products.models import Product
from apps.coupons.models import Coupon  # Import Coupon model

class OrderService:
    
    @staticmethod
    def _calculate_cart_total(items_data):
        """Calculate total cart value from items data"""
        return sum(item['product'].price * item['quantity'] for item in items_data)
    
    @staticmethod
    def _get_coupon_by_code(coupon_code):
        """Get coupon object by code or return None"""
        if not coupon_code:
            return None
        try:
            return Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            raise ValidationError(f"Coupon with code '{coupon_code}' does not exist.")
    
    @staticmethod
    @transaction.atomic
    def create_order(user, validated_data):
        """Create a new order with items and handle coupon usage."""
        items_data = validated_data.pop('items', [])
        coupon_code = validated_data.pop('coupon', None)  # Get coupon code
        shipping_address = validated_data.pop('shipping_address')
        
        # Convert coupon code to coupon object
        coupon = OrderService._get_coupon_by_code(coupon_code)

        # Calculate cart total for coupon validation
        cart_total = OrderService._calculate_cart_total(items_data)

        # Validate coupon before creating order
        if coupon:
            if not coupon.is_valid(cart_total):
                if cart_total < coupon.min_cart_value:
                    raise ValidationError(
                        f"This coupon requires a minimum cart value of ${coupon.min_cart_value}. "
                        f"Your cart total is ${cart_total}."
                    )
                else:
                    raise ValidationError("This coupon is invalid or has expired.")
            
            # Check usage limit
            if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
                raise ValidationError("This coupon has reached its usage limit.")

        # Create order
        order = Order.objects.create(
            user=user,
            coupon=coupon,  # Now this is a Coupon object, not a string
            shipping_address=shipping_address,
            **validated_data
        )
        
        # Create order items
        order_items = []
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            order_item = OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                price_per_unit=product.price
            )
            order_items.append(order_item)
        
        OrderItem.objects.bulk_create(order_items)
        
        # Calculate total
        order.calculate_total()

        # Update coupon usage if applied
        if coupon:
            coupon.used_count += 1
            coupon.save(update_fields=["used_count"])
        
        return order
    
    @staticmethod
    @transaction.atomic
    def update_order(order, validated_data):
        """Update an existing order and adjust coupon usage if changed."""
        items_data = validated_data.pop('items', None)
        new_coupon_code = validated_data.get('coupon')  # Get coupon code
        
        # Convert coupon code to coupon object
        new_coupon = OrderService._get_coupon_by_code(new_coupon_code)

        # Calculate cart total for coupon validation if items are provided
        cart_total = None
        if items_data is not None:
            cart_total = OrderService._calculate_cart_total(items_data)
        else:
            # Use existing order total if items aren't being updated
            cart_total = sum(item.product.price * item.quantity for item in order.items.all())

        # Validate new coupon if different
        if new_coupon and new_coupon != order.coupon:
            if not new_coupon.is_valid(cart_total):
                if cart_total < new_coupon.min_cart_value:
                    raise ValidationError(
                        f"This coupon requires a minimum cart value of ${new_coupon.min_cart_value}. "
                        f"Your cart total is ${cart_total}."
                    )
                else:
                    raise ValidationError("This coupon is invalid or has expired.")
            
            # Check usage limit
            if new_coupon.usage_limit and new_coupon.used_count >= new_coupon.usage_limit:
                raise ValidationError("This coupon has reached its usage limit.")

        # Handle coupon usage count
        if order.coupon and order.coupon != new_coupon:
            # Revert usage from old coupon
            if order.coupon.used_count > 0:
                order.coupon.used_count -= 1
                order.coupon.save(update_fields=["used_count"])
        
        if new_coupon and new_coupon != order.coupon:
            # Increment usage for new coupon
            new_coupon.used_count += 1
            new_coupon.save(update_fields=["used_count"])

        # Update order fields
        order.coupon = new_coupon
        order.shipping_address = validated_data.get('shipping_address', order.shipping_address)
        order.save()
        
        # Update items if provided
        if items_data is not None:
            order.items.all().delete()
            order_items = []
            for item_data in items_data:
                product = item_data['product']
                quantity = item_data['quantity']
                
                order_item = OrderItem(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price_per_unit=product.price
                )
                order_items.append(order_item)
            
            OrderItem.objects.bulk_create(order_items)
        
        # Recalculate total
        order.calculate_total()
        
        return order
    
    @staticmethod
    def update_order_status(order, new_status):
        """Update order status with validation"""
        if new_status not in dict(Order.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")
        
        order.status = new_status
        order.save()

        # Update all related OrderItems
        order.items.update(status=new_status)

        return order