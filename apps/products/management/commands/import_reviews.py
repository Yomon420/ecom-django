import requests
from django.core.management.base import BaseCommand
from apps.reviews.models import Review
from apps.products.models import Product
from datetime import datetime

class Command(BaseCommand):
    help = 'Import reviews from dummyjson and link to products'

    def handle(self, *args, **kwargs):
        url = 'https://dummyjson.com/products?limit=0'
        response = requests.get(url)
        data = response.json()

        for product_data in data['products']:
            product_id = product_data['id']
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Product with ID {product_id} not found. Skipping..."))
                continue

            for review_data in product_data.get('reviews', []):
                Review.objects.create(
                    product=product,
                    rating=review_data['rating'],
                    comment=review_data['comment'],
                    reviewer_name=review_data['reviewerName'],
                    reviewer_email=review_data['reviewerEmail'],
                    date=datetime.fromisoformat(review_data['date'].replace('Z', '+00:00'))
                )

            self.stdout.write(self.style.SUCCESS(f"Added reviews for product ID {product_id}"))
