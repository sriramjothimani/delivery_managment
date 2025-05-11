from crewai.tools import BaseTool
from typing import Dict, List
from pydantic import BaseModel, Field
from delivery_management.tools.shared_data import get_shared, set_shared

class OptimizationData(BaseModel):
    stage: str = Field(..., description="Optimization stage name")
    fleet_distribution: Dict = Field(..., description="Fleet type counts")
    metrics: Dict = Field(..., description="Performance metrics")

class OptimizationCollectorTool(BaseTool):
    name: str = "OptimizationCollector"
    description: str = "Collects and processes optimization outputs from all stages"

    def _run(self) -> List[OptimizationData]:
        """Collect and process all optimization stage outputs"""
        stages = [
            ("Initial Clustering", "h3_clustered_orders"),
            ("Time Optimization", "time_optimized_routes"),
            ("Weight Optimization", "weight_optimized_routes"),
            ("Volume Optimization", "volume_optimized_routes")
        ]

        results = []
        for name, key in stages:
            data = get_shared(key)
            print(f"\nDEBUG: Data for {name} ({key}):")  # Debug print
            print(f"Type: {type(data)}")  # Debug print
            print(f"Content: {data}")  # Debug print
            
            if data and isinstance(data, dict):
                results.append(self._process_stage(name, data))
        
        return results

    def _process_stage(self, name: str, data: Dict) -> OptimizationData:
        """Process a single optimization stage's data"""
        fleet_counts = {"Small": 0, "Medium": 0, "Large": 0}
        route_count = 0

        for route in data.get("routes", []):
            fleet_type = route.get("fleet_type")
            if fleet_type in fleet_counts:
                fleet_counts[fleet_type] += 1
            route_count += 1

        # Track stage sequence
        stages = get_shared("optimization_stages") or []
        stages.append(name)
        set_shared("optimization_stages", stages)
        
        return OptimizationData(
            stage=name,
            fleet_distribution=fleet_counts,
            metrics={
                "route_count": route_count,
                "stage_order": len(stages)
            }
        )