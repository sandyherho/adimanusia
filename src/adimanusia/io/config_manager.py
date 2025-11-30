"""Configuration file parser for lattice climbing simulations."""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    name: str
    energy: float
    policy: str
    lookahead: int = 5
    alpha: float = 0.5
    beta: float = 0.3
    color: Optional[str] = None


class ConfigManager:
    """Parse and validate configuration files."""
    
    DEFAULTS = {
        'scenario_name': 'Custom Scenario',
        'scenario_type': 'custom',
        'grade': '5.10',
        'wall_height': 40,
        'wall_width': 20,
        'base_terrain': 0.35,
        'max_steps': 80,
        'seed': None,
        'n_cores': None,
        'save_csv': True,
        'save_netcdf': True,
        'save_png': True,
        'save_gif': True,
        'output_dir': 'outputs',
        'animation_fps': 12,
        'animation_dpi': 100,
    }
    
    @staticmethod
    def load(config_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")
        
        config = ConfigManager.DEFAULTS.copy()
        agents = []
        
        in_agents_section = False
        
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                
                if not line or line.startswith('#'):
                    continue
                
                if line.lower() == '[agents]':
                    in_agents_section = True
                    continue
                
                if line.startswith('[') and line.endswith(']'):
                    in_agents_section = False
                    continue
                
                if in_agents_section:
                    agent = ConfigManager._parse_agent_line(line)
                    if agent:
                        agents.append(agent)
                    continue
                
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if '#' in value:
                    value = value.split('#')[0].strip()
                
                config[key] = ConfigManager._parse_value(value)
        
        config['agents'] = agents
        return config
    
    @staticmethod
    def _parse_agent_line(line: str) -> Optional[AgentConfig]:
        """Parse agent definition: name, energy, policy, lookahead, alpha, beta"""
        parts = [p.strip() for p in line.split(',')]
        
        if len(parts) < 3:
            return None
        
        try:
            name = parts[0]
            energy = float(parts[1])
            policy = parts[2].lower()
            lookahead = int(parts[3]) if len(parts) > 3 else 5
            alpha = float(parts[4]) if len(parts) > 4 else 0.5
            beta = float(parts[5]) if len(parts) > 5 else 0.3
            color = parts[6] if len(parts) > 6 else None
            
            return AgentConfig(
                name=name,
                energy=energy,
                policy=policy,
                lookahead=lookahead,
                alpha=alpha,
                beta=beta,
                color=color
            )
        except (ValueError, IndexError):
            return None
    
    @staticmethod
    def _parse_value(value: str) -> Any:
        """Parse string to Python type."""
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        if value.lower() == 'none':
            return None
        try:
            if '.' in value or 'e' in value.lower():
                return float(value)
            else:
                return int(value)
        except ValueError:
            return value
    
    @staticmethod
    def get_scenario_config(scenario: str) -> Dict[str, Any]:
        """Get default configuration for built-in scenario."""
        config = ConfigManager.DEFAULTS.copy()
        
        if scenario == 'pump_clock':
            config.update({
                'scenario_name': 'Case 1 - The Pump Clock',
                'scenario_type': 'pump_clock',
                'grade': '5.11c',
                'wall_height': 40,
                'wall_width': 20,
                'max_steps': 80,
            })
            config['agents'] = [
                AgentConfig('Greedy', energy=150, policy='greedy', lookahead=1, alpha=0.5, beta=0.0),
                AgentConfig('Prudent', energy=150, policy='prudent', lookahead=5, alpha=0.6, beta=0.4),
            ]
        
        elif scenario == 'crux_roulette':
            config.update({
                'scenario_name': 'Case 2 - The Crux Roulette',
                'scenario_type': 'crux_roulette',
                'grade': '5.12a',
                'wall_height': 40,
                'wall_width': 20,
                'max_steps': 70,
            })
            config['agents'] = [
                AgentConfig('Greedy', energy=130, policy='greedy', lookahead=1, alpha=0.5, beta=0.0),
                AgentConfig('Prudent', energy=130, policy='prudent', lookahead=6, alpha=0.5, beta=0.5),
            ]
        
        elif scenario == 'labyrinth':
            config.update({
                'scenario_name': 'Case 3 - The Labyrinth',
                'scenario_type': 'labyrinth',
                'grade': '5.11b',
                'wall_height': 40,
                'wall_width': 20,
                'base_terrain': 0.0,
                'max_steps': 100,
            })
            config['agents'] = [
                AgentConfig('Greedy', energy=200, policy='greedy', lookahead=1, alpha=0.5, beta=0.0),
                AgentConfig('Prudent', energy=200, policy='prudent', lookahead=6, alpha=0.4, beta=0.6),
            ]
        
        elif scenario == 'redpoint_crux':
            config.update({
                'scenario_name': 'Case 4 - The Redpoint Crux',
                'scenario_type': 'redpoint_crux',
                'grade': '5.12b',
                'wall_height': 40,
                'wall_width': 20,
                'max_steps': 80,
            })
            config['agents'] = [
                AgentConfig('Greedy', energy=100, policy='greedy', lookahead=1, alpha=0.5, beta=0.0),
                AgentConfig('Prudent', energy=100, policy='prudent', lookahead=5, alpha=0.4, beta=0.5),
            ]
        
        else:
            raise ValueError(f"Unknown scenario: {scenario}")
        
        return config
