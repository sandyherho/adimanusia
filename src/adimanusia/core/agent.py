"""
Climbing Agent with Decision Policies.

Two distinct decision-making strategies:

1. GREEDY CLIMBER ("The Gym Bro"):
   - Always moves to highest quality hold available
   - Prioritizes immediate comfort over strategy
   - Fast but susceptible to traps and poor pacing

2. PRUDENT CLIMBER ("The Tactician"):  
   - Balances height gain, energy cost, and route-reading
   - Uses lookahead to avoid dead ends
   - May take harder moves now to save energy later
   - Considers position quality (escapes, rest potential)

Both agents have EQUAL energy budgets - strategy determines success.
"""

import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

from .lattice import LatticeWall


class ClimberStatus(Enum):
    """Climber state."""
    CLIMBING = "Climbing"
    TOPPED = "Topped Out"
    STUCK = "Stuck"
    PUMPED = "Pumped Off"


class ClimberPolicy(Enum):
    """Decision policy."""
    GREEDY = "greedy"
    PRUDENT = "prudent"


@dataclass
class MoveRecord:
    """Record of a single move."""
    step: int
    from_pos: Tuple[int, int]
    to_pos: Tuple[int, int]
    cost: float
    energy_before: float
    energy_after: float
    height_gain: int
    lateral_move: int  # -1=left, 0=straight, 1=right


