#!/bin/bash

TAR_FILE="SNAILS_database_collection.tar.gz"

if [ ! -f "$TAR_FILE" ]; then
    echo "Error: $TAR_FILE not found in SNAILS_Artifacts/databases/. Refer to SNAILS_MSSQL_download_link.txt for the download options."
    exit 1
fi

chmod 777 ./restore_snails_backups.sql
chmod -R 777 ./bak

if [ ! -f "./bak/SBODemoUS.bak" ]; then
    echo "Decompressing SNAILS_database_collection.tar.gz"
    tar -xzvf "$TAR_FILE"
    mv *.bak ./bak/
    echo "Decompression complete."
fi

echo "Downloading SBODemoUS.bak"
wget https://d.dam.sap.com/a/mZu2WcN -O ./bak/SBODemoUS.bak

echo "Building snails-db docker container"
docker rm snails-db
docker build --no-cache -t snails-db .

echo "Copying dbinfo.json into .local folder"
cp ../../.local_example/dbinfo.json ../../.local/dbinfo.json
