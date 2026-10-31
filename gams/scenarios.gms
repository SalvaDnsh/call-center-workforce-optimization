$title Call-center staffing: parameter grids
$include gams/model_core.inc
Sets rhsScenario /r0*r14/, costScenario /k0*k21/;
Parameters rhsValue(rhsScenario), costValue(costScenario);
rhsValue(rhsScenario) = 10 + 5*(ord(rhsScenario)-1);
rhsValue('r13')=12; rhsValue('r14')=13;
costValue(costScenario) = 100 + 10*(ord(costScenario)-1);
costValue('k21')=171;
Scalars baseCap, baseCost;
baseCap=dailyCap('parsian');
baseCost=shiftCost('h4');
File out /gams/scenarios_gams.csv/;
put out;
put 'parameter,value,objective,objective_bound,model_status,solve_status'/;
loop(rhsScenario,
    dailyCap('parsian')=rhsValue(rhsScenario);
    Solve staffing using mip minimizing z;
    abort$(staffing.modelstat<>1 or staffing.solvestat<>1) 'RHS scenario optimum not certified';
    put 'parsian_shortage_cap,' rhsValue(rhsScenario):0:0 ',' z.l:0:6 ',' staffing.objest:0:6 ',' staffing.modelstat:0:0 ',' staffing.solvestat:0:0/;
);
dailyCap('parsian')=baseCap;
loop(costScenario,
    shiftCost('h4')=costValue(costScenario);
    Solve staffing using mip minimizing z;
    abort$(staffing.modelstat<>1 or staffing.solvestat<>1) 'Shift-cost scenario optimum not certified';
    put 'shift_04_cost,' costValue(costScenario):0:0 ',' z.l:0:6 ',' staffing.objest:0:6 ',' staffing.modelstat:0:0 ',' staffing.solvestat:0:0/;
);
shiftCost('h4')=baseCost;
putclose out;
