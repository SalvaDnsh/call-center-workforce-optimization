# Mathematical formulation

The model describes a repeating day. Hours and shift-start times are indexed by
$H=\{0,\ldots,23\}$, with arithmetic modulo 24. Clients are indexed by $c$.

## Shift activity and costs

A shift starting at $j$ is productive at offsets $\{0,1,2,4,5,6\}$.
Its break is at offset 3. Define $A_{tj}=1$ if $(t-j)\bmod24$ belongs to those productive offsets, and 0 otherwise.

The full seven-hour shift is paid. If $w_h=18$ for $9\le h<17$ and $w_h=27$ otherwise, its cost is

$$C_j=\sum_{r=0}^{6}w_{(j+r)\bmod24}.$$

For example, $C_{15}=2(18)+5(27)=171$. Break time contributes to pay, but does not contribute to productive coverage.

## Variables

| Symbol | Interpretation |
|---|---|
| $n_{cj}$ | Operators assigned to client $c$ whose shift starts at hour $j$ |
| $s_{ct}$ | Staffing shortage for client $c$ at hour $t$ |
| $u_{ct}$ | Unpenalized upper-envelope variable for surplus staffing |

All 144 variables are nonnegative integers. Active coverage is

$$q_{ct}=\sum_{j\in H}A_{tj}n_{cj}.$$

## Objective

$$\min\;\sum_{c,j}C_jn_{cj}+\sum_{c,t}P_{ct}s_{ct}.$$

For Parsian, $P_{ct}=60$ between 07:00 and 18:00 (hours 7 through 17), and 30 otherwise. For Mehr Iranian, it is 45 at every hour.

## Constraints

$$\sum_c n_{cj}\le100\qquad\forall j,$$

$$80\le\sum_cq_{ct}\le420\qquad\forall t,$$

$$d_{ct}-s_{ct}\le q_{ct}\le d_{ct}+u_{ct}\qquad\forall c,t,$$

$$0\le s_{ct}\le10\qquad\forall c,t,$$

$$\sum_ts_{\mathrm{Parsian},t}\le40,\qquad
\sum_ts_{\mathrm{Mehr},t}\le30.$$

The Python matrix represents these as 146 rows with lower/upper row bounds, plus variable bounds. A solver may expand a row with two finite bounds into two inequalities.

The surplus inequalities match the submitted formulation. Because surplus has no objective cost, the raw $u$ values are not unique and need not equal actual surplus. Exported baseline surplus is normalized to $\max(q-d,0)$; this preserves feasibility and cost. Positive shortage penalties make optimal shortages equal $\max(d-q,0)$.

Daily shortage is a sum over hourly shortfalls, so its unit is operator-hours. The model counts shift assignments rather than named employees. It does not model stochastic calls, waiting-time distributions, individual qualifications, or multi-day rostering.

## What the scenario checks mean

Let $v^0$ denote the exported baseline decision vector. For each sampled parameter value $\theta$, the program independently solves the modified integer program and tests:

1. Is $v^0$ feasible under the modified constraints?
2. If feasible, does its modified cost equal the certified optimum to numerical tolerance?

If both hold, the same complete reference vector remains optimal at that sampled value. Another optimal vector may also exist. This check differs from preserving only the zero/nonzero pattern of a subset of variables. It also differs from classical LP basis sensitivity: integer programs do not have the same basis-based sensitivity interpretation.

The 04:00 experiment changes $C_4$ for both clients simultaneously. It is a direct coefficient perturbation. If an underlying hourly pay rate changes, several overlapping shift costs would change, which is a different experiment.
