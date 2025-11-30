# `adimanusia`: **Lattice Climbing Agent-Based Model**

> *"He who would learn to fly one day must first learn to walk and run and climb and dance; one cannot fly into flying."*  
> — Friedrich Nietzsche, *Thus Spoke Zarathustra*

---

## What is This?

`adimanusia` simulates **decision-making under constraint** using rock climbing as a metaphor. Two AI agents with identical energy budgets attempt the same route. One follows instinct (Greedy), the other thinks ahead (Prudent). The question: **who tops out?**

This isn't just a climbing simulator—it's a study in how **local optimization fails** when resources are finite and terrain is deceptive.

---

## The Core Insight

Consider two strategies for the same problem:

| Strategy | Philosophy | Outcome |
|----------|------------|---------|
| **Greedy** | "Grab the best hold in front of me" | Fast start, often stranded |
| **Prudent** | "What does this move cost me later?" | Slower, but summits |

The Greedy climber maximizes *immediate comfort*. The Prudent climber maximizes *terminal height*. With equal energy, different philosophies yield radically different results.

---

## Installation

```bash
git clone https://github.com/sandyherho/adimanusia.git
cd adimanusia
pip install -e .
```

## Quick Start

```bash
# Run all four test scenarios
adimanusia --all

# Run individual cases
adimanusia case1   # The Pump Clock (endurance)
adimanusia case2   # The Crux Roulette (risk selection)
adimanusia case3   # The Labyrinth (route-finding)
adimanusia case4   # The Redpoint Crux (energy conservation)
```

---

## The Model

### State Space

Each climber exists in a state $s_t = (r, c, E)$ where:

- $r$ = row (height on the wall)
- $c$ = column (lateral position)
- $E$ = remaining energy

The wall is an $H \times W$ grid. Start at the bottom, goal is the top.

### Hold Quality

Every position has a **quality** $q \in [0, 1]$ representing how good the hold is:

| Quality | Hold Type | What It Means |
|---------|-----------|---------------|
| $q = 1.0$ | Jug | "Thank God" holds—rest here |
| $q = 0.5$ | Moderate | Solid but not restful |
| $q = 0.25$ | Crimp | Small edges, burns energy fast |
| $q = 0.1$ | Sloper | Desperate friction moves |
| $q = 0$ | Blank | No hold—can't go there |

### The Cost Function

Moving to a hold costs energy inversely proportional to its quality:

$$C(r, c) = \frac{1}{q(r, c)}$$

A jug ($q = 1$) costs 1 energy. A sloper ($q = 0.1$) costs 10. Blank rock is impassable.

**This is the crux of the model**: good holds are cheap, bad holds are expensive. A route full of jugs that dead-ends wastes less energy *per move* but may waste *all* your energy if you can't continue.

### Movement

Climbers move on an 8-connected grid (up, diagonal, or traverse—no downclimbing):

$$\mathcal{A}(r, c) = \{(r', c') : r' \in \{r, r+1\}, \; |c' - c| \leq 1, \; (r', c') \neq (r, c)\}$$

A move is valid only if:
1. The destination has holds ($q \geq 0.08$)
2. You can afford it ($E \geq C$)

### Termination

The simulation ends when:

| Status | Condition | Meaning |
|--------|-----------|---------|
| **Topped Out** | $r = H - 1$ | Success! Clipped the chains. |
| **Stuck** | No neighbors exist | Climbed into a dead-end |
| **Pumped Off** | Can't afford any move | Out of gas |

---

## Decision Policies

### The Greedy Climber

*"Take the jug."*

$$\pi_G(s) = \arg\max_{a \in \mathcal{A}_{valid}} \; q(a)$$

Always moves to the highest-quality available hold. Tie-breaker: prefer upward movement, then stay in line.

**Strengths**: Fast decisions, minimal computation, feels good in the moment.

**Weaknesses**: Follows "sucker sequences" into dead-ends, poor energy pacing, no awareness of what's ahead.

### The Prudent Climber

*"What does this cost me in 5 moves?"*

$$\pi_P(s) = \arg\max_{a \in \mathcal{A}_{valid}} \; U(a)$$

Where the utility function balances multiple factors:

$$U(a) = (1 - \beta)\left[\alpha \cdot H(a) + (1 - \alpha) \cdot \epsilon(a)\right] + \beta \cdot F(a)$$

**Components:**

