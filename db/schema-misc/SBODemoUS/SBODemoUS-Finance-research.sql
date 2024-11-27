-- 10: What is the project code and name of the projects valid after 2020?
select AcctName, avg(debLTotal), avg(CredLTotal)
from OACT
;

select * from OPRJ; -- Project codes
select * from FRC1; -- Extend cat. f. financial rep.
select * from OFRC; -- Financial report categories
select * from ODPV; -- Fixed assets depreciation value
select * from ODTP; -- Fixed assets depreciation types
select * from ORCR; -- Recurring Postings
select * from ORTT; -- CPI and FC rates
select * from OACG; -- Accounts Category
select * from OACT; -- General Ledger (GL) Accounts
select * from JDT1; -- Journal entry - rows
select * from BGT1; -- Budget rows
select * from OTAX; -- VAT Transactions
select * from TAX1; -- VAT Transactions - rows

-- Synthesis Queries:

-- Set random floats:
update OCRD SET CDPNum = CAST(RAND(CHECKSUM(NEWID())) * 50 as int) ;

select CAST(RAND(CHECKSUM(NEWID())) * 50 as int);

-- Set random chars:
update OSLP SET Email =  left(CONVERT(varchar(255), NEWID()), 7);

-- Set random date:
DECLARE @StartDate AS date;
DECLARE @EndDate AS date;
SELECT @StartDate = '01/01/1950', -- Date Format - DD/MM/YYY
       @EndDate = '12/31/2005';
SELECT DATEADD(DAY, RAND(CHECKSUM(NEWID()))*(1+DATEDIFF(DAY, @StartDate, @EndDate)),@StartDate) AS 'RandomDate';

-- Data Synthesis Log:
update OACT SET category = CAST(RAND(CHECKSUM(NEWID())) * 50 as int) ;
update FRC1 SET CalcMethod =  left(CONVERT(varchar(255), NEWID()), 7);
update FRC1 SET CalMethod2 =  left(CONVERT(varchar(255), NEWID()), 7);
update FRC1 SET CalMethod3 =  left(CONVERT(varchar(255), NEWID()), 7);

