import json
import h3
from typing import Any, Type
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, PrivateAttr
from delivery_management.tools.shared_data import set_shared

from typing import List, Optional
from pydantic import BaseModel, Field

class LocationMeta(BaseModel):
    location_id: str = Field(..., description="Location ID of geo location")
    latitude: float = Field(..., description="latitude of geo location")
    longitude: float = Field(..., description="longitude of geo location")
    altitude: float = Field(..., description="altitude of geo location")
    distance_from_warehouse: float = Field(..., description="distance from warehouse to the geo location")

class SKUMeta(BaseModel):
    name: str = Field(..., description="name of the product")
    category: str = Field(..., description="category of the product")
    is_hazardous: bool = Field(..., description="is the product hazardous")
    is_perishable: bool = Field(..., description="is the product perishable")

class ClusteredOrder(BaseModel):
    h3_index: Optional[str] = Field(None, description="h3 index of the cluster")
    order_id: str = Field(..., description="unique id of the order")
    weight: float = Field(..., description="weight of the order")
    volume: float = Field(..., description="volume of the order")
    product: str = Field(..., description="name of the product")
    quantity: int = Field(..., description="quantity of the product")
    metadata: Optional[SKUMeta] = Field(..., description="metadata of the product")

class LocationCluster(BaseModel):
    location_id: str = Field(..., description="unique id of the location")
    location: Optional[LocationMeta] = Field(..., description="location metadata")
    total_weight: float = Field(...,description="sum of weights of all the orders in the cluster")
    total_volume: float = Field(...,description="sum of volumes of all the orders in the cluster")
    est_delivery_time_hours: float = Field(...,description="estimated delivery time for the location")
    orders: List[ClusteredOrder] = Field(..., description="list of clustered orders")

class ProductSummary(BaseModel):
    product: str = Field(..., description="unique id of the product")
    total_quantity: int = Field(..., description="total quantity of the product")
    metadata: Optional[SKUMeta] = Field(..., description="product metadata")

class PriorityOrder(BaseModel):
    order_id: str = Field(..., description="unique id of the order")
    location_id: str = Field(..., description="location id")
    priority: str = Field(..., description="priority of the order")
    product: str = Field(..., description="product id of the order")
    quantity: int = Field(..., description="quantitiy of the product under the order")
    metadata: Optional[SKUMeta] = Field(..., description="product metadata")

class WeightVolumeSummary(BaseModel):
    total_weight_kg: float = Field(..., description="total weight of the products in kg for a location")
    total_volume_cm3: float = Field(..., description="total volume of the products in cm3 for a location")
    location_id: Optional[str] = Field(..., description="unique id of the location")  

class H3LocationCluster(BaseModel):
    h3_index: str = Field(..., description="H3 index representing the geographic cluster")
    locations: List[LocationCluster] = Field(..., description="list of locations grouped under the H3 index")

class ClusteredOrdersInput(BaseModel):
    locations: List[LocationCluster] = Field(..., description="unique id of the location")
    priority_orders: List[PriorityOrder] = Field(..., description="priority orders list")
    h3_clusters: Optional[List[H3LocationCluster]] = Field(..., description="Geo clustered locations using H3 index")

class H3ClusteredOrdersInput(BaseModel):
    priority_orders: List[PriorityOrder] = Field(..., description="priority orders list")
    h3_clusters: Optional[List[H3LocationCluster]] = Field(..., description="Geo clustered locations using H3 index")

