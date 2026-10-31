$title Cyclic call-center staffing: baseline
$include gams/model_core.inc
Solve staffing using mip minimizing z;
abort$(staffing.modelstat<>1 or staffing.solvestat<>1) 'Baseline optimum not certified', staffing.modelstat, staffing.solvestat;
Display z.l, starts.l, shortage.l;
File out /gams/baseline_gams.csv/;
put out;
put 'client,hour,shift_starts,shortage,surplus_upper_envelope,objective,objective_bound,model_status,solve_status'/;
loop((c,h),
    put c.tl ',' (ord(h)-1):0:0 ',' starts.l(c,h):0:0 ',' shortage.l(c,h):0:0 ',' surplus.l(c,h):0:0 ',' z.l:0:6 ',' staffing.objest:0:6 ',' staffing.modelstat:0:0 ',' staffing.solvestat:0:0/;
);
putclose out;
