"""
Sarvam AI integration — RedoClaim
Provides translation, transliteration, and language identification for
Malayalam, Tamil, Telugu, Kannada, and Hindi (plus English), so users can
read audit reports, claim summaries, and guidance in their own language.

Docs: https://docs.sarvam.ai
API base: https://api.sarvam.ai
"""
import asyncio
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SARVAM_BASE_URL = "https://api.sarvam.ai"

# sarvam-translate:v1 accepts up to 2000 characters per request and supports
# every language we care about with formal-mode translation. mayura:v1 is
# capped at 1000 chars but supports colloquial modes — we default to
# sarvam-translate:v1 since RedoClaim's content (legal/regulatory) reads
# best in a formal register.
TRANSLATE_MODEL = "sarvam-translate:v1"
TRANSLATE_MAX_CHARS = 2000

# Language codes RedoClaim exposes to the frontend, mapped to Sarvam's
# BCP-47-style codes.
SUPPORTED_LANGUAGES = {
    "en": {"code": "en-IN", "label": "English"},
    "hi": {"code": "hi-IN", "label": "हिन्दी (Hindi)"},
    "ml": {"code": "ml-IN", "label": "മലയാളം (Malayalam)"},
    "ta": {"code": "ta-IN", "label": "தமிழ் (Tamil)"},
    "te": {"code": "te-IN", "label": "తెలుగు (Telugu)"},
    "kn": {"code": "kn-IN", "label": "ಕನ್ನಡ (Kannada)"},
}

DEFAULT_LANGUAGE = "en"


def normalize_language(lang: Optional[str]) -> str:
    """
    Accept 'ml', 'ml-IN', 'ML', etc. and return the short internal key
    ('ml'). Falls back to the default language if unrecognized.
    """
    if not lang:
        return DEFAULT_LANGUAGE
    key = lang.strip().lower().split("-")[0]
    if key in SUPPORTED_LANGUAGES:
        return key
    return DEFAULT_LANGUAGE


def to_sarvam_code(lang: Optional[str]) -> str:
    return SUPPORTED_LANGUAGES[normalize_language(lang)]["code"]


class SarvamAPIError(Exception):
    pass


