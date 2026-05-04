import yaml



def load_yml_config(file_path: str) -> dict:
    """
    Loads and parses a YAML configuration file.

    Args:
        file_path (str): The relative or absolute path to the .yml file.

    Returns:
        Dict[str, Any]: The parsed configuration as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist at the provided path.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    with open(file_path, "r") as f:
        return yaml.safe_load(f)