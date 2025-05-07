import json
from pathlib import Path
import yaml
import litellm
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from delivery_management.tools import (
    cluster_orders,
    fleet,
    enrich_clustered_orders
)

from delivery_management.tasks import (
    create_routes,
    time_optimize_routes,
    weight_optimize_routes
)

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

class DeliveryManagement():
    """DeliveryManagement crew"""

    BASE_DIR = Path(__file__).resolve().parent
    # Load the YAML configuration
    file_path = BASE_DIR / 'config/agents.yaml'
    with open(file_path, "r") as f:
        agents_config = yaml.safe_load(f)

    # Load Gemini vertex ai service account.json
    file_path = Path('/mnt/c/users/sriramkumar.jothiman/secrets/vertex_ai_service_account.json')
    with open(file_path, "r") as f:
        vertex_credentials = yaml.safe_load(f)    

    vertex_credentials_json = json.dumps(vertex_credentials)
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    llm = LLM(
        model="gemini/gemini-2.0-flash-001",
        temperature=0.2,
        max_tokens=8192,
        vertex_credentials=vertex_credentials_json
    )

    # litellm._turn_on_debug()

    cluster_orders_tool = cluster_orders.ClusterOrdersByGeoTool()\
        .with_orders_file(Path(BASE_DIR / "data/orders.json"))\
        .with_geolocations_file(Path(BASE_DIR / "data/geolocations.json"))\
        .with_static_ref_file(Path(BASE_DIR / "data/static_reference_data.json"))\
        .with_inventory_file(Path(BASE_DIR / "data/inventory.json"))
        
    fleet_tool = fleet.Fleet()

    enrich_clusters_tool = enrich_clustered_orders.EnrichClusteredOrders()

    # Define Agents
 
    greedyFleetManagerAgent = Agent(
        config= agents_config['GreedyFleetManagerAgent'],
        memory= True,
        verbose=True,
        # tools=[fleet_tool],
        # llm='openai/gpt-4-turbo'
        llm = llm
    )

    timeOptimizerAgent = Agent(
        config = agents_config['TimeOptimizerAgent'],
        memory= True,
        verbose= True,
        # tools=[fleet_tool],
        llm = llm
    )

    weightOptimizerAgent = Agent(
        config = agents_config['WeightOptimizerAgent'],
        memory= True,
        verbose= True,
        # tools=[fleet_tool],
        llm = llm
    )

    # Define Tasks

    create_routes = create_routes.create_cluster_orders_into_routes_task(greedyFleetManagerAgent)
    time_optimize_routes = time_optimize_routes.time_optimize_routes_task(timeOptimizerAgent)
    weight_optimize_routes = weight_optimize_routes.fine_tune_routes_task(weightOptimizerAgent)

    def crew(self) -> Crew:
        """Creates the DeliveryManagement crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents= [self.greedyFleetManagerAgent, self.timeOptimizerAgent, self.weightOptimizerAgent], 
            tasks= [self.create_routes, self.time_optimize_routes, self.weight_optimize_routes],
            process=Process.sequential,
            verbose=True,
            cache=False
        )

        # return Crew(
        #     agents= [self.greedyFleetManagerAgent, self.weightOptimizerAgent], 
        #     tasks= [self.create_routes, self.time_optimize_routes, self.weight_optimize_routes],
        #     process=Process.sequential,
        #     verbose=True,
        #     cache=False
        # )
