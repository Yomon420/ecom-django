from django.db import models

class Review(models.Model):
    product = models.ForeignKey(
        'products.Product', on_delete=models.CASCADE, related_name='reviews'
    )
    rating = models.IntegerField()
    comment = models.TextField()
    reviewer_name = models.CharField(max_length=255)
    reviewer_email = models.EmailField()
    date = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"Review for {self.product.name} by {self.reviewer_name}"
