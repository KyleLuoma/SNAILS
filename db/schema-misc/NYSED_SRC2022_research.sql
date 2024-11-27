select count(*) schoolCount from [ACC EM ELP] where subgroup_name = 'white' 	and ell_count <> '0' 	and ENTITY_CD in ( 		select entity_cd 		from [Institution Grouping] 		where group_name = 'Public School' 	)
;

SELECT COUNT(DISTINCT ENTITY_CD) 
FROM [ACC EM ELP]
WHERE ENTITY_CD IN (
    SELECT ENTITY_CD 
    FROM [ACC EM ELP]
    WHERE SUBGROUP_NAME = 'White' AND SUBJECT = 'English Language Learners'
) AND SCHOOL_TYPE = 'Public Elementary School'
;


select * from [ACC HS ELP];
select * from [ACC HS Chronic Absenteeism];
select * from [ACC EM Chronic Absenteeism];
select * from [ACC EM Participation Rate];
select * from [ACC EM NYSESLAT for Participation]
select * from [ACC EM ELP];
select * from [ACC EM Core and Weighted Performance];
select * from [ACC HS Participation Rate];
select * from [ACC HS Graduation Rate];
select * from [ACC HS Core and Weighted Performance];
select * from [Expenditures per Pupil];
select * from [Annual EM MATH];
select * from [Annual NYSAA];
select * from [Annual EM ELA];
select * from [Accountability Status];
select * from [Accountability Levels];
select distinct GROUP_NAME from [Institution Grouping];

select cast(rate as float) from [ACC EM Participation Rate] where rate <> 's';