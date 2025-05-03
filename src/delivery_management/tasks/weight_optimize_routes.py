from crewai import Task
# ------------------------
# Pydantic Output Schema
# ------------------------
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class Locations(BaseModel):
    location_id: str = Field(..., description="Location ID to which the orders to be delivered")
    order_id: str = Field(..., description="Order id to be delivered")
    order_count: int = Field(..., description="count of packages")
    # total_weight_kg: float = Field(..., description="total weight of the orders to be delivered in that location") 
    # total_volume_m3: float = Field(..., description="total volume of the orders to be delivered in that location")
    est_delivery_time_hours: float = Field(..., description="estimated delivery time for all the packages in a particular location")

class Route(BaseModel):
    h3_index: Optional[str] = Field(..., description="H3 index representing the clustered area")
    fleet_id: str = Field(..., description="Unique identifier for the fleet assigned to the route")
    fleet_type: Literal["Small", "Medium", "Large"] = Field(..., description="Type of fleet used for delivery")
    total_weight_kg: float = Field(..., description="a sum of product of quantity and weight of all the packages of all the orders under the route")
    total_volume_m3: float = Field(..., description="a sum of volume of all the packages of all the orders under the route")
    total_delivery_time: float = Field(..., description="estimated total delivery time for the route")
    locations: List[Locations] = Field(..., description="List of Locations with their corresponding order counts")
    justification: str = Field(..., description="a justification under every route on why that is planned the way it is planned")

class VolumeWeightOptimisedRoutes(BaseModel):
    routes: List[Route] = Field(..., description="List of delivery routes derived from the clustered H3 index groups")


# --------------------
# Task Factory
# --------------------
def fine_tune_routes_task(agent):

    return Task(
        name="OptimiseRoutesWithVolumeAndWeight",
        description=(
            "The time-optimized routes produced earlier need final optimization for fleet capacity constraints (volume and weight). "
            "Use the 'EnrichClusteredOrders' tool to enrich these routes with accurate total weight and volume across all locations. "

            "Your goal is to optimize weight distribution while preserving time constraints from previous optimization. "
            "Follow these rules strictly:\n"
            "- Use available fleet capacity limits from the 'FleetTool'.\n"
            "- Do NOT exceed a fleet's maximum weight or volume capacity.\n"
            "- Preserve time constraints - no route may exceed 8 delivery hours.\n"
            "   - Small - max weight 2000kg and max volume 10 cubic_meters \n"
            "   - Medium - max weight 5000kg and max volume 25 cubic_meters \n"
            "   - Large - max weight 10000kg and max volume 50 cubic_meters \n"
            "- Try to reduce significant under-utilization while maintaining time efficiency.\n"
            "- You MAY redistribute locations between routes **within the same H3 index only**.\n"
            "- Do NOT drop or ignore any location with valid orders.\n"
            "- Priority orders (priority: true) must always be preserved in a valid route.\n"
            "- Orders with inventory_issue: true must remain excluded.\n\n"

            "If no improvement is possible for a route, retain it as is.\n\n"
            "**Your response must be a valid JSON object. Do not wrap it in quotes. Include a meaningful explanations with appropriate metrics. **" 
        ),
        expected_output=(
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Large\",\n"
            "      \"total_weight_kg\": 2099.1,\n"
            "      \"total_volume_m3\": 14.808765999999999,\n"
            "      \"total_delivery_time\": 3,\n"
            "      \"locations\": [\n"
            "        {\n"
            "          \"location_id\": \"LOC201\",\n"
            "          \"order_id\": \"ORD2001\",\n"
            "          \"order_count\": 3,\n"
            "          \"est_delivery_time_hours\": 3\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        agent=agent,
        output_json=VolumeWeightOptimisedRoutes
    )
