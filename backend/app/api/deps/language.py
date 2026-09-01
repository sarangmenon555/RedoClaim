"""
Language resolution dependency — RedoClaim
Lets any route accept a `?lang=ml` query param or an `X-Language: ml`
header to get content back in Malayalam, Tamil, Telugu, Kannada, or Hindi.
Falls back to the user's saved `preferred_language`, then to English.
"""
from typing import Optional

from fastapi import Header, Query

from app.services.language.sarvam_service import normalize_language, DEFAULT_LANGUAGE


async def get_request_language(
    lang: Optional[str] = Query(
        None,
        description="Response language: en, hi, ml, ta, te, kn",
    ),
    x_language: Optional[str] = Header(
        None,
        alias="X-Language",
        description="Response language header, alternative to ?lang=",
    ),
) -> str:
    """
    Resolution order: ?lang= query param > X-Language header > default.
    Always returns a validated short code (en/hi/ml/ta/te/kn) — never a
    raw, unvalidated value from the client.
    """
    raw = lang or x_language
    return normalize_language(raw) if raw else DEFAULT_LANGUAGE
