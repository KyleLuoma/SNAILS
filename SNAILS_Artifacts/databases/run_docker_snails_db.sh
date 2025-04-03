docker kill snails-db
docker rm snails-db
echo "Running snails-db container"
docker run -d -p 1433:1433 --volume ./bak:/var/opt/mssql/backup --name snails-db snails-db 
echo "Sleeping for 20 seconds to allow the database to boot up"
sleep 20s
echo "Running backup restoration script"
docker exec snails-db /opt/mssql-tools18/bin/sqlcmd -C -S localhost -U sa -P 'SN@ILS123!!' -i restore_snails_backups.sql
