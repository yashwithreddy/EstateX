import logging

from fastapi import APIRouter

from app.ml.service import ml_service
from app.schemas.ai import ExplainRequest, ExplainResponse, RiskRequest, RiskResponse, ROIRequest, ROIResponse

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


@router.post("/explain", response_model=ExplainResponse)
def explain_roi(payload: ExplainRequest):
    logger.info("ai_explain")
    return ml_service.explain_roi(payload.model_dump())
