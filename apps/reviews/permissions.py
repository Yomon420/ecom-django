# permissions.py in reviews
import logging
from rest_framework import permissions
from apps.orders.models import OrderItem

logger = logging.getLogger(__name__)

class CanReviewProduct(permissions.BasePermission):
    """
    Allows review only if user purchased and the specific product was delivered.
    """

    message = "You cannot review this product."

    def has_permission(self, request, view):
        # Allow safe methods (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # Ensure authenticated
        if not request.user.is_authenticated:
            self.message = "You must be logged in to review products."
            return False

        # Ensure product is in the request
        product_id = request.data.get("product")
        if not product_id:
            self.message = "Product ID is required to post a review."
            return False

        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            self.message = "Invalid product ID."
            return False

        # Debugging: print/log what the system is checking
        qs = OrderItem.objects.filter(
            order__user=request.user,
            product=product_id,
            status="DELIVERED"
        )

        logger.debug("Checking delivered OrderItems for user=%s, product=%s -> %s",
                     request.user, product_id, list(qs.values("id", "order_id", "status")))

        has_purchased = qs.exists()

        if not has_purchased:
            self.message = "You can only review products after they are delivered."
            return False

        return True
