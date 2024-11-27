"""
Copyright 2024 Kyle Luoma

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


This file contains helper functions for schema classification.

NOTE: OpenAI has since deprecated the davinci finetuned model availability.
"""

import pandas as pd
import pyodbc
import sqlite3
import json
from src.util import db_util
from src.util import db_util_sqlite
import os
from src.util import tokenprocessing as tp
from tqdm import tqdm



def main():

    dbname = "PacificIslandLandbirds"
    scores = classify_db_schema(dbname)
    # scores = classify_batch_with_gpt("./auto-scoring/bird_database_schemas.csv")
    # scores = classify_batch_with_canine("./schema-scores/spider-realistic/spider_realistic_schemas.csv")
    # scores.to_csv(f"./schema-scores/spider-realistic/spider_realistic_scores.csv", index=False)
    # scores.to_excel(f"./schema-scores/{dbname}-canine-gen2.xlsx", index = False)




def classify_db_schema(
        db_name,
        tagged = True,
        db_type = "ms sql" # 'ms sql' or 'sqlite'
        ):
    """
    Classifies the naturalness of table and column names in a database schema.
    This relies on the SNAILS db_util.py or db_util_sqlite.py utilities which means
    that databases must be registered in the ./.local/dbinfo.json or dbinfo_sqlite.json files prior to use.
    Parameters:
    db_name (str): The name of the database to classify.
    tagged (bool, optional): Whether to tag the identifiers. Defaults to True.
    db_type (str, optional): The type of the database, either 'ms sql' or 'sqlite'. Defaults to "ms sql".
    Returns:
    pd.DataFrame: A DataFrame containing the table names, table scores, column names, column scores, and model used.
    """
    try:
        import snails_naturalness_classifier as cnc
    except ModuleNotFoundError as e:
        import SNAILS_Artifacts.naturalness_classifiers.snails_naturalness_classifier as cnc
    classifier = cnc.CanineIdentifierClassifier()

    if db_type == "ms sql":
        tables_and_columns = db_util.get_tables_and_columns_from_sql_server_db(
            db_name,
            append_col_types=False
            )
    elif db_type == "sqlite":
        tables_and_columns = db_util_sqlite.get_tables_and_columns_from_sqlite_db(
            db_name=db_name,
            append_col_types=False
        )
    tables = []
    table_scores = []
    columns = []
    column_scores = []
    model_name_list = []
    for table in tables_and_columns:
        print("Classifying naturalness of " + table)
        table_score = classifier.classify_identifier(table, make_tag = tagged)[0]['label']
        print(table, table_score)
        for column in tables_and_columns[table]:
            print("Classifying naturalness of " + column)
            column_score = classifier.classify_identifier(column, make_tag=tagged)[0]['label']
            print(column, column_score)
            tables.append(table)
            table_scores.append(table_score)
            columns.append(column)
            column_scores.append(column_score)
            model_name_list.append('canine gen2')
    return pd.DataFrame({
        "TABLE_NAME": tables,
        "TABLE_SCORE": table_scores,
        "COLUMN_NAME": columns,
        "COLUMN_SCORE": column_scores,
        "MODEL": model_name_list
    })


            
def classify_batch_with_canine(batch_filepath):
    """
    Classifies tables and columns in a batch file using the CanineIdentifierClassifier.
    Args:
        batch_filepath (str): The file path to the batch CSV file containing table and column names.
    Returns:
        pd.DataFrame: A DataFrame containing the table names, table scores, column names, column scores, 
                      and the model used for classification. If the input DataFrame contains a 'DATABASE_NAME' 
                      column, it will also be included in the output DataFrame.
    The function performs the following steps:
    1. Reads the batch file to get table and column names.
    2. Initializes the CanineIdentifierClassifier.
    3. Attempts to read previously saved table scores from a backup file. If not found, initializes an empty dictionary.
    4. Scores the tables using the classifier and saves the scores periodically to a backup file.
    5. Attempts to read previously saved column scores from a backup file. If not found, initializes an empty dictionary.
    6. Scores the columns using the classifier and saves the scores periodically to a backup file.
    7. Adds the table and column scores to the original DataFrame.
    8. Adds the model name to the DataFrame.
    9. Returns a DataFrame with the relevant columns.
    """

    import snails_naturalness_classifier as cnc
    tables_and_columns = pd.read_csv(batch_filepath)
    classifier = cnc.CanineIdentifierClassifier()
    tables = tables_and_columns['TABLE_NAME'].unique().tolist()
    filename = batch_filepath.split("/")[-1].split(".")[0]

    try:
        df = pd.read_csv(f"temp_data/canine_table_score_backup_{filename}.csv")
        scored_tables = df.table.to_list()
        tables = list(set(tables).difference(set(scored_tables)))
        print(len(tables))
        table_scores = {k.table : k.score for k in df.itertuples()}
    except FileNotFoundError:
        table_scores = {}
  
    print("Scoring tables")
    flush_counter = 1
    for table in tqdm(tables):
        table_scores[table] = classifier.classify_identifier(table)[0]['label']
        if flush_counter % 100 == 0:
            pd.DataFrame({
                "table": list(table_scores.keys()), "score": [table_scores[t] for t in table_scores]
                }).to_csv(f"temp_data/canine_table_score_backup_{filename}.csv", index=False)
        flush_counter += 1

    try:
        df = pd.read_csv(f"temp_data/canine_column_score_backup_{filename}.csv")
        column_scores = {k.column: k.score for k in df.itertuples()}

    except FileNotFoundError:
        column_scores = {}

    print("Scoring columns")
    flush_counter = 1
    for column in tqdm(tables_and_columns['COLUMN_NAME'].unique().tolist()):
        if column not in column_scores.keys():
            column_scores[column] = classifier.classify_identifier(column)[0]['label']
            flush_counter += 1
        if flush_counter % 100 == 0:
            pd.DataFrame({
                "column": list(column_scores.keys()), 
                "score": [column_scores[c] for c in column_scores]
            }).to_csv(f"temp_data/canine_column_score_backup_{filename}.csv", index=False)
        
    
    tables_and_columns['TABLE_SCORE'] = tables_and_columns.apply(
        lambda row: table_scores[row.TABLE_NAME],
        axis = 1
    )

    tables_and_columns['COLUMN_SCORE'] = tables_and_columns.apply(
        lambda row: column_scores[row.COLUMN_NAME],
        axis = 1
    )

    tables_and_columns['MODEL'] = classifier.model_name

    return_cols = ['TABLE_NAME', 'TABLE_SCORE', 'COLUMN_NAME', 'COLUMN_SCORE', 'MODEL']
    if "DATABASE_NAME" in tables_and_columns.columns:
        return_cols.append("DATABASE_NAME")

    return tables_and_columns[return_cols]




if __name__ == "__main__":
    main()