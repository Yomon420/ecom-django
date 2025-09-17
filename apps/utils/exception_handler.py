# apps/utils/exceptions.py - Enhanced exception handler
from rest_framework.views import exception_handler
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError
from .responses import error_response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        # Get error code based on exception type
        error_code = get_error_code_from_exception(exc, response.status_code)
        
        # Get user-friendly message
        message = get_user_friendly_message(exc, response)
        
        return error_response(
            errors=response.data,
            message=message,
            code=response.status_code,
            error_code=error_code
        )
    
    return response

def get_error_code_from_exception(exc, status_code):
    """Generate specific error codes based on exception type"""
    exception_codes = {
        'AuthenticationFailed': 'AUTHENTICATION_FAILED',
        'NotAuthenticated': 'NOT_AUTHENTICATED',
        'PermissionDenied': 'PERMISSION_DENIED',
        'NotFound': 'NOT_FOUND',
        'ValidationError': 'VALIDATION_ERROR',
        'ParseError': 'PARSE_ERROR',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'NotAcceptable': 'NOT_ACCEPTABLE',
        'Throttled': 'RATE_LIMIT_EXCEEDED'
    }
    
    exc_name = exc.__class__.__name__
    return exception_codes.get(exc_name, f'HTTP_{status_code}')

def get_user_friendly_message(exc, response):
    """Extract or generate user-friendly error messages"""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, dict):
            # For validation errors, try to get a general message
            if 'non_field_errors' in exc.detail:
                return str(exc.detail['non_field_errors'][0])
            # Return first field error as general message
            for field, errors in exc.detail.items():
                if isinstance(errors, list) and errors:
                    return f"Error in {field}: {errors[0]}"
                return f"Error in {field}: {errors}"
        return str(exc.detail)
    return "An error occurred"