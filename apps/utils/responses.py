from rest_framework.response import Response
from rest_framework import status

def success_response(data=None, message="Success", code=status.HTTP_200_OK):
    return Response(
        {"success": True, "message": message, "data": data},
        status=code
    )

def error_response(errors=None, message="Error", code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {"success": False, "message": message, "errors": errors},
        status=code
    )
