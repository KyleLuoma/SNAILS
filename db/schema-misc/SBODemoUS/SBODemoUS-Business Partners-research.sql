-- 10: What is the email address and federal tax ID of the target with the position of CIO that is of target type C?
select E_Mail, LicTradNum
from TGG1
join OTGG on TGG1.TargetCode = OTGG.TargetCode
where Position = 'CIO' and TargetType = 'C'
;

select * from OTGG; -- Target Group
select * from TGG1; -- Target Group Details
select * from ODUN; -- Dunning Letters
select * from OCRG; -- Card Groups
select * from OCQG; -- Card Properties
select * from OCRD; -- Business Partner
select * from CRD1; -- Business Partners - Addresses
select * from CRD2; -- Business Partners - Payment Methods
select * from OCRB; -- Business Partner - Bank Account
select * from OCPR; -- Contact Persons
select * from OEGP; -- Email group
select * from OSLP; -- Sales Employee
select * from OCOG; -- Commission Groups
select * from OCPT; -- Campaign
select * from OCLG; -- Activities
select * from OCLT; -- Activity Types
select * from OCLA; -- Activity Status
select * from OCLS; -- Activity Subjects

-- Synthesis Queries:

-- Set random floats:
update OCRD SET CDPNum = CAST(RAND(CHECKSUM(NEWID())) * 100 as int) ;

-- Set random chars:
update OSLP SET Email =  left(CONVERT(varchar(255), NEWID()), 7);

-- Set random date:
DECLARE @StartDate AS date;
DECLARE @EndDate AS date;
SELECT @StartDate = '01/01/1950', -- Date Format - DD/MM/YYY
       @EndDate = '12/31/2005';
SELECT DATEADD(DAY, RAND(CHECKSUM(NEWID()))*(1+DATEDIFF(DAY, @StartDate, @EndDate)),@StartDate) AS 'RandomDate';

-- Data Synthesis Log:
update OSLP SET Telephone =  left(CONVERT(varchar(255), NEWID()), 7);
update OSLP SET Mobil =  left(CONVERT(varchar(255), NEWID()), 7);
update OSLP SET Email =  left(CONVERT(varchar(255), NEWID()), 7);
