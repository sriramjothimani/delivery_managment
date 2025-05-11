from pathlib import Path
from crewai import Task
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from delivery_management.tools import fleet, time_constraints
from delivery_management.tools.optimization_collector import OptimizationCollectorTool

class OptimizationStep(BaseModel):
    stage: str = Field(..., description="Optimization stage name")
    fleet_distribution: Dict[Literal["Small", "Medium", "Large"], int] = Field(
        ..., description="Fleet type counts at this stage"
    )
    cost_analysis: Dict[str, float] = Field(
        ..., description="Cost metrics including per_km and maintenance"
    )
    time_efficiency: float = Field(
        ..., description="Time efficiency improvement percentage"
    )
    drawbacks: List[str] = Field(
        ..., description="Identified limitations at this stage"
    )
    improvements: List[str] = Field(
        ..., description="Specific optimizations implemented"
    )

class FleetDistribution(BaseModel):
    Small: int = Field(..., description="Count of small fleets")
    Medium: int = Field(..., description="Count of medium fleets")
    Large: int = Field(..., description="Count of large fleets")
    total_cost: float = Field(..., description="Total operational cost")
    avg_maintenance: float = Field(..., description="Average maintenance factor")

class EfficiencyMetrics(BaseModel):
    total_routes: int = Field(..., description="Total number of routes")
    cost_per_km: Dict[str, float] = Field(..., description="Per km charges by fleet type")
    maintenance_factors: Dict[str, float] = Field(..., description="Maintenance coefficients")
    time_savings: float = Field(..., description="Total time saved in hours")

class OptimizationSummary(BaseModel):
    steps: List[OptimizationStep] = Field(..., description="List of optimization steps")
    final_fleet_assignments: FleetDistribution = Field(..., description="Final fleet assignments")
    efficiency_gains: EfficiencyMetrics = Field(..., description="Efficiency improvements")

def create_summary_task(agent):
    collector = OptimizationCollectorTool()
    fleet_tool = fleet.Fleet()
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    time_constraints_tool = time_constraints.TimeConstraints()\
        .with_data_file(Path(BASE_DIR / "data/time_constraints.json"))

    return Task(
        name="SummarizeOptimizationSteps",
        description=(
            "Analyze and provide a detailed optimization summary using these tools:\n"
            "1. OptimizationCollectorTool - Get stage-wise fleet distribution data\n"
            "2. Fleet tool - Calculate per km charges and maintenance costs\n"
            "3. TimeConstraints tool - Analyze time efficiency improvements\n\n"
            
            "For each optimization stage, analyze:\n"
            "- Drawbacks identified (using fleet and time constraint tools)\n"
            "- Specific improvements implemented\n"
            "- Fleet distribution changes (from OptimizationCollector)\n"
            "- Cost impact (using Fleet tool's per km charges)\n"
            "- Maintenance implications (from Fleet tool)\n\n"
            
            "Include in your summary:\n"
            "1. Detailed textual analysis of each stage\n"
            "2. Structured data with:\n"
            "   - Fleet counts per type\n"
            "   - Cost per km\n"
            "   - Maintenance factors\n"
            "   - Time efficiency metrics\n"
            "3. Overall cost-benefit analysis\n\n"
            
            "Format output with:\n"
            "1. Comprehensive textual summary\n"
            "2. Supporting structured data matching the OptimizationSummary model"
        ),
        expected_output=(
            "{\n"
            "  \"optimization_steps\": [\n"
            "    {\n"
            "      \"stage\": \"Initial Clustering\",\n"
            "      \"fleet_distribution\": {\n"
            "        \"Small\": 15,\n"
            "        \"Medium\": 8,\n"
            "        \"Large\": 2\n"
            "      },\n"
            "      \"avg_utilization\": 45\n"
            "    },\n"
            "    {\n"
            "      \"stage\": \"After Weight Optimization\",\n"
            "      \"fleet_distribution\": {\n"
            "        \"Small\": 10,\n"
            "        \"Medium\": 12,\n"
            "        \"Large\": 3\n"
            "      },\n"
            "      \"avg_utilization\": 68,\n"
            "      \"improvement\": \"+23% utilization\"\n"
            "    }\n"
            "  ],\n"
            "  \"final_summary\": {\n"
            "    \"total_routes\": 25,\n"
            "    \"fleet_distribution\": {\n"
            "      \"Small\": 8,\n"
            "      \"Medium\": 14,\n"
            "      \"Large\": 3\n"
            "    },\n"
            "    \"avg_utilization\": 82,\n"
            "    \"total_cost_savings\": 1500\n"
            "  }\n"
            "}"
        ),
        agent=agent,
        tools=[collector, fleet_tool, time_constraints_tool],
        output_json=OptimizationSummary
    )