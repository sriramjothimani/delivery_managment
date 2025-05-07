from pathlib import Path
from crewai import Task

# ------------------------
# Pydantic Output Schema
# ------------------------
from delivery_management.models.optimized_routes import OptimizedRoutes
from delivery_management.tools import time_constraints, enrich_clustered_orders, fleet

# --------------------
# Task Factory
# --------------------
def time_optimize_routes_task(agent):

    BASE_DIR = Path(__file__).resolve().parent.parent
    enrich_clusters_tool = enrich_clustered_orders.EnrichClusteredOrders()

    time_constraints_tool = time_constraints.TimeConstraints()\
        .with_data_file(Path(BASE_DIR / "data/time_constraints.json"))
    
    fleet_tool = fleet.Fleet()
    return Task(
        name="OptimizeRoutesWithTimeConstraints",
        description=(
            "You are given initial delivery routes clustered by H3 index but not yet optimized for time or weight constraints.\n\n"
            "Use the 'EnrichClusteredOrders' tool to enrich these routes with accurate total weight and volume across all locations. "

            "Your task: First optimize these routes for time constraints:\n"
            "- Delivery window: 08:00 AM–05:00 PM (9 hours).\n"
            "- Maximum total delivery time per route: **8 hours** (excluding breaks and travel overhead).\n"
            "- Drivers may drive 4 hours maximum, then must take a 45-minute break.\n"
            "- Peak hours (07:30–09:00, 16:30–18:30) increase travel time 1.5 and 1.7 times.\n\n"

            "Splitting Rules:\n"
            "- If total delivery time > 8 hours, **split** into multiple sub-routes.\n"
            "- Split by grouping locations based on `est_delivery_time_hours`.\n"
            "- **Only group locations from the same H3 index**.\n"
            "- No mixing locations across different H3 indexes.\n"
            "- No dropping locations.\n\n"

            "Fleet Assignment Rules (Time Optimization Focus):\n"
            "- Prefer smaller fleets for better time efficiency in most cases\n"
            "- Consider that larger fleets may have longer loading/unloading times\n"
            "- Use only available fleet IDs from the Fleet tool\n"
            "- Reserve Large fleets only for:\n"
            "  - Routes with many locations where consolidation saves significant time\n"
            "  - Areas with known traffic bottlenecks\n"
            "- Never assign a larger fleet unless it demonstrably improves time efficiency\n\n"
            
            "Important:\n"
            "- Fleet size affects both capacity and time efficiency\n"
            "- Delivery time limits (max 8 hours) apply to all fleets equally.\n"
            "- Larger fleets cannot deliver beyond the 8-hour window.\n\n"            

            "Strict Rules:\n"
            "- No assumptions about package size, weight, or traffic uniformity.\n"
            "- No route may exceed 8 delivery hours, weight, volume, or driving time limits.\n\n"

            "**Return a properly structured TimeOptimisedRoutes object that includes all required fields for enrichment. Include a meaningful explanations with appropriate metrics.**"
        ),

        expected_output=(
            "A JSON object with the key 'routes', like below:\n"
            "{\n"
            "  \"routes\": [\n"
            "    {\n"
            "      \"h3_index\": \"86a8100c7ffffff\",\n"
            "      \"fleet_id\": \"MH14Y6543\",\n"
            "      \"fleet_type\": \"Large\",\n"
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
        tools=[enrich_clusters_tool, time_constraints_tool, fleet_tool],
        output_json=OptimizedRoutes
    )