1. **Height gain** $H(a)$: Progress toward the summit
   $$H(a) = \frac{r' - r + 1}{2}$$

2. **Energy efficiency** $\epsilon(a)$: Cost-awareness
   $$\epsilon(a) = \frac{1}{1 + C(a)}$$

3. **Future score** $F(a)$: Lookahead evaluation (recursive)
   $$F(a) = \max_{a' \in \mathcal{A}_{valid}(a)} F(a'), \quad F_{terminal} = \frac{r}{H}$$

**Parameters:**
- $\alpha \in [0,1]$: Height vs. efficiency trade-off
- $\beta \in [0,1]$: Immediate vs. future weighting
- $k$: Lookahead depth (typically 4-6 moves)

**Strengths**: Avoids traps, paces energy, reads the route.

**Weaknesses**: Computationally heavier, can be overly cautious.

---

## The Four Scenarios

Each scenario tests a different aspect of decision-making:

### Case 1: The Pump Clock (5.11c)

*An endurance test. Two lines, same energy budget.*

- **Left line**: Starts with jugs, gets progressively harder, dead-ends at 60%
- **Right line**: Sustained moderate climbing with periodic rests

**What it tests**: Energy pacing. The Greedy climber sprints up the jugs and flames out. The Prudent climber takes the "harder" line and summits with energy to spare.

### Case 2: The Crux Roulette (5.12a)

*Three ways through the hard part. Choose wisely.*

- **The Dyno**: One desperate move (cost ~10), easy after
- **The Tech Fest**: Five hard moves (cost ~4 each = 20 total)
- **The Sandbag**: Eight "easy-looking" moves (actually cost ~3.5 each = 28 total)

**What it tests**: Risk assessment. The Greedy climber takes the Sandbag (looks easiest), burns too much energy. The Prudent climber calculates total cost and takes the Dyno.

### Case 3: The Labyrinth (5.11b)

*A maze of holds. Dead-ends everywhere.*

- Obvious jug ladders that lead nowhere
- Hidden traverses that unlock the route
- One true path through the chaos

**What it tests**: Route-reading. The Greedy climber follows the jugs into traps. The Prudent climber's lookahead detects dead-ends and finds the hidden line.

### Case 4: The Redpoint Crux (5.12b)

*Everything leads to THE sequence.*

- Warm-up terrain with two pacing options
- A rest before the crux
- Three micro-beta choices through the crux
- Whoever conserved energy wins

**What it tests**: Strategic conservation. Both climbers face the same crux, but the Prudent climber arrives with more energy because they didn't waste it on the approach.

---

## Performance Metrics

| Metric | Formula | Meaning |
|--------|---------|---------|
| Height efficiency | $\eta = \frac{r_{final}}{H - 1}$ | How high did you get? (1.0 = summit) |
| Energy efficiency | $\rho = \frac{r_{final}}{E_{used}}$ | Height gained per energy spent |
| Success | $\sigma \in \{0, 1\}$ | Did you top out? |
| Time to top | $\tau$ | Steps to reach summit (if successful) |

---

## Output Formats

| Format | Contents | Use Case |
|--------|----------|----------|
| **CSV** | Trajectories, metrics, wall data | Spreadsheet analysis |
| **NetCDF** | Complete simulation state | Scientific workflows |
| **PNG** | Static summary plot | Papers, presentations |
| **GIF** | Animated climb sequence | Visualization, teaching |

---


## The Deeper Question

This model asks: **when does local optimization fail?**

The Greedy climber isn't stupid—grabbing good holds is rational. But rationality at each step doesn't guarantee rationality overall. The Prudent climber sacrifices immediate comfort for global success.

In climbing, this is called "reading the route." In life, it's called wisdom.


---

## For Researchers

This framework generalizes to any constrained sequential decision problem:

- **State**: Position + resource level
- **Actions**: Local moves with position-dependent costs  
- **Constraint**: Finite resource budget
- **Objective**: Maximize terminal position

The climbing metaphor makes the dynamics intuitive, but the math applies to energy systems, financial planning, logistics, and any domain where local greedy choices can lead to global suboptimality.

Key parameters to explore:
- Lookahead depth $k$: How far ahead matters?
- Weight $\alpha$: Progress vs. efficiency trade-off
- Weight $\beta$: Myopic vs. strategic balance
- Wall topology: How do trap structures affect outcomes?

---

## Citation

If you use this work, please cite:

```bibtex
@software{adimanusia2025,
  author = {Herho, Sandy H. S. and Sembiring-Milala, Freden M.},
  title = {adimanusia: Lattice Climbing Agent-Based Model},
  year = {2025},
  url = {https://github.com/sandyherho/adimanusia}
}
```

---

## License

MIT License

---

## Authors

**Sandy H. S. Herho**  
Department of Earth and Planetary Sciences, University of California, Riverside  
sandy.herho@email.ucr.edu

**Freden M. Sembiring-Milala**  
Indonesian Big Wall Expedition (IBEX)
