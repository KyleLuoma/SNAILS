# FROM mcr.microsoft.com/mssql/server:2022-preview-ubuntu-22.04
FROM mcr.microsoft.com/mssql/server:2022-latest

ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD=SN@ILS123!!
ENV MSSQL_PID=Evaluation

EXPOSE 1433

COPY ./restore_snails_backups.sql restore_snails_backups.sql


