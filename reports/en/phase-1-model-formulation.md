# Phase 1 — Mathematical formulation

**Call Center Workforce Optimization**  
Operations Research II · Sharif University of Technology · Fall 1404 (2025)  
Collaborative undergraduate course project

[Report index](../README.md) · [Next: Python implementation](phase-2-python-implementation.md)

## Abstract

This project formulates a daily staffing problem for a call-center provider serving two client organizations, Parsian and Mehr Iranian. Operators begin shifts at hourly intervals and remain assigned to one client for the shift. Each shift contains six working hours and one paid break. An integer linear program chooses shift starts to minimize wages and penalties for unmet staffing demand. Shift-start capacity, hourly operating capacity and client-specific shortage limits restrict the allocation. The formulation represents a repeating 24-hour day and accounts explicitly for shifts crossing midnight.

## 1. Case definition and planning assumptions

Iran Telecom is the service provider in the course case. Its two clients have different hourly staffing requirements and shortage penalties. The planning decision is the number of operators assigned to each client at each possible shift-start time. Staffing requirements are given as operator counts for each one-hour interval.

The case uses the following assumptions:

1. A shift can start at any hour from 00:00 through 23:00.
2. A shift lasts seven consecutive hours: three working hours, one paid break and three further working hours.
3. An operator serves the same client throughout a shift.
4. The daily pattern repeats, so a late shift contributes to coverage after midnight.
5. Wages depend on the clock hour being paid. The break is paid at the corresponding hourly rate.
6. Staffing shortages incur a monetary penalty and must satisfy both hourly and daily limits.

The input data describe the classroom case. The resulting schedule is an aggregate staffing plan, expressed as operator-shift assignments.

## 2. Indices and input parameters

Let $H=\{0,1,\ldots,23\}$ denote both one-hour intervals and possible shift-start times. Hour $t$ means the interval beginning at $t$: for example, $t=7$ is 07:00–08:00. All clock-hour arithmetic is modulo 24. Let $C=\{\mathrm{Parsian},\mathrm{Mehr}\}$ be the client set.

| Parameter | Meaning | Value or source |
| --- | --- | --- |
| $d_{ct}$ | Required operators for client $c$ in hour $t$ | Hourly demand table below |
| $w_t$ | Wage per paid operator-hour | 18 for $9\le t<17$; 27 otherwise |
| $P_{\mathrm{Parsian},t}$ | Penalty per operator-hour of Parsian shortage | 60 for $7\le t<18$; 30 otherwise |
| $P_{\mathrm{Mehr},t}$ | Penalty per operator-hour of Mehr Iranian shortage | 45 at every hour |
| $B$ | Maximum combined shift starts at any hour | 100 operators |
| $L,U$ | Minimum and maximum combined active coverage | 80 and 420 operators |
| $S$ | Maximum shortage per client in any hour | 10 operators |
| $D_{\mathrm{Parsian}}$ | Parsian daily shortage allowance | 40 operator-hours |
| $D_{\mathrm{Mehr}}$ | Mehr Iranian daily shortage allowance | 30 operator-hours |

Wages, penalties and total costs use the monetary unit specified by the case. The wage window and the Parsian penalty window are separate parameters.

### Hourly staffing demand

| Hour beginning | Parsian | Mehr Iranian |
| --- | --- | --- |
| 00:00 | 120 | 70 |
| 01:00 | 95 | 40 |
| 02:00 | 90 | 20 |
| 03:00 | 50 | 30 |
| 04:00 | 30 | 50 |
| 05:00 | 30 | 40 |
| 06:00 | 60 | 40 |
| 07:00 | 110 | 90 |
| 08:00 | 140 | 110 |
| 09:00 | 200 | 110 |
| 10:00 | 180 | 110 |
| 11:00 | 180 | 130 |
| 12:00 | 240 | 150 |
| 13:00 | 220 | 160 |
| 14:00 | 220 | 120 |
| 15:00 | 230 | 130 |
| 16:00 | 250 | 160 |
| 17:00 | 260 | 180 |
| 18:00 | 230 | 200 |
| 19:00 | 250 | 170 |
| 20:00 | 260 | 140 |
| 21:00 | 250 | 110 |
| 22:00 | 220 | 100 |
| 23:00 | 190 | 90 |

Machine-readable inputs are provided in [hourly_demand.csv](../../data/hourly_demand.csv) and [parameters.json](../../data/parameters.json).

## 3. Shift activity and paid cost

The productive offsets within a shift are

$$R=\{0,1,2,4,5,6\}.$$

Define the activity coefficient