class ClusterOrdersByGeoTool(BaseTool):

    name: str = "Cluster Orders by H3 Index"
    description: str = "Clusters input orders by H3 index based on location proximity (6-7 resolution of H3). Returns a dictionary with h3_index, associated orders, total weight, volume, and location IDs. This output is needed by FleetManagerAgent to create optimized routes"

    _orders_path: str = PrivateAttr(default=None)
    _geolocations_path: str = PrivateAttr(default=None)
    _static_ref_path: str = PrivateAttr(default=None)
    _inventory_path: str = PrivateAttr(default=None)
    _orders: list = PrivateAttr(default_factory=list)
    _geolocations: dict = PrivateAttr(default_factory=dict)
    _static_ref: dict = PrivateAttr(default_factory=dict)
    _inventory: dict = PrivateAttr(default_factory=dict)
    
    # Builder methods
    def with_orders_file(self, path: Path):
        self._orders_path = path
        return self

    def with_geolocations_file(self, path: Path):
        self._geolocations_path = path
        return self

    def with_static_ref_file(self, path: Path):
        self._static_ref_path = path
        return self
    
    def with_inventory_file(self, path: Path):
        self._inventory_path = path
        return self

    def load_json_data(self):
        with open(self._orders_path, 'r') as f:
            self._orders = json.load(f)['orders']

        with open(self._geolocations_path, 'r') as f:
            self._geolocations = json.load(f)

        with open(self._static_ref_path, 'r') as f:
            self._static_ref = json.load(f)

        with open(self._inventory_path, 'r') as f:
            inventory_data = json.load(f)
            self._inventory = {
                item["sku"]: item["available_quantity"]
                for item in inventory_data.get("inventory", [])
            }            

    @staticmethod
    def build_location_map(geolocations: dict) -> dict:
        return {
            loc["id"]: {
                "location_id": loc["id"],
                "latitude": loc["latitude"],
                "longitude": loc["longitude"],
                "altitude": loc["altitude"],
                "distance_from_warehouse": loc["distance_from_warehouse"]
            }
            for loc in geolocations.get("delivery_locations", [])
        }

    @staticmethod
    def flatten_sku_map(sku_map: dict) -> dict:
        return {
            sku_id: data
            for category_map in sku_map.values()
            for sku_id, data in category_map.items()
        }

    def cluster(self) -> ClusteredOrdersInput:
        location_map = self.build_location_map(self._geolocations)
        sku_map_flat = self.flatten_sku_map(self._static_ref.get("sku_map", {}))

        location_clusters = defaultdict(list)
        product_counter = defaultdict(int)
        weight_volume_tracker = defaultdict(lambda: {"weight": 0.0, "volume": 0.0})
        priority_orders = []
        raw_order_index = defaultdict(list)  # For tracking which order needs what SKUs

        for order in self._orders:
            order_id = order.get("order_id")
            location_id = order.get("location_id")
            priority = order.get("priority")
            packages = order.get("packages", [])

            if not packages:
                continue

            for package in packages:
                sku = package["sku"]
                quantity = package["quantity"]
                weight = package.get("weight_kg", 0) * quantity
                dimensions = package.get("dimensions_m", {})
                metadata = SKUMeta(**sku_map_flat[sku]) if sku in sku_map_flat else None
                volume = (
                    (dimensions["l"] * dimensions["w"] * dimensions["h"])
                    if all(k in dimensions for k in ["l", "w", "h"]) else 0.0
                ) * quantity

                location_clusters[location_id].append(ClusteredOrder(
                    order_id=order_id,
                    weight=weight,
                    volume=volume,
                    product=sku,
                    quantity=quantity,
                    metadata=metadata
                ))

                product_counter[sku] += quantity
                raw_order_index[sku].append((order_id, location_id, quantity))

                if priority == "high":
                    priority_orders.append(PriorityOrder(
                        order_id=order_id,
                        location_id=location_id,
                        priority=priority,
                        product=sku,
                        quantity=quantity,
                        metadata=metadata
                    ))

                weight_volume_tracker[location_id]["weight"] += weight * quantity
                weight_volume_tracker[location_id]["volume"] += volume * quantity
                weight_volume_tracker["__total__"]["weight"] += weight * quantity
                weight_volume_tracker["__total__"]["volume"] += volume * quantity

        # 🧾 Final outputs
        return ClusteredOrdersInput(
            h3_clusters=None,
            locations=self._build_location_clusters(location_clusters, location_map),
            priority_orders=priority_orders
        )

    def _build_location_clusters(self, location_clusters, location_map) -> List[LocationCluster]:
        return [
            LocationCluster(
                location_id=loc_id,
                location=LocationMeta(**location_map[loc_id]) if loc_id in location_map else None,
                orders=orders,
                total_weight=(total_weight := sum(order.weight for order in orders)),
                total_volume=sum(order.volume for order in orders),
                est_delivery_time_hours=round(((total_weight / 50) * 15) / 60, 2)
            )
            for loc_id, orders in location_clusters.items()
        ]

    def _build_product_summary(self, product_counter, sku_map_flat) -> List[ProductSummary]:
        return [
            ProductSummary(
                product=sku,
                total_quantity=qty,
                metadata=SKUMeta(**sku_map_flat[sku]) if sku in sku_map_flat else None
            )
            for sku, qty in product_counter.items()
        ]

    def _build_weight_volume_summary(self, weight_volume_tracker) -> List[WeightVolumeSummary]:
        return [
            WeightVolumeSummary(
                location_id='TOTAL' if loc_id == "__total__" else loc_id,
                total_weight_kg=round(data["weight"], 2),
                total_volume_cm3=round(data["volume"], 2)
            )
            for loc_id, data in weight_volume_tracker.items()
        ]

    def _apply_h3_geo_clustering(self, clustered_orders_input: ClusteredOrdersInput, resolution: int) -> H3ClusteredOrdersInput:
        """
        Apply H3 clustering on the location data in the ClusteredOrdersInput.
        This function now groups locations by H3 index and associates orders with these clusters.

        :param clustered_orders_input: The input data with geo-location clustered orders.
        :param resolution: The resolution level for H3 clustering (e.g., 7).
        :return: The same data with an H3 index applied to each location cluster.
        """
        
        # Group the orders by location_id
        location_clusters = clustered_orders_input.locations
        h3_clustered_locations = defaultdict(lambda: {"locations": [], "orders": []})

        # Loop through each location cluster and assign orders to their respective H3 index
        for location_cluster in location_clusters:
            location_id = location_cluster.location_id
            location_meta = location_cluster.location

            # Apply H3 geo-clustering based on latitude and longitude
            h3_index = h3.latlng_to_cell(location_meta.latitude, location_meta.longitude, resolution)

            # Add the location and its orders to the appropriate H3 cluster
            h3_clustered_locations[h3_index]["locations"].append(location_cluster)

            # Assign orders based on location_id to this h3_index
            for order in location_cluster.orders:
                order.h3_index = h3_index  # Set the H3 index as the new location identifier
                h3_clustered_locations[h3_index]["orders"].append(order)

        # Convert the defaultdict to a list of H3LocationCluster
        h3_location_clusters = [
            H3LocationCluster(
                h3_index=h3_index,
                locations=values["locations"],
            )
            for h3_index, values in h3_clustered_locations.items()
        ]

        # Return the updated clustered orders input with H3 clustering applied
        return H3ClusteredOrdersInput(
            # product_summary=clustered_orders_input.product_summary,
            priority_orders=clustered_orders_input.priority_orders,
            # weight_volume_summary=clustered_orders_input.weight_volume_summary,
            # inventory_issues=clustered_orders_input.inventory_issues,
            h3_clusters=h3_location_clusters
        )

    def _run(self):
        self.load_json_data()
        clusteredOrders = self.cluster()
        h3_clustered_orders = self._apply_h3_geo_clustering(clusteredOrders, 6)
        set_shared("h3_clustered_orders", h3_clustered_orders)
        return h3_clustered_orders
