"""Data handler for saving simulation results."""

import numpy as np
import pandas as pd
from netCDF4 import Dataset
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from ..core.solver import SimulationResult


class DataHandler:
    """Save simulation data to various formats."""
    
    @staticmethod
    def save_trajectories_csv(filepath: str, result: SimulationResult):
        """Save agent trajectories to CSV."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        rows = []
        for agent in result.agents:
            trajectory = result.trajectories[agent.name]
            energy_hist = result.energy_histories[agent.name]
            
            for step, (pos, energy) in enumerate(zip(trajectory, energy_hist)):
                rows.append({
                    'agent': agent.name,
                    'policy': agent.policy.value,
                    'step': step,
                    'row': pos[0],
                    'col': pos[1],
                    'energy': energy
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, float_format='%.4f')
    
    @staticmethod
    def save_metrics_csv(filepath: str, result: SimulationResult):
        """Save performance metrics to CSV."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        rows = []
        for name, metrics in result.agent_results.items():
            rows.append(metrics)
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, float_format='%.4f')
    
    @staticmethod
    def save_wall_csv(filepath: str, result: SimulationResult):
        """Save wall quality field to CSV."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        wall = result.wall
        rows = []
        for r in range(wall.height):
            for c in range(wall.width):
                q = wall.grid[r, c]
                cost = 1.0 / q if q > 0.05 else float('inf')
                rows.append({
                    'row': r,
                    'col': c,
                    'quality': q,
                    'cost': cost if cost != float('inf') else -1
                })
        
        df = pd.DataFrame(rows)
        df.to_csv(filepath, index=False, float_format='%.4f')
    
    @staticmethod
    def save_netcdf(filepath: str, result: SimulationResult, config: Dict[str, Any]):
        """Save complete data to NetCDF."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        wall = result.wall
        
        with Dataset(filepath, 'w', format='NETCDF4') as nc:
            # Dimensions
            nc.createDimension('row', wall.height)
            nc.createDimension('col', wall.width)
            nc.createDimension('agent', len(result.agents))
            
            max_steps = max(len(t) for t in result.trajectories.values())
            nc.createDimension('step', max_steps)
            
            # Coordinates
            nc_row = nc.createVariable('row', 'i4', ('row',), zlib=True)
            nc_row[:] = np.arange(wall.height)
            nc_row.long_name = 'wall_row'
            
            nc_col = nc.createVariable('col', 'i4', ('col',), zlib=True)
            nc_col[:] = np.arange(wall.width)
            nc_col.long_name = 'wall_column'
            
            # Wall quality
            nc_q = nc.createVariable('quality', 'f8', ('row', 'col'), zlib=True)
            nc_q[:, :] = wall.grid
            nc_q.long_name = 'hold_quality'
            nc_q.units = 'dimensionless'
            
            # Agent trajectories
            nc_traj_r = nc.createVariable('traj_row', 'i4', ('agent', 'step'), zlib=True, fill_value=-1)
            nc_traj_c = nc.createVariable('traj_col', 'i4', ('agent', 'step'), zlib=True, fill_value=-1)
            nc_energy = nc.createVariable('energy', 'f8', ('agent', 'step'), zlib=True, fill_value=np.nan)
            
            for i, agent in enumerate(result.agents):
                traj = result.trajectories[agent.name]
                e_hist = result.energy_histories[agent.name]
                
                for j, (pos, e) in enumerate(zip(traj, e_hist)):
                    nc_traj_r[i, j] = pos[0]
                    nc_traj_c[i, j] = pos[1]
                    nc_energy[i, j] = e
            
            # Results
            nc_height = nc.createVariable('final_height', 'i4', ('agent',), zlib=True)
            nc_success = nc.createVariable('success', 'i4', ('agent',), zlib=True)
            
            for i, agent in enumerate(result.agents):
                m = result.agent_results[agent.name]
                nc_height[i] = m['final_height']
                nc_success[i] = 1 if m['success'] else 0
            
            # Global attributes
            nc.title = "Adimanusia Lattice Climbing Simulation"
            nc.scenario = config.get('scenario_name', 'Unknown')
            nc.grade = config.get('grade', '5.10')
            nc.created = datetime.now().isoformat()
            nc.authors = "Sandy H. S. Herho, Freden M. Sembiring-Milala"
    
    @staticmethod
    def save_all(
        output_dir: str,
        result: SimulationResult,
        config: Dict[str, Any],
        prefix: str = "",
        save_csv: bool = True,
        save_netcdf: bool = True
    ):
        """Save all data formats."""
        output_dir = Path(output_dir)
        
        if save_csv:
            csv_dir = output_dir / "csv"
            csv_dir.mkdir(parents=True, exist_ok=True)
            
            DataHandler.save_trajectories_csv(csv_dir / f"{prefix}_trajectories.csv", result)
            DataHandler.save_metrics_csv(csv_dir / f"{prefix}_metrics.csv", result)
            DataHandler.save_wall_csv(csv_dir / f"{prefix}_wall.csv", result)
        
        if save_netcdf:
            nc_dir = output_dir / "netcdf"
            nc_dir.mkdir(parents=True, exist_ok=True)
            DataHandler.save_netcdf(nc_dir / f"{prefix}.nc", result, config)
