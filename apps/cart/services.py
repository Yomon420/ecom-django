from django.shortcuts import get_object_or_404
from .models import CartItem

def add_cart_item(user, product, quantity=1):
    """
    Add a product to the user's cart.
    If the product already exists in the cart, increment the quantity.
    """
    cart_item, created = CartItem.objects.get_or_create(
        user=user,
        product=product,
        defaults={'quantity': quantity}
    )
    if not created:
        # If the cart item already exists, increase the quantity
        cart_item.quantity += quantity
        cart_item.save()
    return cart_item


def remove_cart_item(user, product_id):
    """
    Remove a product from the user's cart.
    """
    cart_item = get_object_or_404(CartItem, user=user, product_id=product_id)
    cart_item.delete()
    return True


def update_cart_item_quantity(user, product_id, quantity):
    """
    Update the quantity of a specific cart item.
    If quantity is <= 0, remove the item.
    """
    cart_item = get_object_or_404(CartItem, user=user, product_id=product_id)
    if quantity <= 0:
        cart_item.delete()
    else:
        cart_item.quantity = quantity
        cart_item.save()
    return cart_item
