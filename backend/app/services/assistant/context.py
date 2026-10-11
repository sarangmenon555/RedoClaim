import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.assistant.params import parse_datetime

logger = logging.getLogger(__name__)


@dataclass
class Ctx:
    db: AsyncSession
    user: Any
    message: str
    docs: list
    kinds: dict
    params: dict
    claim_id: Optional[str] = None
    history: list = field(default_factory=list)
    results: dict = field(default_factory=dict)
    new_doc_ids: set = field(default_factory=set)

    def docs_of(self, *kinds: str) -> list:
        return [d for d in self.docs if self.kinds.get(str(d.id)) in kinds]

    def first(self, *kinds: str):
        found = self.docs_of(*kinds)
        return found[0] if found else None

    def num(self, key: str) -> Optional[float]:
        value = self.params.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return None

    def whole(self, key: str) -> Optional[int]:
        value = self.num(key)
        return int(value) if value is not None else None

    def text(self, key: str) -> Optional[str]:
        value = self.params.get(key)
        return value if isinstance(value, str) and value.strip() else None

    def flag(self, key: str) -> Optional[bool]:
        value = self.params.get(key)
        return value if isinstance(value, bool) else None

    def when(self, key: str) -> Optional[datetime]:
        return parse_datetime(self.text(key))

    def ages(self) -> Optional[list]:
        value = self.params.get("family_ages")
        return value if isinstance(value, list) and value else None


def ok(label: str, highlights: list, data: Optional[dict] = None, links: Optional[list] = None) -> dict:
    return {
        "status": "ok",
        "label": label,
        "highlights": [h for h in highlights if h],
        "data": data or {},
        "links": links or [],
    }


def need(label: str, question: str, fields: list) -> dict:
    return {"status": "needs_input", "label": label, "question": question, "fields": fields, "highlights": [], "data": {}, "links": []}


def unavailable(label: str, message: str) -> dict:
    return {"status": "unavailable", "label": label, "message": message, "highlights": [], "data": {}, "links": []}


def failed(label: str) -> dict:
    return {
        "status": "error",
        "label": label,
        "message": "Something went wrong while running this check. Please try again in a moment.",
        "highlights": [],
        "data": {},
        "links": [],
    }


def doc_field(kind: str, label: str) -> dict:
    return {"key": f"doc:{kind}", "label": label, "kind": "document"}


def value_field(key: str, label: str, hint: Optional[str] = None) -> dict:
    spec = {"key": key, "label": label, "kind": "value"}
    if hint:
        spec["hint"] = hint
    return spec


async def guarded(ctx: Ctx, label: str, factory: Callable[[], Awaitable[Any]]) -> Tuple[Any, Optional[dict]]:
    try:
        async with ctx.db.begin_nested():
            return await factory(), None
    except HTTPException as exc:
        return None, unavailable(label, str(exc.detail))
    except Exception as exc:
        logger.error(f"Assistant tool '{label}' failed: {exc}", exc_info=True)
        return None, failed(label)
