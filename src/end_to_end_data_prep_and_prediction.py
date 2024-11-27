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
import subprocess
import json
import src.semantic_compare
import src.schema_linking_eval
import src.nl_to_sql_inference_and_prompt_generation as pgn
import src.util.load_nl_questions as lnq
import time
import src.query_profiler as qpr
from tqdm import tqdm
import os
from itertools import product
import multiprocessing as mp

NUM_PROCESSES = 16

def main(
        model: str, 
        service: str, 
        naturalness: str, 
        database: str,
        bypass_nl_sql_inference: bool = True,
        db_list_file: str = ".local/dbinfo.json"
        ):

    date = time.strftime("%m-%d-%Y")
    spider_db_list = os.listdir("./db/spider/db")
    all_databases = [db.replace(".sqlite", "") for db in spider_db_list]
    if "SBO" in database:
        database_subname = database.split("-")[1]
    else:
        database_subname = ""

    xwalk_prefix = ""
    if "spider" in db_list_file:
        xwalk_prefix = "spider-"

    # Program run configurations live here. Comment / uncomment and replace values as-appropriate
    config_dict = {
        "database_name": database.split("-")[0],
        "database_subname": database_subname, # Use for schemas that should be divided into smaller modules (e.g. the SBODemo database). Set to empty string if not applicable.
        #Services:
        #['openai', 'google-vertex', 'google-palm', 'code-llama-aws', 'togetherai]
        "nltosql_service": service, 
        #Models:
        #['gpt-3.5-turbo, 'gpt-4-0125-preview' 'code-bison', 'text-bison', 'code-bison-32k', 
        # 'gemini-1.5-pro-latest', 'code-llama-7b', 'code-llama-34b',
        # 'Phind/Phind-CodeLlama-34B-v2'
        "nltosql_model": model, 
        "test": True,
        "classifier_service": "arbitrary", #GPT, arbitrary
        "classifier_model": "davinci:ft-personal:tagged-classifier-fixed-2023-07-10-23-28-14",
        "column_naturalness": naturalness, # NATIVE, N1, N2, N3, N4
        "table_naturalness": naturalness, # NATIVE, N1, N2, N3, N4
        "schema_xwalk_directory": "./schema-xwalks/consolidated_and_validated/",
        # "schema_xwalk_directory": None,
        "schema_xwalk_filename_suffix": "GPT-FT-corrected", # GPT-FT, GPT-FT-corrected
        "schema_xwalk_filename_prefix": xwalk_prefix,
        "table_pruning": False,
        "plan_matching": False,
        "output_filename": '{dbname}-{tabnat}-{colnat}-{nltosql_model}-evaluation-{date}.xlsx',
        "predicted_filename": '{dbname}-{tabnat}-{colnat}-{nltosql_model}-queries-predicted.xlsx',
    }

    if "spider" in db_list_file:
        config_dict["output_filename"] = "spider-" + config_dict["output_filename"]

    if config_dict['column_naturalness'] == "NATIVE":
        config_dict['schema_xwalk_directory'] = None

    if config_dict['database_subname'] != "":
        config_dict['full_database_name'] = (
            config_dict['database_name'] 
            + "-" 
            + config_dict['database_subname']
            )
    else:
        config_dict['full_database_name'] = config_dict['database_name']

    config_dict['output_filename'] = config_dict['output_filename'].format(
        dbname = config_dict['full_database_name'],
        tabnat = config_dict['table_naturalness'],
        colnat = config_dict['column_naturalness'],
        nltosql_model = config_dict['nltosql_model'],
        date = date
        )
    config_dict['predicted_filename'] = config_dict['predicted_filename'].format(
        dbname = config_dict['full_database_name'],
        tabnat = config_dict['table_naturalness'],
        colnat = config_dict['column_naturalness'],
        nltosql_model = config_dict['nltosql_model']
        )

    tf_dict = {True: 1, False: 0}
    nat_cat_dict = {"NATIVE": 0, "N1": 1, "N2": 2, "N3": 3, "N4": 4}

    db_info_f = open(db_list_file)
    db_info = json.loads(db_info_f.read())
    db_info_f.close()
    for db_entry in db_info:
        if db_entry['database'] == config_dict['database_name']:
            db_info = db_entry
            break

    config_dict["sql_dialect"] = {
        "sql server": "tsql",
        "sqlite": "sqlite"
    }[db_info["db-type"]]

    if db_info["db-type"] == "sqlite":
        import src.util.db_util_sqlite as db_util
    else:
        import src.util.db_util as db_util

    ### Data Loading ###
    filepath="./db/queries/"
    if "spider" in db_list_file:
        filepath=".db/queries/spider/spider-"

    print("### Data Loading ###")
    q_nl_df = lnq.load_nlq_into_df(
        config_dict['full_database_name'] + '.sql',
        filepath=filepath
    )
        
    q_nl_df['schema_pruning'] = tf_dict[config_dict['table_pruning']]

    # Primary, human-evaluated, List of db identifier scores:
    filepath = './data/gold-data/identifier-scores-evaluated-5-9-2024.xlsx'
    if "spider" in db_list_file:
        filepath = './db/spider/spider-dev-identifier-scores.xlsx'
        
    identifier_scores = pd.read_excel(filepath)
    identifier_scores['IDENTIFIER_lower'] = identifier_scores.apply(
        lambda row: row.IDENTIFIER.lower(), axis = 1
        )
    identifier_scores.set_index('IDENTIFIER_lower', inplace=True)

    ### SQL Inference ###
    print("### SQL Inference ###")
    if bypass_nl_sql_inference:
        try:
            q_nl_df = pd.read_excel('./db/queries/predicted/{}'.format(config_dict['predicted_filename']))
        except FileNotFoundError as e:
            bypass_nl_sql_inference = False

        ### Denaturalize queries of queries generated outside of this system (e.g., replicating other NLtoSQL systems)
        if bypass_nl_sql_inference:# and "query_predicted" not in q_nl_df.columns:
            if naturalness.lower() == "native":
                q_nl_df["query_predicted"] = q_nl_df.query_predicted_on_naturalized_schema
            else:
                print("### Denaturalizing imported queries ###")
                q_nl_df["query_predicted"] = q_nl_df.query_predicted_on_naturalized_schema.apply(
                            lambda q: pgn.denaturalize_query(
                                query=q,
                                naturalness={
                                    "table": config_dict["table_naturalness"][1],
                                    "column": config_dict["column_naturalness"][1],
                                    },
                                db_name=config_dict["database_name"],
                                filename_prefix=xwalk_prefix,
                                syntax=config_dict["sql_dialect"]
                            ) 
                        )
    
    # Save a checkpoint so we don't have to re-run the above code and keep calling an LLM.
    if not bypass_nl_sql_inference:
        q_nl_df = nl_to_sql_generation(
                q_nl_df, 
                bypass=bypass_nl_sql_inference,
                db_info=db_info,
                naturalness=config_dict["column_naturalness"],
                db_name=config_dict["database_name"],
                config_dict=config_dict,
                nat_cat_dict=nat_cat_dict,
                db_list_file=db_list_file,
                db_util=db_util
                )
        q_nl_df.to_excel('./db/queries/predicted/{}'.format(config_dict['predicted_filename']), index=False)

    ### Determine Schema and Query Naturalness ###
    print("### Determine Schema and Query Naturalness ###")
    if db_info["db-type"] == "sql server":
        t_c_dict = db_util.get_tables_and_columns_from_sql_server_db(
            config_dict['database_name'],
            append_col_types=False
        )
    elif db_info["db-type"] == "sqlite":
        t_c_dict = db_util.get_tables_and_columns_from_sqlite_db(
            config_dict["database_name"],
            append_col_types=False
        )
    tables = []
    table_scores = []
    table_score_source = []
    cols = []
    col_scores = []
    col_score_source = []
    for t in t_c_dict:
        if t.lower() in identifier_scores.index:
            table_score = identifier_scores.loc[t.lower()].iloc[1]
            table_scores.append(table_score)
            table_score_source.append('human validated')
        elif t.lower() not in tables:
            table_scores.append("N1")
            table_score_source.append('arbitrary')
        tables.append(t.lower())
        for c in t_c_dict[t]:
            if c.lower() in identifier_scores.index:
                col_score = identifier_scores.loc[c.lower()].iloc[1]
                col_scores.append(col_score)
                col_score_source.append('human validated')
            elif c.lower() not in cols:
                col_scores.append("N1")
                col_score_source.append("arbitrary")
            cols.append(c.lower())            
    table_scores_df = pd.DataFrame({
        'TABLE_NAME' : tables, 'TABLE_SCORE': table_scores, 'SOURCE': table_score_source
        })
    column_scores_df = pd.DataFrame({
        'COLUMN_NAME': cols, 'COLUMN_SCORE': col_scores, 'SOURCE': col_score_source
        })
    

    ### Generate gold query statistics and naturalness scores ###
    print("### Generate gold query statistics and naturalness scores ###")
    bypass = False
    if not bypass:
        # execute java jar in os.system
        # java -jar ./bin/SQLParserQueryAnalyzer_jar/SQLParserQueryAnalyzer.jar

        mp_query_data_list = []
        for row in q_nl_df.itertuples():
            mp_query_data_list.append((
                row.number,
                row.query_gold.upper().replace('"', "'"),
                config_dict['sql_dialect']
            ))

        pool = mp.Pool(processes=NUM_PROCESSES)
        mp_query_stats = pool.map(
            mp_query_parse_function,
            mp_query_data_list
        )
        query_stats_dict = {s[0]: s[1] for s in mp_query_stats}
        q_nl_df['query_stats'] = q_nl_df.apply(
            lambda row: query_stats_dict[row.number],
            axis=1
        )
        q_nl_df.to_excel(
            './db/queries/predicted/{}'.format(config_dict['predicted_filename']), index=False
            )
        q_nl_df.shape
    else:
        q_nl_df = pd.read_excel(
            './db/queries/predicted/{}'.format(config_dict['predicted_filename'])
            )
        
    ### Make a list of all aliases in all queries ###
    print("### Make a list of all aliases in all queries ###")
    profiler = qpr.QueryProfiler()
    alias_list = []

    mp_tag_df_gold_list = pool.map(
        profiler.tag_query,
        q_nl_df.query_gold.to_list()
    )
    for tag_df in mp_tag_df_gold_list:
        alias_list += tag_df['table_aliases']
        alias_list += tag_df['column_aliases']
    mp_tag_df_pred_list = pool.map(
        profiler.tag_query,
        q_nl_df.query_predicted.to_list()
    )
    for tag_df in mp_tag_df_pred_list:
        alias_list += tag_df['table_aliases']
        alias_list += tag_df['column_aliases']

    alias_list = set(alias_list)
    alias_list = [alias.lower().strip() for alias in alias_list]

    ### Extract table and column names and look up naturalness scores ###
    print("### Extract table and column names and look up naturalness scores ###")
    col_N1 = []
    col_N2 = []
    col_N3 = []
    tot_cols = []
    tab_N1 = []
    tab_N2 = []
    tab_N3 = []
    tot_tabs = []
    score_cache = {}
    for row in q_nl_df.itertuples():
        if(type(row.query_stats) == str):
            q_stats = json.loads(row.query_stats.replace("'", '"'))
        else:
            q_stats = row.query_stats
        c_N = [0, 0, 0] #[N1, N2, N3]
        t_N = [0, 0, 0] #[N1, N2, N3]
        for stat in q_stats:
            k = list(stat.keys())[0]

            if k not in ['table', 'column']:
                continue

            identifier = stat[k].lower()
            identifier = identifier.replace('[', '').replace(']', '')

            if identifier in identifier_scores.index:
                score = identifier_scores.loc[identifier].iloc[1].strip()
            elif identifier in score_cache:
                score = score_cache[stat[k]]
            elif identifier not in alias_list:
                print(identifier, 'not in schema naturalness score file. Arbitrary N1 assignment.')
                score = "N1"
                score_cache[identifier] = score

            if k == 'column':
                c_N[int(score[1]) - 1] += 1
            elif k == 'table':
                t_N[int(score[1]) - 1] += 1
                
        col_N1.append(c_N[0])
        col_N2.append(c_N[1])
        col_N3.append(c_N[2])
        tot_cols.append(sum(c_N))
        tab_N1.append(t_N[0])
        tab_N2.append(t_N[1])
        tab_N3.append(t_N[2])
        tot_tabs.append(sum(t_N))
    if config_dict['column_naturalness'] == 'NATIVE':
        q_nl_df['Qg_col_N1'] = col_N1
        q_nl_df['Qg_col_N2'] = col_N2
        q_nl_df['Qg_col_N3'] = col_N3
        q_nl_df['Qg_tot_cols'] = tot_cols
    else:
        q_nl_df['Qg_col_N{}'.format(nat_cat_dict[config_dict['column_naturalness']])] = tot_cols
        q_nl_df['Qg_tot_cols'] = tot_cols
        l = ['Qg_col_N1', 'Qg_col_N2', 'Qg_col_N3', 'Qg_col_N4']
        l.remove('Qg_col_N{}'.format(nat_cat_dict[config_dict['column_naturalness']]))
        for col in l:
            q_nl_df[col] = 0

    if config_dict['table_naturalness'] == 'NATIVE':
        q_nl_df['Qg_tab_N1'] = tab_N1
        q_nl_df['Qg_tab_N2'] = tab_N2
        q_nl_df['Qg_tab_N3'] = tab_N3
        q_nl_df['Qg_tot_tabs'] = tot_tabs
    else:
        q_nl_df['Qg_tab_N{}'.format(nat_cat_dict[config_dict['table_naturalness']])] = tot_tabs
        q_nl_df['Qg_tot_tabs'] = tot_tabs
        l = ['Qg_tab_N1', 'Qg_tab_N2', 'Qg_tab_N3', 'Qg_tab_N4']
        l.remove('Qg_tab_N{}'.format(nat_cat_dict[config_dict['table_naturalness']]))
        for col in l:
            q_nl_df[col] = 0

    ### Generate Schema naturalnes scores and stats ###
    print("### Generate Schema naturalnes scores and stats ###")
    col_nat_count = column_scores_df.groupby('COLUMN_SCORE').count()
    tab_nat_count = table_scores_df.groupby('TABLE_SCORE').count()

    for score_str in ['N1', 'N2', 'N3']:
        if score_str not in col_nat_count.index:
            col_nat_count.loc[score_str] = 0
        if score_str not in tab_nat_count.index:
            tab_nat_count.loc[score_str] = 0

    if config_dict['column_naturalness'] == 'NATIVE':
        q_nl_df['schema_col_N1'] = col_nat_count.loc['N1'].iloc[0]
        q_nl_df['schema_col_N2'] = col_nat_count.loc['N2'].iloc[0]
        q_nl_df['schema_col_N3'] = col_nat_count.loc['N3'].iloc[0]
    else:
        col_nat = nat_cat_dict[config_dict['column_naturalness']]
        if col_nat > 3:
            col_nat = 1
        l = [1, 2, 3]
        l.remove(col_nat)
        q_nl_df[
            'schema_col_N{}'.format(
                col_nat
            )] = column_scores_df.shape[0]
        q_nl_df['schema_col_N{}'.format(l[0])] = 0
        q_nl_df['schema_col_N{}'.format(l[1])] = 0
        
    if config_dict['table_naturalness'] == 'NATIVE':
        q_nl_df['schema_tab_N1'] = tab_nat_count.loc['N1'].iloc[0]
        q_nl_df['schema_tab_N2'] = tab_nat_count.loc['N2'].iloc[0]
        q_nl_df['schema_tab_N3'] = tab_nat_count.loc['N3'].iloc[0]
    else:
        tab_nat = nat_cat_dict[config_dict['table_naturalness']]
        if tab_nat > 3:
            tab_nat = 1
        l = [1,2,3]
        l.remove(tab_nat)
        q_nl_df[
            'schema_tab_N{}'.format(
                col_nat
            )] = table_scores_df.shape[0]
        q_nl_df['schema_tab_N{}'.format(l[0])] = 0
        q_nl_df['schema_tab_N{}'.format(l[1])] = 0

    q_nl_df['schema_tab_count'] = table_scores_df.shape[0]
    q_nl_df['schema_col_count'] = column_scores_df.shape[0]


    ### Gold query naturalnes proportions ###
    print("### Gold query naturalnes proportions ###")
    def max(a, b):
        if a > b:
            return a
        else:
            return b

    q_nl_df['Qg_col_N1_pct'] = q_nl_df.apply(
        lambda row: row.Qg_col_N1 / max(row.Qg_tot_cols, 1), axis = 1
        )
    q_nl_df['Qg_col_N2_pct'] = q_nl_df.apply(
        lambda row: row.Qg_col_N2 / max(row.Qg_tot_cols, 1), axis = 1
        )
    q_nl_df['Qg_col_N3_pct'] = q_nl_df.apply(
        lambda row: row.Qg_col_N3 / max(row.Qg_tot_cols, 1), axis = 1
        )
    q_nl_df['Qg_tab_N1_pct'] = q_nl_df.apply(
        lambda row: row.Qg_tab_N1 / max(row.Qg_tot_tabs, 1), axis = 1
        )
    q_nl_df['Qg_tab_N2_pct'] = q_nl_df.apply(
        lambda row: row.Qg_tab_N2 / max(row.Qg_tot_tabs, 1), axis = 1
        )
    q_nl_df['Qg_tab_N3_pct'] = q_nl_df.apply(
        lambda row: row.Qg_tab_N3 / max(row.Qg_tot_tabs, 1), axis = 1
        )
    # Schema naturalness proportions:
    q_nl_df['schema_col_N1_pct'] = q_nl_df.apply(
        lambda row: row.schema_col_N1 / max(row.schema_col_count, 1), axis = 1
        )
    q_nl_df['schema_col_N2_pct'] = q_nl_df.apply(
        lambda row: row.schema_col_N2 / max(row.schema_col_count, 1), axis = 1
        )
    q_nl_df['schema_col_N3_pct'] = q_nl_df.apply(
        lambda row: row.schema_col_N3 / max(row.schema_col_count, 1), axis = 1
        )
    q_nl_df['schema_tab_N1_pct'] = q_nl_df.apply(
        lambda row: row.schema_tab_N1 / max(row.schema_tab_count, 1), axis = 1
        )
    q_nl_df['schema_tab_N2_pct'] = q_nl_df.apply(
        lambda row: row.schema_tab_N2 / max(row.schema_tab_count, 1), axis = 1
        )
    q_nl_df['schema_tab_N3_pct'] = q_nl_df.apply(
        lambda row: row.schema_tab_N3 / max(row.schema_tab_count, 1), axis = 1
        )


    ### Compare gold query to predicted ###
    print("### Compare gold query to predicted ###")

    ## Result Set Comparison ###
    print("## Result Set Comparison ###")
    result_set_match = []
    result_set_compare_note = []

    for row in q_nl_df.itertuples():
        result_dict = src.semantic_compare.compare_gold_to_generated(
            row.query_gold, 
            row.query_predicted, 
            config_dict['database_name'], 
            db_type=config_dict["sql_dialect"],
            db_list_file=db_list_file
            )
        result_set_match.append(
            tf_dict[result_dict['equivalent']]
            )
        result_set_compare_note.append(result_dict['reason'])

    q_nl_df['result_set_match'] = result_set_match
    q_nl_df['result_set_compare_note'] = result_set_compare_note

    ### Query String Comparison ###
    print("### Query String Comparison ###")
    def transform_query(query):
        query = str(query).lower()
        query = query.replace("\n", " ")
        query = query.replace("\t", " ")
        query = query.replace(" ;", "")
        while "  " in query:
            query = query.replace("  ", " ")
        query = query.strip()
        return query

    string_matches = []
    for row in q_nl_df.itertuples():
        gold = transform_query(row.query_gold)
        predicted = transform_query(row.query_predicted)
        string_matches.append(tf_dict[gold == predicted])
    q_nl_df['string_match'] = string_matches

    ### Query Execution Plan Comparison ###
    #removed
    q_nl_df['sql_server_errors'] = ""

    ### Score Schema Linking ###
    print("### Score Schema Linking ###")
    matching_tables = []
    matching_columns = []
    missing_tables = []
    missing_columns = []
    extra_tables = []
    extra_columns = []
    recall = []
    precision = []
    f1 = []

    mp_linking_eval_data = []

    for row in tqdm(q_nl_df.itertuples(), total=q_nl_df.shape[0]):
        if len(str(row.query_predicted)) > 2000:
            qp = row.query_predicted[:2000]
        else:
            qp = str(row.query_predicted)
        mp_linking_eval_data.append((
            row.number,
            row.query_gold,
            qp
        ))

    mp_linking_res = pool.map(mp_schema_linking_eval, mp_linking_eval_data)
    mp_linking_res.sort()
    last_number = -1
    if db_info["db-type"] == "sql server":
        last_number += 1
    for result_tuple in mp_linking_res:
        try:
            assert result_tuple[0] == last_number + 1
        except AssertionError as e:
            print([r[0] for r in mp_linking_res])
            raise e
        linking_res = result_tuple[1]
        # linking_res = schema_linking_eval.compare_query_schema_elements(
        #     gold=row.query_gold, predicted=qp
        # )
        matching_tables.append(linking_res['matching_tables'])
        matching_columns.append(linking_res['matching_columns'])
        missing_tables.append(linking_res['missing_tables'])
        missing_columns.append(linking_res['missing_columns'])
        extra_tables.append(linking_res['extra_tables'])
        extra_columns.append(linking_res['extra_columns'])
        recall.append(linking_res['recall'])
        precision.append(linking_res['precision'])
        f1.append(linking_res['f1'])
        last_number += 1

    q_nl_df['matching_tables'] = matching_tables
    q_nl_df['matching_columns'] = matching_columns
    q_nl_df['missing_tables'] = missing_tables
    q_nl_df['missing_columns'] = missing_columns
    q_nl_df['extra_tables'] = extra_tables
    q_nl_df['extra_columns'] = extra_columns
    q_nl_df['recall'] = recall
    q_nl_df['precision'] = precision
    q_nl_df['f1'] = f1



    ### Error Classifications ###
    print("### Error Classifications ###")
    error_classes = []
    hallucination_counts = []
    syntax_error_counts = []
    misplaced_column_counts = []
    for row in q_nl_df.itertuples():
        syntax_error_count = 0
        hallucination_count = 0
        misplaced_column_count = 0
        
        row_error_classes = []
        if row.sql_server_errors != "":
            for ix, error_type in enumerate(row.sql_server_errors['error_types']):
                if error_type == 'invalid table':
                    row_error_classes.append('halucination')
                    hallucination_count += 1
                elif error_type == 'invalid column':
                    if row.sql_server_errors['error_objects'][ix].lower() not in column_scores_df['COLUMN_NAME'].to_list():
                        row_error_classes.append('halucination')
                        hallucination_count += 1
                    else:
                        row_error_classes.append('misplaced column')
                        misplaced_column_count += 1
                elif error_type == 'incorrect syntax':
                    row_error_classes.append('syntax error')
                    syntax_error_count += 1
        error_classes.append(row_error_classes)
        hallucination_counts.append(hallucination_count)
        syntax_error_counts.append(syntax_error_count)
        misplaced_column_counts.append(misplaced_column_count)

    q_nl_df['error_classification'] = error_classes
    q_nl_df['syntax_error_count'] = syntax_error_counts
    q_nl_df['hallucination_count'] = hallucination_counts
    q_nl_df['misplaced_column_count'] = misplaced_column_counts

    ### Save File in pending evaluation folder ###
    print("### Save File in pending evaluation folder ###")
    filename = config_dict['output_filename']
    # if the file exists, append to it
    append_ctr = 1
    while filename in os.listdir('./data/nl-to-sql_performance_annotations/pending_evaluation'):
        filename = config_dict['output_filename'].replace('.xlsx', '_{}.xlsx'.format(append_ctr))
        append_ctr += 1

    q_nl_df.to_excel(
        './data/nl-to-sql_performance_annotations/pending_evaluation/{}'.format(filename),
        index=False
    )


