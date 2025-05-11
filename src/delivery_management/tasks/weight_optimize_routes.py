from crewai import Task
from delivery_management.models.optimized_routes import OptimizedRoutes
from delivery_management.tools import fleet, enrich_clustered_orders

def fine_tune_routes_task(agent):
    enrich_clusters_tool = enrich_clustered_orders.EnrichClusteredOrders()
    fleet_tool = fleet.Fleet()
    from delivery_management.tools.shared_data import set_shared
    
    def store_output_callback(output) -> OptimizedRoutes:
        set_shared("weight_optimized_routes", output)
        return output.json_dict
        
    return Task(
        name="OptimiseRoutesWithWeight",
        callback=store_output_callback,
        description=(
            "Optimize routes for weight constraints using fleet capabilities.\n"
            "Key Rules:\n"
            "1. Never exceed fleet weight capacities\n"
            "2. Preserve existing time windows\n"
            "3. Only adjust fleet assignments when necessary\n"
            "Follow these rules absolutely:\n"
            "- Use available fleet weight capacity limits from the 'FleetTool'.\n"
            "- Do NOT exceed a fleet's maximum weight capacity under any circumstances\n"
            "- Preserve time constraints - no route may exceed 8 delivery hours\n\n"
            "Fleet Weight Capacity Evaluation:\n"
            "- Small: 2000kg capacity\n"
            "- Medium: 5000kg capacity\n"
            "- Large: 10000kg capacity\n\n"
            "Optimal Fleet Selection Rules:\n"
            "1. First evaluate ALL possible fleet options that can handle the route's weight\n"
            "2. Consider:\n"
            "   * Fleet utilization efficiency\n"
            "   * Available fleet inventory\n"
            "   * Operational costs\n"
            "3. Prefer:\n"
            "   * Higher utilization (70-90% ideal)\n"
            "   * Lower cost per kg\n"
            "4. Only split routes when:\n"
            "   * No available fleet can handle the weight\n"
            "   * Significant efficiency gains possible\n"
            "- Assign appropriate fleet considering:\n"
            "  * Weight capacity requirements\n"
            "  * Available fleet count per type\n"
            "  * Future volume optimization needs\n"
            "- Check fleet availability before assignment\n"
            "- Volume optimization will happen in next stage - but consider likely volume needs\n"
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
        tools=[enrich_clusters_tool, fleet_tool],
        output_json=OptimizedRoutes
    )
