-- 40: What is the deciduous, shrub, herb, debris, litter, ground, and rock coverage of micro habitatis with a Flowering Phenology and a cover percentage greater than 90
select Deciduous, Shrub, Herb, WoodyDebris, Litter, BareGround, Rock
from tbl_MicroHabitat
where Phenology = 'Flowering'
	and cast(CoverPercent as float) > 90
;


select * from tbl_MicroHabitat;

select * from tbl_Db_Revisions;
select * from tbl_Db_Meta;
select * from tbl_Edit_Log;

select * from tbl_events;
select * from tbl_Event_Details;
select * from tbl_Locations;
select * from tbl_sites;

select * from tbl_MacroHabitat;

select * from tlu_Contacts;
select * from xref_Event_Contacts;

select * from tlu_Species_CRLA;
select * from tlu_Species_LABE;
select * from tlu_Species_LAVO;
select * from tlu_Species_ORCA;
select * from tlu_Species_REDW;
select * from tlu_Species_WHIS;