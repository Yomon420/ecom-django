from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, VerifyOTPSerializer, UserSerializer,LoginSerializer
from .services import send_otp_to_email, verify_otp_and_create_user
from django.contrib.auth import get_user_model

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
    """
    Authentication ViewSet
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Register new user and send OTP
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            send_otp_to_email(serializer.validated_data)
            return Response(
                {'message': 'OTP sent to email. Please verify to complete registration.'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        User login with email + password (JWT + profile)
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """
        Verify OTP and create user
        """
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']

            user, result = verify_otp_and_create_user(email, otp)

            if user is None:
                return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'role': user.role,
                },
                'tokens': result  # result is the token dict
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)