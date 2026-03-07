import yaml
import os

def load_monitoring_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'monitoring_config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['monitoring']