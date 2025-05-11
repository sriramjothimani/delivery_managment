from crewai import Task
from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional
from delivery_management.tools.optimization_collector import OptimizationCollectorTool

class OptimizationStep(BaseModel):
    stage: str = Field(..., description="Optimization stage name")
    fleet_distribution: Dict[Literal["Small", "Medium", "Large"], int] = Field(
        ..., description="Fleet type counts at this stage"
    )
    avg_utilization: float = Field(..., description="Average fleet utilization percentage")
    improvement: Optional[str] = Field(None, description="Improvement metrics")

class FleetDistribution(BaseModel):
    Small: int = Field(..., description="Count of small fleets")
    Medium: int = Field(..., description="Count of medium fleets")
    Large: int = Field(..., description="Count of large fleets")

class EfficiencyMetrics(BaseModel):
    total_routes: int = Field(..., description="Total number of routes")
    avg_utilization: float = Field(..., description="Average utilization percentage")
    total_cost_savings: float = Field(..., description="Total cost savings")

class OptimizationSummary(BaseModel):
    steps: List[OptimizationStep] = Field(..., description="List of optimization steps")
    final_fleet_assignments: FleetDistribution = Field(..., description="Final fleet assignments")
    efficiency_gains: EfficiencyMetrics = Field(..., description="Efficiency improvements")

def create_summary_task(agent):
    collector = OptimizationCollectorTool()
    return Task(
        name="SummarizeOptimizationSteps",
        description=(
            "Analyze and summarize how the optimization agents improved fleet assignments step-by-step. "
            "Access the stored outputs from each optimization stage to generate a comprehensive report.\n\n"
            
            "Your report must include:\n"
            "1. Chronological sequence of all optimization steps\n"
            "2. Fleet assignment changes at each stage\n"
            "3. Efficiency improvements (cost, utilization, etc.)\n"
            "4. Key decision points and rationale\n"
            "5. Final fleet assignment statistics\n\n"
            
            "Available optimization stages:\n"
            "- h3_clustered_orders: Initial clustering\n"
            "- time_optimized_routes: Final time-optimized routes\n\n"
            "- weight_optimized_routes: After weight optimization\n"
            "- volume_optimized_routes: After volume optimization\n"
            
            "Format the output as a well-structured JSON document with clear sections."
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
        tools=[collector],
        output_json=OptimizationSummary
    )