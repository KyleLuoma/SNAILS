FROM mcr.microsoft.com/mssql/server:2022-preview-ubuntu-22.04

ENV ACCEPT_EULA=Y
ENV MSSQL_SA_PASSWORD=snailspassword
ENV MSSQL_PID=Evaluation

EXPOSE 1433

CMD ["/opt/mssql/bin/sqlservr"]