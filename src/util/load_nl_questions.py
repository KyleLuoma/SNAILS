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
import zipfile
import os

def load_nlq_into_df(filename: str, filepath: str = "./db/queries/") -> pd.DataFrame:
    """
    Load natural language questions from a file into a pandas DataFrame.
    The function reads a file containing natural language questions and SQL query pairs
    and their associated metadata,
    processes the content, and returns a pandas DataFrame with the following columns:
    - number: The question number (or -1 if not specified).
    - question: The natural language question.
    - hints: A list of hints associated with the question.
    - notes: A list of notes associated with the question.
    - query_gold: The gold standard query associated with the question.
    Args:
        filename (str): The name of the file containing the questions.
        filepath (str, optional): The path to the directory containing the file. Defaults to "./queries/".
    Returns:
        pandas.DataFrame: A DataFrame containing the processed questions and their metadata.
    """

    if not os.path.isfile(os.path.join(filepath, filename)):
        print("Unzipping NL-SQL Gold Queries into ./db/queries/")
        with zipfile.ZipFile("./db/queries/SNAILS_Gold_Queries.zip", "r") as zip_ref:
            zip_ref.extractall("./db/queries/")

    file = open(filepath + filename)
    filetext = file.read()
    file.close()


    lines = filetext.split("\n")

    q_numbers = []
    q_nl = []
    q_notes = []
    q_hints = []
    q_gold = []

    for line in lines:
        if "--" in line and "@" not in line:
            if ':' in line:
                question = line.split(":")[1].strip()
                q_number = int(line.split(":")[0].replace("--", "").strip())
            else:
                question = line.replace("--", "").strip()
                q_number = -1
            q_nl.append(question)
            temp_hints = []
            temp_notes = []
            q_numbers.append(q_number)
            query = ""
            continue
        if ";" in line and "--" not in line:
            q_hints.append(temp_hints)
            q_notes.append(temp_notes)
            q_gold.append(query)
            continue
        if "@NOTE" in line:
            temp_notes.append(line)
            continue
        if "@HINT" in line:
            temp_hints.append(line)
            continue
        query += (line + " ")

        
    return pd.DataFrame(
        {
            "number" : q_numbers,
            "question" : q_nl,
            "hints" : q_hints,
            "notes" : q_notes,
            "query_gold" : q_gold
        }
    )
        
if __name__ == "__main__":
    db_name = "NTSB"
    df = load_nlq_into_df("{}.sql".format(db_name))
    df.to_excel("./queries/{}-queries.xlsx".format(db_name), index=False)