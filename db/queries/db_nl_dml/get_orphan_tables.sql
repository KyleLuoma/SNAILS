select distinct table_name
from information_schema.columns
where table_name not in (
	select tc.table_name
    from information_schema.table_constraints tc
    where constraint_type = 'FOREIGN KEY'
) and table_name in (
	select TABLE_NAME 
	from information_schema.tables
	where table_type = 'BASE TABLE'
)
;