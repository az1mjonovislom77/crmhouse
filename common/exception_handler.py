import logging
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework import status
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, 'message_dict') else exc.messages
        exc = DRFValidationError(detail=detail)

    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, IntegrityError):
        logger.warning("Integrity error: %s", exc, exc_info=exc)
        return Response(
            {"detail": "Ma'lumotlar ziddiyati: yozuv allaqachon mavjud yoki bog'liq yozuv topilmadi."},
            status=status.HTTP_400_BAD_REQUEST)

    logger.exception("Unhandled server error", exc_info=exc)

    return Response(
        {"detail": "Internal server error. Please try again later."},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
