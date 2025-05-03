from typing import List
from pydantic import BaseModel

# ------------------------
# Pydantic Output Schema
# ------------------------
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Route(BaseModel):
    h3_index: Optional[str] = Field(..., description="H3 index representing the clustered area")
    fleet_id: str = Field(..., description="Unique identifier for the fleet assigned to the route")
    fleet_type: Literal["Small", "Medium", "Large"] = Field(..., description="Type of fleet used for delivery")
    total_delivery_time_hours: float = Field(..., description="Total delivery time for the entire route")
    location_ids: List[str] = Field(..., description="List of Location IDs that are mapped to this route")

class ClusteredRoutesOutput(BaseModel):
    routes: List[Route] = Field(..., description="List of delivery routes derived from the clustered H3 index groups")