-- 10: What are the internal serial numbers of the service contract with the customer named microhips and the iten code A00006?
select internalSN
from OINS
where custmrName = 'Microchips' and itemCode = 'A00006'
;

select * from OCTR; -- Service contracts
select * from CTR1; -- Service contract items

select * from OINS; -- Customer equipment card

select * from OQUE; -- Queue

select * from OSCL; -- Service calls
select * from SCL1; -- Service call solutions - Rows
select * from SCL7; -- Service call BP Address

select * from OSCO; -- Service call origin

