from crewai.tools import BaseTool
from typing import Any, List, Type
from pydantic import BaseModel, Field
from delivery_management.data.load_data import DataLoader

class FleetInput(BaseModel):
    fleet_type: str = Field(..., description="Type of fleet (Small, Medium, Large)")

class Units(BaseModel):
    volume: str = Field(..., description="Volume unit cubic meters or centi-meters often represented as cubic_meters")
    weight: str = Field(..., description="Unit of weight, kg gms")

class Capacity(BaseModel):
    volume: float = Field(..., description="total volume that a fleet can accommodate, refer the units.volume for unit measurement")
    weight: float = Field(..., description="total weight that a fleet can carry, refer the unit.weight for weight measurement")
    units: Units = Field(..., description="unit of volume and weight")

class OperationalCost(BaseModel):
    per_km: float = Field(..., description="operational cost of the fleet per km")
    maintenance_monthly: float = Field(..., description="monthly maintenance")
    fuel_efficiency: float = Field(..., description="fuel efficiency factor")

class AvailableFleet(BaseModel):
    type_id: int = Field(..., description="fleet type id")
    type: str = Field(..., description="fleet type")
    count: int = Field(..., description="number of fleet that we have in that specific type for use")
    capacity: Capacity = Field(..., description="volume and weight")
    operational_cost: OperationalCost = Field(..., description="operational cost per_km, maintenance_monthly, fuel_efficience factor")
    fleets: List[str] = Field(..., description="id of the fleets")

class FleetData(BaseModel):
    total_fleet_count: int = Field(..., description="total number of fleets that are available")
    available_fleets: List[AvailableFleet] = Field(..., description="list of available fleets")

class Fleet(BaseTool):
    name: str = "Returns Fleet Data"
    description: str = "Returns the fleet details for a given fleet type"
    args_schema: Type[BaseModel] = FleetInput
    jsondata: Any = DataLoader.load_data("fleets.json")

    def __init__(self):
        super().__init__()

    def get_fleet_by_type(self, fleet_type):
        return [
            fleet for fleet in self.jsondata["available_fleets"]
            if fleet["type"] == fleet_type
        ]

    def _run(self, fleet_type: str) -> FleetData:
        return self.get_fleet_by_type(fleet_type)
