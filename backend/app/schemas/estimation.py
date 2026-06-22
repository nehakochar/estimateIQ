from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubFeatureItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sub_feature_name: str
    description: str
    frontend_hours: float
    backend_hours: float
    mobile_hours: float
    complexity: str = Field(..., description="Low, Medium, or High")
    assumptions: Optional[str] = None


class RequirementEstimateGroup(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: UUID
    req_id: str
    name: str
    req_type: str
    description: str
    sub_features: List[SubFeatureItem]
    subtotal_frontend: float
    subtotal_backend: float
    subtotal_mobile: float
    subtotal_total: float


class ProjectEstimatesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: UUID
    estimation_status: str
    total_frontend_hours: float
    total_backend_hours: float
    total_mobile_hours: float
    grand_total_hours: float
    requirements: List[RequirementEstimateGroup]
