-- 10: For the payment term with the term group code 'Net30', show the number of additional days, number of installments, and whether or not value added tax is applied on the first installment.
select ExtraDays, InstNum, VATFirst
from OCTG
where PymntGroup = 'Net30'
;

-- Synthesis Queries:
-- Set random floats:
update ORCT SET WTOnhldPst = CAST(RAND(CHECKSUM(NEWID())) * 100 as int) ;

-- Set random chars:
update OHEM SET StatusOfE =  left(CONVERT(varchar(255), NEWID()), 2);

-- Set random date:
DECLARE @StartDate AS date;
DECLARE @EndDate AS date;
SELECT @StartDate = '01/01/1950', -- Date Format - DD/MM/YYY
       @EndDate = '12/31/2005';
SELECT DATEADD(DAY, RAND(CHECKSUM(NEWID()))*(1+DATEDIFF(DAY, @StartDate, @EndDate)),@StartDate) AS 'RandomDate';

-- Data Synthesis Log:
update OCHO SET DdctPrcnt = CAST(RAND(CHECKSUM(NEWID())) * .1 as float);
update OCHO SET Deduction = (LinesSum * DdctPrcnt);
update ORCT SET WTOnhldPst = CAST(RAND(CHECKSUM(NEWID())) * 100 as int) ;