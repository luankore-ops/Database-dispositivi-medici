"""
security.py
------------
Protezioni HTTP di base per il backend FastAPI.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Aggiunge HTTP security headers alle risposte dell'API.
    """

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:

        response = await call_next(request)

        # Impedisce al browser di interpretare
        # erroneamente il Content-Type.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Impedisce l'inclusione dell'applicazione
        # all'interno di iframe.
        response.headers["X-Frame-Options"] = "DENY"

        # Non inviare informazioni sul referrer.
        response.headers["Referrer-Policy"] = "no-referrer"

        # Evita il caching delle risposte API.
        response.headers["Cache-Control"] = "no-store"

        # Disabilita funzionalità browser non necessarie.
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=()"
        )

        return response