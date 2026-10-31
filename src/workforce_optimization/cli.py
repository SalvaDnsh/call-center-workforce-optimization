"""Solve, export reproducible evidence, and run explicitly defined scenarios."""
import argparse
import csv
import json
import platform
from pathlib import Path

import numpy as np
import scipy

from .model import ROOT, GROUPS, build_problem, check_solution
from .solve import solve, require_optimal


def write_csv(path, records):
    records = list(records)
    if not records:
        raise ValueError("Cannot export an empty table")
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    temporary.replace(path)


def save_baseline(problem, result, directory):
    directory.mkdir(parents=True, exist_ok=True)
    values = np.array(result["values"])
    active_x = np.rint(problem.coverage @ values[:24]).astype(int)
    active_y = np.rint(problem.coverage @ values[24:48]).astype(int)
    # The original surplus variables are unpenalized upper envelopes. Export
    # actual surplus rather than an arbitrary larger value selected by a solver.
    values[48:72] = np.maximum(active_x - problem.demand[:, 0], 0)
    values[96:120] = np.maximum(active_y - problem.demand[:, 1], 0)
    result["values"] = values.tolist()
    result["checks"] = check_solution(problem, values)
    result["environment"] = {"python": platform.python_version(),
                             "numpy": np.__version__, "scipy": scipy.__version__}
    result["cost_breakdown"] = {
        "wages": float(problem.c[:48] @ values[:48]),
        "parsian_shortage_penalty": float(problem.c[72:96] @ values[72:96]),
        "mehr_shortage_penalty": float(problem.c[120:144] @ values[120:144]),
    }
    result["total_shift_assignments"] = int(values[:48].sum())
    result["daily_shortage_operator_hours"] = {
        "parsian": int(values[72:96].sum()), "mehr": int(values[120:144].sum())}
    (directory / "baseline_solution.json").write_text(json.dumps(result, indent=2)+"\n")
    write_csv(directory / "shift_schedule.csv", [
        {"start_hour": h, "parsian": int(values[h]), "mehr": int(values[24+h]),
         "total": int(values[h]+values[24+h]), "cost_per_shift": problem.shift_cost[h]}
        for h in range(24)])
    write_csv(directory / "hourly_coverage.csv", [
        {"hour": h, "demand_parsian": int(problem.demand[h, 0]),
         "active_parsian": int(active_x[h]), "shortage_parsian": int(values[72+h]),
         "surplus_parsian": int(values[48+h]), "demand_mehr": int(problem.demand[h, 1]),
         "active_mehr": int(active_y[h]), "shortage_mehr": int(values[120+h]),
         "surplus_mehr": int(values[96+h]), "total_active": int(active_x[h]+active_y[h])}
        for h in range(24)])
    write_csv(directory / "all_variables.csv", [
        {"variable": group, "hour": h, "value": int(values[24*k+h])}
        for k, group in enumerate(GROUPS) for h in range(24)])
    return result


def scenarios(baseline, directory, backend, time_limit, data_directory=None):
    reference = np.array(baseline["values"])
    definitions = [
        ("parsian_shortage_cap", "shortage_cap_parsian", list(range(10, 71, 5))+[12, 13]),
        ("shift_04_cost", "shift4_cost", list(range(100, 301, 10))+[171]),
    ]
    all_rows = {}
    for name, parameter, grid in definitions:
        records = []
        for value in sorted(set(grid)):
            problem = build_problem(data_directory, **{parameter: value})
            result = solve(problem, backend, time_limit)
            feasible = check_solution(problem, reference)["feasible"]
            reference_objective = float(problem.c @ reference) if feasible else None
            stable = (reference_objective is not None and
                      abs(reference_objective-result["objective"]) <= 1e-5) if result["status"] == "optimal" else None
            records.append({"parameter_value": value, "status": result["status"],
                            "objective": result["objective"], "dual_bound": result["dual_bound"],
                            "relative_gap": result["relative_gap"], "reference_feasible": feasible,
                            "reference_objective": reference_objective,
                            "reference_still_optimal": stable})
            write_csv(directory / f"{name}.csv", records)
            print(f"{name}={value}: {result['status']}, objective={result['objective']}", flush=True)
        if any(row["status"] != "optimal" for row in records):
            raise RuntimeError(f"Some {name} scenarios were not certified; inspect the exported statuses.")
        objectives = np.array([row["objective"] for row in records])
        if name == "parsian_shortage_cap" and np.any(np.diff(objectives) > 1e-5):
            raise RuntimeError("Relaxing a shortage cap increased an alleged optimal cost.")
        if name == "shift_04_cost" and np.any(np.diff(objectives) < -1e-5):
            raise RuntimeError("Increasing a nonnegative cost reduced an alleged optimal cost.")
        write_csv(directory / f"{name}.csv", records)
        all_rows[name] = records
    return all_rows


def main():
    parser = argparse.ArgumentParser(description="Cyclic call-center workforce optimization")
    parser.add_argument("command", choices=["solve", "analyze", "plots"])
    parser.add_argument("--backend", choices=["scipy", "pyomo", "gurobi"], default="scipy")
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--data", type=Path, default=ROOT / "data")
    parser.add_argument("--time-limit", type=float, default=120)
    args = parser.parse_args()
    if args.command == "plots":
        from .plots import make_plots
        make_plots(args.output)
        return
    problem = build_problem(args.data)
    result = require_optimal(solve(problem, args.backend, args.time_limit))
    save_baseline(problem, result, args.output)
    print(f"Baseline: {result['objective']:.0f}; gap={result['relative_gap']}", flush=True)
    if args.command == "analyze":
        scenarios(result, args.output, args.backend, args.time_limit, args.data)
        from .plots import make_plots
        make_plots(args.output)


if __name__ == "__main__":
    main()
