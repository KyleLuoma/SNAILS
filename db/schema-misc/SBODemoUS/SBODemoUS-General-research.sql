-- 10: What are the table names of business object briefs with the description fields that have the word Memo in them?
select TableName
from OBOB
where DescField like '%Memo%'
;

select * from OBOB; -- Business object brief

select * from OCPT; -- Cockpit main table
select * from CPT1; -- Cockpit sub table


select * from ORSC; -- Resources
select * from RSC1; -- Resources warehouses
select * from RSC4; -- Resources employees
select * from RSC6; -- Resources Daily Capacities


select * from OKPS; -- KPI Set
select * from ODAB; -- Dashboard
select * from DAB1; -- Dashboard queries
select * from CDIC; -- Dictionary
select * from ORSG; -- Resource properties

select * from OPMG; -- Project management - Document
select * from PMG1; -- Project management - stages
select * from PMG2; -- Project management - stages - open issues
select * from PMG4; -- Project management - stages - documents
select * from PMG6; -- Project management - stages - activities
select * from PMG8; -- Project management - summary