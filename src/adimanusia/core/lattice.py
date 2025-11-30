"""
Lattice Wall Environment - Realistic Climbing Route Simulation.

Implements authentic climbing features using proper terminology:
    - Jugs: Large positive holds (low cost)
    - Crimps: Small edges requiring finger strength (high cost)
    - Slopers: Rounded holds requiring friction (very high cost)
    - Pinches: Holds requiring thumb opposition (medium-high cost)
    - Pockets: Holes in rock (variable cost)
    - Rails: Horizontal edges (medium cost)
    - Rest stances: No-hands rests or good stances
    - Crux: Hardest section of a route
    - Redpoint crux: The move that typically causes falls
    - Dyno: Dynamic move requiring commitment
    - Traverse: Horizontal movement
    - Stemming corner: Using opposing walls
    - Roof: Horizontal overhang section
    - Arete: Outside corner feature
    - Dihedral: Inside corner (book shape)

Cost model: C(hold) = 1 / quality
    - Quality 1.0 = Jug (cost 1)
    - Quality 0.5 = Rail (cost 2)  
    - Quality 0.25 = Crimp (cost 4)
    - Quality 0.1 = Sloper (cost 10)
"""

import numpy as np
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass


@dataclass
class RouteFeature:
    """A named feature on the wall."""
    name: str
    row_start: int
    row_end: int
    col_start: int
    col_end: int
    quality: float
    description: str = ""


