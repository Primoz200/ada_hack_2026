"""Pathway configuration endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models.api import PathwayOut
from app.models.tables import Pathway
from app.seed.demo import PATHWAY_ROWS

router = APIRouter(tags=["pathways"])


@router.get("/api/pathways", response_model=list[PathwayOut], operation_id="listPathways")
def list_pathways(session: Annotated[Session, Depends(get_session)]) -> list[Pathway]:
    """Return configured recovery pathways and their questionnaire/game details."""
    pathways = list(session.exec(select(Pathway)).all())
    order = {code: index for index, (code, _) in enumerate(PATHWAY_ROWS)}
    return sorted(pathways, key=lambda pathway: order.get(pathway.code, len(order)))
