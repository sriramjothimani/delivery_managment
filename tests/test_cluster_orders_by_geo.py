import json
from pathlib import Path
from delivery_management.tools.cluster_orders import ClusterOrdersByGeoTool  # Replace with actual import

# Test cases for ClusterOrdersByGeoTool

BASE_DIR = Path(__file__).resolve().parent.parent

def test_cluster_order():
    clusterOrdersTool = ClusterOrdersByGeoTool()\
            .with_orders_file(Path(BASE_DIR / "src/delivery_management/data/orders.json"))\
            .with_geolocations_file(Path(BASE_DIR / "src/delivery_management/data/geolocations.json"))\
            .with_static_ref_file(Path(BASE_DIR / "src/delivery_management/data/static_reference_data.json"))\
            .with_inventory_file(Path(BASE_DIR / "src/delivery_management/data/inventory.json"))
    result = clusterOrdersTool.run()
    json = result.model_dump()
    print(json)
    
