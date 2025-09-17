from rest_framework import serializers
from .models import User, EmailOTP
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from .services import generate_tokens_for_user

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    is_superuser = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'role',
            'created_at', 'is_superuser'
        ]
        read_only_fields = ['id', 'created_at', 'is_superuser']

class RegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("USER_ALREADY_EXISTS", code="USER_ALREADY_EXISTS")
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages, code="WEAK_PASSWORD")
        return value

    def validate(self, data):
        # Only validate password confirmation if it's provided
        if 'password_confirm' in data:
            if data['password'] != data['password_confirm']:
                raise serializers.ValidationError({
                    'password_confirm': ['Passwords do not match']
                }, code="PASSWORD_MISMATCH")
            data.pop('password_confirm')  # Remove from data before saving
        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only numbers", code="INVALID_OTP_FORMAT")
        return value

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError(
                _("Both email and password are required."),
                code="MISSING_CREDENTIALS"
            )

        user = authenticate(username=email, password=password)
        
        if not user:
            # Check if user exists but account is inactive
            try:
                user_obj = User.objects.get(email=email)
                if not user_obj.is_active:
                    raise serializers.ValidationError(
                        _("Account is not activated. Please check your email."),
                        code="ACCOUNT_NOT_ACTIVATED"
                    )
            except User.DoesNotExist:
                pass
            
            raise serializers.ValidationError(
                _("Invalid email or password."),
                code="INVALID_CREDENTIALS"
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _("User account is disabled."),
                code="ACCOUNT_DISABLED"
            )

        tokens = generate_tokens_for_user(user)

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_superuser": user.is_superuser,
            },
            "tokens": tokens,
        }

class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        from rest_framework_simplejwt.tokens import RefreshToken, TokenError

        try:
            refresh = RefreshToken(data["refresh"])
            return {"access": str(refresh.access_token)}
        except TokenError as e:
            if "expired" in str(e).lower():
                raise serializers.ValidationError(
                    {"refresh": "Refresh token has expired"},
                    code="TOKEN_EXPIRED"
                )
            raise serializers.ValidationError(
                {"refresh": "Token is invalid"},
                code="INVALID_TOKEN"
            )