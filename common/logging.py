import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor

_RESERVED = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
    "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
    "created", "msecs", "relativeCreated", "thread", "threadName",
    "processName", "process", "message", "taskName",
})

_db_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="req-log")

_log = logging.getLogger("api.requests")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        data = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                data[key] = value
        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False, default=str)


class RequestLoggingMiddleware:
    _SKIP_PREFIXES = ('/static/', '/media/', '/admin/', '/api/schema/', '/api/swagger/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000)

        user = getattr(request, "user", None)
        is_authenticated = bool(user and getattr(user, "is_authenticated", False))
        user_label = str(user) if is_authenticated else "anonymous"

        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        _log.log(
            level,
            "%s %s → %s",
            request.method,
            request.path,
            response.status_code,
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "user": user_label,
            },
        )

        if not any(request.path.startswith(p) for p in self._SKIP_PREFIXES):
            self._enqueue_db_write(request, response, duration_ms, user, is_authenticated)

        return response

    @staticmethod
    def _enqueue_db_write(request, response, duration_ms, user, is_authenticated):
        ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or ''
        if ',' in ip:
            ip = ip.split(',')[0].strip()

        payload = {
            'user_id': user.pk if is_authenticated else None,
            'method': request.method,
            'path': request.path[:500],
            'status_code': response.status_code,
            'duration_ms': duration_ms,
            'ip_address': ip or None,
        }
        _db_pool.submit(_write_log, payload)


def _write_log(payload):
    from django.db import connection
    try:
        from user.models import RequestLog
        RequestLog.objects.create(**payload)
    except Exception:
        _log.exception("RequestLog DB write failed")
    finally:
        connection.close()
