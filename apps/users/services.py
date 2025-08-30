from .models import User, EmailOTP
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django.utils import timezone
from datetime import timedelta

def generate_otp():
    return str(random.randint(100000, 999999))

def generate_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

def send_otp_to_email(validated_data):
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=10)

    # Update or create OTP entry
    EmailOTP.objects.update_or_create(
        email=validated_data['email'],
        defaults={
            'otp': otp,
            'expires_at': expires_at,
            'password': validated_data['password'],
            'role': validated_data.get('role', 'customer'),
            'first_name': validated_data.get('first_name', ''),
            'last_name': validated_data.get('last_name', ''),
        }
    )

    # Send email
    send_mail(
        subject="Your OTP Code",
        message=f"Your verification code is: {otp}",
        from_email="noreply@example.com",
        recipient_list=[validated_data['email']],
        fail_silently=False,
    )

def verify_otp_and_create_user(email, otp):
    try:
        otp_obj = EmailOTP.objects.get(email=email)
    except EmailOTP.DoesNotExist:
        return None, "OTP not found."

    if otp_obj.otp != otp:
        return None, "Invalid OTP."
    
    if otp_obj.is_expired():
        return None, "OTP has expired."

    if User.objects.filter(email=email).exists():
        return None, "User already exists."

    # Create user now
    user = User.objects.create_user(
        email=otp_obj.email,
        password=otp_obj.password,
        role=otp_obj.role,
        first_name=otp_obj.first_name,
        last_name=otp_obj.last_name,
        is_active=True
    )

    otp_obj.delete()  # Remove used OTP

    tokens = generate_tokens_for_user(user)
    return user, tokens

