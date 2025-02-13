import yaml

def read_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data 