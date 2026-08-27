from __future__ import annotations

DEFAULT_SECURE_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def csp_for_origin(origin: str) -> str:
    """CSP allowing only same-origin connections for the SPA shell."""
    return (
        "default-src 'none'; "
        "connect-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "frame-ancestors 'none'"
    )
