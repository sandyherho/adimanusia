# adimanusia

**Lattice Climbing Agent-Based Model**

*Greedy vs Prudent: Who reads the route better?*

## Overview

`adimanusia` is a Python library for simulating decision-making strategies on constrained lattice environments, inspired by rock climbing route-finding.

Two agents with **equal energy budgets** compete on realistic climbing scenarios:

- **Greedy Climber**: Always moves to the highest-quality hold (lowest cost)
- **Prudent Climber**: Uses lookahead to balance height gain, energy efficiency, and route-reading

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Run all scenarios
adimanusia --all

# Run specific case
adimanusia case1   # The Pump Clock
adimanusia case2   # The Crux Roulette  
adimanusia case3   # The Labyrinth
adimanusia case4   # The Redpoint Crux
```

## Scenarios

### Case 1: The Pump Clock (5.11c)
40m endurance route. Left line starts easy but pumps out. Right line is sustained but paced.

### Case 2: The Crux Roulette (5.12a)
Three crux options at 60% height:
- The Dyno: One desperate move
- The Tech Fest: Sustained technical climbing
- The Sandbag: Looks easy, isn't

### Case 3: The Labyrinth (5.11b)
Complex route-finding puzzle with dead ends, hidden traverses, and one true line.

### Case 4: The Redpoint Crux (5.12b)
Classic testpiece. Everything leads to THE sequence at 2/3 height.

## Model

### State Space
- Position: `(row, col)` on lattice
- Energy: remaining budget `E`

### Hold Quality
- `q = 1.0`: Jug (cost = 1)
- `q = 0.5`: Moderate (cost = 2)
- `q = 0.25`: Crimp (cost = 4)
- `q = 0.1`: Sloper (cost = 10)
- `q = 0.0`: Blank (impassable)

### Decision Policies

**Greedy**:
```
π_G(s) = argmax_a q(a)
```

**Prudent**:
```
π_P(s) = argmax_a [α·height_gain + (1-α)·efficiency + β·future_options]
```

## Output

- CSV: Trajectories, metrics, wall data
- NetCDF: Complete simulation data
- PNG: Static summary plots
- GIF: Animated climbing sequences

## Authors

- Sandy H. S. Herho (sandy.herho@email.ucr.edu)
- Freden M. Sembiring-Milala

## License

MIT License
