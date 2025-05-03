from crewai import Task
from typing import List
from pydantic import BaseModel

# ------------------------
# Pydantic Output Schema
# ------------------------
from delivery_management.models.greedy_clusters import ClusteredRoutesOutput

# --------------------
# Task Factory
# --------------------
def create_cluster_orders_into_routes_task(agent):

    return Task(
        name="ClusterOrdersIntoRoutes",
        description=(
            "You are given a set of validated delivery orders grouped by H3 index using the 'ClusterOrdersByGeoTool'. "
            "Each H3 cluster contains one or more delivery locations, and each location has one or more orders.\n\n"

            "Your primary objective is to create delivery routes such that the total estimated delivery time for each route "
            "does not exceed 8 operational hours. Delivery time for each location is provided.\n\n"

            "Steps:\n"
            "- Within each H3 cluster, group locations into one or more routes, ensuring each group's cumulative delivery time stays within 8 hours.\n"
            "- Try to avoid splitting locations across multiple routes unless necessary.\n"
            "- Preserve H3 clustering: do not mix locations from different H3 indexes.\n\n"

            "Fleet Assignment:\n"
            "- After forming delivery-time-respecting routes, assign a fleet for each route.\n"
            "- Use the Fleet Tool to fetch available fleet types, their weight and volume capacity, and their availability counts.\n"
            "- Select the smallest possible fleet that can fully accommodate the total weight and volume of the route.\n"
            "- If a smaller fleet is unavailable or inadequate, escalate to the next bigger fleet size.\n"
            "- Document fallback decisions with clear justification.\n"
            "- Do not assume infinite availability for any fleet type.\n\n"

            "Constraints:\n"
            "- MUST include all orders marked as 'priority': true.\n"
            "- Each route must include: h3_index, fleet_id, fleet_type, total_delivery_time_hours, location_ids.\n"
            "- One route must not contain locations from multiple H3 clusters.\n\n"

            "**Return a valid compact JSON object without wrapping it as a string. Include a meaningful explanations with appropriate metrics.**"
        ),
        expected_output=(
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Small\",\n"
            "      \"total_delivery_time_hours\": 7.8,\n"
            "      \"location_ids\": [\"LOC201\", \"LOC202\"]\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        agent=agent,
        output_json=ClusteredRoutesOutput
    )

