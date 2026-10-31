# Reproduce and inspect the results

## Tested route

Run commands from the repository root:

```bash
python -m pip install -r requirements.txt
python run.py solve --output results
python run.py analyze --output results
python -m unittest discover -s tests -v
```

The recorded run used Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, and Matplotlib 3.10.8. The `requirements-tested.txt` file pins these Python package versions. The general requirements specify supported version ranges rather than an exhaustive environment lock.

The SciPy backend uses `scipy.optimize.milp`, which wraps HiGHS. The requested relative MIP gap is zero, and each solve has a configurable time limit (120 seconds by default). A baseline is accepted only after the solver reports optimality and the full exported decision vector passes independent row-bound, variable-bound, and integrality checks.

Both scenario series check their expected monotonic direction. Every exported scenario records its status, objective bound, relative gap, and the baseline-reference checks. If any scenario is not certified optimal, analysis stops before presenting that series as a completed optimal curve. Increase `--time-limit` if a machine reaches its limit.

For separate experiments, use a different output directory to retain the checked snapshot:

```bash
python run.py analyze --output scratch_results --time-limit 300
```

## Validation performed

- Matched the 24 pairs of demand inputs to the supplied assignment.
- Checked cyclic shift activity, including a midnight break.
- Checked the assignment's 15:00 shift-cost example (171).
- Reproduced the reported baseline optimum (184,848).
- Validated feasibility, integrality, and actual hourly shortages.
- Certified all 37 sampled scenarios and checked the expected monotonic direction.
- Rendered the coverage and scenario figures from the exported CSV files.

Different library versions may produce another equally optimal schedule. The objective value and constraint satisfaction are the appropriate comparisons; individual variable values need not be identical. Reference-vector stability flags can also differ when another baseline optimum is selected.

## Optional Python backends

The `pyomo` adapter requires the `pyomo` package and a CBC executable on `PATH`. The `gurobi` adapter requires `gurobipy` and a suitable license where applicable. Each uses the same Python-generated coefficient matrix. These adapters were not run in the preparation environment because those runtimes were absent. Their presence is not a claim of validated cross-solver equivalence.

```bash
python -m pip install -r requirements-optional.txt
python run.py solve --backend pyomo --output results_pyomo
python run.py solve --backend gurobi --output results_gurobi
```

## GAMS

The readable GAMS model and scenario driver are supplied separately. They were not executed in the preparation environment. Regenerate the GAMS data include whenever the source data changes, then run from the repository root:

```bash
python tools/export_gams_data.py
gams gams/model.gms
gams gams/scenarios.gms
```

Generated GAMS output is written to `gams/baseline_gams.csv` or `gams/scenarios_gams.csv`. These files record model and solve status. The scenario driver aborts on an uncertified solve. The regenerated GAMS outputs should be compared to the Python results before describing them as cross-validated.

## Original materials

`reports/original/` contains unchanged submitted PDFs. `archive/original_code.zip` contains original code and accompanying output artifacts, including the historical plots and spreadsheet. It omits one byte-identical notebook copy. The CSV manifest maps every original path to its archived entry and records SHA-256 checksums. Original artifacts can contain historical methodological or numerical issues documented in the review notes; they are retained as provenance rather than presented as current verified results.
