from crewai.tools import BaseTool

from typing import List
from pydantic import BaseModel, Field

from delivery_management.tasks.create_routes import ClusteredRoutesOutput
from backup.models.clustered_orders import H3ClusteredOrdersInput
from delivery_management.tools.shared_data import get_shared

class EnrichedLocation(BaseModel):
    location_id: str = Field(..., description="unique id of the delivery location")
    order_id: str = Field(..., description="unique id of the order")
    order_count: int = Field(..., description="total package count")
    total_weight_kg: float = Field(..., description="total weight of the products to be delivered in that location")
    total_volume_m3: float = Field(..., description="total volume of the products to be delivered in that location")
    est_delivery_time_hours: float = Field(..., description="estimated delivery time for all the packages in a particular location")

class EnrichedRoute(BaseModel):
    h3_index: str = Field(..., description="h3 index of the geo location cluster")
    fleet_id: str = Field(..., description="fleet id")
    fleet_type: str = Field(..., description="type of the fleet small, medium and large")
    total_weight_kg: float = Field(..., description="total weight of all the products to be delivered in the route")
    total_volume_m3: float = Field(..., description="total volume of all the products to be delivered in the route")
    total_delivery_time: float = Field(..., description="estimated total delivery time for the route in hours")
    locations: List[EnrichedLocation] = Field(..., description="unique id of the product")

class EnrichedRoutesOutput(BaseModel):
    routes: List[EnrichedRoute] = Field(..., description="unique id of the product")


class EnrichClusteredOrders(BaseTool):

    name: str = "Enrich Orders"
    description: str = "Enrich the H3 index based clustered order to add total weight and volume"

    def enrich_routes(
        self,
        clustered_routes_output: ClusteredRoutesOutput
    ) -> EnrichedRoutesOutput:
        
        clustered_orders_input: H3ClusteredOrdersInput = get_shared("h3_clustered_orders")
        # Create a lookup map for location_id to orders
        # location_map = {locations.location_id: locations for locations in clustered_orders_input.h3_clusters}

        location_map = {
            location.location_id: location
            for cluster in clustered_orders_input.h3_clusters
            for location in cluster.locations
        }

        enriched_routes = []

        for route in clustered_routes_output["routes"]:
            enriched_locations = []
            route_weight = 0.0
            route_volume = 0.0

            for loc_id in route["location_ids"]:
                location_cluster = location_map.get(loc_id)
                if not location_cluster:
                    continue

                location_weight = sum(order.weight for order in location_cluster.orders)
                location_volume = sum(order.volume for order in location_cluster.orders)
                order_id = location_cluster.orders[0].order_id if location_cluster.orders else None

                route_weight += location_weight
                route_volume += location_volume

                enriched_location = EnrichedLocation(
                    location_id=loc_id,
                    order_id=order_id,
                    order_count=len(location_cluster.orders),
                    total_weight_kg=location_weight,
                    total_volume_m3=location_volume,
                    est_delivery_time_hours= round(((location_weight/50) * 15)/60, 2)
                )
                enriched_locations.append(enriched_location)
            
            enriched_route = EnrichedRoute(
                h3_index=route["h3_index"],
                fleet_id=route["fleet_id"],
                fleet_type=route["fleet_type"],
                total_weight_kg=route_weight,
                total_volume_m3=route_volume,
                total_delivery_time=sum(location.est_delivery_time_hours for location in enriched_locations),
                locations=enriched_locations
            )
            enriched_routes.append(enriched_route)

        return EnrichedRoutesOutput(routes=enriched_routes)

    def _run(self, clustered_routes_output: ClusteredRoutesOutput) -> EnrichedRoutesOutput:
        return self.enrich_routes(clustered_routes_output)