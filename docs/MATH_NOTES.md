# adimanusia: Mathematical Notes

## 1. State Space

$$s_t = (r_t, c_t, E_t) \in \mathbb{Z}^+ \times \mathbb{Z}^+ \times \mathbb{R}^+$$

- $r$: row (height), $c$: column (lateral position), $E$: energy
- Grid dimensions: $H \times W$ (height × width)
- Initial state: $s_0 = (0, c_0, E_0)$
- Terminal state: $r = H-1$ (summit)

---

## 2. Hold Quality Field

Quality function $q: \mathbb{Z}^2 \to [0,1]$

$$q(r,c) = \begin{cases} 1.0 & \text{jug (excellent)} \\ 0.5 & \text{moderate} \\ 0.25 & \text{crimp (hard)} \\ 0.1 & \text{sloper (desperate)} \\ 0 & \text{blank (impassable)} \end{cases}$$

---

## 3. Cost Function

Energy cost to move to position $(r,c)$:

$$C(r,c) = \frac{1}{q(r,c)}, \quad q > 0$$

$$C(r,c) = \infty, \quad q = 0$$

---

## 4. Action Space

8-connected movement (no downclimbing):

$$\mathcal{A}(r,c) = \{(r',c') : r' \in \{r, r+1\}, \; c' \in \{c-1, c, c+1\}, \; (r',c') \neq (r,c)\}$$

Valid actions filtered by:

$$\mathcal{A}_{valid}(s) = \{a \in \mathcal{A}(r,c) : q(a) \geq q_{min} \;\land\; E \geq C(a)\}$$

where $q_{min} = 0.08$ (passability threshold).

---

## 5. Transition Dynamics

State transition after action $a = (r', c')$:

$$s_{t+1} = (r', c', E_t - C(r', c'))$$

Energy evolution:

$$E_{t+1} = E_t - C(r_{t+1}, c_{t+1})$$

---

## 6. Termination Conditions

$$\text{Status} = \begin{cases} \texttt{TOPPED} & r_t = H-1 \\ \texttt{STUCK} & \mathcal{A}(r_t, c_t) = \emptyset \\ \texttt{PUMPED} & \mathcal{A}_{valid}(s_t) = \emptyset \;\land\; \mathcal{A}(r_t,c_t) \neq \emptyset \\ \texttt{CLIMBING} & \text{otherwise} \end{cases}$$

---

## 7. Decision Policies

### 7.1 Greedy Policy

$$\pi_G(s) = \underset{a \in \mathcal{A}_{valid}(s)}{\arg\max} \; q(a)$$

Tie-breaker: prefer $\max(r')$, then $\min(|c' - c|)$.

### 7.2 Prudent Policy

$$\pi_P(s) = \underset{a \in \mathcal{A}_{valid}(s)}{\arg\max} \; U(a)$$

Utility function:

$$U(a) = \lambda_1 \cdot H(a) + \lambda_2 \cdot \epsilon(a) + \lambda_3 \cdot F(a) + \lambda_4 \cdot P(a)$$

where $\lambda_1 + \lambda_2 + \lambda_3 + \lambda_4 = 1$.

**Component definitions:**

**(i) Height gain** (normalized):
$$H(a) = \frac{r' - r + 1}{2}, \quad H \in [0,1]$$

**(ii) Energy efficiency**:
$$\epsilon(a) = \frac{1}{1 + C(a)}, \quad \epsilon \in (0,1)$$

**(iii) Future score** (k-step lookahead):
$$F(a) = \max_{a' \in \mathcal{A}_{valid}(a)} \left[ \frac{r'}{H} \cdot \mathbb{1}_{[k=0]} + F(a') \cdot \mathbb{1}_{[k>0]} \right]$$

with recursion depth $k$ and energy propagation $E' = E - C(a)$.

**(iv) Position quality** (escape routes):
$$P(a) = \frac{|\mathcal{A}_{valid}(a)|}{8} \cdot \bar{q}(\mathcal{N}(a))$$

where $\bar{q}(\mathcal{N})$ is mean neighbor quality.

---

## 8. Parameterization

Prudent policy uses:
- $\alpha \in [0,1]$: height vs. efficiency trade-off
- $\beta \in [0,1]$: future vs. immediate trade-off
- $k \in \mathbb{Z}^+$: lookahead depth

Simplified utility:

$$U(a) = (1-\beta)\left[\alpha \cdot H(a) + (1-\alpha) \cdot \epsilon(a)\right] + \beta \cdot F(a)$$

---

## 9. Performance Metrics

**Height efficiency**:
$$\eta = \frac{r_{final}}{H-1} \in [0,1]$$

**Energy efficiency**:
$$\rho = \frac{r_{final}}{E_0 - E_{final}} = \frac{r_{final}}{E_{used}}$$

**Success indicator**:
$$\sigma = \mathbb{1}_{[r_{final} = H-1]} \in \{0,1\}$$

**Path length**:
$$L = |\{s_0, s_1, \ldots, s_T\}| = T + 1$$

**Time to summit** (if successful):
$$\tau = \min\{t : r_t = H-1\}$$

---

## 10. Total Energy Expenditure

For trajectory $\{(r_0,c_0), (r_1,c_1), \ldots, (r_T,c_T)\}$:

$$E_{total} = \sum_{t=1}^{T} C(r_t, c_t) = \sum_{t=1}^{T} \frac{1}{q(r_t, c_t)}$$

Constraint: $E_{total} \leq E_0$

---

## 11. Scenario Configurations

| Case | $H$ | $W$ | $E_0$ | Challenge |
|------|-----|-----|-------|-----------|
| Pump Clock | 40 | 20 | 150 | Sustained pacing |
| Crux Roulette | 40 | 20 | 130 | Risk selection |
| Labyrinth | 40 | 20 | 200 | Route-finding |
| Redpoint Crux | 40 | 20 | 100 | Energy conservation |

---

## 12. Key Insight

Local optimality $\neq$ Global optimality:

$$\sum_{t} \max_a q(a_t) \not\Rightarrow \max \sum_t r_t$$

Greedy maximizes immediate quality; Prudent maximizes terminal height.

---

## Summary Table

| Symbol | Definition |
|--------|------------|
| $s = (r,c,E)$ | State (row, column, energy) |
| $q(r,c)$ | Hold quality ∈ [0,1] |
| $C(r,c) = 1/q$ | Movement cost |
| $\mathcal{A}(s)$ | Action space |
| $\pi_G$ | Greedy policy |
| $\pi_P$ | Prudent policy |
| $\eta$ | Height efficiency |
| $\rho$ | Energy efficiency |
| $\sigma$ | Success indicator |
| $k$ | Lookahead depth |
| $\alpha, \beta$ | Policy weights |