class LatticeWall:
    """
    2D Lattice climbing wall with realistic route features.
    
    Grid is (height x width) where:
        - Row 0 is ground level
        - Row height-1 is the summit/anchors
        - Columns represent horizontal positions
    
    Each cell contains a quality value q ∈ [0, 1]:
        - q = 0: Blank rock (impassable)
        - q ∈ (0, 0.15]: Desperate moves
        - q ∈ (0.15, 0.3]: Hard crimps/slopers  
        - q ∈ (0.3, 0.5]: Moderate holds
        - q ∈ (0.5, 0.8]: Good holds
        - q ∈ (0.8, 1.0]: Jugs and rests
    """
    
    # Hold quality constants (climbing terminology)
    HOLD_JUG = 1.0              # "Thank God" hold
    HOLD_GOOD_JUG = 0.9         # Solid jug
    HOLD_BUCKET = 0.8           # Large positive hold
    HOLD_RAIL = 0.6             # Horizontal edge
    HOLD_LEDGE = 0.55           # Small ledge
    HOLD_POCKET = 0.5           # Two-finger pocket
    HOLD_PINCH = 0.4            # Requires thumb
    HOLD_CRIMP = 0.3            # Small edge
    HOLD_BAD_CRIMP = 0.25       # Marginal crimp
    HOLD_SLOPER = 0.2           # Friction dependent
    HOLD_BAD_SLOPER = 0.15      # Desperate sloper
    HOLD_DESPERATE = 0.12       # Nearly impossible
    HOLD_BLANK = 0.0            # No hold
    
    # Terrain quality
    TERRAIN_SLAB = 0.45         # Less than vertical
    TERRAIN_VERTICAL = 0.35     # Straight up
    TERRAIN_OVERHANG = 0.25     # Slightly overhanging
    TERRAIN_STEEP = 0.2         # Very overhanging
    TERRAIN_ROOF = 0.15         # Horizontal
    
    PASSABLE_THRESHOLD = 0.08
    
    def __init__(
        self,
        height: int = 40,
        width: int = 20,
        base_terrain: float = 0.35,
        seed: Optional[int] = None
    ):
        """
        Initialize climbing wall.
        
        Args:
            height: Number of rows (vertical extent)
            width: Number of columns (horizontal extent)
            base_terrain: Default terrain quality
            seed: Random seed
        """
        self.height = height
        self.width = width
        self.base_terrain = base_terrain
        self.seed = seed
        
        if seed is not None:
            np.random.seed(seed)
        
        # Initialize with base terrain
        self.grid = np.full((height, width), base_terrain, dtype=np.float64)
        
        # Route metadata
        self.start_positions = [(0, width // 2)]
        self.scenario_name = "Custom Wall"
        self.scenario_description = ""
        self.features: List[RouteFeature] = []
        self.grade = "5.10"  # Climbing grade
    
    # =========================================================================
    # BASIC SETTERS
    # =========================================================================
    
    def set_hold(self, row: int, col: int, quality: float):
        """Place a single hold."""
        if 0 <= row < self.height and 0 <= col < self.width:
            self.grid[row, col] = np.clip(quality, 0.0, 1.0)
    
    def set_region(self, r1: int, r2: int, c1: int, c2: int, quality: float):
        """Set quality for rectangular region."""
        r1, r2 = max(0, r1), min(self.height, r2)
        c1, c2 = max(0, c1), min(self.width, c2)
        self.grid[r1:r2, c1:c2] = np.clip(quality, 0.0, 1.0)
    
    def set_column(self, col: int, quality: float, r1: int = 0, r2: Optional[int] = None):
        """Set quality for a column."""
        r2 = r2 if r2 else self.height
        self.set_region(r1, r2, col, col + 1, quality)
    
    def set_row(self, row: int, quality: float, c1: int = 0, c2: Optional[int] = None):
        """Set quality for a row."""
        c2 = c2 if c2 else self.width
        self.set_region(row, row + 1, c1, c2, quality)
    
    def add_feature(self, feature: RouteFeature):
        """Add a named route feature."""
        self.set_region(
            feature.row_start, feature.row_end,
            feature.col_start, feature.col_end,
            feature.quality
        )
        self.features.append(feature)
    
    def add_hold_line(self, positions: List[Tuple[int, int]], quality: float):
        """Add a line of holds at specified positions."""
        for r, c in positions:
            self.set_hold(r, c, quality)
    
    def add_jug_ladder(self, col: int, r1: int, r2: int, spacing: int = 2):
        """Add evenly spaced jugs up a column."""
        for r in range(r1, r2, spacing):
            self.set_hold(r, col, self.HOLD_JUG)
    
    def add_blank_section(self, r1: int, r2: int, c1: int, c2: int):
        """Create impassable blank rock."""
        self.set_region(r1, r2, c1, c2, self.HOLD_BLANK)
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    
    def get_quality(self, row: int, col: int) -> float:
        """Get hold quality at position."""
        if 0 <= row < self.height and 0 <= col < self.width:
            return self.grid[row, col]
        return 0.0
    
    def get_cost(self, row: int, col: int) -> float:
        """Get energy cost to use hold."""
        q = self.get_quality(row, col)
        if q < self.PASSABLE_THRESHOLD:
            return float('inf')
        return 1.0 / q
    
    def is_passable(self, row: int, col: int) -> bool:
        """Check if position has usable holds."""
        return self.get_quality(row, col) >= self.PASSABLE_THRESHOLD
    
    def is_valid(self, row: int, col: int) -> bool:
        """Check bounds and passability."""
        return (0 <= row < self.height and 
                0 <= col < self.width and 
                self.is_passable(row, col))
    
    def get_neighbors(self, row: int, col: int, allow_down: bool = False) -> List[Tuple[int, int]]:
        """
        Get valid moves from position.
        
        Standard climbing movement (8-connected, up or lateral):
            - Can move up-left, up, up-right
            - Can traverse left or right
            - Cannot downclimb unless allow_down=True
        """
        moves = []
        
        row_deltas = [-1, 0, 1] if allow_down else [0, 1]
        col_deltas = [-1, 0, 1]
        
        for dr in row_deltas:
            for dc in col_deltas:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if self.is_valid(nr, nc):
                    moves.append((nr, nc))
        
        return moves
    
    def is_summit(self, row: int) -> bool:
        """Check if at top of route."""
        return row >= self.height - 1
    
    # =========================================================================
    # SCENARIO 1: THE PUMP CLOCK
    # A race against fatigue - two routes with different pacing strategies
    # =========================================================================
    
    def set_pump_clock_scenario(self):
        """
        Case 1: The Pump Clock
        
        A sustained 40m route where energy management is critical.
        Two main line options:
        
        LEFT LINE (The Sprint): 
            - Starts with excellent holds (fast initial progress)
            - Gets progressively harder (pump builds)
            - Rest stance at 60% requires traversing right
            - Final headwall is sustained crimping
        
        RIGHT LINE (The Pacemaker):
            - Starts moderate (slower but sustainable)
            - Consistent difficulty throughout
            - Has small rests every ~8 moves
            - Direct finish on good holds
        
        The greedy climber takes the jugs and gets pumped out.
        The prudent climber paces and makes the anchors.
        """
        self.scenario_name = "The Pump Clock"
        self.scenario_description = (
            "40m endurance route. Left line starts easy but pumps out. "
            "Right line is sustained but paced. Who manages energy better?"
        )
        self.grade = "5.11c"
        self.height = 40
        self.width = 20
        
        # Resize grid
        self.grid = np.full((self.height, self.width), self.TERRAIN_VERTICAL, dtype=np.float64)
        
        # === LEFT LINE: The Sprint (columns 3-6) ===
        
        # Section 1 (rows 0-12): "The Warm-up Jugs"
        # Tempting big holds that burn energy fast
        self.add_feature(RouteFeature(
            "Warm-up Jugs", 0, 12, 3, 7, self.HOLD_BUCKET,
            "Big positive holds - too good to be true"
        ))
        
        # Section 2 (rows 12-20): "The Pump Zone"
        # Holds get worse as you're getting tired
        for r in range(12, 20):
            decay = 0.8 - (r - 12) * 0.05  # Progressive difficulty
            self.set_row(r, decay, c1=3, c2=7)
        
        # Section 3 (rows 20-25): "The Dead Point"
        # Very hard section - this is where sprinters fail
        self.add_feature(RouteFeature(
            "The Dead Point", 20, 26, 3, 7, self.HOLD_BAD_SLOPER,
            "Desperate slopers on tired arms"
        ))
        
        # Section 4 (rows 25-32): "The Traverse of Desperation"  
        # Must traverse right to find the rest
        self.set_row(25, self.HOLD_BLANK, c1=3, c2=10)  # Blank forces traverse
        self.set_row(26, self.HOLD_CRIMP, c1=6, c2=14)  # Thin traverse line
        
        # Section 5 (rows 32-40): "Final Headwall"
        # Sustained climbing to anchors
        self.set_region(32, 40, 10, 15, self.HOLD_CRIMP)
        
        # === RIGHT LINE: The Pacemaker (columns 13-17) ===
        
        # Consistent moderate terrain with periodic rests
        for r in range(0, 40):
            # Base difficulty
            self.set_row(r, self.HOLD_PINCH, c1=13, c2=18)
            
            # Rest stances every 8 moves (the secret to success)
            if r % 8 == 7:
                self.set_hold(r, 15, self.HOLD_GOOD_JUG)  # Rest stance
        
        # Final section slightly easier (reward for pacing)
        self.set_region(35, 40, 13, 18, self.HOLD_RAIL)
        
        # === CONNECTING FEATURES ===
        
        # Start ledge
        self.set_row(0, self.HOLD_LEDGE)
        
        # Summit anchors
        self.set_row(39, self.HOLD_JUG)
        
        # Cross-routes at key points
        self.set_row(10, self.HOLD_RAIL, c1=6, c2=14)  # Early escape
        
        self.start_positions = [(0, 5), (0, 15)]  # Left or right start
    
    # =========================================================================
    # SCENARIO 2: THE CRUX ROULETTE  
    # Multiple crux options - which gamble pays off?
    # =========================================================================
    
    def set_crux_roulette_scenario(self):
        """
        Case 2: The Crux Roulette
        
        A route with THREE different crux options at the 60% mark.
        Same energy budget - which risk/reward profile wins?
        
        LEFT CRUX (The Dyno): 
            - Single very hard move (cost 12)
            - Easy climbing before and after
            - High risk, high reward if you stick it
        
        CENTER CRUX (The Tech Fest):
            - 5 consecutive moderate-hard moves (cost 4 each = 20 total)
            - Consistent difficulty, no single stopper
            - Moderate risk, moderate reward
        
        RIGHT CRUX (The Sandbag):
            - Looks easy but hidden bad holds
            - 8 moves at cost 3.5 each = 28 total
            - Low apparent risk, actually worst option
        
        Above cruxes: All routes merge to same moderate finish.
        """
        self.scenario_name = "The Crux Roulette"
        self.scenario_description = (
            "Three crux options: The Dyno (one hard move), The Tech Fest "
            "(sustained technical), The Sandbag (looks easy, isn't). "
            "Choose wisely."
        )
        self.grade = "5.12a"
        self.height = 40
        self.width = 20
        
        self.grid = np.full((self.height, self.width), self.TERRAIN_VERTICAL, dtype=np.float64)
        
        # === LOWER SECTION (rows 0-20): Approach ===
        # Three parallel lines of similar difficulty
        
        # Left approach
        self.set_region(0, 20, 2, 6, self.HOLD_RAIL)
        
        # Center approach  
        self.set_region(0, 20, 8, 12, self.HOLD_RAIL)
        
        # Right approach
        self.set_region(0, 20, 14, 18, self.HOLD_RAIL)
        
        # === CRUX ZONE (rows 20-28) ===
        
        # Block off to force crux choices
        self.set_row(20, self.HOLD_BLANK)
        
        # LEFT: The Dyno (single desperate move)
        self.set_hold(20, 4, self.HOLD_DESPERATE)  # The dyno - cost ~10
        self.set_region(21, 28, 2, 6, self.HOLD_BUCKET)  # Easy after
        
        # CENTER: The Tech Fest (sustained technical)
        for r in range(20, 26):
            self.set_hold(r, 10, self.HOLD_BAD_CRIMP)  # 6 moves at cost 4
        self.set_region(26, 28, 8, 12, self.HOLD_RAIL)
        
        # RIGHT: The Sandbag (deceptively hard)
        for r in range(20, 28):
            # Looks like rails but they're actually bad slopers
            self.set_hold(r, 16, self.HOLD_SLOPER)  # 8 moves at cost 5
        
        # === UPPER SECTION (rows 28-40): Merge and Finish ===
        
        # Funnel back to center
        self.set_region(28, 32, 6, 14, self.HOLD_LEDGE)
        
        # Final headwall - same for all
        self.set_region(32, 40, 8, 12, self.HOLD_PINCH)
        
        # Summit
        self.set_row(39, self.HOLD_JUG)
        
        # Rest spots
        self.set_hold(19, 4, self.HOLD_JUG)   # Rest before left crux
        self.set_hold(19, 10, self.HOLD_JUG)  # Rest before center crux  
        self.set_hold(19, 16, self.HOLD_JUG)  # Rest before right crux
        
        self.start_positions = [(0, 10)]
    
    # =========================================================================
    # SCENARIO 3: THE LABYRINTH
    # Complex route-finding with dead ends and hidden shortcuts
    # =========================================================================
    
    def set_labyrinth_scenario(self):
        """
        Case 3: The Labyrinth
        
        A maze-like wall with multiple interconnected systems.
        Route-finding is as important as climbing ability.
        
        Features:
        - Dead-end jug hauls that look promising
        - Hidden traverse sequences
        - "Sucker holds" that lead nowhere
        - One optimal path through the maze
        - Multiple sub-optimal but viable paths
        
        The greedy climber follows jugs into dead ends.
        The prudent climber reads the route and finds the way.
        """
        self.scenario_name = "The Labyrinth"
        self.scenario_description = (
            "A maze of holds with dead ends, hidden traverses, and one true line. "
            "Route-reading matters as much as strength."
        )
        self.grade = "5.11b"
        self.height = 40
        self.width = 20
        
        # Start with mostly blank wall
        self.grid = np.full((self.height, self.width), self.HOLD_BLANK, dtype=np.float64)
        
        # === BUILD THE MAZE ===
        
        # Start area (rows 0-5): Wide ledge
        self.set_region(0, 3, 0, 20, self.HOLD_LEDGE)
        
        # --- TRAP 1: The Jug Ladder to Nowhere (left side) ---
        # Obvious jugs that dead-end
        for r in range(3, 18, 2):
            self.set_hold(r, 3, self.HOLD_JUG)
        self.set_hold(18, 3, self.HOLD_BLANK)  # Dead end!
        
        # --- TRAP 2: The Easy Ramp (center-left) ---
        # Diagonal of good holds leading to roof
        for i in range(12):
            self.set_hold(3 + i, 6 + i // 2, self.HOLD_RAIL)
        # Roof blocks progress
        self.set_region(15, 17, 8, 14, self.HOLD_BLANK)
        
        # --- THE TRUE PATH ---
        
        # Section 1: Start traverse right (rows 3-6)
        self.set_region(3, 6, 10, 18, self.HOLD_CRIMP)
        
        # Section 2: Up the right side (rows 6-15)
        self.set_region(6, 15, 16, 19, self.HOLD_PINCH)
        
        # Section 3: Traverse left under roof (row 15)
        self.set_row(15, self.HOLD_CRIMP, c1=8, c2=17)
        
        # Section 4: Break through via hidden pocket line (rows 16-22)
        self.add_hold_line([(16, 8), (17, 8), (18, 7), (19, 7), (20, 8), (21, 9), (22, 10)], 
                          self.HOLD_POCKET)
        
        # Section 5: Upper dihedral (rows 22-32)
        self.set_region(22, 32, 9, 13, self.HOLD_RAIL)
        
        # --- TRAP 3: False Summit (left branch from dihedral) ---
        self.set_region(28, 34, 4, 8, self.HOLD_BUCKET)
        self.set_region(34, 36, 4, 8, self.HOLD_BLANK)  # Capped by roof
        
        # --- TRUE FINISH ---
        
        # Section 6: Exit traverse (row 32)
        self.set_row(32, self.HOLD_PINCH, c1=12, c2=18)
        
        # Section 7: Final corner (rows 32-40)
        self.set_region(32, 40, 15, 18, self.HOLD_LEDGE)
        
        # Summit
        self.set_row(39, self.HOLD_JUG, c1=14, c2=19)
        
        # Key rest stances (rewards for route-finding)
        self.set_hold(14, 17, self.HOLD_JUG)   # Rest on right wall
        self.set_hold(22, 11, self.HOLD_JUG)   # Rest in dihedral
        self.set_hold(32, 16, self.HOLD_JUG)   # Rest before finish
        
        self.start_positions = [(1, 10)]
    
    # =========================================================================
    # SCENARIO 4: THE REDPOINT CRUX
    # One make-or-break sequence that defines success
    # =========================================================================
    
    def set_redpoint_crux_scenario(self):
        """
        Case 4: The Redpoint Crux
        
        A classic route with one infamous crux sequence.
        Everything leads up to 5 moves that define success or failure.
        
        Structure:
        - Rows 0-18: Warm-up terrain (moderate, sustainable)
        - Rows 18-20: Pre-crux rest ("The Shake-out")
        - Rows 20-25: THE CRUX (very hard, multiple path options)
        - Rows 25-28: Recovery holds
        - Rows 28-40: Cruise to anchors
        
        The crux has three micro-beta options:
        - Left: Two very hard moves (desperate + sloper)
        - Center: Three hard moves (all crimps)
        - Right: Four medium moves (sustained but safer)
        
        Energy conservation on the approach determines crux success.
        Route choice through crux determines final outcome.
        """
        self.scenario_name = "The Redpoint Crux"
        self.scenario_description = (
            "Classic testpiece. Everything leads to THE sequence at 2/3 height. "
            "Save enough gas for the crux, then pick your micro-beta."
        )
        self.grade = "5.12b"
        self.height = 40
        self.width = 20
        
        self.grid = np.full((self.height, self.width), self.TERRAIN_VERTICAL, dtype=np.float64)
        
        # === WARM-UP (rows 0-18) ===
        # Two options: cruise line (right) and pump line (left)
        
        # Pump line (left, cols 3-7): Good holds that waste energy
        self.set_region(0, 18, 3, 8, self.HOLD_BUCKET)
        
        # Cruise line (right, cols 12-17): Moderate but efficient
        self.set_region(0, 18, 12, 18, self.HOLD_PINCH)
        
        # Periodic small rests on cruise line
        for r in range(5, 18, 4):
            self.set_hold(r, 15, self.HOLD_RAIL)
        
        # Central scramble option (cols 8-12): Variable quality
        for r in range(0, 18):
            q = self.HOLD_RAIL if r % 3 == 0 else self.HOLD_CRIMP
            self.set_hold(r, 10, q)
        
        # === PRE-CRUX REST (rows 18-20): "The Shake-out" ===
        self.set_region(18, 21, 6, 14, self.HOLD_JUG)
        self.add_feature(RouteFeature(
            "The Shake-out", 18, 21, 6, 14, self.HOLD_JUG,
            "Last rest before the business"
        ))
        
        # === THE CRUX (rows 21-26) ===
        # Three micro-beta options
        
        # Block off everything else
        self.set_row(21, self.HOLD_BLANK)
        
        # LEFT BETA: Two desperate moves (high risk)
        self.set_hold(21, 5, self.HOLD_DESPERATE)   # Move 1: cost ~10
        self.set_hold(22, 5, self.HOLD_BAD_SLOPER)  # Move 2: cost ~6
        self.set_region(23, 27, 4, 7, self.HOLD_BUCKET)  # Easy after
        
        # CENTER BETA: Three hard crimps (medium risk)
        self.set_hold(21, 10, self.HOLD_BAD_CRIMP)  # Move 1: cost ~4
        self.set_hold(22, 10, self.HOLD_BAD_CRIMP)  # Move 2: cost ~4
        self.set_hold(23, 10, self.HOLD_BAD_CRIMP)  # Move 3: cost ~4
        self.set_region(24, 27, 9, 12, self.HOLD_RAIL)  # Moderate after
        
        # RIGHT BETA: Four sustained moves (lower risk, higher total cost)
        for r in range(21, 25):
            self.set_hold(r, 15, self.HOLD_CRIMP)  # 4 moves at cost ~3.3 = 13.3
        self.set_region(25, 27, 14, 17, self.HOLD_PINCH)  # Continued difficulty
        
        # === RECOVERY AND CRUISE (rows 27-40) ===
        
        # Merge point with good holds
        self.set_region(27, 30, 8, 14, self.HOLD_RAIL)
        
        # Final headwall - moderate sustained
        self.set_region(30, 40, 8, 14, self.HOLD_LEDGE)
        
        # Summit anchors
        self.set_row(39, self.HOLD_JUG)
        
        # Recovery rests
        self.set_hold(27, 11, self.HOLD_JUG)  # Post-crux recovery
        self.set_hold(35, 11, self.HOLD_JUG)  # Final rest
        
        self.start_positions = [(0, 10)]
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def copy(self) -> 'LatticeWall':
        """Deep copy of wall."""
        new_wall = LatticeWall(
            height=self.height,
            width=self.width,
            base_terrain=self.base_terrain,
            seed=self.seed
        )
        new_wall.grid = self.grid.copy()
        new_wall.start_positions = self.start_positions.copy()
        new_wall.scenario_name = self.scenario_name
        new_wall.scenario_description = self.scenario_description
        new_wall.features = self.features.copy()
        new_wall.grade = self.grade
        return new_wall
    
    def get_difficulty_profile(self) -> np.ndarray:
        """Get mean difficulty per row (for visualization)."""
        profile = np.zeros(self.height)
        for r in range(self.height):
            passable = self.grid[r, :] > self.PASSABLE_THRESHOLD
            if np.any(passable):
                profile[r] = np.mean(1.0 / self.grid[r, passable])
            else:
                profile[r] = float('inf')
        return profile
    
    def __repr__(self) -> str:
        return f"LatticeWall('{self.scenario_name}', {self.height}x{self.width}, {self.grade})"
