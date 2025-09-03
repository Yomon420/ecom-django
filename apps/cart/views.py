from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CartItem
from .serializers import CartItemSerializer
from rest_framework.permissions import IsAuthenticated

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return CartItem.objects.none()
        
        queryset = CartItem.objects.all()
        
        # Regular users only see their own cart
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(user=self.request.user)
        
        # Admin can filter by user_id
        user_id = self.request.query_params.get('user_id')
        if user_id and (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by("id")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)