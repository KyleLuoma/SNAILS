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

import openai
import pandas as pd
from src.util.callgpt import call_gpt
from src.util.callgooglenl import call_codey
from src.util.call_llama import call_code_llama
from src.util.callgooglenl import call_vertex
from src.util.calltogetherai import call_togetherai
import time
from src.util.db_util import get_tables_and_columns_from_sql_server_db, get_tables_and_columns_df
import src.util.db_util
import src.util.db_util_sqlite
import pyodbc
from src.query_profiler import QueryProfiler

def do_single_question(
        original_prompt: str,
        use_database: str,
        question: str,
        xwalk_directory: str = None,
        column_naturalness: int = 0, 
        table_naturalness: int = 0,
        log: bool = True,
        filename_suffix: str = 'GPT-FT',
        filename_prefix: str = '',
        task: str = 'query',
        service: str = 'openai', # ['openai', 'google-vertex', 'google-palm', 'code-llama-aws']
        model_name: str = 'GPT-3.5', #['GPT-3.5', 'code-bison', 'code-bison32k, 'code-llama-7b', 'code-llama-34b', 'gemini-1.5-pro-latest']
        db_type: str = "sql server",
        db_list_file: str = ".local/dbinfo.json"
        ) -> dict:
    """
    Executes a single natural language question against a specified database using a specified AI service and
    generates a predicted SQL query.
    Args:
    original_prompt (str): The initial prompt to be used.
    use_database (str): The database to query.
    question (str): The question to be appended to the prompt.
    xwalk_directory (str, optional): Directory for crosswalk files. Defaults to None.
    column_naturalness (int, optional): Level of naturalness for columns. Defaults to 0.
    table_naturalness (int, optional): Level of naturalness for tables. Defaults to 0.
    log (bool, optional): Whether to log the attempt. Defaults to True.
    filename_suffix (str, optional): Suffix for filenames. Defaults to 'GPT-FT'.
    filename_prefix (str, optional): Prefix for filenames. Defaults to ''.
    task (str, optional): The task to perform ('query' or 'tables'). Defaults to 'query'.
    service (str, optional): The AI service to use ('openai', 'google-vertex', 'google-palm', 'code-llama-aws'). Defaults to 'openai'.
    model_name (str, optional): The model name to use. Defaults to 'GPT-3.5'.
    db_type (str, optional): The type of database ('sql server' or 'sqlite'). Defaults to "sql server".
    db_list_file (str, optional): Path to the database list file. Defaults to ".local/dbinfo.json".
    Returns:
    dict: A dictionary containing the prompt, SQL response, result dataframe, naturalness, and denaturalized response.
    """
    
    # print(f"DEBUG: column_naturalness: {column_naturalness}, table_naturalness: {table_naturalness}")
    
    if db_type == "sqlite":
        do_query = src.util.db_util_sqlite.do_query
        get_tables_and_columns_from_sql_server_db = src.util.db_util_sqlite.get_tables_and_columns_from_sqlite_db
        get_tables_and_columns_df = src.util.db_util_sqlite.get_tables_and_columns_df
    else:
        do_query = src.util.db_util.do_query

    schema_prompt = original_prompt

    if xwalk_directory != None:
        if xwalk_directory[-1] != '/':
            xwalk_directory += '/'
        naturalness, schema_prompt = naturalize_prompt(
            schema_prompt, 
            use_database, 
            xwalk_directory=xwalk_directory, 
            column_naturalness=column_naturalness, 
            table_naturalness=table_naturalness,
            filename_suffix=filename_suffix,
            filename_prefix=filename_prefix
            )
    else:
        naturalness = {'table': 0, 'column': 0}
    prompt = schema_prompt + question

    response = None
    if service == 'openai':
        while response == None:
            try:
                response = call_gpt(
                    prompt,
                    model=model_name
                    )
                
            except openai.error.RateLimitError as e:
                print("You've hit the rate limit. Try again in a few minutes.")
                print(e)
                time.sleep(60)

            except Exception as e:
                print(e)
                time.sleep(5)

    elif service == "togetherai":
        response = call_togetherai(prompt=prompt, model=model_name)
        print("DEBUG: response object from call_together_ai function:", response)

    elif service == 'google-vertex':
        if model_name == 'gemini-1.5-pro-latest':
            response = call_vertex(
                prompt,
                model=model_name
            )
        else:
            response = call_codey(
                prompt,
                model=model_name
                )
        
    elif service == 'code-llama-aws' or service == 'togetherai':
        response = call_code_llama(prompt + "\nSELECT")

    if response != None:
        response = response.replace("```sql", "")
        response = response.replace("```", "")
        response = response.strip()
        if xwalk_directory == None or naturalness['table'] + naturalness['column'] == 0:
            denaturalized_response = response
        elif naturalness['table'] + naturalness['column'] > 0:
            denaturalized_response = denaturalize_query(
                response, 
                naturalness, 
                xwalk_directory, 
                use_database,
                filename_suffix = filename_suffix,
                filename_prefix=filename_prefix,
                syntax=db_type
                )
        if task == 'query':
            try:
                print("Querying database\n")
                result_df = do_query(
                    denaturalized_response, 
                    use_database,
                    db_list_file=db_list_file
                    )
                if result_df.shape[0] > 10:
                    print("Here are the first 10 results:")
                    print(result_df.head(10))
                    print("There are {} more results.".format(result_df.shape[0] - 10))
                else:
                    print("Here are the results:")
                    print(result_df)
            except pyodbc.ProgrammingError as e:
                print("That query didn't work. Here's the error message:")
                print(e)
                result_df = pd.DataFrame({"error": [e]})
            except pyodbc.DataError as e:
                print("Encountered a problem attempting to execute the query")
                print(e)
                result_df = pd.DataFrame({"error": [e]})
            except Exception as e:
                print("Encountered a problem attempting to execute the query")
                print(e)
                result_df = pd.DataFrame({"error": [e]})                        
        elif task == 'tables':
            denaturalized_response = denaturalized_response.replace(';', '').strip()
            table_list = denaturalized_response.split(',')
            table_list = [table.strip() for table in table_list]
            result_df = pd.DataFrame({"table": table_list})
            print("Here are the tables:")
            print(result_df)

        if log:
            log_attempt(
                prompt=prompt, 
                response=response, 
                result_df=result_df, 
                database=use_database,
                model_name=model_name,
                naturalness=naturalness,
                denaturalized_response=denaturalized_response
                )
        
        return {
            'prompt': prompt,
            'response': response,
            'result_df': result_df,
            'naturalness': naturalness,
            'denaturalized_response': denaturalized_response
        }