class SarvamClient:
    """Thin async wrapper around the Sarvam AI text APIs."""

    def __init__(self):
        self.api_key = settings.SARVAM_API_KEY
        self.enabled = bool(self.api_key)
        if not self.enabled:
            logger.warning(
                "SARVAM_API_KEY not set — regional language features will "
                "fall back to returning original (English) text."
            )

    def _headers(self) -> dict:
        return {
            "api-subscription-key": self.api_key,
            "Content-Type": "application/json",
        }

    async def _post(self, path: str, payload: dict, retries: int = 2) -> dict:
        if not self.enabled:
            raise SarvamAPIError("Sarvam API key not configured")

        last_error = None
        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(retries + 1):
                try:
                    resp = await client.post(
                        f"{SARVAM_BASE_URL}{path}",
                        headers=self._headers(),
                        json=payload,
                    )
                    if resp.status_code == 429 and attempt < retries:
                        await asyncio.sleep(1.5 * (attempt + 1))
                        continue
                    resp.raise_for_status()
                    return resp.json()
                except httpx.HTTPStatusError as e:
                    last_error = e
                    body = e.response.text[:300] if e.response is not None else ""
                    logger.error(f"Sarvam API error {e.response.status_code}: {body}")
                    if e.response is not None and e.response.status_code in (400, 401, 403, 422):
                        raise SarvamAPIError(f"Sarvam API error: {body}") from e
                except httpx.HTTPError as e:
                    last_error = e
                    logger.warning(f"Sarvam API request failed (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(1.0 * (attempt + 1))

        raise SarvamAPIError(f"Sarvam API request failed after retries: {last_error}")

    # ── Translation ──────────────────────────────────────────────
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        mode: str = "formal",
        speaker_gender: str = "Male",
    ) -> str:
        """
        Translate a single chunk of text (<= TRANSLATE_MAX_CHARS).
        target_language / source_language accept short codes ('ml') or
        Sarvam codes ('ml-IN') — both are normalized here.
        """
        if not text or not text.strip():
            return text

        target_code = to_sarvam_code(target_language)
        source_code = "auto" if source_language == "auto" else to_sarvam_code(source_language)

        if target_code == source_code:
            return text

        payload = {
            "input": text,
            "source_language_code": source_code,
            "target_language_code": target_code,
            "model": TRANSLATE_MODEL,
            "mode": mode,
            "speaker_gender": speaker_gender,
        }
        try:
            data = await self._post("/translate", payload)
            return data.get("translated_text", text)
        except SarvamAPIError as e:
            logger.error(f"Translation failed, returning original text: {e}")
            return text

    async def translate_long_text(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        mode: str = "formal",
    ) -> str:
        """
        Translate arbitrary-length text by chunking on paragraph/sentence
        boundaries to stay under TRANSLATE_MAX_CHARS per request, then
        rejoining. Chunks are translated concurrently (bounded) for speed.
        """
        if not text or not text.strip():
            return text

        if len(text) <= TRANSLATE_MAX_CHARS:
            return await self.translate(text, target_language, source_language, mode)

        chunks = _chunk_text(text, TRANSLATE_MAX_CHARS)
        semaphore = asyncio.Semaphore(4)

        async def _translate_chunk(chunk: str) -> str:
            async with semaphore:
                return await self.translate(chunk, target_language, source_language, mode)

        translated_chunks = await asyncio.gather(*[_translate_chunk(c) for c in chunks])
        return "".join(translated_chunks)

    # ── Transliteration ──────────────────────────────────────────
    async def transliterate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
        spoken_form: bool = False,
        numerals_format: str = "international",
    ) -> str:
        if not text or not text.strip():
            return text

        target_code = to_sarvam_code(target_language)
        source_code = "auto" if source_language == "auto" else to_sarvam_code(source_language)

        payload = {
            "input": text[:1000],
            "source_language_code": source_code,
            "target_language_code": target_code,
            "spoken_form": spoken_form,
            "numerals_format": numerals_format,
        }
        try:
            data = await self._post("/transliterate", payload)
            return data.get("transliterated_text", text)
        except SarvamAPIError as e:
            logger.error(f"Transliteration failed, returning original text: {e}")
            return text

    # ── Language identification ─────────────────────────────────
    async def identify_language(self, text: str) -> dict:
        if not text or not text.strip():
            return {"language_code": None, "script_code": None}

        payload = {"input": text[:1000]}
        try:
            data = await self._post("/text-lid", payload)
            return {
                "language_code": data.get("language_code"),
                "script_code": data.get("script_code"),
            }
        except SarvamAPIError as e:
            logger.error(f"Language identification failed: {e}")
            return {"language_code": None, "script_code": None}


def _chunk_text(text: str, max_chars: int) -> list[str]:
    """
    Split text into chunks no larger than max_chars, breaking on paragraph
    boundaries first, then sentence boundaries, then hard-splitting as a
    last resort. Keeps translation quality high by not cutting mid-sentence
    where avoidable.
    """
    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}" if current else para
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(para) <= max_chars:
            current = para
            continue

        # Paragraph itself too long — split on sentences.
        sentences = para.replace("। ", "।\n").split("\n") if "।" in para else para.split(". ")
        buf = ""
        for sent in sentences:
            piece = f"{buf} {sent}".strip() if buf else sent
            if len(piece) <= max_chars:
                buf = piece
            else:
                if buf:
                    chunks.append(buf)
                # Hard-split if a single sentence still exceeds the limit.
                if len(sent) > max_chars:
                    for i in range(0, len(sent), max_chars):
                        chunks.append(sent[i:i + max_chars])
                    buf = ""
                else:
                    buf = sent
        if buf:
            current = buf

    if current:
        chunks.append(current)

    return chunks


sarvam_client = SarvamClient()
