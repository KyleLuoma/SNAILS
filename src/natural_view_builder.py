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

import src.util.db_util as db_util
import pandas as pd
from pyodbc import ProgrammingError, IntegrityError

class NaturalViewBuilder:
    """
    A class used to build natural views for a database using crosswalks.
    Attributes
    ----------
    xwalk_directory : str
        The directory where the crosswalk files are stored.
    nat_label_lookup : dict
        A dictionary mapping naturalness levels to their labels.
    nat_num_lookup : dict
        A dictionary mapping naturalness labels to their levels.
    Methods
    -------
    initialize_db_nl_schema(database_name: str) -> None
        Initializes the natural language schema in the database.
    populate_db_nl_tables(database_name: str, xwalk_directory: str = None) -> None
        Populates the natural language tables in the database using crosswalk files.
    create_views_in_database(database_name: str, naturalness_level: str = None) -> None
        Creates views in the database based on the naturalness level.
    build_natural_view_queries(database_name: str, target_schema: str = "dbo", xwalk_directory: str = None, view_schema_name: str = "db_nl", naturalness_level: str = "N1") -> list
        Builds the SQL queries for creating natural views in the database.
    """


    def __init__(
            self,
            xwalk_directory: str = "./schema-xwalks/consolidated_and_validated"
            ):
        self.xwalk_directory = xwalk_directory
        self.nat_label_lookup = {
            "N1": "Regular",
            "N2": "Low",
            "N3": "Least"
        }
        self.nat_num_lookup = {self.nat_label_lookup[k]: k for k in self.nat_label_lookup}



    def initialize_db_nl_schema(
            self,
            database_name: str
            ) -> None:
        """
        Initializes the natural language schema in the specified database.
        This method performs the following steps:
        1. Executes the SQL script to create the natural language schema.
        2. Executes the SQL script to create a within-database naturalness crosswalk
        Args:
            database_name (str): The name of the database where the schema will be initialized.
        Raises:
            ProgrammingError: If there is an error executing the SQL script to create the schema.
        """
        try:
            with open("./queries/db_nl_dml/create_db_nl_schema.sql") as f:
                db_util.do_query(
                    f.read(),
                    database_name=database_name
                )
        except ProgrammingError as p:
            print(p)

        with open("./queries/db_nl_dml/create_db_nl_tables.sql") as f:
            db_util.do_query(
                f.read(),
                database_name=database_name
            )



    def populate_db_nl_tables(
            self, 
            database_name: str,
            xwalk_directory: str = None
            ) -> None:
        """
        Populates the database natural language tables with cross-references 
        between native and natural identifiers for tables and columns.
        Args:
            database_name (str): The name of the database to populate.
            xwalk_directory (str, optional): The directory where the crosswalk 
            Excel file is located. If not provided, defaults to self.xwalk_directory.
        Returns:
            None
        """
        if xwalk_directory == None:
            xwalk_directory = self.xwalk_directory
        if xwalk_directory[-1] != "/":
            xwalk_directory += "/"
        crosswalk = pd.read_excel(
            f"{xwalk_directory}{database_name}-consolidated-xwalk.xlsx"
            )
        crosswalk["native_identifier_lwr"] = crosswalk.native_identifier.str.lower()
        table_crosswalk = crosswalk.query(
            "table_or_column == 'table'"
            ).set_index("native_identifier_lwr")
        column_crosswalk = crosswalk.query(
            "table_or_column == 'column'"
            ).set_index("native_identifier_lwr")
        tables_and_columns = db_util.get_tables_and_columns_from_sql_server_db(
            db_name=database_name,
            append_col_types=False
        )
        for table in tables_and_columns:
            if table not in table_crosswalk.native_identifier.to_list():
                print("Skipping table", table, "because it is not in the crosswalk")
                continue
            insert_query =   "INSERT INTO db_nl.native_natural_table_cross_reference "
            insert_query += f"(native_table_name, natural_table_name) "
            insert_query += f"VALUES ('{table}', '{table_crosswalk.loc[table.lower()].N1_identifier}')"
            try:
                db_util.do_query(
                    query=insert_query,
                    database_name=database_name
                )
            except IntegrityError as ie:
                pass

            for column in tables_and_columns[table]:
                if column not in column_crosswalk.native_identifier.to_list():
                    continue
                insert_query =   "INSERT INTO db_nl.native_natural_column_cross_reference "
                insert_query += f"(native_table_name, native_column_name, natural_column_name) "
                insert_query += f"VALUES ('{table}', '{column}', "
                insert_query += f"'{column_crosswalk.loc[column.lower()].N1_identifier}');"
                try:
                    db_util.do_query(
                        query=insert_query,
                        database_name=database_name
                    )
                except IntegrityError as ie:
                    pass
        


    def create_views_in_database(
            self, 
            database_name: str,
            naturalness_level: str = None
            ) -> None:
        """
        Creates views in the specified database. If a naturalness level is provided, 
        it creates a schema for that level and builds the views within that schema. 
        Otherwise, it builds the views in the default schema.
        Args:
            database_name (str): The name of the database where views will be created.
            naturalness_level (str, optional): The level of naturalness for the views. 
                                Defaults to None.
        Returns:
            None
        """
        if naturalness_level == None:
            view_queries = self.build_natural_view_queries(database_name)
        else:
            view_schema_name = f"{self.nat_label_lookup[naturalness_level]}_Naturalness"
            try:
                db_util.do_query(query=f"CREATE SCHEMA {view_schema_name}", database_name=database_name)
            except:
                pass
            view_queries = self.build_natural_view_queries(
                database_name=database_name,
                naturalness_level=naturalness_level,
                view_schema_name=view_schema_name
            )
        for view in view_queries:
            view_name = view.split("CREATE VIEW")[1].split(" AS")[0]
            print(view)
            try:
                db_util.do_query(
                    query=f"DROP VIEW {view_name}", database_name=database_name
                )
            except Exception as e:
                print(e)
                print("Could not drop view", view_name)
            db_util.do_query(
                query=view,
                database_name=database_name
            )



    def build_natural_view_queries(
            self, 
            database_name: str,
            target_schema: str = "dbo",
            xwalk_directory: str = None,
            view_schema_name: str = "db_nl",
            naturalness_level: str = "N1",
            xwalk_df: pd.DataFrame = None
            ) -> list:
        """
        Builds SQL queries to create natural views for tables in a SQL Server database.
        Args:
            database_name (str): The name of the database to query.
            target_schema (str, optional): The schema of the target tables. Defaults to "dbo".
            xwalk_directory (str, optional): The directory containing the crosswalk files. Defaults to None.
            view_schema_name (str, optional): The schema name for the views. Defaults to "db_nl".
            naturalness_level (str, optional): The level of naturalness for the identifiers. Defaults to "N1".
        Returns:
            list: A list of SQL view creation queries.
        """
        if xwalk_directory == None:
            xwalk_directory = self.xwalk_directory
        if xwalk_directory[-1] != "/":
            xwalk_directory += "/"
        tables_and_columns = db_util.get_tables_and_columns_from_sql_server_db(
            database_name, 
            append_col_types=False
            )
        if type(xwalk_df) == None:
            crosswalk = pd.read_excel(f"{xwalk_directory}{database_name}-consolidated-xwalk.xlsx")
        else:
            crosswalk = xwalk_df
        crosswalk["native_identifier_lwr"] = crosswalk.native_identifier.str.lower()
        table_crosswalk = crosswalk.query("table_or_column == 'table'").set_index("native_identifier_lwr")
        column_crosswalk = crosswalk.query("table_or_column == 'column'")
        column_crosswalk = column_crosswalk.drop_duplicates(subset=["native_identifier_lwr"])
        column_crosswalk = column_crosswalk.set_index("native_identifier_lwr")

        view_queries = []
        tables_in_xwalk = table_crosswalk.native_identifier.str.lower().to_list()
        columns_in_xwalk = column_crosswalk.native_identifier.str.lower().to_list()
        for table in tables_and_columns:
            if table.lower() not in tables_in_xwalk:
                continue
            columns_and_aliases = [
                f"[{c}] AS [{column_crosswalk.loc[c.lower()][f"{naturalness_level}_identifier"]}]" 
                for c in tables_and_columns[table] 
                if c.lower() in columns_in_xwalk
                ]
            if len(columns_and_aliases) == 0:
                continue
            view_query =  f"CREATE VIEW {view_schema_name}.[{table_crosswalk.loc[table.lower()][f"{naturalness_level}_identifier"]}] AS\n"
            view_query += f"SELECT {', '.join(columns_and_aliases)}\n"
            view_query += f"FROM {target_schema}.[{table}];"
            view_queries.append(view_query)
        return view_queries



if __name__ == "__main__":
    for db_name in [
                    "ASIS_20161108_HerpInv_Database",
                    "ATBI",
                    "CratersWildlifeObservations",
                    "KlamathInvasiveSpecies",
                    "NYSED_SRC2022",
                    "NorthernPlainsFireManagement",
                    "PacificIslandLandbirds",
                    "SBODemoUS",
                    "NTSB"
                    ]:
        print(db_name)
        builder = NaturalViewBuilder()
        ## Create native : Regular naturalness crosswalks in the database
        # builder.initialize_db_nl_schema(database_name=db_name)
        # builder.populate_db_nl_tables(database_name=db_name)

        ## Build db_nl view for highest naturalness:
        # builder.create_views_in_database(database_name=db_name)

        ## Build virtual schemas at all naturalness levels:
        for nat_level in ["N1", "N2", "N3"]:
            builder.create_views_in_database(database_name=db_name, naturalness_level=nat_level)