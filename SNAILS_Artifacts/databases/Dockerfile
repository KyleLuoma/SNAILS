FROM mcr.microsoft.com/mssql/server:2022-preview-ubuntu-22.04

ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD=SN@ILS123!!
ENV MSSQL_PID=Evaluation

EXPOSE 1433

COPY ./ASIS_20161108_HerpInv_Database.bak /var/opt/mssql/backup/ASIS_20161108_HerpInv_Database.bak
COPY ./ATBI.bak /var/opt/mssql/backup/ATBI.bak
COPY ./CratersWildlifeObservations.bak /var/opt/mssql/backup/CratersWildlifeObservations.bak
COPY ./KlamathInvasiveSpecies.bak /var/opt/mssql/backup/KlamathInvasiveSpecies.bak
COPY ./MacroInvertebrates.bak /var/opt/mssql/backup/MacroInvertebrates.bak
COPY ./NorthernPlainsFireManagement.bak /var/opt/mssql/backup/NorthernPlainsFireManagement.bak
COPY ./NTSB.bak /var/opt/mssql/backup/NTSB.bak
COPY ./NYSED_SRC2022.bak /var/opt/mssql/backup/NYSED_SRC2022.bak
COPY ./PacificIslandLandbirds.bak /var/opt/mssql/backup/PacificIslandLandbirds.bak
COPY ./SBODemoUS.bak /var/opt/mssql/backup/SBODemoUS.bak

COPY ./restore_snails_backups.sql restore_snails_backups.sql
RUN (/opt/mssql/bin/sqlservr --accept-eula & ) | sleep 15 && /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P 'SN@ILS123!!' -i restore_snails_backups.sql

CMD ["/opt/mssql/bin/sqlservr"]
