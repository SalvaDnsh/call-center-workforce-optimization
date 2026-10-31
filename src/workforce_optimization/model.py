"""One data source and one matrix formulation for all Python backends."""
from dataclasses import dataclass
from pathlib import Path
import csv
import json

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GROUPS = ("starts_parsian", "starts_mehr", "surplus_parsian",
          "shortage_parsian", "surplus_mehr", "shortage_mehr")


@dataclass
class Problem:
    c: np.ndarray
    a: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    variable_upper: np.ndarray
    labels: list
    demand: np.ndarray
    coverage: np.ndarray
    shift_cost: np.ndarray


def load_data(directory=None):
    directory = Path(directory) if directory else ROOT / "data"
    with (directory / "hourly_demand.csv").open(newline="", encoding="utf-8") as f:
        records = list(csv.DictReader(f))
    if [int(row["hour"]) for row in records] != list(range(24)):
        raise ValueError("Demand must contain each hour 0 through 23, in order.")
    demand = np.array([[int(r["parsian"]), int(r["mehr"])] for r in records])
    config = json.loads((directory / "parameters.json").read_text())
    if demand.shape != (24, 2) or np.any(demand < 0):
        raise ValueError("Demand must be a nonnegative 24 by 2 array.")
    return demand, config


def build_problem(directory=None, shortage_cap_parsian=None,
                  shift4_cost=None):
    demand, p = load_data(directory)
    # A seven-hour paid shift: work 3 hours, rest 1 hour, work 3 hours.
    coverage = np.array([[(hour - start) % 24 in (0, 1, 2, 4, 5, 6)
                         for start in range(24)] for hour in range(24)], dtype=float)
    hourly_wage = np.array([p["wage_day"] if 9 <= h < 17 else p["wage_night"]
                           for h in range(24)])
    shift_cost = np.array([sum(hourly_wage[(start + offset) % 24]
                               for offset in range(7)) for start in range(24)], dtype=float)
    if shift4_cost is not None:
        shift_cost[4] = float(shift4_cost)
    cap = p["daily_shortage_parsian"] if shortage_cap_parsian is None else float(shortage_cap_parsian)
    if cap < 0 or np.any(shift_cost < 0):
        raise ValueError("Scenario costs and shortage caps must be nonnegative.")
    c = np.zeros(144)
    c[:24] = c[24:48] = shift_cost
    c[72:96] = [p["penalty_parsian_day"] if 7 <= h < 18
                else p["penalty_parsian_night"] for h in range(24)]
    c[120:144] = p["penalty_mehr"]
    rows, lower, upper, labels = [], [], [], []

    def add(label, entries, lb=-np.inf, ub=np.inf):
        row = np.zeros(144)
        for index, coefficient in entries:
            row[index] += coefficient
        rows.append(row)
        lower.append(lb)
        upper.append(ub)
        labels.append(label)

    for h in range(24):
        add(f"shift_capacity_{h}", [(h, 1), (24+h, 1)], ub=p["shift_capacity"])
    for h in range(24):
        active = list(np.flatnonzero(coverage[h]))
        add(f"active_staff_{h}", [(j, 1) for j in active] + [(24+j, 1) for j in active],
            lb=p["minimum_active"], ub=p["maximum_active"])
        add(f"parsian_demand_lower_{h}", [(j, 1) for j in active] + [(72+h, 1)], lb=demand[h, 0])
        add(f"parsian_demand_upper_{h}", [(j, 1) for j in active] + [(48+h, -1)], ub=demand[h, 0])
        add(f"mehr_demand_lower_{h}", [(24+j, 1) for j in active] + [(120+h, 1)], lb=demand[h, 1])
        add(f"mehr_demand_upper_{h}", [(24+j, 1) for j in active] + [(96+h, -1)], ub=demand[h, 1])
    add("daily_shortage_parsian", [(72+h, 1) for h in range(24)], ub=cap)
    add("daily_shortage_mehr", [(120+h, 1) for h in range(24)], ub=p["daily_shortage_mehr"])
    variable_upper = np.full(144, np.inf)
    variable_upper[72:96] = variable_upper[120:144] = p["hourly_shortage_limit"]
    return Problem(c, np.array(rows), np.array(lower), np.array(upper),
                   variable_upper, labels, demand, coverage, shift_cost)


def check_solution(problem, values, tolerance=1e-5):
    values = np.asarray(values, dtype=float)
    if values.shape != (144,) or not np.all(np.isfinite(values)):
        return {"feasible": False, "reason": "Invalid decision vector"}
    activity = problem.a @ values
    residual = max(0.0, float(np.max(problem.lower - activity)),
                   float(np.max(activity - problem.upper)), float(np.max(-values)),
                   float(np.max(values - problem.variable_upper)))
    integer_error = float(np.max(np.abs(values - np.rint(values))))
    return {"feasible": residual <= tolerance and integer_error <= tolerance,
            "maximum_constraint_violation": residual,
            "maximum_integrality_violation": integer_error}
