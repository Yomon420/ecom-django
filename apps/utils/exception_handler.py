from rest_framework.views import exception_handler
from .responses import error_response

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        return error_response(
            errors=response.data,
            message=str(exc),
            code=response.status_code
        )
    return response
