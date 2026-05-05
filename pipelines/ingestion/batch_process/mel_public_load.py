"""Batch ingestion pipeline for Melbourne City Data APIs using dlt."""

import dlt
from dlt.sources.rest_api import rest_api_source
from dataclasses import dataclass
from typing import Any, Optional
from pathlib import Path
from utils.utility import load_yml_config


@dataclass
class MelPublicAPI:
    
    pipeline_name: str = 'melbourne_city_data'
    dataset_name: Optional[str] = "dlt"
    env: str = 'local_dev'
    destination: str = "filesystem"
    table_format: str = "delta"
    base_url: str = "https://data.melbourne.vic.gov.au/api/explore/v2.1/"

    @property
    def bucket_url(self) -> str:
        """Generates the target GCS bucket URL based on the current environment.

        Returns:
            str: The fully qualified GCS bucket URL (e.g., gs://woolie-project-lakehouse/dev).
        """
        return f"gs://woolie-project-lakehouse/{self.env}/bronze"

    def _build_config(
            self, 
            resource_name: str, 
            path: str, 
            params: dict[str, Any]
        ) -> dict[str, Any]:
        """Builds the REST API source configuration dictionary for dlt.

        Args:
            resource_name (str): The logical name of the API resource.
            path (str): The endpoint path relative to the base URL.
            params (dict[str, Any]): The query parameters to pass to the API.

        Returns:
            dict[str, Any]: A dlt REST API source configuration dictionary.
        """
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
            query_params: dict[str, Any],
            write_disposition: str = "append"
        ):
        """Executes the dlt pipeline for a specific API resource.

        Args:
            resource_name (str): The name of the resource to extract and load.
            endpoint_path (str): The API endpoint path.
            query_params (dict[str, Any]): The API query parameters.
            write_disposition (str, optional): The write behavior for the destination. Defaults to "append".

        Returns:
            Any: The pipeline load info object containing execution metrics and status.
        """
        config = self._build_config(
            resource_name, 
            endpoint_path, 
            query_params
        )
        source = rest_api_source(config)

        dest = dlt.destinations.filesystem(bucket_url=self.bucket_url)
        # Using the same pipeline name ensures dlt reuses the state/connection

        pipeline = dlt.pipeline(
            pipeline_name=self.pipeline_name,
            destination=dest,
            dataset_name=self.dataset_name,
        )
        
        load_info = pipeline.run(
            data = source,
            table_format=self.table_format,
            write_disposition=write_disposition
        )
        print(f"Successfully loaded: {resource_name} to {self.env} layer")
        return load_info

def main() -> None:
    """Main entry point for the Melbourne API batch ingestion pipeline.

    Loads configurations from a YAML file, initializes the API wrapper,
    and sequentially triggers ingestion for each defined resource.
    """
    # 1. Load the dynamic configuration
    config_path = Path(__file__).parent / "config.yml"
    config_data = load_yml_config(config_path)["melbourne_api"]

    # 2. Initialize the API wrapper once
    mel_api = MelPublicAPI(
        pipeline_name = config_data['pipeline_name'],
        base_url= config_data["base_url"]
    )

    # 3. Dynamically loop through resources
    for res in config_data["resources"]:
        mel_api.run(
            resource_name=res["name"],
            endpoint_path=res["path"],
            query_params=res["params"],
            write_disposition= res["write_disposition"]
        )

if __name__ == "__main__":
    main()