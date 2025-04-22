import json
from pathlib import Path
from crewai.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from typing import List

from delivery_management.data.load_data import DataLoader


class AverageDeliverTime(BaseModel):
    weight_not_exceeding: str = Field(
        ...,
        description="Maximum weight for which the delivery time estimate applies (e.g., '20kg')."
    )
    delivery_time: str = Field(
        ...,
        description="Estimated delivery time per package under the weight limit (e.g., '5 mins')."
    )


class OperationalHours(BaseModel):
    start: str = Field(
        ...,
        description="Start of fleet operation time in HH:MM format (e.g., '09:00')."
    )
    end: str = Field(
        ...,
        description="End of fleet operation time in HH:MM format (e.g., '18:00')."
    )


class MandatoryRest(BaseModel):
    duration: int = Field(
        ...,
        description="Duration of mandatory rest after max continuous driving time, in minutes."
    )
    units: str = Field(
        ...,
        description="Units for rest duration (e.g., 'minutes')."
    )


class MaxContinuousDrivingTime(BaseModel):
    hours: int = Field(
        ...,
        description="Maximum number of continuous driving hours before mandatory rest."
    )
    mandatory_rest: MandatoryRest = Field(
        ...,
        description="Mandatory rest details after reaching max continuous driving time."
    )


class PeakTrafficPeriod(BaseModel):
    start: str = Field(
        ...,
        description="Start time of the peak traffic window (e.g., '07:30')."
    )
    end: str = Field(
        ...,
        description="End time of the peak traffic window (e.g., '09:00')."
    )
    impact_factor: float = Field(
        ...,
        description="Multiplicative factor for time estimation during peak hours (e.g., 1.5)."
    )


class TimeConstraints(BaseModel):
    average_deliver_time: AverageDeliverTime = Field(
        ...,
        description="Estimated delivery time based on weight thresholds."
    )
    average_distance_between_locations: str = Field(
        ...,
        description="Estimated average distance between delivery points (e.g., '5 km')."
    )
    average_speed: str = Field(
        ...,
        description="Average fleet driving speed under normal traffic (e.g., '30 km/h')."
    )
    operational_hours: OperationalHours = Field(
        ...,
        description="Operational working hours for fleet delivery."
    )
    max_continuous_driving_time: MaxContinuousDrivingTime = Field(
        ...,
        description="Driver limitations on continuous driving and rest requirements."
    )
    peak_traffic_hours: List[PeakTrafficPeriod] = Field(
        ...,
        description="List of known peak traffic windows with time impact multipliers."
    )


class TimeConstraintsInput(BaseModel):
    time_constraints: TimeConstraints = Field(
        ...,
        description="Top-level input structure for delivery route time constraint settings."
    )

class TimeConstraints(BaseTool):
    name: str = "Time constraints"
    description: str = "Returns various time constraints that affect the delivery schedule"
    jsondata: Any = DataLoader.load_data("time_constraints.json")
    _data_file_path: str = PrivateAttr(default=None)
    _time_constraints: list = PrivateAttr(default_factory=dict)

    def __init__(self):
        super().__init__()

    def with_data_file(self, path: Path):
        self._data_file_path = path
        return self
    
    def load_json_data(self):
        with open(self._data_file_path, 'r') as f:
            self._time_constraints = json.load(f)

    
    def _run(self) -> TimeConstraintsInput:
        self.load_json_data()
        return self._time_constraints