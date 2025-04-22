from crewai import Task
from typing import List
from pydantic import BaseModel

# ------------------------
# Pydantic Output Schema
# ------------------------
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# class FleetInfo(BaseModel):
#     fleet_id: str = Field(..., description="Unique identifier for the fleet assigned to the route")
#     fleet_type: Literal["Small", "Medium", "Large"] = Field(..., description="Type of fleet used for delivery")

# class RoutedOrder(BaseModel):
#     order_id: str = Field(..., description="Unique identifier of the order")
#     sku: str = Field(..., description="Stock keeping unit of the product")
#     quantity: int = Field(..., description="Quantity of the product")
#     weight_kg: float = Field(..., description="Weight of the product in kilograms")
#     volume_m3: float = Field(..., description="Volume of the product in cubic meters")
#     location_id: str = Field(..., description="Location ID to which the order is to be delivered")

# class Route(BaseModel):
#     route_id: str = Field(..., description="Unique ID for the route, can be the H3 index")
#     h3_index: Optional[str] = Field(..., description="H3 index representing the clustered area")
#     fleet: FleetInfo = Field(..., description="Fleet assigned to this route")
#     total_weight_kg: float = Field(..., description="a sum of product of quantity and weight of all the packages of all the orders under the route")
#     total_volume_m3: float = Field(..., description="a sum of volume of all the packages of all the orders under the route")
#     orders: List[RoutedOrder] = Field(..., description="List of orders assigned to this route")

class Route(BaseModel):
    h3_index: Optional[str] = Field(..., description="H3 index representing the clustered area")
    fleet_id: str = Field(..., description="Unique identifier for the fleet assigned to the route")
    fleet_type: Literal["Small", "Medium", "Large"] = Field(..., description="Type of fleet used for delivery")
    location_ids: List[str] = Field(..., description="List of Location IDs that are mapped to this route")

class ClusteredRoutesOutput(BaseModel):
    routes: List[Route] = Field(..., description="List of delivery routes derived from the clustered H3 index groups")

# --------------------
# Task Factory
# --------------------
def create_cluster_orders_into_routes_task(agent):

    return Task(
        name="ClusterOrdersIntoRoutes",
        description=(
            "Use the 'ClusterOrdersByGeoTool' to group validated orders by H3 index. "
            "Use the Fleet tool to retrieve available fleet types and their capacity (weight and volume). "
            "Create optimized delivery routes such that the total weight and volume of all orders in each route fits within the assigned fleet’s capacity. "
            "If a cluster exceeds the capacity of one vehicle, you may split it into multiple routes. Choose appropriate combinations of fleet types (e.g., Small + Large) to optimize utilization. "
            "Exclude any orders listed in 'inventory_issues'. "
            "Ensure each route includes: the H3 index, assigned fleet ID, fleet type, list of location IDs in the route, total weight in kg, and total volume in cubic meters. "
            "**Return a valid JSON object. Do not wrap it as a string. Do not explain the output. Just return the JSON.**"
        ),
        expected_output=(
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Small\",\n"
            "      \"location_ids\": [\"LOC201\", \"LOC202\"]\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        agent=agent,
        output_json=ClusteredRoutesOutput
    )


    # return Task(
    #     name="ClusterOrdersIntoRoutes",
    #     description=(
    #         "Use the 'ClusterOrdersByGeoTool' to get order groups clustered by H3 index. Use the Fleet tool to get the fleet details"
    #         "Each route should balance total weight and volume to fit within a single delivery truck. " 
    #         "Note, a cluster of locations sometimes mapped to a single fleet isn't efficient as the total weight or volume might out number its capacity. "
    #         "In that case we might need another fleet, but we should make some thoughtful decisions that a large truck and a small truck should be chosen."
    #         "Make sure we ignore the orders that fall into inventory_issues"
    #     ),
    #     expected_output=(
    #         "A JSON object with key 'routes', which is a list of route objects. "
    #         "Your output must be in the below JSON format:"
    #         "{'routes': [{'h3_index':'86a8100c7ffffff', 'fleet_id': 'MH14Y6543', 'fleet_type': 'Small', 'location_ids': ['LOC201', 'LOC202'], "
    #         "'total_weight_kg': 800.0, 'total_volume_m3': 4.2}]}"
    #     ),
    #     agent=agent,
    #     output_json=ClusteredRoutesOutput
    # )

