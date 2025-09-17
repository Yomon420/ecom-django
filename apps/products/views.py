from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product
from .serializers import ProductSerializer


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to create, update, delete.
    Regular authenticated users can only read.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed for any authenticated user
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed for admin users
        return request.user and request.user.is_authenticated and request.user.is_staff


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'], url_path='categories')
    def unique_categories(self, request):
        """
        Returns a list of unique product categories.
        """
        categories = Product.objects.values_list('category', flat=True).distinct()
        return Response(categories)