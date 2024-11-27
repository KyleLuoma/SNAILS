#!/bin/bash

TAR_FILE="SNAILS_database_collection.tar.gz"

if [ ! -f "$TAR_FILE" ]; then
    echo "Error: $TAR_FILE not found in SNAILS_Artifacts/databases/. Refer to SNAILS_MSSQL_download_link.txt for the download options."
    exit 1
fi

echo "Decompressing SNAILS_database_collection.tar.gz"
tar -xzvf "$TAR_FILE"
echo "Decompression complete."

docker build