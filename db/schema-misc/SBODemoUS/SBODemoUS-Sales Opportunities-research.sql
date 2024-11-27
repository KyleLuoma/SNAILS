-- 10: Show the sales opportunity average gross profit in local currency by year created
select year(CreateDate) yearCreated, avg(SumProfL) avgLocProfit
from OOPR
group by year(CreateDate)
;

select * from OOPR; -- Opportunity
select * from OPR1; -- Opportunity rows
select * from OPRC; -- Cost center
select * from OOND; -- Industries