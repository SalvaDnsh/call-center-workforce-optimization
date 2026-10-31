* Run drivers from the repository root. Integer model of the same course case.
Sets
    h /h0*h23/
    c /parsian,mehr/;
Alias (h,t,j);
Set active(t,j);
active(t,j) = yes$(mod(ord(t)-ord(j)+24,24)=0
                    or mod(ord(t)-ord(j)+24,24)=1
                    or mod(ord(t)-ord(j)+24,24)=2
                    or mod(ord(t)-ord(j)+24,24)=4
                    or mod(ord(t)-ord(j)+24,24)=5
                    or mod(ord(t)-ord(j)+24,24)=6);
Parameters demand(c,t), shiftCost(j), penalty(c,t), dailyCap(c);
Scalars shiftCap, activeMin, activeMax, shortageMax;
$include gams/data.inc

Integer Variables starts(c,j), shortage(c,t), surplus(c,t);
Variable z;
starts.lo(c,j)=0; starts.up(c,j)=inf;
shortage.lo(c,t)=0; shortage.up(c,t)=shortageMax;
surplus.lo(c,t)=0; surplus.up(c,t)=inf;

Equations capacity(j), hourlyMin(t), hourlyMax(t), demandLow(c,t),
          demandUp(c,t), dailyShortage(c), objective;
capacity(j).. sum(c,starts(c,j)) =l= shiftCap;
hourlyMin(t).. sum((c,j)$active(t,j),starts(c,j)) =g= activeMin;
hourlyMax(t).. sum((c,j)$active(t,j),starts(c,j)) =l= activeMax;
demandLow(c,t).. sum(j$active(t,j),starts(c,j))+shortage(c,t) =g= demand(c,t);
demandUp(c,t).. sum(j$active(t,j),starts(c,j))-surplus(c,t) =l= demand(c,t);
dailyShortage(c).. sum(t,shortage(c,t)) =l= dailyCap(c);
objective.. z =e= sum((c,j),shiftCost(j)*starts(c,j))
                 +sum((c,t),penalty(c,t)*shortage(c,t));

Model staffing /all/;
staffing.optcr=0;
staffing.optca=0;
staffing.reslim=300;
