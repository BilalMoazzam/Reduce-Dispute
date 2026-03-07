import importlib
import yaml
import os

def load_agents(config_path='config/agents.yaml'):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    agents = {}
    for name, cfg in config['agents'].items():
        if not cfg.get('enabled', True):
            continue
        module_path, class_name = cfg['class'].rsplit('.', 1)
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)
        if cfg.get('type') == 'base':
            agents[name] = agent_class 
        else:
            agents[name] = agent_class()
    return agents