from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Location(BaseModel):
    location_id: str = Field(..., description="Location ID to which the orders to be delivered")
    order_id: str = Field(..., description="Order id to be delivered")

class Route(BaseModel):
    h3_index: Optional[str] = Field(..., description="H3 index representing the clustered area")
    fleet_id: str = Field(..., description="Unique identifier for the fleet assigned to the route")
    fleet_type: Literal["Small", "Medium", "Large"] = Field(..., description="Type of fleet used for delivery")
    # total_delivery_time: float = Field(..., description="estimated total delivery time for the route")
    locations: List[Location] = Field(..., description="List of Locations with their corresponding order counts")
    # justification: str = Field(..., description="a justification under every route on why that is planned the way it is planned")

class TimeOptimisedRoutes(BaseModel):
    routes: List[Route] = Field(..., description="List of delivery routes derived from the clustered H3 index groups")