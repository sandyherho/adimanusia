"""
Simulation Solver for Lattice Climbing Model.

Orchestrates simulation of Greedy vs Prudent climbers on realistic routes.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import multiprocessing
from tqdm import tqdm

from .lattice import LatticeWall
from .agent import Climber, ClimberStatus


@dataclass
class SimulationResult:
    """Container for simulation results."""
    wall: LatticeWall
    agents: List[Climber]
    agent_results: Dict[str, Dict[str, Any]]
    trajectories: Dict[str, List[Tuple[int, int]]]
    energy_histories: Dict[str, List[float]]
    step_count: int
    config: Dict[str, Any] = field(default_factory=dict)


class Solver:
    """
    Simulation solver for lattice climbing.
    
    Runs agents through the wall and collects results.
    """
    
    def __init__(
        self,
        max_steps: int = 100,
        n_cores: Optional[int] = None,
        verbose: bool = True
    ):
        self.max_steps = max_steps
        self.n_cores = n_cores if n_cores else multiprocessing.cpu_count()
        self.verbose = verbose
    
    def solve(
        self,
        wall: LatticeWall,
        agents: List[Climber],
        start_position: Optional[Tuple[int, int]] = None
    ) -> SimulationResult:
        """
        Run simulation for all agents.
        
        Args:
            wall: The climbing wall
            agents: List of climbers to simulate
            start_position: Override start position
        
        Returns:
            SimulationResult with all data
        """
        # Determine start
        if start_position is None:
            start_position = wall.start_positions[0] if wall.start_positions else (0, wall.width // 2)
        
        # Reset agents
        for agent in agents:
            agent.reset(start_position)
        
        # Storage
        trajectories = {agent.name: [start_position] for agent in agents}
        energy_histories = {agent.name: [agent.max_energy] for agent in agents}
        
        active_agents = list(agents)
        
        if self.verbose:
            print(f"      Wall: {wall.scenario_name}")
            print(f"      Start: {start_position}")
            print(f"      Agents: {[a.name for a in agents]}")
        
        # Simulation loop
        step = 0
        pbar = tqdm(
            total=self.max_steps,
            desc="      Climbing",
            ncols=70,
            bar_format='{desc}: {percentage:3.0f}%|{bar}| {n}/{total}',
            disable=not self.verbose
        )
        
        while step < self.max_steps and active_agents:
            still_active = []
            
            for agent in active_agents:
                if agent.status == ClimberStatus.CLIMBING:
                    agent.step(wall)
                    trajectories[agent.name].append(agent.position)
                    energy_histories[agent.name].append(agent.energy)
                    
                    if agent.status == ClimberStatus.CLIMBING:
                        still_active.append(agent)
            
            active_agents = still_active
            step += 1
            pbar.update(1)
            
            if not active_agents:
                break
        
        pbar.close()
        
        # Collect results
        agent_results = {}
        for agent in agents:
            max_height = wall.height - 1
            final_height = agent.position[0]
            energy_used = agent.max_energy - agent.energy
            
            height_eff = final_height / max_height if max_height > 0 else 0
            energy_eff = final_height / energy_used if energy_used > 0 else 0
            
            agent_results[agent.name] = {
                'name': agent.name,
                'policy': agent.policy.value,
                'status': agent.status.value,
                'final_height': final_height,
                'max_height': max_height,
                'height_efficiency': height_eff,
                'initial_energy': agent.max_energy,
                'final_energy': agent.energy,
                'energy_used': energy_used,
                'energy_efficiency': energy_eff,
                'total_steps': agent.steps,
                'total_cost': agent.total_cost,
                'path_length': len(agent.path),
                'success': agent.status == ClimberStatus.TOPPED,
                'time_to_top': agent.time_to_top,
            }
        
        if self.verbose:
            print(f"\n      Simulation completed in {step} steps")
            for name, result in agent_results.items():
                status = result['status']
                h = result['final_height']
                e = result['energy_used']
                print(f"      {name}: {status} at h={h}, E_used={e:.1f}")
        
        return SimulationResult(
            wall=wall,
            agents=agents,
            agent_results=agent_results,
            trajectories=trajectories,
            energy_histories=energy_histories,
            step_count=step
        )
