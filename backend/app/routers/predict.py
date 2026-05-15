import logging

from fastapi import APIRouter

from app.ml.service import ml_service
from app.schemas.ai import RiskRequest, RiskResponse, ROIRequest, ROIResponse, RentalYieldRequest, RentalYieldResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/predict", tags=["predict"])


@router.post("/roi", response_model=ROIResponse)
def predict_roi(payload: ROIRequest):
    logger.info("predict_roi called")
    return ml_service.predict_roi(payload.model_dump())


@router.post("/risk", response_model=RiskResponse)
def predict_risk(payload: RiskRequest):
    logger.info("predict_risk called")
    return ml_service.predict_risk(payload.model_dump())


@router.post("/rental-yield", response_model=RentalYieldResponse)
def predict_rental_yield(payload: RentalYieldRequest):
    logger.info("predict_rental_yield called")
    return ml_service.predict_rental_yield(payload.model_dump())
