--Tables with data:
--select * from OHTM -- teams
--select * from HTM1 -- team members
--select * from OHEM -- employees
--select * from AHE6 -- roles
--select * from AHEM -- employee history
--select * from HEM6 -- Employee roles
--select * from Hld1 -- Holiday dates
--select * from OHLD -- Holiday table
--select * from OHTY -- Employee types

-- Set random floats:
update OHEM SET nChildren = CAST(RAND(CHECKSUM(NEWID())) * 10 as int) ;

-- Set random chars:
update OHEM SET StatusOfE =  left(CONVERT(varchar(255), NEWID()), 2);

-- Set random date:
DECLARE @StartDate AS date;
DECLARE @EndDate AS date;
SELECT @StartDate = '01/01/1950', -- Date Format - DD/MM/YYY
       @EndDate = '12/31/2005';
SELECT DATEADD(DAY, RAND(CHECKSUM(NEWID()))*(1+DATEDIFF(DAY, @StartDate, @EndDate)),@StartDate) AS 'RandomDate';