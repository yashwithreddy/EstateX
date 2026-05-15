import logging

from fastapi import APIRouter

from app.ml.service import ml_service
from app.schemas.ai import RiskRequest, RiskResponse, ROIRequest, ROIResponse, RentalYieldRequest, RentalYieldResponse

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])
logger = logging.getLogger(__name__)


@router.post("/roi", response_model=ROIResponse)
def predict_roi(payload: ROIRequest):
    logger.info("ai_roi")
    return ml_service.predict_roi(payload.model_dump())


@router.post("/risk", response_model=RiskResponse)
def predict_risk(payload: RiskRequest):
    logger.info("ai_risk")
    return ml_service.predict_risk(payload.model_dump())


@router.post("/rental-yield", response_model=RentalYieldResponse)
def predict_rental_yield(payload: RentalYieldRequest):
    logger.info("ai_rental_yield")
    return ml_service.predict_rental_yield(payload.model_dump())
