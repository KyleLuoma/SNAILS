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


This file is provided for SNAILS artifact reproducibility purposes.
The provided MS SQL SNAILS database instances have already had the natural
view buidling process applied, and so it is not necessary to run this prior
to querying a natural view in the SNAILS dataset.
"""

import SNAILS_Artifacts.naturalness_classifiers.schemaclassifier as schemaclassifier
import src.schemarenamer as schemarenamer
import src.natural_view_builder as natural_view_builder
import pandas as pd
import argparse

def main(args):
    if args.database != None:
        db_name = args.database
    else:
        db_name = "ATBI"

    if args.build_view != None:
        build_view = True
    else:
        build_view = False

    score_save_path = f"./data/schema_classifier_renamer_view_builder_output/{db_name}_db_classifier_score_df.xlsx"
    try:
        db_classifier_score_df = pd.read_excel(score_save_path)
        print(f"Loading database naturalness scores from {score_save_path}.")
    except FileNotFoundError as e:
        print(f"No score file exists, creating new scorefile with the schema classifier.")
        db_classifier_score_df = schemaclassifier.classify_db_schema(
            db_name, 
            db_type="ms sql"
            )
        db_classifier_score_df.to_excel(score_save_path)

    xwalk_save_path = f"./data/schema_classifier_renamer_view_builder_output/{db_name}_schema_xwalk.xlsx"
    try:
        schema_xwalk = pd.read_excel(xwalk_save_path)
        print(f"Loading database naturalness crosswalk from {xwalk_save_path}.")
    except FileNotFoundError as e:
        print(f"No naturalness crosswalk exists, generating natural identifiers using the schema renamer. This will take a while.")
        schema_xwalk = schemarenamer.do_schema_renaming(
            db_name, 
            continuous_write=False, 
            db_classifier_score_df=db_classifier_score_df,
            db_type="ms sql",
            only_most_natural=True,
            verbose=False
            )
        schema_xwalk.to_excel(xwalk_save_path)
        print(f"Schema crosswalk saved to {xwalk_save_path}. Before generating natural views, you should inspect the results and make any necessary corrections.")

    if not build_view:
        return

    view_builder = natural_view_builder.NaturalViewBuilder()
    view_queries = view_builder.build_natural_view_queries(
        database_name=db_name,
        xwalk_df=schema_xwalk,
        )
    view_sql = ""
    for query in view_queries:
        view_name = query.split(".")[1].split(" AS")[0]
        view_sql += f"{query}\n\n"
    view_save_path = f"./data/schema_classifier_renamer_view_builder_output/{db_name}_natural_views.sql"
    with open(view_save_path, "w") as vf:
        vf.write(view_sql)
    print(f"natural views for {db_name} saved to {view_save_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process database name.")
    parser.add_argument("--database", required=True, help="Name of the database")
    parser.add_argument(
        "--build_view", 
        required=False, 
        help="Generate the view .sql queries. Retrieves saved .xlsx files if they exist, otherwise runs classification and renaming first.",
        action="store_const", 
        const=True
        )
    args = parser.parse_args()
    main(args)

    

