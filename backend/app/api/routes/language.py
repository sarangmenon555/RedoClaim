"""
Language API — RedoClaim
Exposes Sarvam AI translation/transliteration/detection to the frontend,
and lets users view a saved claim's audit report in Malayalam, Tamil,
Telugu, Kannada, or Hindi.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Claim
from app.api.deps.auth import get_current_user
from app.services.language.sarvam_service import (
    sarvam_client,
    SUPPORTED_LANGUAGES,
    normalize_language,
)
from app.services.language.localization import localize_audit_response

logger = logging.getLogger(__name__)
router = APIRouter()


# ── 1. Supported languages ─────────────────────────────────────────
@router.get("/supported")
async def get_supported_languages():
    """List of languages RedoClaim supports for translated output."""
    return {
        "languages": [
            {"code": key, "sarvam_code": v["code"], "label": v["label"]}
            for key, v in SUPPORTED_LANGUAGES.items()
        ],
        "sarvam_configured": sarvam_client.enabled,
    }


# ── 2. Generic text translation ─────────────────────────────────────
class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    target_language: str = Field(..., description="en, hi, ml, ta, te, or kn")
    source_language: str = Field("auto", description="auto, en, hi, ml, ta, te, or kn")
    mode: str = Field("formal", description="formal, modern-colloquial, classic-colloquial, code-mixed")


@router.post("/translate")
async def translate_text(
    req: TranslateRequest,
    current_user=Depends(get_current_user),
):
    if normalize_language(req.target_language) not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported target_language: {req.target_language}")

    translated = await sarvam_client.translate_long_text(
        text=req.text,
        target_language=req.target_language,
        source_language=req.source_language,
        mode=req.mode,
    )
    return {
        "original_text": req.text,
        "translated_text": translated,
        "target_language": normalize_language(req.target_language),
    }


# ── 3. Transliteration ──────────────────────────────────────────────
class TransliterateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    target_language: str = Field(..., description="en, hi, ml, ta, te, or kn")
    source_language: str = Field("auto")
    spoken_form: bool = False


@router.post("/transliterate")
async def transliterate_text(
    req: TransliterateRequest,
    current_user=Depends(get_current_user),
):
    if normalize_language(req.target_language) not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported target_language: {req.target_language}")

    transliterated = await sarvam_client.transliterate(
        text=req.text,
        target_language=req.target_language,
        source_language=req.source_language,
        spoken_form=req.spoken_form,
    )
    return {
        "original_text": req.text,
        "transliterated_text": transliterated,
        "target_language": normalize_language(req.target_language),
    }


# ── 4. Language detection ───────────────────────────────────────────
class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


@router.post("/detect")
async def detect_language(
    req: DetectRequest,
    current_user=Depends(get_current_user),
):
    result = await sarvam_client.identify_language(req.text)
    return result


# ── 5. Translate a saved claim's audit report ───────────────────────
@router.get("/claims/{claim_id}/translate")
async def translate_claim_report(
    claim_id: str,
    target_language: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the claim's audit report + summary translated into the
    requested language. Translations are cached on the claim so repeat
    requests for the same language don't re-hit the Sarvam API.
    """
    lang = normalize_language(target_language)
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(400, f"Unsupported target_language: {target_language}")

    claim = await db.get(Claim, claim_id)
    if not claim or str(claim.owner_id) != str(current_user.id):
        raise HTTPException(404, "Claim not found")
    if not claim.audit_report:
        raise HTTPException(400, "This claim has no audit report yet.")

    cache = claim.translated_reports or {}
    if lang in cache:
        return {
            "claim_id": claim_id,
            "language": lang,
            "report": cache[lang],
            "cached": True,
        }

    if lang == "en":
        translated_report = claim.audit_report
    else:
        translated_report = await localize_audit_response(claim.audit_report, lang)
        cache[lang] = translated_report
        claim.translated_reports = cache
        await db.flush()

    return {
        "claim_id": claim_id,
        "language": lang,
        "report": translated_report,
        "cached": False,
    }
