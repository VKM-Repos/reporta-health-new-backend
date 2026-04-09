# apps/core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        # Normalize error responses to always have a 'detail' key
        if isinstance(response.data, dict) and 'detail' not in response.data:
            response.data = {'detail': response.data}

    return response