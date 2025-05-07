from crewai import Task
# ------------------------
# Pydantic Output Schema
# ------------------------
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from delivery_management.models.optimized_routes import OptimizedRoutes
from delivery_management.tools import fleet
from delivery_management.tools import enrich_clustered_orders, fleet

# --------------------
# Task Factory
# --------------------
def fine_tune_routes_task(agent):
    enrich_clusters_tool = enrich_clustered_orders.EnrichClusteredOrders()
    fleet_tool = fleet.Fleet()
    
    return Task(
        name="OptimiseRoutesWithVolume",
        description=(
            "The weight-optimized routes produced earlier need final optimization for fleet volume constraints. "
            "Use the 'EnrichClusteredOrders' tool to enrich these routes with accurate total volume across all locations. "
            
            "Your goal is to STRICTLY optimize for volume constraints while preserving weight and time optimization. "
            "Follow these rules absolutely:\n"
            "- Use available fleet volume capacity limits from the 'FleetTool'.\n"
            "- Do NOT exceed a fleet's maximum volume capacity under any circumstances\n"
            "- Preserve weight and time constraints from previous optimizations\n\n"
            "Fleet Volume Capacity Evaluation:\n"
            "- Small: 10 cubic_meters capacity\n"
            "- Medium: 20 cubic_meters capacity\n"
            "- Large: 50 cubic_meters capacity\n\n"
            "Optimal Fleet Selection Rules:\n"
            "1. First evaluate ALL possible fleet options that can handle the route's volume\n"
            "2. Consider:\n"
            "   * Fleet utilization efficiency\n"
            "   * Available fleet inventory\n"
            "   * Operational costs\n"
            "3. Prefer:\n"
            "   * Higher utilization (70-90% ideal)\n"
            "   * Lower cost per cubic_meter\n"
            "4. Only split routes when:\n"
            "   * No available fleet can handle the volume\n"
            "   * Significant efficiency gains possible\n"
            "- Assign appropriate fleet considering:\n"
            "  * Volume capacity requirements\n"
            "  * Available fleet count per type\n"
            "  * Weight constraints from previous optimization\n"
            "- Check fleet availability before assignment\n"
            "- Include meaningful explanations with appropriate metrics.\n"
        ),
        expected_output=(
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Large\",\n"
            "      \"locations\": [\n"
            "        {\n"
            "          \"location_id\": \"LOC201\",\n"
            "          \"order_id\": \"ORD2001\",\n"
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}"
        ),
        agent=agent,
        tools=[enrich_clusters_tool, fleet_tool],
        output_json=OptimizedRoutes
    )