def naturalize_prompt(
        schema_prompt: str, db_name: str, 
        xwalk_directory: str = './db/schema-xwalks/consolidated_and_validated/', 
        column_naturalness: int = 0, table_naturalness: int = 0,
        filename_suffix: str = 'GPT-FT',
        filename_prefix: str = ''
        ) -> dict:
    """Naturalize the prompt by replacing table and column names with natural language names.
    
    Parameters
    ----------
    schema_prompt : str
        The prompt to naturalize.
    db_name : str
        The name of the database on which the resulting query will be run.
    xwalk_directory : str, optional
        The directory in which the crosswalk files are stored. The default is None.
    column_naturalness : int, optional
        The level of naturalness to use for column names. The default is 0. Other values include 1, 2, 3
    table_naturalness : int, optional
        The level of naturalness to use for table names. The default is 0. Other values include 1, 2, 3
    filename_suffix : str, optional
        The suffix to use for the crosswalk files. The default is 'GPT-FT'.

    Returns
    -------
    naturalness : dict
        A dictionary with keys:
        'table' and 'column': values corresponding to the naturalness level used for each.
    """
    xwalk_filename = f"{filename_prefix}{db_name}-consolidated-xwalk.xlsx"
    xwalk_df = pd.read_excel(xwalk_directory + xwalk_filename)
    xwalk_df["native_identifier"] = xwalk_df["native_identifier"].str.lower()
    xwalk_df.set_index("native_identifier", inplace=True)

    table_xwalk = xwalk_df.query('table_or_column == "table"').copy()
    column_xwalk = xwalk_df.query('table_or_column == "column"').copy()

    prompt_tables = schema_prompt.split("<TABLE_NAME>")[1:]
    for i in range(len(prompt_tables)):
        prompt_tables[i] = prompt_tables[i].split("</TABLE_NAME>")[0]

    prompt_columns = schema_prompt.split("<COLUMN_NAME>")[1:]
    for i in range(len(prompt_columns)):
        prompt_columns[i] = prompt_columns[i].split("</COLUMN_NAME>")[0]
        col_token_list = prompt_columns[i].split(" ")
        if len(col_token_list) > 1:
            # prompt_columns[i] = " ".join(col_token_list[:-1])
            prompt_columns[i] = " ".join(col_token_list)

    for table in prompt_tables:
        replacement = table_xwalk.loc[table.strip().lower()][f"N{table_naturalness}_identifier"]
        # print("\nDEBUG TABLE:", table, replacement)
        schema_prompt = schema_prompt.replace(f"<TABLE_NAME>{table}</TABLE_NAME>", replacement)

    for column in prompt_columns:
        # print("\nDEBUG COLUMN:", column)
        replacement = column_xwalk.loc[column.strip().lower()][f"N{column_naturalness}_identifier"]
        schema_prompt = schema_prompt.replace(f"<COLUMN_NAME>{column}</COLUMN_NAME>", replacement)
                            
    return {
        'table': int(table_naturalness), 
        'column': int(column_naturalness),
        }, schema_prompt


