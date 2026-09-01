"""
Report localization — RedoClaim
Walks a JSON-shaped API response (audit reports, claim summaries, guides)
and translates the human-readable text leaves into the user's chosen
language, while leaving codes, IDs, enums, dates, numbers, and URLs
untouched. This is what powers "view this report in Malayalam / Tamil /
Telugu / Kannada / Hindi" on the frontend.
"""
import asyncio
import logging
import re
import uuid as uuid_lib

from app.services.language.sarvam_service import sarvam_client, normalize_language

logger = logging.getLogger(__name__)

_ISO_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$"
)
_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

# Machine-readable tokens that appear as values throughout RedoClaim's JSON
# responses (enum values, insurance types, statuses, script/language codes).
# Left untranslated so the frontend can keep matching on them.
_SKIP_VALUES = {
    "health", "motor", "life",
    "submitted", "under_review", "rejected", "appealing", "resolved", "escalated",
    "gro", "insurer_escalation", "ombudsman", "bima_bharosa", "consumer_court",
    "high", "medium", "low",
    "pdf", "docx", "xlsx", "pptx",
    "en", "hi", "ml", "ta", "te", "kn",
    "en-IN", "hi-IN", "ml-IN", "ta-IN", "te-IN", "kn-IN",
}

# Concurrency cap so we don't fire off dozens of simultaneous Sarvam calls
# for one large report.
_MAX_CONCURRENT_TRANSLATIONS = 6


def _is_translatable(value: str) -> bool:
    stripped = value.strip()
    if len(stripped) < 3:
        return False
    if stripped.lower() in _SKIP_VALUES:
        return False
    if _URL_RE.match(stripped):
        return False
    if _ISO_DATETIME_RE.match(stripped):
        return False
    try:
        uuid_lib.UUID(stripped)
        return False
    except (ValueError, AttributeError):
        pass
    # Pure numbers / currency-like strings ("₹45,000") — skip, no useful
    # translation content, and we don't want the model reformatting figures.
    if re.match(r"^[\d,.\s₹%+-]+$", stripped):
        return False
    return True


async def _translate_all(strings: list[str], target_language: str) -> dict[str, str]:
    """Translate a de-duplicated list of strings, bounded concurrency."""
    unique_strings = list(dict.fromkeys(strings))
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_TRANSLATIONS)

    async def _translate_one(s: str) -> tuple[str, str]:
        async with semaphore:
            if len(s) > 2000:
                translated = await sarvam_client.translate_long_text(s, target_language)
            else:
                translated = await sarvam_client.translate(s, target_language)
            return s, translated

    results = await asyncio.gather(*[_translate_one(s) for s in unique_strings])
    return dict(results)


def _collect_strings(obj, out: list[str]) -> None:
    if isinstance(obj, dict):
        for v in obj.values():
            _collect_strings(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _collect_strings(v, out)
    elif isinstance(obj, str):
        if _is_translatable(obj):
            out.append(obj)


def _rebuild(obj, translations: dict[str, str]):
    if isinstance(obj, dict):
        return {k: _rebuild(v, translations) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_rebuild(v, translations) for v in obj]
    elif isinstance(obj, str):
        return translations.get(obj, obj)
    return obj


async def localize_audit_response(response: dict, target_language: str) -> dict:
    """
    Returns a deep-translated copy of `response`. If `target_language`
    normalizes to English, or Sarvam isn't configured, returns the
    original response unchanged (no wasted API calls).
    """
    lang = normalize_language(target_language)
    if lang == "en" or not sarvam_client.enabled:
        return response

    strings: list[str] = []
    _collect_strings(response, strings)
    if not strings:
        return response

    try:
        translations = await _translate_all(strings, lang)
    except Exception as e:
        logger.error(f"Report localization failed, returning original: {e}")
        return response

    return _rebuild(response, translations)
