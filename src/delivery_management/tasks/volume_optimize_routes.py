from crewai import Task
from pathlib import Path
from delivery_management.models.optimized_routes import OptimizedRoutes
from delivery_management.tools import fleet, time_constraints, enrich_clustered_orders

def fine_tune_routes_task(agent):
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    enrich_clusters_tool = enrich_clustered_orders.EnrichClusteredOrders()
    time_constraints_tool = time_constraints.TimeConstraints()\
        .with_data_file(Path(BASE_DIR / "data/time_constraints.json"))
    fleet_tool = fleet.Fleet()
    
    from delivery_management.tools.shared_data import set_shared
    
    def store_output_callback(output) -> OptimizedRoutes:
        set_shared("volume_optimized_routes", output)
        return output.model_dump()
        
    return Task(
        name="OptimiseRoutesWithVolume",
        callback=store_output_callback,
        description=(
            "Final optimization for volume while preserving all time and weight decisions.\n"
            "Key Rules:\n"
            "1. Validate time and weight constraints first\n"
            "2. Only adjust packing configurations\n"
            "3. Never violate previous optimizations\n"
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
            "      \"justification\": \"bla bla blah\",\n"
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
        tools=[enrich_clusters_tool, fleet_tool, time_constraints_tool],
        output_json=OptimizedRoutes
    )