def denaturalize_query(
        query: str, 
        naturalness: dict,
        xwalk_directory: str = './db/schema-xwalks/consolidated_and_validated/',
        db_name: str = "PacificIslandLandbirds", 
        filename_suffix: str = 'GPT-FT',
        filename_prefix: str = '',
        syntax="tsql",
        target_naturalness: str = "native"
        ) -> str:
    """Denaturalize a query by replacing natural language table and column names with their native identifiers.

    Parameters
    ----------
    query : str
        The query to denaturalize.
    naturalness : dict
        A dictionary with keys 'table' and 'column' and values corresponding to the naturalness level used for each.
    xwalk_directory : str, optional
        The directory in which the crosswalk files are stored.
    db_name : str, optional
        The name of the database on which the resulting query will be run. The default is "PacificIslandLandbirds".
    filename_suffix : str, optional
        The suffix to use for the crosswalk files. The default is 'GPT-FT'.
    filename_prefix : str, optional
        The prefix to use for the crosswalk files. The default is ''.
    """
    if syntax == "sql server":
        syntax = "tsql"

    if naturalness["table"] == 0:
        source_table_naturalness = "native"
    else:
        source_table_naturalness = {
            1: "N1",
            2: "N2",
            3: "N3"
        }[int(naturalness["table"])]

    if naturalness["column"] == 0:
        source_column_naturalness = "native"
    else:
        source_column_naturalness = {
            1: "N1",
            2: "N2",
            3: "N3"
        }[int(naturalness["column"])]

    profiler = QueryProfiler()
    xwalk_filename = f"{filename_prefix}{db_name}-consolidated-xwalk.xlsx"
    xwalk_df = pd.read_excel(xwalk_directory + xwalk_filename)
    xwalk_df[f"{target_naturalness}_identifier"] = xwalk_df[f"{target_naturalness}_identifier"].str.upper()

    table_xwalk = xwalk_df.query('table_or_column == "table"').copy()
    table_xwalk[f"{source_table_naturalness}_identifier"] = table_xwalk[f"{source_table_naturalness}_identifier"].str.upper()

    table_xwalk.set_index(f"{source_table_naturalness}_identifier", inplace=True)

    column_xwalk = xwalk_df.query('table_or_column == "column"').copy()
    column_xwalk[f"{source_column_naturalness}_identifier"] = column_xwalk[f"{source_column_naturalness}_identifier"].str.upper()
    column_xwalk.set_index(f"{source_column_naturalness}_identifier", inplace=True)

    # Extract string literals to preserve case
    string_literals = query.split("'")
    string_literals = [string_literals[l] for l in range(1, len(string_literals), 2)]
    # print("DEBUG string literals", string_literals)

    query_tag_dict = profiler.tag_query(
        query,
        syntax=syntax
        )
    query = query_tag_dict['tagged_query']

    query_columns = query.split("<COLUMN_NAME>")[1:]
    for i in range(len(query_columns)):
        query_columns[i] = query_columns[i].split("</COLUMN_NAME>")[0].strip()
    
    query_tables = query.split("<TABLE_NAME>")[1:]
    for i in range(len(query_tables)):
        query_tables[i] = query_tables[i].split("</TABLE_NAME>")[0].strip()

    for column in query_columns:
        l_bracket = r_bracket = ""
        if "[" in column and "]" in column:
            l_bracket = "["
            r_bracket = "]"
        column = column.replace("[", "").replace("]", "")

        # If it's an alias not named as an identifier and it is referenced
        # as a column name:
        if column in query_tag_dict['column_aliases'] and column not in column_xwalk.index:
            query = query.replace(f"<COLUMN_NAME> {l_bracket}{column}{r_bracket} </COLUMN_NAME>", f"[{column}]")
        # If it is an alias that matches a column name:
        elif column in column_xwalk.index and column in query_tag_dict["column_aliases"]:
            replacement = column_xwalk.loc[column][f"{target_naturalness}_identifier"]
            alias_replacement = replacement
            if " " in replacement.strip():
                alias_replacement = f"[{replacement}]"
            query = query.replace(
                f"<COLUMN_NAME> {l_bracket}{column}{r_bracket} </COLUMN_NAME>", 
                f"[{replacement}]"
                )
            query = query.replace(
                f" {column} ", 
                f" {alias_replacement} "
                )
            query = query.replace(f" {column}\n", f" {replacement}\n")
        # If it is neither an alias nor a real column name (e.g. a halucination):
        elif column not in column_xwalk.index and column not in column_xwalk.index:
            query = query.replace(f"<COLUMN_NAME> {l_bracket}{column}{r_bracket} </COLUMN_NAME>", f"[{column}]")
        # Otherwise, it's not an alias, and it's a valid column:
        else:    
            replacement = column_xwalk.loc[column][f"{target_naturalness}_identifier"]
            query = query.replace(f"<COLUMN_NAME> {l_bracket}{column}{r_bracket} </COLUMN_NAME>", f"[{replacement}]")

    for table in query_tables:

        l_bracket = r_bracket = ""
        if "[" in table and "]" in table:
            l_bracket = "["
            r_bracket = "]"
        table = table.replace("[", "").replace("]", "")

        # if table in query_tag_dict['table_aliases'] or table not in table_xwalk.index.to_list():
        if table not in table_xwalk.index.to_list():
            table = table.replace("[", "").replace("]", "")
            query = query.replace(f"<TABLE_NAME> {l_bracket}{table}{r_bracket} </TABLE_NAME>", f"[{table}]")
        else:
            replacement = table_xwalk.loc[table][f"{target_naturalness}_identifier"]
            query = query.replace(f"<TABLE_NAME> {l_bracket}{table}{r_bracket} </TABLE_NAME>", f"[{replacement}]")

    while "  " in query:
        query = query.replace("  ", " ")
    query = query.replace(" . ", ".")
    query = query.replace("( ", "(")
    query = query.replace(" )", ")")
    query = query.replace(" ,", ",")
    query = query.replace(" FROM ", "\nFROM ")
    query = query.replace(" WHERE ", "\nWHERE ")
    query = query.replace(" GROUP BY ", "\nGROUP BY ")
    query = query.replace(" ORDER BY ", "\nORDER BY ")
    query = query.replace(" HAVING ", "\nHAVING ")
    query = query.replace(" JOIN ", "\nJOIN ")
    query = query.replace('[\"', '[')
    query = query.replace('\"]', ']')
    query = query.replace("< >", "<>")
    for sl in string_literals:
        query = query.replace(f"'{sl.upper()}'", f"'{sl}'")

    if syntax == "sqlite":
        query = query.replace("[", "`")
        query = query.replace("]", "`")

    return query


