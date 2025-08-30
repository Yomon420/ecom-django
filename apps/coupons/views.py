# apps/coupons/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.core.exceptions import ValidationError
from .models import Coupon
from .serializers import CouponSerializer
from .services import validate_coupon

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer

    def get_permissions(self):
        """
        Custom permissions per action:
        - Anyone can validate coupons
        - Only admin can modify coupons
        - Anyone can read coupons
        """
        if self.action == 'validate_coupon_code':
            return [AllowAny()]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [AllowAny()]  # For list and retrieve

    @action(detail=False, methods=['post'], url_path='validate')
    def validate_coupon_code(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"error": "Coupon code is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            coupon = validate_coupon(code)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(CouponSerializer(coupon).data, status=status.HTTP_200_OK)