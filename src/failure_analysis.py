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
import load_consolidated_results as lcr
import json
import time

def ms_sql_failure_message_parser(
        message: str,
        driver: str = 'ODBC SQL Server Driver'
        ) -> list:
    """ Parse MS SQL Server error message

    Args:
        message (str): error message returned by MS SQL Server
        driver (str): driver used to connect to MS SQL Server

    Returns:
        list: list of errors
    """
    message = message.replace('"', '')
    message = message.replace('(SQLExecDirectW)', '')
    split_on = f"[Microsoft][{driver}][SQL Server]"
    errors = message.split(split_on)
    errors_clean = []
    for error in errors:
        error = error.replace(";", "")
        error = error.split('[')[0]
        error = error.strip()
        errors_clean.append(error)
    errors_clean = errors_clean[1:]
    print(errors_clean)
    return errors_clean



def classify_errors(
        message: str,
        driver: str = None,
        no_parse: bool = False,
        parsed_errors: list = None      
        ) -> dict:
    """ Classify errors into categories and types

    Args:
        message (str): error message returned by MS SQL Server
        driver (str): driver used to connect to MS SQL Server
        no_parse (bool): whether to parse the error message or not
        parsed_errors (list): list of errors already parsed

    Returns:
        dict: dictionary with keys 'error_categories', 'error_types', and 'error_objects'
    """
    error_categories = []
    error_types = []
    error_objects = []
    if not no_parse:
        if driver == None:
            errors = ms_sql_failure_message_parser(message)
        else:
            errors = ms_sql_failure_message_parser(message, driver)
    elif errors != None:
        errors = parsed_errors
    err_object = ""
    for error in errors:
        if 'invalid column name' in error.lower():
            error_types.append('invalid column')
            error_categories.append('schema linking')
            err_object = error.split("'")[1]
        elif 'invalid object name' in error.lower():
            err_object = error.split("'")[1]
            error_types.append('invalid table')
            error_categories.append('schema linking')
        elif 'incorrect syntax near' in error.lower():
            error_types.append('incorrect syntax')
            err_object = error.split("'")[1]
            error_categories.append('invalid SQL')
        elif 'multi-part identifier' in error.lower():
            error_types.append('invalid multipart')
            err_object = error.split('identifier ')[1].strip().split(' ')[0].strip()
            error_categories.append('schema linking')
        elif 'ambiguous column name' in error.lower():
            error_types.append('ambiguous column')
            err_object = error.split("'")[1].strip()
            error_categories.append('other')
        elif 'non-boolean type' in error.lower():
            error_types.append('expected boolean but got non boolean type')
            err_object = error.split("'")[1]
            error_categories.append('schema linking')
        elif 'it is not contained in either an aggregate' in error.lower():
            error_types.append('wrong columns')
            err_object = error.split('Column ')[1].split(' is invalid')[0].strip().replace("'", "")
            error_categories.append('group by')
        elif 'conversion failed when converting the' in error.lower():
            error_types.append('varchar conversion failed')
            err_object = error.split("'")[1]
            error_categories.append('invalid SQL')
        elif '(8134)' in error.lower():
            error_types.append('divide by zero')
            err_object = ''
            error_categories.append('other')
        elif '(153)' in error.lower():
            error_types.append('invalid first in fetch statement')
            err_object = ''
            error_categories.append('invalid SQL')
        elif '(116)' in error.lower():
            error_types.append('only one expression allowed when subquery not in exists')
            err_object = ''
            error_categories.append('invalid SQL')
        elif '(8117)' in error.lower():
            error_types.append('invalid operand for varchar')
            err_object = error.split('is invalid for ')[1].split(' operator')[0].strip()
            error_categories.append('invalid SQL')
        elif '(145)' in error.lower():
            error_types.append('distinct with order by column not in select list')
            err_object = ''
            error_categories.append('other')
        elif '(195)' in error.lower():
            error_types.append('unrecognized function')
            err_object = error.split(' is not a recognized')[0].replace("'", "").strip()
            error_categories.append('invalid SQL')
        elif '(512)' in error.lower():
            error_types.append('subquery returned more than one value when not permitted')
            err_object = ''
            error_categories.append('nested')
        elif '(107)' in error.lower():
            error_types.append('column prefix does not match table or alias')
            err_object = error.split("'")[1]
            error_categories.append('schema linking')
        elif '(1011)' in error.lower():
            error_types.append('correlation specified multiple times')
            err_object = error.split("'")[1]
            error_categories.append('other')
        elif '(402)' in error.lower():
            error_types.append('data type operator incompatibility')
            err_object = ''
            error_categories.append('other')
        elif '(103)' in error.lower():
            error_types.append('identifier too long')
            err_object = error.split("'")[1]
            error_categories.append('invalid SQL')
        elif '(1033)' in error.lower():
            error_types.append('order by clause invalid')
            err_object = ''
            error_categories.append('invalid SQL')
        elif '(306)' in error.lower():
            error_types.append('cannot compare text or ntext')
            err_object = ''
            error_categories.append('invalid SQL')
        elif '(105)' in error.lower():
            error_types.append('unclosed quotation')
            err_object = error.split("'")[1]
            error_categories.append('invalid SQL')
        else:
            error_types.append(error)

        error_objects.append(err_object)
    return {
        'error_categories': error_categories,
        'error_types': error_types,
        'error_objects': error_objects
    }


