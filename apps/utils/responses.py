from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

def success_response(data=None, message="Success", code=status.HTTP_200_OK):
    return Response({
        "success": True,
        "message": message,
        "data": data,
        "timestamp": timezone.now().isoformat()
    }, status=code)

def error_response(errors=None, message="Error", code=status.HTTP_400_BAD_REQUEST, error_code=None):
    # Generate error code if not provided
    if not error_code:
        error_code = get_error_code_from_status(code)
    
    response_data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": timezone.now().isoformat()
        }
    }
    
    # Structure field errors properly
    if errors:
        if isinstance(errors, dict):
            details = {}
            for field, field_errors in errors.items():
                if isinstance(field_errors, list):
                    details[field] = [str(error) for error in field_errors]
                else:
                    details[field] = [str(field_errors)]
            if details:
                response_data["error"]["details"] = details
        else:
            response_data["error"]["details"] = {"general": [str(errors)]}
    
    return Response(response_data, status=code)

def validation_error_response(serializer_errors, message="Validation failed"):
    return error_response(
        errors=serializer_errors,
        message=message,
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code="VALIDATION_ERROR"
    )

def get_error_code_from_status(status_code):
    """Map HTTP status codes to error codes"""
    error_codes = {
        400: 'BAD_REQUEST',
        401: 'UNAUTHORIZED',
        403: 'FORBIDDEN',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        409: 'CONFLICT',
        422: 'VALIDATION_ERROR',
        429: 'RATE_LIMIT_EXCEEDED',
        500: 'INTERNAL_ERROR'
    }
    return error_codes.get(status_code, 'UNKNOWN_ERROR')