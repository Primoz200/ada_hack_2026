"""Camera exercise configuration endpoint."""

from fastapi import APIRouter

from app.models.api import CameraExerciseOut
from app.services.scoring import camera_exercises

router = APIRouter(prefix="/api/camera", tags=["camera"])


@router.get(
    "/exercises", response_model=list[CameraExerciseOut], operation_id="listCameraExercises"
)
def list_camera_exercises() -> list[CameraExerciseOut]:
    """Return the available camera exercise cue timelines."""
    return [CameraExerciseOut.model_validate(exercise) for exercise in camera_exercises()]