def mp_query_parse_function(query_data: tuple) -> tuple:
    question_num = query_data[0]
    query = query_data[1]
    syntax = query_data[2]
    result = subprocess.run(
        'java -jar ./bin/SQLParserQueryAnalyzer_jar/SQLParserQueryAnalyzer.jar --query "{}" --syntax {}'.format(
            query,
            syntax
            ),
        capture_output=True
    )
    if "@BEGINJSON" not in str(result):
        return (question_num, f"Unable to parse query {question_num}: {query}")
    json_string = str(result).split("@BEGINJSON")[1].split("@ENDJSON")[0]
    json_string = json_string.replace("\\n", "").replace("\\r", "").replace("\\t", "")
    while "  " in json_string:
        json_string = json_string.replace("  ", " ").lower()
    return (question_num, json.loads(json_string))


def mp_schema_linking_eval(data: tuple) -> tuple:
    number = data[0]
    query_gold = data[1]
    predicted = data[2]
    linking_res = src.schema_linking_eval.compare_query_schema_elements(
        gold=query_gold, predicted=predicted
    )
    return (number, linking_res)


def nl_to_sql_generation(
        q_nl_df: pd.DataFrame,
        bypass: bool = False,
        naturalness: str = None,
        db_name: str = None,
        config_dict: dict = None,
        nat_cat_dict: dict = None,
        db_info: dict = None,
        db_list_file: str = ".local/dbinfo.json",
        db_util = src.util.db_util
        ) -> pd.DataFrame:
    
    if naturalness is not None:
        print("Resetting naturalness for batch job.")
        col_naturalness = naturalness
        tab_naturalness = naturalness
    else:
        col_naturalness = config_dict['column_naturalness']
        tab_naturalness = config_dict['table_naturalness']

    if db_name is None:
        db_name = config_dict['database_name']

    quota = 0
    if not bypass:
        def nl_to_sql_f():
            pass

        nl_to_sql_f = pgn.do_single_question

        table_list = None
        column_list = None
        q_prompts = []
        q_sql_predicteds = []
        q_sql_predicteds_naturalized = []

        for row in q_nl_df.itertuples():

            print(f"#### Query {row.number} of {q_nl_df.shape[0]} ####")

            # For databases with modules (e.g. SBODemo), only use the tables in the module
            # Currently SBODemo is the only database with modules, but if this changes
            # then this code will need to be updated
            if config_dict['database_subname'] != "" or "SBODemo" in db_name:
                if "-" in db_name:
                    db_subnm = db_name.split("-")[1]
                else:
                    db_subnm = config_dict['database_subname']
                sbod_df = pd.read_excel('./db/schema-misc/SBODemoUS/SBOD_table_descriptions_combined_reduced.xlsx')
                sbod_col_df = pd.read_excel('./db/schema-misc/SBODemoUS/SBOD_table_column_descriptions_combined_reduced.xlsx')
                sbod_df = sbod_df[sbod_df.module == db_subnm]
                sbod_col_df = sbod_col_df[sbod_col_df.module == db_subnm]
                sbod_df = sbod_df[sbod_df.cardinality > 0]
                table_list = sbod_df.table.unique().tolist()
                column_list = sbod_col_df.field.unique().tolist()
            
            # Generate the prompt to be used for the query
            do_tagging = True
            if config_dict['schema_xwalk_directory'] is None:
                do_tagging = False
            
            db_prompt = db_util.make_db_schema_prompt(
                db_name.split("-")[0], 
                table_list=table_list,
                column_list=column_list,
                identifier_tags=do_tagging
                )

            q_sql_predicted = pgn.do_single_question(
                db_prompt, 
                db_name.split("-")[0],  
                row.question,
                config_dict['schema_xwalk_directory'],
                column_naturalness = int(nat_cat_dict[col_naturalness]),
                table_naturalness =  int(nat_cat_dict[tab_naturalness]),
                log=True,
                filename_suffix = config_dict['schema_xwalk_filename_suffix'],
                filename_prefix = config_dict['schema_xwalk_filename_prefix'],
                service=config_dict['nltosql_service'],
                model_name=config_dict['nltosql_model'],
                db_type=db_info["db-type"],
                db_list_file=db_list_file
            )

            if quota > 0:
                time.sleep(60 / (quota - 1))

            q_sql_predicteds.append(q_sql_predicted['denaturalized_response'])
            q_prompts.append(q_sql_predicted['prompt'])
            q_sql_predicteds_naturalized.append(q_sql_predicted['response'])

        q_nl_df['prompt'] = q_prompts
        q_nl_df['query_predicted'] = q_sql_predicteds
        q_nl_df['query_predicted_on_naturalized_schema'] = q_sql_predicteds_naturalized
        q_nl_df['col_naturalness_modifier'] = col_naturalness
        q_nl_df['tab_naturalness_modifier'] = tab_naturalness
    else:
        q_nl_df = pd.read_excel(
            './db/queries/predicted/{}'.format(config_dict['predicted_filename'])
            )
    return q_nl_df


