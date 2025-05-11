from crewai import Task
from typing import List
from pathlib import Path
from pydantic import BaseModel
from delivery_management.tools import (
    cluster_orders,
    fleet
)
# ------------------------
# Pydantic Output Schema
# ------------------------
from delivery_management.models.greedy_routes import GreedyRoutes

# --------------------
# Task Factory
# --------------------
def create_cluster_orders_into_routes_task(agent):
    BASE_DIR = Path(__file__).resolve().parent.parent

    cluster_orders_tool = cluster_orders.ClusterOrdersByGeoTool()\
        .with_orders_file(Path(BASE_DIR / "data/orders.json"))\
        .with_geolocations_file(Path(BASE_DIR / "data/geolocations.json"))\
        .with_static_ref_file(Path(BASE_DIR / "data/static_reference_data.json"))\
        .with_inventory_file(Path(BASE_DIR / "data/inventory.json"))
        
    fleet_tool = fleet.Fleet()

    from delivery_management.tools.shared_data import set_shared
    
    def store_output_callback(output: GreedyRoutes):
        # Store both the raw output and parsed model
        set_shared("h3_clustered_orders", output.model_dump())
        return output.model_dump()
        
    return Task(
        name="ClusterOrdersIntoRoutes",
        callback=store_output_callback,
        description=(
            "You are given a set of validated delivery orders grouped by H3 index using the 'ClusterOrdersByGeoTool'. "
            "Each H3 cluster contains one or more delivery locations, and each location has one or more orders.\n\n"

            "Your objective is to create initial delivery routes within each H3 cluster by organizing locations such that "
            "the **total estimated delivery time per route does not exceed 8 operational hours**.\n\n"

            "Guidelines:\n"
            "- For each H3 cluster, group delivery locations into one or more routes.\n"
            "- Ensure that each route's total delivery time stays within the 8-hour limit.\n"
            "- Minimize unnecessary splitting of locations across multiple routes, but allow it when delivery time constraints require.\n"
            "- Do NOT mix locations from different H3 clusters in the same route.\n"
            "- Do NOT perform fleet selection or weight/volume optimization in this step.\n\n"

            "**Output**:\n"
            "Return a JSON object containing:\n"
            "- h3_index\n"
            "- a list of location objects (locations) included in the route\n\n"

            "Fleet assignment and load balancing will be handled in later stages.\n"
            "**Return a valid compact JSON object. Do not wrap it in quotes.**"
        ),
        expected_output=(
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"locations\": [\n"
            "        {\n"
            "          \"location_id\": \"LOC201\",\n"
            "          \"order_id\": \"ORD2001\"\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        agent=agent,
        tools=[cluster_orders_tool, fleet_tool],
        output_json=GreedyRoutes
    )

