"""Logging utilities for simulations."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


class SimulationLogger:
    """Logger for simulation runs."""
    
    def __init__(self, name: str, log_dir: str = "logs", verbose: bool = True):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        
        # Setup file logger
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)
        
        self.logger.info(f"Simulation started: {name}")
    
    def log_parameters(self, config: Dict[str, Any]):
        """Log configuration parameters."""
        self.logger.info("Configuration:")
        for key, value in config.items():
            if key != 'agents':
                self.logger.info(f"  {key}: {value}")
    
    def log_results(self, results: Dict[str, Dict[str, Any]]):
        """Log simulation results."""
        self.logger.info("Results:")
        for name, metrics in results.items():
            self.logger.info(f"  {name}:")
            for key, value in metrics.items():
                self.logger.info(f"    {key}: {value}")
    
    def log_timing(self, times: Dict[str, float]):
        """Log timing information."""
        self.logger.info("Timing:")
        for section, duration in times.items():
            self.logger.info(f"  {section}: {duration:.3f}s")
    
    def info(self, msg: str):
        self.logger.info(msg)
    
    def error(self, msg: str):
        self.logger.error(msg)
    
    def finalize(self):
        """Close logger."""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
