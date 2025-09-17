from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, VerifyOTPSerializer, UserSerializer, LoginSerializer, RefreshTokenSerializer
from .services import send_otp_to_email, verify_otp_and_create_user
from django.contrib.auth import get_user_model
from apps.utils.responses import success_response, error_response, validation_error_response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)
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

    @swagger_auto_schema(
        method='get',
        operation_description="Retrieve the currently authenticated user's details.",
        responses={
            200: openapi.Response("User details retrieved successfully", UserSerializer()),
            401: openapi.Response("Authentication required"),
        },
    )
    @swagger_auto_schema(
        method='patch',
        operation_description="Update the currently authenticated user's details.",
        request_body=UserSerializer,
        responses={
            200: openapi.Response("User updated successfully", UserSerializer()),
            400: openapi.Response("Validation errors"),
            401: openapi.Response("Authentication required"),
        },
    )
    @swagger_auto_schema(
        method='delete',
        operation_description="Delete (or deactivate) the currently authenticated user account.",
        responses={
            204: openapi.Response("Account successfully deleted"),
            401: openapi.Response("Authentication required"),
        },
    )
    @action(detail=False, methods=["get", "patch", "delete"], url_path="me")
    def me(self, request):
        user = request.user
        
        try:
            if request.method == "GET":
                serializer = self.get_serializer(user)
                return success_response(
                    data=serializer.data,
                    message="User details retrieved successfully"
                )
                
            elif request.method == "PATCH":
                serializer = self.get_serializer(
                    user, data=request.data, partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return success_response(
                        data=serializer.data,
                        message="Profile updated successfully"
                    )
                return validation_error_response(serializer.errors)
                
            elif request.method == "DELETE":
                user.delete()  # or soft-delete if you prefer
                return success_response(
                    message="Account deleted successfully",
                    code=status.HTTP_204_NO_CONTENT
                )
                
        except Exception as e:
            logger.error(f"Error in UserViewSet.me: {str(e)}", exc_info=True)
            return error_response(
                message="An error occurred while processing your request",
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                error_code="INTERNAL_ERROR"
            )


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        method="post",
        operation_description="Register a new user account. Sends OTP to email for verification.",
        request_body=RegisterSerializer,
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "OTP sent to email. Please verify to complete registration.",
                        "data": None,
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            ),
            422: openapi.Response(
                description="Validation errors",
                examples={
                    "application/json": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Validation failed",
                            "details": {
                                "email": ["This email is already registered"],
                                "password": ["Password too short"]
                            },
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            ),
            500: openapi.Response("Failed to send OTP")
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
                logger.error(f"Failed to send OTP: {str(e)}", exc_info=True)
                return error_response(
                    message="Failed to send verification email. Please try again.",
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error_code="OTP_SEND_FAILED"
                )
        
        return validation_error_response(serializer.errors)

    @swagger_auto_schema(
        method="post",
        operation_description="Login with email and password",
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
                                "role": "customer",
                                "is_superuser": False
                            },
                            "tokens": {
                                "access": "jwt-access-token",
                                "refresh": "jwt-refresh-token"
                            }
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            ),
            422: openapi.Response(
                description="Invalid credentials or validation errors",
                examples={
                    "application/json": {
                        "success": False,
                        "error": {
                            "code": "INVALID_CREDENTIALS",
                            "message": "Invalid email or password",
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            )
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
        
        return validation_error_response(serializer.errors, message="Login failed")

    @swagger_auto_schema(
        method="post",
        operation_description="Verify OTP and complete user registration",
        request_body=VerifyOTPSerializer,
        responses={
            201: openapi.Response(
                description="Account verified successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Account verified successfully",
                        "data": {
                            "user": {
                                "id": 1,
                                "email": "john@example.com",
                                "role": "customer"
                            },
                            "tokens": {
                                "access": "jwt-access-token",
                                "refresh": "jwt-refresh-token"
                            }
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            ),
            422: openapi.Response(
                description="Validation errors",
                examples={
                    "application/json": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Validation failed",
                            "details": {
                                "otp": ["OTP must contain only numbers"]
                            },
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="OTP verification failed",
                examples={
                    "application/json": {
                        "success": False,
                        "error": {
                            "code": "OTP_EXPIRED",
                            "message": "OTP has expired",
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            )
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
                logger.error(f"Error verifying OTP: {str(e)}", exc_info=True)
                return error_response(
                    message="An error occurred while verifying OTP",
                    code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    error_code="VERIFICATION_ERROR"
                )

            if user is None:
                # Map specific error messages to error codes
                error_mapping = {
                    "OTP not found.": ("OTP_NOT_FOUND", "No OTP found for this email"),
                    "Invalid OTP.": ("INVALID_OTP", "The verification code is incorrect"),
                    "OTP has expired.": ("OTP_EXPIRED", "Verification code has expired. Please request a new one"),
                    "User already exists.": ("USER_ALREADY_EXISTS", "An account with this email already exists")
                }
                
                error_code, user_message = error_mapping.get(result, ("VERIFICATION_FAILED", result))
                
                return error_response(
                    message=user_message,
                    code=status.HTTP_400_BAD_REQUEST,
                    error_code=error_code
                )

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
        
        return validation_error_response(serializer.errors, message="Invalid input")
    
    @swagger_auto_schema(
        method="post",
        operation_description="Refresh access token using refresh token",
        request_body=RefreshTokenSerializer,
        responses={
            200: openapi.Response(
                description="New access token generated",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Token refreshed successfully",
                        "data": {
                            "access": "new-jwt-access-token"
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            ),
            422: openapi.Response(
                description="Invalid or expired refresh token",
                examples={
                    "application/json": {
                        "success": False,
                        "error": {
                            "code": "TOKEN_EXPIRED",
                            "message": "Refresh token has expired",
                            "details": {
                                "refresh": ["Refresh token has expired"]
                            },
                            "timestamp": "2024-01-15T10:30:00Z"
                        }
                    }
                }
            )
        }
    )
    @action(detail=False, methods=["post"], url_path="refresh")
    def refresh(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        
        if serializer.is_valid():
            return success_response(
                data=serializer.validated_data,
                message="Token refreshed successfully"
            )
        
        return validation_error_response(serializer.errors, message="Token refresh failed")