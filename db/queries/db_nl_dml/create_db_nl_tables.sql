if object_id(N'db_nl.native_natural_table_cross_reference', N'U') is null 
begin
create table db_nl.native_natural_table_cross_reference (
    native_table_name varchar(512),
    natural_table_name varchar(512),
    primary key (native_table_name)
)
;
end

if object_id(N'db_nl.native_natural_column_cross_reference', N'U') is null 
begin
create table db_nl.native_natural_column_cross_reference (
    native_table_name varchar(512),
    native_column_name varchar(512),
    natural_column_name varchar(512),
    primary key (native_table_name, native_column_name),
    foreign key (native_table_name) references db_nl.native_natural_table_cross_reference(native_table_name)
)
;
end