if __name__ == "__main__":
    """
    Running this as main with the below combinations of benchmark, database, model, and naturalness level
    reproduces the NL-to-SQL annotations used in our analysis.
    NOTE: Unfortunately, the Phind-CodeLlama model cited in our paper is no longer available on TogetherAI,
    so we cannot offer a simple reproducibility solution here. SQL inference output from this model is
    available in the ./db/queries/predicted directory.
    """
    for combo in product(
        [("spider", db) for db in [
        'battle_death',
        'car_1',
        'concert_singer',
        'course_teach',
        'cre_Doc_Template_Mgt',
        'dog_kennels',
        'employee_hire_evaluation',
        'flight_2',
        'museum_visit',
        'network_1',
        'orchestra',
        'pets_1',
        'poker_player',
        'real_estate_properties',
        'singer',
        'student_transcripts_tracking',
        'tvshow',
        'voter_1',
        'world_1',
        'wta_1'
        ]] +
        [("snails", db) for db in [
        "ASIS_20161108_HerpInv_Database",
        "ATBI",
        "CratersWildlifeObservations",
        "KlamathInvasiveSpecies",
        "NorthernPlainsFireManagement",
        "NTSB",
        "NYSED_SRC2022",
        "PacificIslandLandbirds",
        "SBODemoUS-Banking",
        "SBODemoUS-Business Partners",
        "SBODemoUS-Finance",
        "SBODemoUS-General",
        "SBODemoUS-Human Resources",
        "SBODemoUS-Inventory and Production",
        "SBODemoUS-Reports",
        "SBODemoUS-Sales Opportunities",
        "SBODemoUS-Service"
        ]]
        ,
        [
            "gpt-4o", 
            "gpt-3.5-turbo",
            "DINSQL",
            "CodeS",
            # "Phind-CodeLlama-34B-v2" #Use only with bypass_nl_sql_inference=True in main call below
        ],
        [
            "NATIVE", 
            "N1", 
            "N2", 
            "N3"
        ]
    ):
        print(combo)
        main(
            model=combo[1],
            service="openai",
            naturalness=combo[2],
            database=combo[0][1],
            bypass_nl_sql_inference=False,
            db_list_file={
                "spider": ".local/spider_dbinfo.json",
                "snails": ".local/dbinfo.json"
                }[combo[0][0]]
        )