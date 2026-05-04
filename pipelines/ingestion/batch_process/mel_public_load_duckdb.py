import dlt
# import yaml
from dlt.sources.rest_api import rest_api_source
from dataclasses import dataclass
from typing import Any
from pathlib import Path
from utils.utility import load_yml_config
@dataclass
class MelPublicAPI:
    pipeline_name: str
    dataset_name: str = "bronze_zone"
    destination: str = "duckdb"
    base_url: str = "https://data.melbourne.vic.gov.au/api/explore/v2.1/"

    def _build_config(
            self, 
            resource_name: str, 
            path: str, 
            params: dict[str, Any]
        ) -> dict[str, Any]:

        return {
            "client": {"base_url": self.base_url},
            "resources": [{
                "name": resource_name,
                "endpoint": {
                    "path": path,
                    "data_selector": "results",
                    "paginator": "single_page",
                    "params": params
                }
            }]
        }

    def run(
            self, 
            resource_name: str, 
            endpoint_path: str, 
            query_params: dict[str, Any]
        ):
        config = self._build_config(resource_name, endpoint_path, query_params)
        source = rest_api_source(config)
        
        # Using the same pipeline name ensures dlt reuses the state/connection
        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=self.destination,
            dataset_name=self.dataset_name,
        )
        
        load_info = pipeline.run(source)
        print(f"Successfully loaded: {resource_name}")
        return load_info



def main() -> None:
    # 1. Load the dynamic configuration
    config_path = Path(__file__).parent / "config.yml"
    config_data = load_yml_config(config_path)["melbourne_api"]

    # 2. Initialize the API wrapper once
    mel_api = MelPublicAPI(
        pipeline_name=config_data["pipeline_name"],
        dataset_name=config_data["dataset_name"]
    )

    # 3. Dynamically loop through resources
    for res in config_data["resources"]:
        mel_api.run(
            resource_name=res["name"],
            endpoint_path=res["path"],
            query_params=res["params"]
        )

if __name__ == "__main__":
    main()