def make_failure_file_from_annotations(
        annotation_directory: str = './nl-to-sql_performance_annotations/'
        ) -> pd.DataFrame:
    """ Make a failure file from the annotations

    Args:
        annotation_directory (str): directory where the annotations are stored

    Returns:
        pd.DataFrame: failure file
    """
    db_info = json.load(open('.local/dbinfo.json'))
    loader = lcr.ConsolidatedResultsLoader()
    annot_df = loader.get_joined_dataframes()
    error_df = pd.DataFrame({
        "model": [],
        "database": [],
        "question_number": [],
        "naturalness": [],
        "error_categories": [],
        "error_types": [],
        "error_objects": []
    })
    for row in annot_df.itertuples():
        if 'error' in row.result_set_compare_note:
            new_row = {}
            error_classification = classify_errors(
                row.result_set_compare_note,
                db_info[0]['driver']
            )
            for ix in range(0, len(error_classification['error_categories'])):
                new_row['model'] = [row.model]
                new_row['database'] = [row.database]
                new_row['question_number'] = [row.question_number]
                new_row['naturalness'] = [row.naturalness]
                new_row['error_categories'] = [error_classification['error_categories'][ix]]
                new_row['error_types'] = [error_classification['error_types'][ix]]
                new_row['error_objects'] = [error_classification['error_objects'][ix]]
                error_df = pd.concat([
                    error_df, 
                    pd.DataFrame(new_row)
                    ])
    error_df = error_df.drop_duplicates().dropna(how="all")
    return error_df.reset_index(drop=True)


def write_failure_file_to_folder(folder: str = './failure_analysis/') -> None:
    timestamp = time.strftime("%m-%d-%Y")
    df = make_failure_file_from_annotations()
    df.to_excel(f"{folder}failure-annotations-{timestamp}.xlsx", index=False)


if __name__ == '__main__':
    test_message = "predicted query failed with error: ('42S22', \"[42S22] [Microsoft][ODBC SQL Server Driver][SQL Server]Invalid column name 'Station_ID'. (207) (SQLExecDirectW); [42S22] [Microsoft][ODBC SQL Server Driver][SQL Server]Invalid column name 'Common_Name'. (207); [42S22] [Microsoft][ODBC SQL Server Driver][SQL Server]Invalid column name 'Common_Name'. (207); [42S22] [Microsoft][ODBC SQL Server Driver][SQL Server]Invalid column name 'Common_Name'. (207)\")"
    ms_sql_failure_message_parser(test_message)
    write_failure_file_to_folder()