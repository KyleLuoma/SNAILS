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
from src.util.db_util import *
import src.util.db_util
import src.util.db_util_sqlite


def record_evaluation(result_df, query_id, result, message):
    result_df.loc[result_df['query_id'] == query_id, 'Semantic_Equivalence'] = result
    result_df.loc[result_df['query_id'] == query_id, 'Reason'] = message
    return result_df


def compare_gold_to_generated(
        gold, 
        generated, 
        database_name,
        db_type: str = "ms-sql",
        db_list_file: str = "./local/db_info.json"
        ):
    """
    Compare the results of a gold (expected) SQL query to a generated (predicted) SQL query to determine if they are semantically equivalent.
    Parameters:
    gold (str): The gold (expected) SQL query.
    generated (str): The generated (predicted) SQL query.
    database_name (str): The name of the database to query.
    db_type (str, optional): The type of the database. Default is "ms-sql". Options are "sqlite" and "tsql".
    db_list_file (str, optional): The path to the JSON file containing database connection information. Default is "./local/db_info.json".
    Returns:
    dict: A dictionary with keys "equivalent" (bool) indicating if the queries are semantically equivalent, and "reason" (str) providing the reason for the result.
    """
    if db_type == "sqlite":
        do_query = src.util.db_util_sqlite.do_query
    elif db_type == "tsql":
        do_query = src.util.db_util.do_query
    else:
        do_query = src.util.db_util.do_query
    
# Fetch results from databases:
    result_dict = {
        "equivalent": False,
        "reason": ""
    }

    generated_results = pd.DataFrame()
    gold_results = pd.DataFrame()

    try:
        gold_results = do_query(
            query=gold, 
            database_name=database_name,
            db_list_file=db_list_file
            )
    except Exception as e:
        return {
            "equivalent": False,
            "reason": "gold query failed with error: {}".format(e)
        }

    try:
        generated_results = do_query(
            query=generated, 
            database_name=database_name,
            db_list_file=db_list_file
            )
    except Exception as e:
        return {
            "equivalent": False,
            "reason": "predicted query failed with error: {}".format(e)
        }

    # ------ Analyze semantic correctness (i.e. same results) ------

    # Check if both results are the same size (if not, then not semantically equivalent)
    if generated_results.shape[0] != gold_results.shape[0]:
        result_dict['equivalent'] = False
        result_dict['reason'] = 'asymmetrical tuple result size'
        return result_dict

    # Check if generated columns are fewer than gold.
    # If generated is higher than gold, it's still possible that the question was answered.
    if generated_results.shape[1] < gold_results.shape[1]:
        result_dict['equivalent'] = False
        result_dict['reason'] = 'Insufficient number of columns in generated result set'

    # Check if result is an empty set (if empty, then tag as undetermined)
    if generated_results.shape[0] == 0 and gold_results.shape[0] == 0:
        result_dict['equivalent'] = False
        result_dict['reason'] = 'empty result set'

    # Compare every row of generated results to every row of gold results:
    # If any row of generated results does not match any row of gold results, then not semantically equivalent
    # If we get through all rows of generated results and they all match, then still could be semantically equivalent
    generated_gold_col_pairs = [] # List of tuples of (generated_col_name, gold_col_name) that match
    generated_sort_by_col = generated_results.columns[0]
    gold_sort_by_col = gold_results.columns[0]

    max_values = 0

    try:
        # Pair up matching columns in gold and generated results. This allows us to 
        # handle cases where the columns are in different orders, and may also
        # have different names. 
        # It's not sufficient for full evaluation because we're only sorting
        # Individual columns; but we pair up the columns here
        # and do a full dataframe comparison next.
        for generated_col_name in generated_results.columns:
            for gold_col_name in gold_results.columns:

                generated_col_temp = generated_results[generated_col_name].copy().astype(str)
                gold_col_temp = gold_results[gold_col_name].copy().astype(str)
                
                generated_col_temp.sort_values(inplace = True, ignore_index = True)
                gold_col_temp.sort_values(inplace = True, ignore_index = True)

                if generated_col_temp.equals(gold_col_temp):
                    generated_gold_col_pairs.append((generated_col_name, gold_col_name))
                    if generated_results[generated_col_name].value_counts().shape[0] > max_values:
                        max_values = generated_results[generated_col_name].value_counts().shape[0]
                        generated_sort_by_col = generated_col_name
                        gold_sort_by_col = gold_col_name

    except TypeError as e:
        result_dict['equivalent'] = False
        result_dict['reason'] = 'type error in column comparison'
        return result_dict
    except UnicodeDecodeError as e:
        result_dict['equivalent'] = False
        result_dict['reason'] = 'UnicodeDecodeError in column comparison'
        return result_dict

    match = True
    generated_results[generated_sort_by_col] = generated_results[generated_sort_by_col].astype(str)
    gold_results[gold_sort_by_col] = gold_results[gold_sort_by_col].astype(str)

    try:
        generated_results = generated_results.sort_values(by = [generated_sort_by_col])
        gold_results = gold_results.sort_values(by = [gold_sort_by_col])
    except:
        print("sorting failed")

    # Using the sorted dataframes, sorted by the most unique columns, we can no
    # compare individual records in each column. If any column does not match,
    # then the result sets are not semantically equivalent    
    col_matches = 0
    for generated_col_ix in range(0, generated_results.shape[1]):
        for gold_col_ix in range(0, gold_results.shape[1]):
            col_matched = True
            for i in range(0, generated_results.shape[0]):
                if str(generated_results.iloc[i, generated_col_ix]) != str(gold_results.iloc[i, gold_col_ix]):
                    col_matched = False
                    break
            if col_matched:
                col_matches += 1
                break
            
    if col_matches != gold_results.shape[1]:
        match = False
        notmatched_message = "full tuple compare failed"

    if not match:
        result_dict['equivalent'] = False
        result_dict['reason'] = notmatched_message
        return result_dict

    else:
        result_dict['equivalent'] = True
        result_dict['reason'] = 'full tuple compare succeeded'
        return result_dict



