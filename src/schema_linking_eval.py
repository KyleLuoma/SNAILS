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

import src.query_profiler as qp
import pandas as pd
import multiprocessing
from multiprocessing import Process


def compare_query_schema_elements(
        gold: str, predicted: str,
        verbose: bool = False,
        profiler_use_shell: bool = False
        ) -> dict:
    """
    Compares the schema elements (tables and columns) of two SQL queries and calculates
    precision, recall, and F1 score based on the matching, missing, and extra elements.
    Args:
        gold (str): The gold standard SQL query.
        predicted (str): The predicted SQL query to be compared against the gold standard.
        verbose (bool, optional): If True, prints detailed comparison results. Defaults to False.
    Returns:
        dict: A dictionary containing the following keys:
            - matching_tables (set): Tables that are present in both gold and predicted queries.
            - matching_columns (set): Columns that are present in both gold and predicted queries.
            - missing_tables (set): Tables that are present in the gold query but missing in the predicted query.
            - missing_columns (set): Columns that are present in the gold query but missing in the predicted query.
            - extra_tables (set): Tables that are present in the predicted query but not in the gold query.
            - extra_columns (set): Columns that are present in the predicted query but not in the gold query.
            - linking_score (float): The recall score of the predicted query.
            - recall (float): The recall score of the predicted query.
            - precision (float): The precision score of the predicted query.
            - f1 (float): The F1 score of the predicted query.
    """
    profiler = qp.QueryProfiler(use_shell=profiler_use_shell)

    gold_df = profiler.get_identifiers_and_labels_df(
        query=gold.strip().lower(),
        include_brackets=False
    )

    pred_df = profiler.get_identifiers_and_labels_df(
        query=str(predicted).strip().lower(),
        include_brackets=False
    )

    gold_tables = set(gold_df.query(
        "stat_key == 'table'"
        )['stat_value'].to_list())
    pred_tables = set(pred_df.query(
        "stat_key == 'table'"
    )['stat_value'].to_list())

    gold_columns = set(gold_df.query(
        "stat_key == 'column'"
    )['stat_value'].to_list())
    pred_columns = set(pred_df.query(
        "stat_key == 'column'"
    )['stat_value'].to_list())

    pred_missing_tables = gold_tables - pred_tables
    pred_missing_columns = gold_columns - pred_columns
    pred_matching_columns = pred_columns.intersection(gold_columns)
    pred_matching_tables = pred_tables.intersection(gold_tables)
    pred_extra_tables = pred_tables - gold_tables
    pred_extra_columns = pred_columns - gold_columns

    # Recall is count of identifiers in predicted that are also in gold
    # divided by count of identifiers required (matched + missing)
    try:
        recall = (
            (len(pred_matching_columns) + len(pred_matching_tables))
                /
            (len(pred_matching_columns) + len(pred_matching_tables) + len(pred_missing_columns) + len(pred_missing_tables))
            )
    except ZeroDivisionError as e:
        recall = 0
    
    # Precision is count of identifiers in predicted that are also in gold
    # divided by count of identifiers in the predicted query (matched + extra)
    try:
        precision = (
            (len(pred_matching_columns) + len(pred_matching_tables))
                /
            (len(pred_matching_columns) + len(pred_matching_tables) + len(pred_extra_columns) + len(pred_extra_tables))
        )
    except ZeroDivisionError as e:
        precision = 0

    try:
        f1 = 2 * ((precision * recall) / (recall + precision))
    except ZeroDivisionError as e:
        f1 = 0

    if(verbose):
        print("Matching tables:", pred_matching_tables)
        print("Matching columns:", pred_matching_columns)
        print("Missing tables:", pred_missing_tables)
        print("Missing columns:", pred_missing_columns)
        print("Extra tables:", pred_extra_tables)
        print("Extra columns:", pred_extra_columns)
        print("Linking score (Recall):", str(recall))
        print("Linking score (Precision)", str(precision))
        print("Linking score (F1)", str(f1))

    return {
        "matching_tables": pred_matching_tables,
        "matching_columns": pred_matching_columns,
        "missing_tables": pred_missing_tables,
        "missing_columns": pred_missing_columns,
        "extra_tables": pred_extra_tables,
        "extra_columns": pred_extra_columns,
        "linking_score": recall,
        "recall": recall,
        "precision": precision,
        "f1": f1
    }


def mp_compare_query_schema_elements(q_nl_df: pd.DataFrame) -> dict:
    """
    Compares query schema elements in a DataFrame using multiprocessing.
    This function takes a DataFrame containing natural language queries and their corresponding
    gold and predicted schema elements. It uses multiprocessing to compare the schema elements
    for each query and stores the results in a dictionary.
    Args:
        q_nl_df (pd.DataFrame): A DataFrame with columns 'query_gold', 'query_predicted', and 'number'.
                                'query_gold' contains the gold standard schema elements,
                                'query_predicted' contains the predicted schema elements,
                                and 'number' is a unique identifier for each query.
    Returns:
        dict: A dictionary where the keys are query numbers and the values are the results of
              comparing the gold and predicted schema elements for each query.
    """

    def f(gold, predicted, q_num, result_dict):
        result = compare_query_schema_elements(gold, predicted)
        result_dict[q_num] = result

    manager = multiprocessing.Manager()
    result_dict = manager.dict()
    processes = []
    for row in q_nl_df.itertuples():
        processes.append(
            Process(
                target=f,
                args=(
                    row.query_gold,
                    row.query_predicted,
                    row.number,
                    result_dict
                )
            )
        )
    for p in processes:
        p.start()
    for p in processes:
        p.join()
    return result_dict


def update_scores_in_existing_results(filename):
    eval_df = pd.read_excel(filename)
    eval_df['recall'] = eval_df.linking_score
    precision_scores = []
    f1_scores = []
    for row in eval_df.itertuples():
        score_df = compare_query_schema_elements(row.query_gold, row.query_predicted, verbose=True)
        precision_scores.append(score_df['precision'])
        f1_scores.append(score_df['f1'])
    eval_df['precision'] = precision_scores
    eval_df['f1'] = f1_scores
    eval_df.to_excel(filename)
    
def compare_queries():
    gold = """
 select PointID, SnakeID, [Board #], UTMX, UTMY 
 from tblFieldDataCoverBoard cb 
 join tblLocations l on cb.LocationID = l.LocationID 
 join tblLocationsPoints lp on l.LocationID = lp.LocationID 
 where Recapture = 'new' and siteid = '18CB1' 

"""
    predicted = """
SELECT
  LP.POINTID,
  FD.SNAKEID,
  FD.\\"BOARD #\\",
  LP.UTMX,
  LP.UTMY
FROM TBLLOCATIONSPOINTS AS LP
JOIN TBLFIELDDATACOVERBOARD AS FD
  ON LP.LOCATIONID = FD.LOCATIONID
JOIN TBLLOCATIONS AS L
  ON LP.LOCATIONID = L.LOCATIONID
WHERE
  L.SITEID = '18CB1';
"""
    res =  compare_query_schema_elements(gold, predicted)
    print(res)

if __name__ == '__main__':
    # compare_queries()
    mp_compare_query_schema_elements(pd.DataFrame({
        "number": [0, 1],
        "query_gold": [
            "SELECT A FROM ONE",
            "SELECT B FROM TWO"
        ],
        "query_predicted": [
            "SELECT AYE FROM ONE",
            "SELECT B FROM TWO"
        ]
    }))
    
    


