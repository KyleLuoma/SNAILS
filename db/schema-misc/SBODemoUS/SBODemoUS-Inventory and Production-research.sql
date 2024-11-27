-- 10: What is the average volume of items in the 'Items' Item group?
select avg(volume) avgVolume
from OITM
join OITB on OITM.ItmsGrpCod = OITB.ItmsGrpCod
join ITM4 on OITM.ItemCode = ITM4.ItemCode
where ItmsGrpNam = 'Items'
;

select * from OITB; -- Item Groups
select * from OITM; -- Items
select * from ITM4; -- Package in items
select * from ITM1; -- Item Prices
select * from ITM2; -- Items - Multiple Preferred Vendors
select * from ITM3; -- Items - localization fields
select * from ITM7; -- Asset item depreciation params
select * from ITM8; -- Asset Item Balances
select * from ITM9; -- Item - UoM Prices

select * from OPKG; -- Package types

select * from OBCD; -- Bar Code Master Data

select * from OBFC; -- Bin Field Configuration
select * from OBIN; -- Bin location

select * from OCYC; -- Cycle

