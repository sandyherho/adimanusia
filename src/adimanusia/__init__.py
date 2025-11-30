"""
adimanusia: Lattice Climbing Agent-Based Model

Comparing decision-making strategies on constrained environments.
Greedy vs Prudent: Who reads the route better?
"""

__version__ = "0.0.1"
__author__ = "Sandy H. S. Herho, Freden M. Sembiring-Milala"
__email__ = "sandy.herho@email.ucr.edu"
__license__ = "MIT"

from .core.lattice import LatticeWall
from .core.agent import Climber, ClimberStatus, ClimberPolicy
from .core.solver import Solver, SimulationResult
from .io.config_manager import ConfigManager
from .io.data_handler import DataHandler

__all__ = [
    "LatticeWall",
    "Climber",
    "ClimberStatus",
    "ClimberPolicy",
    "Solver",
    "SimulationResult",
    "ConfigManager",
    "DataHandler",
]