def log_attempt(
        prompt: str, 
        response: str, 
        result_df: pd.DataFrame, 
        database: str,
        model_name: str,
        naturalness: dict = {'table': 0, 'column': 0}, 
        denaturalized_response: str = None
        ):

    #a filename string with a timestamp and database name
    filename = "{}{}.txt".format(database, time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))

    f = open('logs/{}'.format(filename), 'a')
    f.write(f"@MODEL:\n{model_name}\n\n")
    f.write("@DATABASE:\n" + database + '\n\n')
    f.write(
        "@NATURALNESS:\nTable: " 
        + str(naturalness['table']) 
        + "\nColumn: "
        + str(naturalness['column'])
        + '\n\n')
    f.write("@PROMPT:\n" + prompt + '\n\n')
    f.write("@RESPONSE:\n" + response + '\n')
    if denaturalized_response != None:
        f.write("\n@DENATURALIZED RESPONSE:\n" + denaturalized_response + '\n')
    f.write("\n\n@RESULTS:\n")
    write_string = result_df.to_string()
    #remove invalid characters from write_string
    write_string = write_string.replace('\u0101', 'a')
    write_string = write_string.replace("\u02bb", "'")
    try:
        f.write(write_string)
    except UnicodeEncodeError as e:
        print(e)
        f.write("error writing result")
    f.close()



