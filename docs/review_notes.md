# Portfolio preparation and review notes

## Historical coursework

The three submitted Persian reports and original Python/GAMS sources document a collaborative undergraduate project. The original reports were copied without content changes. They contain the group authorship and historical explanation of the submitted analyses.

## Subsequent preparation

The portfolio preparation consolidates repeated model definitions into a shared Python coefficient matrix; generates shift coverage and paid-shift costs from their definitions; separates input data, current outputs, and original submissions; adds an open-source SciPy/HiGHS execution route; and documents what was and was not rerun. The Python package, tests, plots, and English documentation are later refactoring and verification work, prepared with AI assistance, rather than an assertion that these exact files were submitted for the course.

## Findings addressed

| Finding in supplied materials | Treatment |
|---|---|
| Two byte-identical `Gurobipy_objective_Function.ipynb` copies | One archived copy; both source paths remain in the manifest |
| Repeated data and constraints across many scripts | One data source and one shared Python matrix model |
| Single-client cost changes and shared shift-cost changes appear in different scripts | Current 04:00 scenario explicitly changes both clients' whole-shift coefficient |
| Fixed-vector and fixed-support sensitivity methods are mixed in descriptions | Current CSV flags test one complete reference vector at sampled values |
| LP “basis” wording is used for an integer program | Model notes state the integer-program interpretation and limits |
| Hard-coded reference values, comparison thresholds, and scan limits | Current checks use the actual exported baseline vector and explicit parameter grids |
| Original GAMS curves contain small movements inconsistent with the expected optimal-cost direction | Regenerated curves use certified SciPy/HiGHS results with zero requested relative gap and monotonicity checks |
| Unpenalized surplus variables can exceed actual surplus | Current baseline exports normalize surplus to its actual nonnegative amount |

## A numerical example

The original RHS output gives 185,592 at allowance 12 and 185,595 at allowance 13. Increasing an upper bound on total shortage expands the feasible set, so a minimization optimum cannot increase. The checked rerun gives **185,592** and **185,586**, respectively.

The original GAMS code requests a relative gap of 0.0001. At a cost near 185,000, that permits an objective-bound gap around 18.5 units. Such a setting can explain small variations in returned feasible costs, but the original solver logs were not supplied, so the exact cause of each discrepancy cannot be established from the CSV alone. The revised results do not label those historical values as proven optima.

The existing coefficient CSV records model status 8 for most scenarios. Current verification instead retains an explicit optimality status, bound, and gap for every scenario. The original reports and CSVs remain available in the provenance archive.

## Scope of verification

The baseline and all 37 current scenarios were executed using SciPy/HiGHS. The optional refactored Pyomo/Gurobi adapters and the GAMS files were not executed in the preparation environment. The exact sensitivity intervals reported in the coursework were not independently re-established; current reference-stability results apply only to their stated grid.
