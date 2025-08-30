from django.db import models
from django.contrib.auth.models import User

class CartItem(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)  # user_id
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)  # product_id
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product} ({self.quantity})"