class Climber:
    """
    Climbing agent with configurable strategy.
    
    Attributes:
        name: Climber identifier
        energy: Current energy level
        max_energy: Starting energy
        policy: Decision strategy
        position: Current (row, col)
        path: History of positions
        status: Current state
        lookahead: Search depth for prudent policy
    """
    
    COLORS = {
        'greedy': '#E74C3C',    # Red - aggressive
        'prudent': '#3498DB',   # Blue - calculated
    }
    
    def __init__(
        self,
        name: str,
        energy: float = 150.0,
        policy: str = "greedy",
        lookahead: int = 5,
        alpha: float = 0.5,      # Height vs efficiency balance
        beta: float = 0.3,       # Future options weight
        color: Optional[str] = None
    ):
        """
        Initialize climber.
        
        Args:
            name: Identifier
            energy: Starting energy budget
            policy: 'greedy' or 'prudent'
            lookahead: Search depth for prudent climber
            alpha: Weight for height gain (vs energy saving)
            beta: Weight for future options (escape routes)
            color: Visualization color
        """
        self.name = name
        self.max_energy = energy
        self.energy = energy
        self.lookahead = lookahead
        self.alpha = np.clip(alpha, 0.0, 1.0)
        self.beta = np.clip(beta, 0.0, 1.0)
        
        policy_lower = policy.lower()
        if policy_lower == "greedy":
            self.policy = ClimberPolicy.GREEDY
        elif policy_lower == "prudent":
            self.policy = ClimberPolicy.PRUDENT
        else:
            raise ValueError(f"Unknown policy: {policy}")
        
        self.color = color if color else self.COLORS.get(policy_lower, '#FFFFFF')
        
        # State (set on reset)
        self.position: Tuple[int, int] = (0, 0)
        self.path: List[Tuple[int, int]] = []
        self.energy_history: List[float] = []
        self.move_history: List[MoveRecord] = []
        self.status = ClimberStatus.CLIMBING
        self.total_cost = 0.0
        self.steps = 0
        self.time_to_top: Optional[int] = None
    
    def reset(self, start_pos: Tuple[int, int]):
        """Reset to starting position."""
        self.position = start_pos
        self.path = [start_pos]
        self.energy = self.max_energy
        self.energy_history = [self.max_energy]
        self.move_history = []
        self.status = ClimberStatus.CLIMBING
        self.total_cost = 0.0
        self.steps = 0
        self.time_to_top = None
    
    def decide_move(self, wall: LatticeWall) -> Optional[Tuple[int, int]]:
        """
        Decide next move based on policy.
        
        Returns target position or None if no valid move.
        """
        if self.status != ClimberStatus.CLIMBING:
            return None
        
        # Check summit
        if wall.is_summit(self.position[0]):
            self.status = ClimberStatus.TOPPED
            if self.time_to_top is None:
                self.time_to_top = self.steps
            return None
        
        # Get valid moves
        neighbors = wall.get_neighbors(self.position[0], self.position[1])
        
        if not neighbors:
            self.status = ClimberStatus.STUCK
            return None
        
        # Filter by affordability
        affordable = []
        for pos in neighbors:
            cost = wall.get_cost(pos[0], pos[1])
            if self.energy >= cost:
                affordable.append((pos, cost))
        
        if not affordable:
            self.status = ClimberStatus.PUMPED
            return None
        
        # Apply policy
        if self.policy == ClimberPolicy.GREEDY:
            return self._decide_greedy(wall, affordable)
        else:
            return self._decide_prudent(wall, affordable)
    
    def _decide_greedy(
        self,
        wall: LatticeWall,
        affordable: List[Tuple[Tuple[int, int], float]]
    ) -> Tuple[int, int]:
        """
        Greedy policy: Always grab the best hold.
        
        Priority:
        1. Highest quality hold (lowest cost)
        2. If tied, prefer upward movement
        3. If still tied, prefer current column
        """
        best_pos = None
        best_quality = -1.0
        best_height = -1
        
        for pos, cost in affordable:
            quality = wall.get_quality(pos[0], pos[1])
            height = pos[0]
            
            # Prefer higher quality
            if quality > best_quality:
                best_quality = quality
                best_height = height
                best_pos = pos
            # Tie-break: prefer height gain
            elif quality == best_quality and height > best_height:
                best_height = height
                best_pos = pos
        
        return best_pos
    
    def _decide_prudent(
        self,
        wall: LatticeWall,
        affordable: List[Tuple[Tuple[int, int], float]]
    ) -> Tuple[int, int]:
        """
        Prudent policy: Strategic multi-factor decision.
        
        Evaluates moves based on:
        1. Height gain (progress toward goal)
        2. Energy efficiency (sustainable pace)
        3. Future options (avoid dead ends)
        4. Position quality (escape routes, rest potential)
        
        Uses limited lookahead to detect traps.
        """
        current_row, current_col = self.position
        
        best_pos = None
        best_score = -float('inf')
        
        for pos, cost in affordable:
            # Factor 1: Height gain (normalized to [0, 1])
            height_gain = (pos[0] - current_row) / 2.0  # Max is +1
            height_gain = max(0, height_gain + 0.5)     # Shift to [0, 1]
            
            # Factor 2: Energy efficiency (prefer lower cost moves)
            efficiency = 1.0 / (1.0 + cost)  # Inverse cost, normalized
            
            # Factor 3: Future options (lookahead for dead ends)
            future_score = self._evaluate_future(wall, pos, self.energy - cost, 
                                                  depth=min(self.lookahead, 4))
            
            # Factor 4: Position quality (neighbors, escape routes)
            position_score = self._evaluate_position(wall, pos)
            
            # Combine factors
            # alpha: height vs efficiency trade-off
            # beta: future vs immediate trade-off
            immediate = self.alpha * height_gain + (1 - self.alpha) * efficiency
            strategic = self.beta * future_score + (1 - self.beta) * position_score
            
            score = 0.6 * immediate + 0.4 * strategic
            
            if score > best_score:
                best_score = score
                best_pos = pos
        
        return best_pos
    
    def _evaluate_future(
        self,
        wall: LatticeWall,
        pos: Tuple[int, int],
        energy: float,
        depth: int
    ) -> float:
        """
        Look ahead to evaluate future prospects.
        
        Returns score in [0, 1] based on:
        - Can we keep climbing?
        - How high can we get?
        - Are there dead ends ahead?
        """
        if depth == 0 or energy <= 0:
            # Terminal: score based on height achieved
            return pos[0] / wall.height
        
        if wall.is_summit(pos[0]):
            return 1.0  # Summit is always good
        
        neighbors = wall.get_neighbors(pos[0], pos[1])
        
        if not neighbors:
            return 0.0  # Dead end
        
        # Find best future from this position
        best_future = 0.0
        n_viable = 0
        
        for next_pos in neighbors:
            cost = wall.get_cost(next_pos[0], next_pos[1])
            if energy >= cost:
                n_viable += 1
                future = self._evaluate_future(wall, next_pos, energy - cost, depth - 1)
                best_future = max(best_future, future)
        
        # Penalize positions with few options
        option_bonus = min(n_viable / 4.0, 1.0) * 0.2
        
        return best_future * 0.8 + option_bonus
    
    def _evaluate_position(
        self,
        wall: LatticeWall,
        pos: Tuple[int, int]
    ) -> float:
        """
        Evaluate position quality.
        
        Considers:
        - Number of escape routes
        - Quality of surrounding holds
        - Presence of rest potential
        """
        neighbors = wall.get_neighbors(pos[0], pos[1])
        
        if not neighbors:
            return 0.0
        
        # Count viable neighbors
        n_neighbors = len(neighbors)
        
        # Average quality of neighbors
        qualities = [wall.get_quality(n[0], n[1]) for n in neighbors]
        avg_quality = np.mean(qualities) if qualities else 0
        
        # Check for rest potential (any jug nearby?)
        has_rest = any(q > 0.7 for q in qualities)
        rest_bonus = 0.2 if has_rest else 0
        
        # Combine
        escape_score = min(n_neighbors / 5.0, 1.0)
        quality_score = avg_quality
        
        return 0.4 * escape_score + 0.4 * quality_score + 0.2 * (1 if has_rest else 0)
    
    def execute_move(self, wall: LatticeWall, target: Tuple[int, int]) -> bool:
        """Execute move to target position."""
        if self.status != ClimberStatus.CLIMBING:
            return False
        
        cost = wall.get_cost(target[0], target[1])
        
        if self.energy < cost:
            self.status = ClimberStatus.PUMPED
            return False
        
        # Record move
        record = MoveRecord(
            step=self.steps,
            from_pos=self.position,
            to_pos=target,
            cost=cost,
            energy_before=self.energy,
            energy_after=self.energy - cost,
            height_gain=target[0] - self.position[0],
            lateral_move=np.sign(target[1] - self.position[1])
        )
        self.move_history.append(record)
        
        # Update state
        self.energy -= cost
        self.total_cost += cost
        self.position = target
        self.path.append(target)
        self.energy_history.append(self.energy)
        self.steps += 1
        
        # Check summit
        if wall.is_summit(target[0]):
            self.status = ClimberStatus.TOPPED
            self.time_to_top = self.steps
        
        return True
    
    def step(self, wall: LatticeWall) -> bool:
        """Execute one decision-action cycle."""
        if self.status != ClimberStatus.CLIMBING:
            return False
        
        target = self.decide_move(wall)
        
        if target is None:
            return False
        
        return self.execute_move(wall, target)
    
    def get_height(self) -> int:
        """Current height (row)."""
        return self.position[0]
    
    def copy(self) -> 'Climber':
        """Create copy of climber."""
        return Climber(
            name=self.name,
            energy=self.max_energy,
            policy=self.policy.value,
            lookahead=self.lookahead,
            alpha=self.alpha,
            beta=self.beta,
            color=self.color
        )
    
    def __repr__(self) -> str:
        return (f"Climber('{self.name}', {self.policy.value}, "
                f"E={self.energy:.1f}/{self.max_energy:.1f}, "
                f"pos={self.position}, {self.status.value})")
