from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_user
from app.api.deps.language import get_request_language
from app.core.database import get_db
from app.services.assistant.engine import handle_message

router = APIRouter()

AI_DISCLAIMER = (
    "This is AI-generated guidance for information only, not legal advice. It can contain errors or misread documents. "
    "Verify citations and deadlines at irdai.gov.in before acting, and consider a licensed advocate for high-value claims."
)


class AssistantRequest(BaseModel):
    message: str = Field(default="", max_length=6000)
    document_ids: list[str] = Field(default_factory=list, max_length=8)
    new_document_ids: list[str] = Field(default_factory=list, max_length=8)
    context: dict = Field(default_factory=dict)
    history: list[dict] = Field(default_factory=list, max_length=12)


@router.post("/ask")
async def assistant_ask(
    body: AssistantRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    lang: str = Depends(get_request_language),
):
    result = await handle_message(
        db=db, user=current_user, lang=lang, message=body.message,
        document_ids=body.document_ids, new_document_ids=body.new_document_ids,
        context=body.context, history=body.history,
    )
    await db.commit()
    result["ai_disclaimer"] = AI_DISCLAIMER
    return result
