from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, VerifyOTPSerializer, UserSerializer,LoginSerializer
from .services import send_otp_to_email, verify_otp_and_create_user
from django.contrib.auth import get_user_model
from apps.utils.responses import success_response, error_response

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_superuser:
            return User.objects.all().order_by("id")
        return User.objects.filter(id=self.request.user.id)
    

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

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

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return success_response(
                data=serializer.validated_data,
                message="Login successful"
            )
        return error_response(errors=serializer.errors, message="Login failed")

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