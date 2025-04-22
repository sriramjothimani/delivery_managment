from pathlib import Path
from crewai import Task

# ------------------------
# Pydantic Output Schema
# ------------------------
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from delivery_management.tools import time_constraints

class Locations(BaseModel):
    location_id: str = Field(..., description="Location ID to which the orders to be delivered")
    order_id: str = Field(..., description="Order id to be delivered")
    # order_count: int = Field(..., description="count of packages")
    est_delivery_time_hours: float = Field(..., description="estimated delivery time for all the packages in a particular location")

class Route(BaseModel):
    h3_index: Optional[str] = Field(..., description="H3 index representing the clustered area")
    fleet_id: str = Field(..., description="Unique identifier for the fleet assigned to the route")
    fleet_type: Literal["Small", "Medium", "Large"] = Field(..., description="Type of fleet used for delivery")
    # total_package_count: int = Field(..., description="total package count of all order under the route")
    locations: List[Locations] = Field(..., description="List of Locations with their corresponding order counts")
    justification: str = Field(..., description="a justification under every route on why that is planned the way it is planned")

class TimeOptimisedRoutes(BaseModel):
    routes: List[Route] = Field(..., description="List of delivery routes derived from the clustered H3 index groups")


# --------------------
# Task Factory
# --------------------
def time_optimize_routes_task(agent):

    BASE_DIR = Path(__file__).resolve().parent.parent

    time_constraints_tool = time_constraints.TimeConstraints()\
        .with_data_file(Path(BASE_DIR / "data/time_constraints.json"))


    return Task(
        name="OptimizeRoutesWithTimeConstraints",
        description=(
            "You are given a set of delivery routes with assigned fleets and location-level delivery metadata. "
            "The Greedy fleet manager agent is expected to optimize the routes only with weight, this is not fully optimized"
            "Your task is to validate and optimize those routes so that they comply with real-world operational and time-based constraints.\n\n"
            "Constraints:\n"
            "- Operational window is from 08:00 AM to 05:00 PM (9 hours).\n"
            "- A route exceeding total_delivery_time 9 hours must be split across multiple fleets, while respecting weight and volume limits.\n"
            "- Drivers may drive continuously for a maximum of 4 hours, followed by a 45-minute mandatory break.\n"
            "- Travel time is influenced by distance (typically 3–6 km between locations) and fleet speed.\n"
            "- Peak traffic periods (07:30–09:00, 16:30–18:30) increase travel and delivery time by a defined impact factor.\n\n"
            # "- Fleets IDs cannot be picked randomly, we should refer the list of fleets from the available_fleets of Fleet tool"
            "Guidelines:\n"
            "- When there is a need for split, you should use cummulative est_delivery_time_hours under every location and make sure they are less than 9 hours.\n"
            "- while splitting the route follow the below guidelies to pick an appropriate fleet"
            "   - Try to fit a small fleet to strat with "
            "   - If not feasible, split the route to fit as many small fleets as possible"
            "   - do not pick a medium until all the small fleets are exhausted"
            "   - same applies to large fleet, do not pick a large unless all mediums are exhausted"
            "- You must not make assumptions like all deliveries happen during peak hours or all packages being under a certain size.\n"
            "- Avoid exceeding total route time, weight, volume, or continuous driving limits.\n\n"
            "Output must be a valid JSON object"
            "Each route must include meaningful explanations inclusing valid metrics in 'justification' field explaining why the plan is valid or why it was split."   
        ),
        expected_output=(
            "A JSON object with the key 'routes', like below:\n"
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Large\",\n"
            # "      \"total_weight_kg\": 2099.1,\n"
            # "      \"total_volume_m3\": 14.808765999999999,\n"
            "      \"locations\": [\n"
            "        {\n"
            "          \"location_id\": \"LOC201\",\n"
            "          \"order_id\": \"ORD2001\",\n"
            # "          \"order_count\": 3,\n"
            "          \"est_delivery_time_hours\": 4\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        agent=agent,
        tools=[time_constraints_tool],
        output_json=TimeOptimisedRoutes
    )

