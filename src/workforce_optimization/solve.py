"""Solver adapters. Only certified optimal solutions are accepted as optima."""
import numpy as np
from .model import check_solution


def solve(problem, backend="scipy", time_limit=120):
    if backend == "scipy":
        from scipy.optimize import milp, Bounds, LinearConstraint
        result = milp(problem.c, integrality=np.ones(144),
                      bounds=Bounds(np.zeros(144), problem.variable_upper),
                      constraints=LinearConstraint(problem.a, problem.lower, problem.upper),
                      options={"mip_rel_gap": 0.0, "time_limit": float(time_limit)})
        status = {0: "optimal", 1: "limit_reached", 2: "infeasible", 3: "unbounded"}.get(result.status, "error")
        values = result.x
        objective = result.fun
        bound = getattr(result, "mip_dual_bound", None)
        gap = getattr(result, "mip_gap", None)
        message = result.message
    elif backend == "gurobi":
        import gurobipy as gp
        m = gp.Model("call_center_staffing")
        m.Params.OutputFlag = 0
        m.Params.MIPGap = 0
        m.Params.MIPGapAbs = 0
        m.Params.TimeLimit = time_limit
        m.Params.Threads = 1
        v = [m.addVar(lb=0, ub=float(problem.variable_upper[j]),
                      vtype=gp.GRB.INTEGER, name=f"v_{j}") for j in range(144)]
        m.setObjective(gp.quicksum(float(problem.c[j]) * v[j] for j in range(144)), gp.GRB.MINIMIZE)
        for i, row in enumerate(problem.a):
            expr = gp.quicksum(float(row[j]) * v[j] for j in np.flatnonzero(row))
            if np.isfinite(problem.lower[i]):
                m.addConstr(expr >= float(problem.lower[i]), name=problem.labels[i]+"_lower")
            if np.isfinite(problem.upper[i]):
                m.addConstr(expr <= float(problem.upper[i]), name=problem.labels[i]+"_upper")
        m.optimize()
        status = "optimal" if m.Status == gp.GRB.OPTIMAL else "infeasible" if m.Status == gp.GRB.INFEASIBLE else "not_certified"
        values = np.array([x.X for x in v]) if m.SolCount else None
        objective = m.ObjVal if m.SolCount else None
        bound = m.ObjBound if m.SolCount else None
        gap = m.MIPGap if m.SolCount else None
        message = f"Gurobi status {m.Status}"
    elif backend == "pyomo":
        import pyomo.environ as pe
        m = pe.ConcreteModel()
        m.v = pe.Var(range(144), domain=pe.NonNegativeIntegers,
                     bounds=lambda m, j: (0, None if np.isinf(problem.variable_upper[j]) else float(problem.variable_upper[j])))
        m.objective = pe.Objective(expr=sum(float(problem.c[j])*m.v[j] for j in range(144)))
        m.constraints = pe.ConstraintList()
        for i, row in enumerate(problem.a):
            expr = sum(float(row[j])*m.v[j] for j in np.flatnonzero(row))
            if np.isfinite(problem.lower[i]):
                m.constraints.add(expr >= float(problem.lower[i]))
            if np.isfinite(problem.upper[i]):
                m.constraints.add(expr <= float(problem.upper[i]))
        solver = pe.SolverFactory("cbc")
        if not solver.available(exception_flag=False):
            raise RuntimeError("Pyomo backend requires a separately installed CBC executable.")
        result = solver.solve(m, options={"ratio": 0, "allowableGap": 0, "seconds": time_limit}, load_solutions=False)
        condition = result.solver.termination_condition
        status = "optimal" if condition == pe.TerminationCondition.optimal else "infeasible" if condition == pe.TerminationCondition.infeasible else "not_certified"
        if len(result.solution):
            m.solutions.load_from(result)
            values = np.array([pe.value(m.v[j]) for j in range(144)])
            objective = pe.value(m.objective)
        else:
            values, objective = None, None
        raw_bound = result.problem.lower_bound
        bound = float(raw_bound) if raw_bound is not None else None
        gap = abs(objective-bound) / max(1.0, abs(objective)) if objective is not None and bound is not None else None
        message = str(condition)
    else:
        raise ValueError(f"Unknown backend: {backend}")
    checks = check_solution(problem, values) if values is not None else {"feasible": False}
    if status == "optimal" and not checks["feasible"]:
        raise RuntimeError(f"Solver returned an invalid solution: {checks}")
    return {"status": status, "objective": float(objective) if objective is not None else None,
            "dual_bound": float(bound) if bound is not None else None,
            "relative_gap": float(gap) if gap is not None else None,
            "backend": backend, "message": message, "checks": checks,
            "values": np.rint(values).astype(int).tolist() if values is not None else None}


def require_optimal(result):
    if result["status"] != "optimal":
        raise RuntimeError(f"An optimum was not certified: {result['status']}: {result['message']}")
    return result
