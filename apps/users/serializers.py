from rest_framework import serializers
from .models import User, EmailOTP
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from .services import generate_tokens_for_user

User = get_user_model()

# UserSerializer is for output/display like displaying profile infomation.
class UserSerializer(serializers.ModelSerializer):
    is_superuser = serializers.BooleanField(read_only=True) 

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'created_at',
            'is_superuser',
        ]
        read_only_fields = ['id', 'created_at', 'is_superuser']


# RegisterSerializer is for input/creation like handling user registration to securely handle password
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'first_name', 'last_name', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError(_("Both email and password are required."))

        user = authenticate(username=email, password=password)
        
        if not user:
            try:
                user_obj = User.objects.get(email=email)
                if not user_obj.is_active:
                    raise serializers.ValidationError(_("Account is not activated. Please check your email."))
            except User.DoesNotExist:
                pass
            raise serializers.ValidationError(_("Invalid credentials."))

        if not user.is_active:
            raise serializers.ValidationError(_("User account is disabled."))

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