$$
A_{tj}=\begin{cases}
1,&(t-j)\bmod24\in R,\\
0,&\text{otherwise}.
\end{cases}
$$

Thus, a shift starting at 22:00 contributes working time at 22:00, 23:00, 00:00, 02:00, 03:00 and 04:00, with a paid break at 01:00. This cyclic definition accounts for coverage at the beginning of the modeled day from shifts that started on the preceding repetition of the day.

All seven hours contribute to the shift cost:

$$C_j=\sum_{r=0}^{6}w_{(j+r)\bmod24}.$$

For a shift beginning at 15:00, two paid hours fall in the lower-wage window and five in the higher-wage window:

$$C_{15}=2(18)+5(27)=171.$$

The break therefore contributes to wages while contributing zero active coverage. Separating the cost calculation from the activity matrix preserves this distinction.

## 4. Decision variables

| Variable | Definition | Unit |
| --- | --- | --- |
| $n_{cj}$ | Operators assigned to client $c$ whose shifts start at $j$ | Operator-shift assignments |
| $s_{ct}$ | Staffing shortage for client $c$ in hour $t$ | Operators in that hour |
| $u_{ct}$ | Upper-envelope allowance for surplus coverage | Operators in that hour |

All variables are nonnegative integers. There are $2\times24=48$ variables of each type, giving 144 variables in total. Active coverage is a derived quantity:

$$q_{ct}=\sum_{j\in H}A_{tj}n_{cj}.$$

For example, increasing a single $n_{cj}$ by one increases client $c$'s coverage by one at six productive hours and leaves the break-hour coverage unchanged.

## 5. Objective function

The objective minimizes the total daily cost:

$$\min Z=\sum_{c\in C}\sum_{j\in H}C_jn_{cj}+\sum_{c\in C}\sum_{t\in H}P_{ct}s_{ct}.$$

The first term is shift pay, including paid breaks. The second term is the penalty for hourly staffing shortfalls. The daily shortage allowance limits the amount of shortfall the optimizer can accept even when paying a penalty would otherwise be cheaper than adding a shift.

## 6. Constraints

### 6.1. Shift-start capacity

At most 100 operators may start at the same hour across the two clients:

$$\sum_{c\in C}n_{cj}\le100\qquad\forall j\in H.$$

This limit applies to shift starts rather than the number already working.

### 6.2. Hourly active capacity

Combined productive coverage must remain between 80 and 420:

$$80\le\sum_{c\in C}q_{ct}\le420\qquad\forall t\in H.$$

Operators on the paid break are excluded from this count through $A_{tj}$.

### 6.3. Demand coverage

Each client's coverage is bounded relative to demand by its shortage and surplus variables:

$$d_{ct}-s_{ct}\le q_{ct}\le d_{ct}+u_{ct}\qquad\forall c\in C,\ t\in H.$$

Positive shortage penalties make the cost-minimizing shortage equal to $\max(d_{ct}-q_{ct},0)$. The unpenalized surplus variable can be any sufficiently large feasible upper envelope. For reporting, actual surplus is calculated directly as $\max(q_{ct}-d_{ct},0)$.

### 6.4. Hourly and daily shortage limits

$$0\le s_{ct}\le10\qquad\forall c\in C,\ t\in H,$$

$$\sum_{t\in H}s_{\mathrm{Parsian},t}\le40,$$

$$\sum_{t\in H}s_{\mathrm{Mehr},t}\le30.$$

Daily shortage is the sum of one-hour staffing shortfalls. Its unit is operator-hours: a shortage of five operators in each of two hours contributes ten operator-hours.

### 6.5. Integrality

$$n_{cj},s_{ct},u_{ct}\in\mathbb Z_{\ge0}.$$

Integer shift assignments reflect the indivisibility of operators. The formulation jointly evaluates the coverage created by overlapping shifts and the associated service penalties.

## 7. Model interpretation and handoff

The formulation links each operational rule to a distinct model component. The activity matrix handles working time and breaks; hourly wages determine complete shift costs; shortage variables quantify unmet client demand; and capacity and service-level bounds define feasible schedules. This separation also supports controlled experiments in which a single parameter changes while the remaining case data stay fixed.

The [second report](phase-2-python-implementation.md) explains how these equations become a solver model and presents the baseline staffing plan. The [third report](phase-3-gams-and-scenario-analysis.md) develops the GAMS representation and interprets the parameter experiments.

## Supporting material

- [Compact mathematical reference](../../docs/model.md)
- [Input data](../../data/hourly_demand.csv)
- [Supplementary Persian phase 1 report](../original/phase_1_report_fa.pdf)
