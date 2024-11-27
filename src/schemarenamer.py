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
"""

import pandas as pd
import pyodbc
import sqlite3
import json
import openai
import src.util.callgpt as callgpt
import os
import src.util.db_util as db_util
import src.util.db_util_sqlite as db_util_sqlite
import SNAILS_Artifacts.naturalness_modifier.data_dict_reader.DataDictInterpreter as ddi
import SNAILS_Artifacts.naturalness_classifiers.schemaclassifier as schemaclassifier
from tqdm import tqdm

def main():
    db_classifier_score_df = schemaclassifier.classify_db_schema(
        "ATBI", 
        db_type="ms sql"
        )
    schema_xwalk = do_schema_renaming(
        "ATBI", 
        continuous_write=False, 
        db_classifier_score_df=db_classifier_score_df,
        db_type="ms sql"
        )
    schema_xwalk.to_excel("./temp_data/renamer_test.xlsx")
    pass
    


def transform_score_df(score_df: pd.DataFrame) -> pd.DataFrame:
    table_scores = score_df[["TABLE_NAME", "TABLE_SCORE"]].rename(columns={
        "TABLE_NAME": "IDENTIFIER",
        "TABLE_SCORE": "SCORE"
    })
    column_scores = score_df[["COLUMN_NAME", "COLUMN_SCORE"]].rename(columns={
        "COLUMN_NAME": "IDENTIFIER",
        "COLUMN_SCORE": "SCORE"
    })
    combined_df = pd.concat([table_scores, column_scores])
    combined_df["IDENTIFIER"] = combined_df.IDENTIFIER.str.lower()
    combined_df = combined_df.drop_duplicates(subset=["IDENTIFIER"])
    return combined_df



def do_schema_renaming(
        database_name = "PacificIslandLandbirds", 
        score_lookup_file: str = "./data/gold-data/identifier-scores-evaluated-5-9-2024.xlsx",
        continuous_write: bool = False,
        db_type: str = "ms sql",
        db_classifier_score_df: pd.DataFrame = None,
        only_most_natural: bool = False,
        verbose: bool = True
        ) -> pd.DataFrame:
    """
    Renames schema identifiers in a database based on human-evaluated scores.
    Parameters:
    database_name (str): The name of the database to process.
    score_lookup_file (str): Path to the Excel file containing human-evaluated identifier scores.
    continuous_write (bool): If True, writes logs continuously during processing.
    db_type (str): The type of the database (e.g., "ms sql" or "sqlite").
    db_classifier_score_df (pd.DataFrame): DataFrame containing classifier scores. If None, scores are read from the score_lookup_file.
    only_most_natural (bool): If true, only creates column for the most natural category. Default is False.
    Returns:
    pd.DataFrame: DataFrame containing the original and generated schema identifiers along with their naturalness scores and any errors encountered.
    """
    if not verbose:
        def dummy_print(*args, **kwargs):
            pass
        print = dummy_print
    try:
        data_dict_interpreter_factory = ddi.DataDictInterpreterFactory(database_name=database_name)
        data_dict_interpreter = data_dict_interpreter_factory.get_current_interpreter()
    except FileNotFoundError as e:
        print(e)
        data_dict_interpreter = None

    # Retrieve list of human-evaluated schema identifiers:
    if type(db_classifier_score_df) != None:
        score_df = pd.read_excel(score_lookup_file)
    else:
        score_df = transform_score_df(score_df=db_classifier_score_df)

    score_df["IDENTIFIER_lower"] = score_df["IDENTIFIER"].str.lower()
    score_df.set_index("IDENTIFIER_lower", inplace=True)

    # Retrieve list of tables and columns from database:
    if db_type == "ms sql":
        tables_and_columns = db_util.get_tables_and_columns_df(
            db_util.get_tables_and_columns_from_sql_server_db(database_name, append_col_types=False)
            )
    elif db_type == "sqlite":
        tables_and_columns = db_util_sqlite.get_tables_and_columns_df(
            db_util_sqlite.get_tables_and_columns_from_sqlite_db(database_name, append_col_types=False)
            )
    
    # Join the tables_and_columns df with the identifier scores to get the naturalness class
    tables_df = tables_and_columns[['table']].rename(columns={'table': 'native_identifier'})
    tables_df['table_or_column'] = 'table'
    columns_df = tables_and_columns[['column']].rename(columns={'column': 'native_identifier'})
    columns_df['table_or_column'] = 'column'
    
    # Create identifier dataframe and native_naturalness column
    identifier_df =  pd.concat([tables_df, columns_df]).drop_duplicates()
    identifier_df['source_database'] = database_name
    identifier_df['native_naturalness'] = identifier_df['native_identifier'].apply(lambda x: score_df.loc[x.lower()]['SCORE'])

    print(identifier_df)

    # Lists for holding generated identifiers
    N1_identifiers = []
    N2_identifiers = []
    N3_identifiers = []
    errors = []

    log_file = f'./logs/schema-renaming/schema_renamer_identifier_gen_log_{database_name}.csv'
    gen_log = open(log_file, 'w')
    gen_log.write("native_identifier,native_naturalness,N1,N2,N3,error\n")
    gen_log.close()

    # Generate identifier dict using fine tuning function
    for row in tqdm(identifier_df.itertuples(), total=identifier_df.shape[0], desc=f"Creating more natural {database_name} identifiers"):
        try:
            generated_identifiers = do_fewshot_identifier_transform(
                row.native_identifier.strip(),
                row.native_naturalness.strip(),
                data_dict_interpreter=data_dict_interpreter,
                only_most_natural=only_most_natural,
                verbose=verbose
                )
            N1_identifiers.append(generated_identifiers['N1'])
            if not only_most_natural:
                N2_identifiers.append(generated_identifiers['N2'])
                N3_identifiers.append(generated_identifiers['N3'])
            errors.append("None")
        except Exception as e:
            print(e)
            N1_identifiers.append(row.native_identifier.strip())
            if not only_most_natural:
                N2_identifiers.append(row.native_identifier.strip())
                N3_identifiers.append(row.native_identifier.strip())
            errors.append(f"Identifier Generation Failure: {e}")
        if continuous_write:
            gen_log = open(log_file, 'a')
            gen_log.write(f"{row.native_identifier},{row.native_naturalness},{N1_identifiers[-1]},{N2_identifiers[-1]},{N3_identifiers[-1]},{errors[-1]}\n")
            gen_log.close()
    

    # Add lists to identifier data frame
    identifier_df['N1_identifier'] = N1_identifiers
    if not only_most_natural:
        identifier_df['N2_identifier'] = N2_identifiers
        identifier_df['N3_identifier'] = N3_identifiers
    identifier_df['errors'] = errors

    return identifier_df

  

def do_fewshot_identifier_transform(
        identifier, 
        naturalness,
        data_dict_interpreter: ddi.DataDictInterpreter = None,
        only_most_natural: bool = False,
        verbose: bool = True,
        gpt_model: str = "gpt-4o"
        ) -> dict:
    
    naturalness_dict = {}
    naturalness_dict['Original_Ident'] = identifier
    naturalness_dict['Original_Naturalness'] = naturalness
    naturalness_dict[naturalness] = identifier

    if naturalness == 'N1' and not only_most_natural:
        f = open('./prompts/fewshot-N1-to-N2.txt')
        n1_n2_prompt = f.read()
        f.close()
        f = open('./prompts/fewshot-N1-to-N3.txt')
        n1_n3_prompt = f.read()
        f.close()
        f = open('./prompts/fewshot-N2-to-N3.txt')
        n2_n3_prompt = f.read()
        f.close()

        naturalness_dict['N2'] = callgpt.call_gpt(
            n1_n2_prompt.replace('_IDENTIFIER_', identifier), 
            verbose=verbose,
            model=gpt_model
        ).strip()

        naturalness_dict['N3'] = callgpt.call_gpt(
            n1_n3_prompt.replace('_IDENTIFIER_', identifier)
        ).strip()
        if naturalness_dict['N2'] == naturalness_dict['N3']:
            naturalness_dict['N3'] = callgpt.call_gpt(
                n2_n3_prompt.replace('_IDENTIFIER_', naturalness_dict['N2']), 
                verbose=verbose,
                model=gpt_model
            )

    if naturalness == 'N2':
        if data_dict_interpreter != None:
            naturalness_dict['N1'] = data_dict_interpreter.getNaturalIdentifier(identifier, verbose=verbose)
        else:
            naturalness_dict['N1'] = identifier

        f = open('./prompts/fewshot-N2-to-N3.txt')
        n2_n3_prompt = f.read()
        f.close()

        if not only_most_natural:
            naturalness_dict['N3'] = callgpt.call_gpt(
                n2_n3_prompt.replace('_IDENTIFIER_', identifier), 
                verbose=verbose,
                model=gpt_model
            ).strip()

    if naturalness == 'N3':
        if data_dict_interpreter != None:
            f = open('./prompts/fewshot-N1-to-N2.txt')
            n1_n2_prompt = f.read()
            f.close()
            naturalness_dict['N1'] = data_dict_interpreter.getNaturalIdentifier(identifier)
            if not only_most_natural:
                naturalness_dict['N2'] = callgpt.call_gpt(
                    n1_n2_prompt.replace('_IDENTIFIER_', naturalness_dict['N1']),
                    verbose=verbose,
                    model=gpt_model
                ).strip()
        else:
            naturalness_dict['N1'] = identifier
            naturalness_dict['N2'] = identifier

    return naturalness_dict
        
        

if __name__ == '__main__':
    main()
    # r = do_fewshot_identifier_transform("C_Tb", "N1")
    # print(r)
    pass
