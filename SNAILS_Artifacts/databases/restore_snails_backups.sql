RESTORE DATABASE ASIS_20161108_HerpInv_Database FROM DISK='/var/opt/mssql/backup/ASIS_20161108_HerpInv_Database.bak'
WITH MOVE 'ASIS_20161108_HerpInv_Database' TO '/var/opt/mssql/data/ASIS_20161108_HerpInv_Database.mdf',
     MOVE 'ASIS_20161108_HerpInv_Database_log' TO '/var/opt/mssql/data/ASIS_20161108_HerpInv_Database_log.ldf'
;

RESTORE DATABASE ATBI from disk='/var/opt/mssql/backup/ATBI.bak' 
WITH MOVE 'ATBI' TO '/var/opt/mssql/data/ATBI.mdf', 
     MOVE 'ATBI_log' TO '/var/opt/mssql/data/ATBI_log.ldf'
;

RESTORE DATABASE CratersWildlifeObservations FROM DISK='/var/opt/mssql/backup/CratersWildlifeObservations.bak'
WITH MOVE 'CratersWildlifeObservations' TO '/var/opt/mssql/data/CratersWildlifeObservations.mdf',
    MOVE 'CratersWildlifeObservations_log' TO '/var/opt/mssql/data/CratersWildlifeObservations_log.ldf'
;

RESTORE DATABASE KlamathInvasiveSpecies FROM DISK='/var/opt/mssql/backup/KlamathInvasiveSpecies.bak'
WITH MOVE 'KlamathInvasiveSpecies' TO '/var/opt/mssql/data/KlamathInvasiveSpecies.mdf',
    MOVE 'KlamathInvasiveSpecies_log' TO '/var/opt/mssql/data/KlamathInvasiveSpecies_log.ldf'
;

RESTORE DATABASE MacroInvertebrates FROM DISK='/var/opt/mssql/backup/MacroInvertebrates.bak'
WITH MOVE 'MacroInvertebrates' TO '/var/opt/mssql/data/MacroInvertebrates.mdf',
    MOVE 'MacroInvertebrates_log' TO '/var/opt/mssql/data/MacroInvertebrates_log.ldf'
;

RESTORE DATABASE NorthernPlainsFireManagement FROM DISK='/var/opt/mssql/backup/NorthernPlainsFireManagement.bak'
WITH MOVE 'NorthernPlainsFireManagement' TO '/var/opt/mssql/data/NorthernPlainsFireManagement.mdf',
    MOVE 'NorthernPlainsFireManagement_log' TO '/var/opt/mssql/data/NorthernPlainsFireManagement_log.ldf'
;

RESTORE DATABASE NTSB FROM DISK='/var/opt/mssql/backup/NTSB.bak'
WITH MOVE 'NTSB' TO '/var/opt/mssql/data/NTSB.mdf',
    MOVE 'NTSB_log' TO '/var/opt/mssql/data/NTSB_log.ldf'
;

RESTORE DATABASE NYSED_SRC2022 FROM DISK='/var/opt/mssql/backup/NYSED_SRC2022.bak'
WITH MOVE 'NYSED_SRC2022' TO '/var/opt/mssql/data/NYSED_SRC2022.mdf',
    MOVE 'NYSED_SRC2022_log' TO '/var/opt/mssql/data/NYSED_SRC2022_log.ldf'
;

RESTORE DATABASE PacificIslandLandbirds FROM DISK='/var/opt/mssql/backup/PacificIslandLandbirds.bak'
WITH MOVE 'PacificIslandLandbirds' TO '/var/opt/mssql/data/PacificIslandLandbirds.mdf',
    MOVE 'PacificIslandLandbirds_log' TO '/var/opt/mssql/data/PacificIslandLandbirds_log.ldf'
;

RESTORE DATABASE SBODemoUS FROM DISK='/var/opt/mssql/backup/SBODemoUS.bak'
WITH MOVE 'SBODemoUS' TO '/var/opt/mssql/data/SBODemoUS.mdf',
    MOVE 'SBODemoUS_log' TO '/var/opt/mssql/data/SBODemoUS_log.ldf'
;
