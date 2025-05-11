from crewai.tools import BaseTool
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from delivery_management.tools.shared_data import get_shared

class EnrichedOrder(BaseModel):
    order_id: str = Field(..., description="Unique order identifier")
    product: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product display name")
    quantity: int = Field(..., description="Quantity ordered")
    weight: float = Field(..., description="Total weight in kg")
    volume: float = Field(..., description="Total volume in cubic meters")
    category: str = Field(..., description="Product category")
    is_hazardous: bool = Field(..., description="Hazardous material flag")
    is_perishable: bool = Field(..., description="Perishable goods flag")

class EnrichedLocation(BaseModel):
    location_id: str = Field(..., description="Location identifier")
    latitude: float = Field(..., description="GPS latitude")
    longitude: float = Field(..., description="GPS longitude")
    orders: List[EnrichedOrder] = Field(..., description="Orders at this location")

class EnrichedRoute(BaseModel):
    h3_index: str = Field(..., description="H3 geospatial index")
    fleet_id: str = Field(..., description="Assigned vehicle ID")
    fleet_type: str = Field(..., description="Vehicle size class")
    total_weight: float = Field(..., description="Route total weight")
    total_volume: float = Field(..., description="Route total volume")
    estimated_time: float = Field(..., description="Estimated delivery time in hours")
    locations: List[EnrichedLocation] = Field(..., description="Delivery locations")

class FinalOutputEnricher(BaseTool):
    name: str = "Final Output Enricher"
    description: str = "Enhances final delivery routes with detailed order information"

    def _run(self, routes: Dict) -> Dict:
        """Enrich final routes output with detailed order data"""
        clustered_orders = get_shared("h3_clustered_orders")
        enriched_routes = []
        
        # Convert clustered_orders to dict if needed
        if hasattr(clustered_orders, 'dict'):
            clustered_orders = clustered_orders.dict()
            
        for route in routes["routes"]:
            cluster = next(
                (c for c in clustered_orders.get("h3_clusters", [])
                 if c.get("h3_index") == route["h3_index"]),
                None
            )
            if not cluster:
                continue
                
            enriched_locations = []
            total_weight = 0
            total_volume = 0
            total_time = 0
            
            for loc in route["locations"]:
                cluster_loc = next(
                    (cl for cl in cluster["locations"] 
                    if cl["location_id"] == loc["location_id"]),
                    None
                )
                if not cluster_loc:
                    continue
                    
                enriched_orders = []
                for order in cluster_loc["orders"]:
                    if order["order_id"] == loc["order_id"]:
                        enriched_orders.append(EnrichedOrder(
                            order_id=order["order_id"],
                            product=order["product"],
                            product_name=order["metadata"]["name"],
                            quantity=order["quantity"],
                            weight=order["weight"],
                            volume=order["volume"],
                            category=order["metadata"]["category"],
                            is_hazardous=order["metadata"]["is_hazardous"],
                            is_perishable=order["metadata"]["is_perishable"]
                        ))
                        total_weight += order["weight"]
                        total_volume += order["volume"]
                        total_time += cluster_loc["est_delivery_time_hours"]
                
                enriched_locations.append(EnrichedLocation(
                    location_id=cluster_loc["location_id"],
                    latitude=cluster_loc["location"]["latitude"],
                    longitude=cluster_loc["location"]["longitude"],
                    orders=enriched_orders
                ))
            
            enriched_routes.append(EnrichedRoute(
                h3_index=route["h3_index"],
                fleet_id=route["fleet_id"],
                fleet_type=route["fleet_type"],
                locations=enriched_locations,
                total_weight=total_weight,
                total_volume=total_volume,
                estimated_time=total_time
            ))
        
        return {"enriched_routes": enriched_routes}