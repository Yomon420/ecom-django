# from .models import Product

# class ProductService:
#     @staticmethod
#     def get_all_products():
#         return Product.objects.all()
    
#     def get_product_by_id(product_id):
#         try:
#             return Product.objects.get(id=product_id)
#         except Product.DoesNotExist:
#             return None
    
#     @staticmethod
#     def create_product(product_data):
#         return Product.objects.create(**product_data)
    
#     @staticmethod
#     def update_product(product, product_data):
#         for field, value in product_data.items():
#             setattr(product, field, value)
#         product.save()
#         return product
    
#     @staticmethod
#     def delete_product(product):
#         product.delete()
    
#     @staticmethod
#     def get_products_by_category(category):
#         return Product.objects.filter(category=category)