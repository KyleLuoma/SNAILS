select 
    fkt.table_name fk_table, fkt.column_name fk_column, fkt.ORDINAL_POSITION fk_ordinal,
    rc.constraint_name fk_constraint_name, unique_constraint_name pk_constraint_name, 
    pkt.table_name pk_table, pkt.column_name pk_column, pkt.ORDINAL_POSITION pk_ordinal
from information_schema.referential_constraints rc
join (
    select tc.table_name, column_name, tc.constraint_name, ORDINAL_POSITION
    from information_schema.table_constraints tc
    join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    where constraint_type = 'FOREIGN KEY'
    ) fkt on rc.constraint_name = fkt.constraint_name 
join (
    select tc.table_name, column_name, tc.constraint_name, ORDINAL_POSITION
    from information_schema.table_constraints tc
    join information_schema.key_column_usage kcu on tc.constraint_name = kcu.constraint_name
    where constraint_type = 'PRIMARY KEY'
) pkt on rc.unique_constraint_name = pkt.constraint_name
where fkt.ORDINAL_POSITION = pkt.ORDINAL_POSITION and CONSTRAINT_SCHEMA <> 'db_nl'