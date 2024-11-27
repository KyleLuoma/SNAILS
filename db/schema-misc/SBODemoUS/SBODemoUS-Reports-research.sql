--10: What are the background, foreground, bold, and border red / green / blue values for the reporting elements with a height less than 5 and greater than 0?
select height, BGRed, BGGreen, BGBlue, FGRed, FGGreen, FGBlue, MrkrRed, MrkrBlue, MrkrGreen, BrdrRed, BrdrBlue, BrdrGreen
from RITM
where height < 5 and height > 0
;

select * from OECM; -- Electronic communication types or protocols
select * from ECM1; -- Parameters for various types of electronic communications
select * from ECM4; -- Import mapping determination

select * from OFLT; -- Report - selection criteria

select * from OQAG; -- Query authorization groups
select * from OUQR; -- Queries
select * from UGR1; -- Queries


select * from RTYP; -- Document type list
select * from RDOC; -- Document
select * from RITM; -- Reporting element

select * from OCRT; -- CRDB Tables Tree List