from crewai import Task
# ------------------------
# Pydantic Output Schema
# ------------------------
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

from delivery_management.tools import enrich_clustered_orders, fleet

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
    # total_weight_kg: float = Field(..., description="a sum of product of quantity and weight of all the packages of all the orders under the route")
    # total_volume_m3: float = Field(..., description="a sum of volume of all the packages of all the orders under the route")
    total_delivery_time: float = Field(..., description="estimated total delivery time for the route")
    locations: List[Locations] = Field(..., description="List of Locations with their corresponding order counts")
    justification: str = Field(..., description="a justification under every route on why that is planned the way it is planned")

class VolumeWeightOptimisedRoutes(BaseModel):
    routes: List[Route] = Field(..., description="List of delivery routes derived from the clustered H3 index groups")


# --------------------
# Task Factory
# --------------------
def fine_tune_routes_task(agent):

    enrich_clusters_tool = enrich_clustered_orders.EnrichClusteredOrders()

    return Task(
        name="OptimiseRoutesWithVolumeAndWeight",
        description=(
            "The H3-clustered routes produced earlier are not yet optimized for fleet capacity constraints (volume and weight). "
            "Use the 'EnrichClusteredOrders' tool to enrich these routes with accurate total weight and volume across all locations. "
            "Fleet capacity limits such as volume and weight can be fetched using fleet_tool: "
            "`capacity.volume`, `capacity.weight`, and their respective units from `capacity.units.volume` and `capacity.units.weight`. "
            "Review the enriched routes and ensure that each one respects the fleet's capacity limits. "
            "Start analyzing the route and try to fit it with the following constraints,"
            " - Try to fit a small fleet to strat with "
            " - If not feasible, split the route to fit as many small fleets as possible"
            " - do not pick a medium until all the small fleets are exhausted"
            " - same applies to large fleet, do not pick a large unless all mediums are exhausted"
            " and the following guidelines,"
            " - start with the total_weight_kg at the route level"
            " - drill down to the location level while splitting the route to multiple fleets"
            "**Your response must be a valid JSON object. Do not wrap it in quotes. And include an meaningful explanations inclusing valid metrics in a field called justification under every route. **"
        ),
        expected_output=(
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Large\",\n"
            # "      \"total_weight_kg\": 2099.1,\n"
            # "      \"total_volume_m3\": 14.808765999999999,\n"
            "        \total_delivery_time\: 3,\n"
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
        tools=[enrich_clusters_tool],
        output_json=VolumeWeightOptimisedRoutes
    )


    # return Task(
    #     name="OptimiseRoutesWithVolumeAndWeight",
    #     description=(
    #         "The H3 clustered orders lag volume and weight optimization. The clusters are not created as per the proper sum of all the weights/volume of orders"
    #         "Use 'EnrichClusteredOrders' tool which refer static data and enrich the H3 clustered order to have total volume and weight across locations under a route" 
    #         "The fleets capacity of volume and weight can be identified from capacity.volume and capacity.weight. Their units from capacity.units.weight and capacity.units.volume"
    #         "Use the EnrichedRoutesOutput and optimise it with volume and weight limitations of the fleets."
    #     ),
    #     expected_output=(
    #         "A JSON object with key 'routes', which is a list of route objects. "
    #         "Your output must be in the below JSON format:"
    #         "{'routes': [{'h3_index':'86a8100c7ffffff', 'fleet_id': 'MH14Y6543', 'fleet_type': 'Small', 'location_ids': ['LOC201', 'LOC202'], "
    #         "'total_weight_kg': 800.0, 'total_volume_m3': 4.2}]}"
    #     ),
    #     agent=agent,
    #     tools=[enrich_clusters_tool],
    #     output_json=VolumeWeightOptimisedRoutes
    # )