def denaturalize_query_test():
    query_to_denaturalize = """
SELECT
  TLP.location_id_code,
  T.SnakeID,
  T."Board #",
  TLP.universal_transverse_mercator_XCoordinate,
  TLP.universal_transverse_mercator_YCoordinate
FROM table_field_data_coverboard_surveys AS T
INNER JOIN table_locations AS TL
  ON T.location_id_code = TL.location_id_code
INNER JOIN table_locations_points AS TLP
  ON TL.location_id_code = TLP.location_id_code
WHERE
  TL.SiteID = '18cb1';
"""

    query_to_denaturalize = """
SELECT cell_mobile_number
FROM Students s 
WHERE first_name = 'Timmothy' AND last_name = 'Ward'
LIMIT 1
"""

    naturalness = {'table': 1, 'column': 1}
    xwalk_directory = './schema-xwalks/consolidated_and_validated/'
    db_name = "ASIS_20161108_HerpInv_Database"

    result = denaturalize_query(
        query_to_denaturalize, 
        naturalness, 
        xwalk_directory, 
        db_name,
        syntax="sqlite"
    )

    print(result)



def do_single_question_test():
    question = "An SQL query to answer the question: "
    answer = do_single_question(
        original_prompt=question,
        use_database="NTSB",
        question="how many customers are there in california?",
        xwalk_directory="./db/schema-xwalks/consolidated_and_validated/",
        column_naturalness=0,
        table_naturalness=0,
        log=False,
        service="togetherai",
        model_name="Phind/Phind-CodeLlama-34B-v2"
    )
    print(answer)


if __name__ == "__main__":
    # do_single_question_test()
    denaturalize_query_test()
