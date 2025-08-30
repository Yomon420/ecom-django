from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Order
from .serializers import OrderSerializer
from django.conf import settings
from .services import OrderService
from apps.payment.models import Payment
from apps.payment.serializers import PaymentSerializer
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Admin can see all orders, regular users only their own"""
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)

    def check_order_permission(self, order):
        """Check if user has permission to access this order"""
        if self.request.user.is_staff or self.request.user.is_superuser:
            return True  # Admin can access any order
        return order.user == self.request.user  # Regular users only their own

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"])
    def update_status(self, request, pk=None):
        """Update order status - Admin only"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {"error": "Only admin users can update order status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        new_status = request.data.get("status")
        
        try:
            OrderService.update_order_status(order, new_status)
            return Response({
                "message": f"Order status updated to {new_status}",
                "status": order.status,
                "status_display": order.get_status_display()
            })
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["get"])
    def status_options(self, request, pk=None):
        """Get available status options for this order"""
        order = self.get_object()
        if not self.check_order_permission(order):
            return Response(
                {"error": "You don't have permission to access this order"},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response({
            "status_choices": dict(Order.STATUS_CHOICES)
        })
    
    @action(detail=True, methods=['post'])
    def create_payment(self, request, pk=None):
        """
        Create payment intent for an order
        POST /api/orders/{id}/create_payment/
        """
        order = self.get_object()
        
        # Check permission - admin can't create payments for users
        if not self.check_order_permission(order):
            return Response(
                {"error": "You can only create payments for your own orders"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Admin shouldn't create payments for users (security risk)
        if (request.user.is_staff or request.user.is_superuser) and order.user != request.user:
            return Response(
                {"error": "Admin cannot create payments for other users"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if order is already paid
        if order.status == 'paid':
            return Response(
                {"error": "Order is already paid"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for existing successful payment
        existing_payment = Payment.objects.filter(order=order, status='succeeded').first()
        if existing_payment:
            return Response(
                {"error": "Order already has a successful payment"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create PaymentIntent with Stripe
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),
                currency="usd",
                metadata={
                    "order_id": order.id,
                    "user_id": request.user.id
                },
                automatic_payment_methods={"enabled": True},
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": "Payment processing error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Save payment in DB
        payment = Payment.objects.create(
            order=order,
            stripe_payment_intent_id=intent["id"],
            amount=order.total_amount,
            status="pending"
        )
        
        # Update order status
        order.status = "awaiting_payment"
        order.save()
        
        return Response({
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id,
            "message": "Payment intent created successfully"
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def payment_status(self, request, pk=None):
        """
        Check payment status for an order
        GET /api/orders/{id}/payment_status/
        Admin can check any order, users can only check their own
        """
        order = self.get_object()
        
        # Check permission using our helper method
        if not self.check_order_permission(order):
            return Response(
                {"error": "You don't have permission to access this order's payment status"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            payment = Payment.objects.get(order=order)
            serializer = PaymentSerializer(payment)
            return Response(serializer.data)
        except Payment.DoesNotExist:
            return Response(
                {"error": "No payment found for this order"}, 
                status=status.HTTP_404_NOT_FOUND
            )