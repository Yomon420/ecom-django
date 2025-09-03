from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, VerifyOTPSerializer, UserSerializer,LoginSerializer
from .services import send_otp_to_email, verify_otp_and_create_user
from django.contrib.auth import get_user_model
from apps.utils.responses import success_response, error_response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return User.objects.none()
            
        if self.request.user.is_staff or self.request.user.is_superuser:
            return User.objects.all().order_by("id")
        return User.objects.filter(id=self.request.user.id)

    # Single endpoint that handles GET, PATCH, and DELETE for /users/me
    @swagger_auto_schema(
        method='get',
        operation_description="Retrieve the currently authenticated user's details.",
        responses={200: UserSerializer()},
    )
    @swagger_auto_schema(
        method='patch',
        operation_description="Update the currently authenticated user's details.",
        request_body=UserSerializer,
        responses={200: UserSerializer()},
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Delete (or deactivate) the currently authenticated user account.",
        responses={204: "Account successfully deleted"},
    )
    @action(detail=False, methods=["get", "patch", "delete"], url_path="me")
    def me(self, request):
        user = request.user
        
        if request.method == "GET":
            serializer = self.get_serializer(user)
            return Response(serializer.data)
            
        elif request.method == "PATCH":
            serializer = self.get_serializer(
                user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
            
        elif request.method == "DELETE":
            user.delete()  # or soft-delete if you prefer
            return Response(status=status.HTTP_204_NO_CONTENT)
    



class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        method="post",
        request_body=RegisterSerializer,
        responses={
            200: openapi.Response("OTP sent successfully"),
            400: openapi.Response("Validation errors"),
        }
    )
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                send_otp_to_email(serializer.validated_data)
                return success_response(
                    message="OTP sent to email. Please verify to complete registration."
                )
            except Exception as e:
                return error_response(message="Failed to send OTP", errors=str(e))
        return error_response(errors=serializer.errors)

    @swagger_auto_schema(
        method="post",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Login successful",
                        "data": {
                            "user": {
                                "id": 1,
                                "email": "john@example.com",
                                "first_name": "John",
                                "last_name": "Doe",
                            },
                            "tokens": {
                                "access": "jwt-access-token",
                                "refresh": "jwt-refresh-token"
                            }
                        }
                    }
                }
            ),
            400: "Invalid credentials"
        }
    )
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return success_response(
                data=serializer.validated_data,
                message="Login successful"
            )
        return error_response(errors=serializer.errors, message="Login failed")

    @swagger_auto_schema(
        method="post",
        request_body=VerifyOTPSerializer,
        responses={
            201: openapi.Response("Account verified successfully"),
            400: "Invalid OTP or input"
        }
    )
    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            try:
                user, result = verify_otp_and_create_user(email, otp)
            except Exception as e:
                return error_response(message="Internal error verifying OTP", errors=str(e))

            if user is None:
                return error_response(message="OTP verification failed", errors=result)

            return success_response(
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                    },
                    "tokens": result,
                },
                message="Account verified successfully",
                code=status.HTTP_201_CREATED,
            )
        return error_response(errors=serializer.errors, message="Invalid input")
