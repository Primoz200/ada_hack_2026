"""Camera exercise definitions for the frontend game (single source of truth: Primož's exercises.py)."""
from fastapi import APIRouter

from app.models.schemas import CameraExercise
from app.services import camera_model

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get("/exercises", response_model=list[CameraExercise], operation_id="listCameraExercises")
def list_exercises():
    return [CameraExercise(level=level, **{k: ex.get(k) for k in (
        "key", "name", "detector", "duration_s", "first_cue_s", "cue_period_s", "n_cues", "up_s",
        "open_window_s", "instructions")}) for level, ex in sorted(camera_model.EXERCISES.items())]
