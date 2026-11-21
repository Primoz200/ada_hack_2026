from fastapi import APIRouter
from sqlmodel import select

from app.deps import Db
from app.models import Pathway
from app.models.schemas import PathwayOut
from app.services import queries

router = APIRouter(prefix="/api", tags=["pathways"])


@router.get("/pathways", response_model=list[PathwayOut], operation_id="listPathways")
def list_pathways(db: Db):
    return [queries.pathway_out(p) for p in db.exec(select(Pathway)).all()]