def do_batch_compare(database_name, result_file):
    """
    Perform a batch comparison of generated queries against gold standard queries.
    This function reads queries from an Excel file, executes them against a specified database,
    and compares the results to determine semantic equivalence. The results of the comparison
    are saved to an Excel file.
    Parameters:
    database_name (str): The name of the database to query.
    result_file (str): The path to the Excel file containing the queries to compare.
    The Excel file should have the following columns:
    - query_id: Unique identifier for the query.
    - question: The natural language question.
    - gold_query: The gold standard SQL query.
    - denaturalized_response: The generated SQL query to compare against the gold standard.
    The function performs the following steps:
    1. Reads the queries from the Excel file.
    2. Executes the gold and generated queries against the specified database.
    3. Compares the results of the queries to determine semantic equivalence.
    4. Records the results of the comparison, including reasons for any mismatches.
    5. Saves the comparison results to an Excel file.
    The comparison checks for:
    - Asymmetrical tuple result size.
    - Insufficient number of columns in the generated result set.
    - Empty result sets.
    - Full tuple comparison, including column pairing and sorting.
    If the results are not semantically equivalent, the mismatched result sets are saved to separate Excel files.
    Returns:
    None
    """

    query_df = pd.read_excel(result_file, sheet_name = 'Sheet1')
    table_name = 'semantic_evaluation'
    full_compare = True
    result_df = query_df.copy()
    result_df['Semantic_Equivalence'] = ['UNDETERMINED' for i in range(0, query_df.shape[0])]
    result_df['Reason'] = ['' for i in range(0, query_df.shape[0])]

    for row in query_df.itertuples():
        gold = row.gold_query
        generated = row.denaturalized_response

        # Fetch results from databases:

        print("\n\n\n----------------------------------------------------------------")
        print("Question:", row.question)

        generated_results = pd.DataFrame()
        gold_results = pd.DataFrame()

        try:
            print("\nRunning GOLD", row.gold_query.strip())
            gold_results = do_query(gold, database_name)
            print("\n", gold_results)
        except Exception as e:
            print(e)

        try:
            print("\nRunning generated", row.denaturalized_response.strip())
            generated_results = do_query(generated, database_name)
            print("\n", generated_results)
        except Exception as e:
            print(e)

        # ------ Analyze semantic correctness (i.e. same results) ------

        # Check if both results are the same size (if not, then not semantically equivalent)
        if generated_results.shape[0] != gold_results.shape[0]:
            result_df = record_evaluation(
                result_df, row.query_id, 'FALSE', 'asymmetrical tuple result size'
            )
            continue

        # Check if generated columns are fewer than gold.
        # If generated is higher than gold, it's still possible that the question was answered.
        if generated_results.shape[1] < gold_results.shape[1]:
            result_df = record_evaluation(
                result_df, row.query_id, 'FALSE', 'Insufficient number of columns in generated result set'
            )
            continue

        # Check if result is an empty set (if empty, then tag as undetermined)
        if generated_results.shape[0] == 0 and gold_results.shape[0] == 0:
            result_df = record_evaluation(
                result_df, row.query_id, 'UNDETERMINED', 'empty result set'
            )
            continue

        # Compare every row of generated results to every row of gold results:
        # If any row of generated results does not match any row of gold results, then not semantically equivalent
        # If we get through all rows of generated results and they all match, then semantically equivalent
        if full_compare:

            generated_gold_col_pairs = [] # List of tuples of (generated_col_name, gold_col_name) that match

            generated_sort_by_col = generated_results.columns[0]
            gold_sort_by_col = gold_results.columns[0]

            max_values = 0

            try:
                # Pair up matching columns in gold and generated results. This allows us to 
                # handle cases where the columns are in different orders, and may also
                # have different names. 
                # It's not sufficient for full evaluation because we're only sorting
                # Individual columns; but we pair up the columns here
                # and do a full dataframe comparison next.
                for generated_col_name in generated_results.columns:
                    for gold_col_name in gold_results.columns:

                        generated_col_temp = generated_results[generated_col_name].copy().astype(str)
                        gold_col_temp = gold_results[gold_col_name].copy().astype(str)
                        
                        generated_col_temp.sort_values(inplace = True, ignore_index = True)
                        gold_col_temp.sort_values(inplace = True, ignore_index = True)

                        print(gold_col_temp)
                        print(generated_col_temp)

                        if generated_col_temp.equals(gold_col_temp):
                            generated_gold_col_pairs.append((generated_col_name, gold_col_name))
                            print(generated_col_name, "Value counts:", generated_results[generated_col_name].value_counts().shape[0])
                            if generated_results[generated_col_name].value_counts().shape[0] > max_values:
                                max_values = generated_results[generated_col_name].value_counts().shape[0]
                                generated_sort_by_col = generated_col_name
                                gold_sort_by_col = gold_col_name

            except TypeError as e:
                print("TypeError", e)
                result_df = record_evaluation(
                    result_df, row.query_id, 'FALSE', 'type error in column comparison'
                )
                continue

            print("generated sorting column:", generated_sort_by_col)
            print("Gold sorting column:", gold_sort_by_col)


            print("Performing full comparison")
            print("Sorting generated by", generated_sort_by_col)
            print("Sorting gold by", gold_sort_by_col)
            match = True
            generated_results[generated_sort_by_col] = generated_results[generated_sort_by_col].astype(str)
            gold_results[gold_sort_by_col] = gold_results[gold_sort_by_col].astype(str)
            try:
                generated_results = generated_results.sort_values(by = [generated_sort_by_col])
                gold_results = gold_results.sort_values(by = [gold_sort_by_col])
            except:
                print("sorting failed")

            print("generated:")
            print(generated_results)
            print("GOLD:")
            print(gold_results)

            col_matches = 0

            # Using the sorted dataframes, sorted by the most unique columns, we can no
            # compare individual records in each column. If any column does not match,
            # then the result sets are not semantically equivalent.
            for generated_col_ix in range(0, generated_results.shape[1]):
                for gold_col_ix in range(0, gold_results.shape[1]):
                    col_matched = True
                    for i in range(0, generated_results.shape[0]):
                        if str(generated_results.iloc[i, generated_col_ix]) != str(gold_results.iloc[i, gold_col_ix]):
                            col_matched = False
                            break
                    if col_matched:
                        col_matches += 1
                        break
                print("col_matches", col_matches)
                    
            if col_matches != gold_results.shape[1]:
                match = False
                notmatched_message = "full tuple compare failed"

            if not match:
                result_df = record_evaluation(
                    result_df, row.query_id, 'FALSE', notmatched_message
                )
                pd.concat(
                    [generated_results, gold_results], 
                    axis = 1, 
                    sort = False
                    ).to_excel(
                    './batch-results/semantic-failure-result-sets/tuple-mismatch-q{}.xlsx'.format(row.query_id)
                )
            else:
                result_df = record_evaluation(
                    result_df, row.query_id, 'TRUE', 'full tuple compare succeeded'
                )


        else:
            # For the first tuple in gold results, gold_results.iloc[0]
            #    For each tuple in generated results compare to gold results.
            #    We need to perform a bag comparison of two bags with items in an arbitrary order

            # Disprove that for every tuple in gold there exists at least one matching tuple in generated:
            # Do this by cycling through all tuples in generated to see if we can find a situation where no
            # tuple in generated matches the first tuple in the gold result set.
            # If the results are equivalent, then there must be at least one tuple in generated that matches
            # any given tuple (including the first one) in gold.
            generated_matched_gold_row = False
            gold_list = [str(i) for i in gold_results.iloc[0].values]
            gold_list.sort()
            for generated_row in generated_results.iterrows():
                # Create sorted lists of generated and gold tuples:
                generated_list = [str(i) for i in generated_row[1].values]
                generated_list.sort()
                if generated_list == gold_list:
                    generated_matched_gold_row = True
        #    If there are no matches, then mark as not semantically equivalent
            if not generated_matched_gold_row:
                print(row.query_id)
                result_df = record_evaluation(
                    result_df, 'FALSE', 'generated tuples not matched to gold tuple'
                )
                continue

            # Now do the opposite, search all gold tuples for a match against first generated tuple
            gold_matched_generated_row = False
            generated_list = [str(i) for i in generated_results.iloc[0].values]
            generated_list.sort()
            for gold_row in gold_results.iterrows():
                gold_list = [str(i) for i in gold_row[1].values]
                gold_list.sort()
                if gold_list == generated_list:
                    gold_matched_generated_row = True
            if not gold_matched_generated_row:
                print(row.query_id)
                result_df = record_evaluation(
                    result_df, 'FALSE', 'gold tuples not matched to generated tuple'
                )
                continue

            # If we get this far, mark as semantically equivalent.
            result_df = record_evaluation(
                result_df, row.query_id, 'TRUE', 'could not disprove equivalence'
            )

    result_df.to_excel('./batch-results/semantic-evaluation-results.xlsx')


if __name__ == '__main__':
    database_name = 'PacificIslandLandbirds'
    result_file = './batch-results/pacificislandlandbirds-gpt-results.xlsx'
    do_batch_compare(database_name, result_file)

        


    
    



