import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    logger.exception("Unhandled server error", exc_info=exc)

    return Response(
        {"detail": "Internal server error. Please try again later."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
