"""
Request/Response logging middleware for Reporta Health
"""
import time
import logging
import json
import random

logger = logging.getLogger('api')

MAX_BODY_BYTES = 10_000   # 10 KB — skip body read above this
MAX_RESPONSE_BYTES = 2_000  # 2 KB — truncate captured response bodies
LOG_SAMPLE_RATE = 0.05    # Log only 5% of successful (2xx) requests


class RequestResponseLoggingMiddleware:
    """
    Logs every API request and response with:
    - method, path, status code
    - response time
    - user (if authenticated)
    - request body (POST/PUT/PATCH only, sensitive fields stripped, nested-safe)
    - response body (4xx/5xx only, truncated)
    """
    SENSITIVE_FIELDS = {'password', 'token', 'access', 'refresh', 'authorization'}
    LOG_BODY_METHODS = {'POST', 'PUT', 'PATCH'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        request_body = self._get_request_body(request)

        response = self.get_response(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        user = self._get_user(request)

        # FIX 3: Sample successful requests to control log volume
        if response.status_code < 400 and random.random() > LOG_SAMPLE_RATE:
            return response

        log_data = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration_ms': duration_ms,
            'user': user,
        }

        if request_body:
            log_data['body'] = request_body

        # FIX 4: Capture response body on errors for easier debugging
        if response.status_code >= 400:
            log_data['response_body'] = self._get_response_body(response)

        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))

        return response

    def _get_request_body(self, request):
        """Return sanitized request body for write methods only."""
        if request.method not in self.LOG_BODY_METHODS:
            return None

        # FIX 1: Guard against large payloads before reading the stream
        content_length = request.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_BODY_BYTES:
            return {'_skipped': f'body too large ({content_length} bytes)'}

        content_type = request.content_type or ''
        if 'application/json' not in content_type:
            return None  # Skip multipart/form-data (file uploads) entirely

        try:
            body = json.loads(request.body)
            return self._strip_sensitive(body)
        except (json.JSONDecodeError, Exception):
            return None

    def _strip_sensitive(self, data):
        """Recursively remove sensitive fields from logged body."""  # FIX 2
        if isinstance(data, dict):
            return {
                k: '***' if k.lower() in self.SENSITIVE_FIELDS
                else self._strip_sensitive(v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [self._strip_sensitive(item) for item in data]
        return data

    def _get_response_body(self, response):
        """Safely extract a truncated response body for error logging."""
        try:
            # Avoid consuming streaming responses
            if hasattr(response, 'streaming_content'):
                return {'_skipped': 'streaming response'}
            content = response.content[:MAX_RESPONSE_BYTES]
            return json.loads(content.decode('utf-8', errors='replace'))
        except (json.JSONDecodeError, Exception):
            return None

    def _get_user(self, request):
        """Return user identifier if authenticated."""
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return str(user.email)
        return 'anonymous'