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
import os
import datetime

class ConsolidatedResultsLoader:
    """
    Class for loading and storing the consolidated results of the NL-to-SQL annotation files
    and other analysis outputs such as token analysis and query statistics

    Attributes
    ----------
    config_dict : dict
        Dictionary containing the configuration parameters for the analysis
    """

    def __init__(self):
        self.config_dict = {
            'annotation_dir': './data/nl-to-sql_performance_annotations/',
            'models': [
                'gemini-1.5-pro-latest',
                'gpt-3.5-turbo', 
                'gpt-4-0125-preview', 
                'gpt-4o',
                'DINSQL',
                'code-bison-32k', 
                'code-llama-7b', 
                'code-llama-34b',
                'Phind-CodeLlama-34B-v2',
                'CodeS'
                ],
            'database': 'all', #Database name or 'all'
            'native_only': True,
            'model_order': {
                'gemini-1.5-pro': 40,
                'gpt-4o': 45,
                'gpt-4-turbo': 50,
                'gpt-3.5': 100,
                'Phind-CodeLlama-34B-v2': 190,
                'code-llama-34b': 200,
                'code-llama-7b': 300,
                'code-bison-32k': 400,
                'DINSQL': 46,
                'CodeS': 500
            },
            'sbod_module_number': {
                'Banking': 100,
                'Business Partners': 200,
                'Finance': 300,
                'General': 400,
                'Human Resources': 500,
                'Inventory and Production': 600,
                'Reports': 700,
                'Sales Opportunities': 800,
                'Service': 900
            },
            'naturalness_order': {
                "NATIVE": 100,
                "N1": 200,
                "N2": 300,
                "N3": 400,
                "N4": 150
            }
        }

    def get_joined_dataframes(
        self,
        jointype='left'
        ) -> pd.DataFrame:
        """
        Joins all of the dataframes into a single dataframe. The join condition is a composite of model, database name, naturalness level, and question number
        """

        # Join question tokens:
        joined_df = self.load_annotation_files().set_index([
            'tokenizer_model', 'database', 'number'
            ]).join(
                self.load_question_token_analysis_files()[['model', 'database', 'number', 'question_tokens']].rename(
                        columns={'model': 'tokenizer_model'}
                    ).set_index(
                        ['tokenizer_model', 'database', 'number']
                    ),
                how=jointype,
                lsuffix='_annotation',
                rsuffix='_question_tokens'
            ).reset_index(drop=False)
        
        # Join prompt token counts
        joined_df = joined_df.rename(columns={'col_naturalness_modifier': 'naturalness'}).set_index([
            'tokenizer_model', 'database', 'naturalness', 'number', 
        ]).join(
            self.load_prompt_tokens().set_index(
                ['tokenizer_model', 'database', 'naturalness', 'number']
            )[['prompt_token_count']],
            how=jointype,
            lsuffix='_annotation',
            rsuffix='_prompt_tokens'
        ).reset_index(drop=False)

        # Join word identifier sentence similarity scores
        joined_df = joined_df.rename(columns={'number': 'question_number'}).set_index([
            'database', 'question_number', 'naturalness'
        ]).join(
            self.load_world_level_similarities().set_index(
                ['database', 'question_number', 'naturalness']
            ).rename(columns={
                'mean_max_similarity': 'word_level_mean_max_cosine_similarity'
                })[['word_level_mean_max_cosine_similarity']],
            how=jointype
        ).reset_index(drop=False)
        
        # Join sentence level similarity scores
        sent_sim_df = self.load_sentence_level_similarities()
        sent_sim_df = sent_sim_df.rename(columns={
            'native_cosine_similarity': 'NATIVE',
            'N1_cosine_similarity': 'N1',
            'N2_cosine_similarity': 'N2',
            'N3_cosine_similarity': 'N3'
        })[['database', 'question_number', 'NATIVE', 'N1', 'N2', 'N3']]
        sent_sim_df = sent_sim_df.drop_duplicates().dropna(how="all")
        sent_sim_df = sent_sim_df.melt(
            id_vars=['database', 'question_number'],
            value_vars=['NATIVE', 'N1', 'N2', 'N3'],
            value_name='sentence_level_cosine_similarity',
            var_name='naturalness'
        )
        joined_df = joined_df.set_index([
            'database', 'question_number', 'naturalness'
        ]).join(
            sent_sim_df.set_index(
                ['database', 'question_number', 'naturalness']
            ),
            how=jointype
        ).reset_index()

        # Join token:char ratios
        ratio_df = self.load_query_token_character_ratio_file()
        joined_df = joined_df.set_index([
            'tokenizer_model', 'database', 'naturalness', 'question_number'
        ]).join(
            ratio_df.set_index([
                'tokenizer_model', 'database', 'naturalness', 'question_number'
            ]),
            how=jointype
        ).reset_index()
        
        joined_df = joined_df.drop([col for col in joined_df.columns if 'Unnamed:' in col], axis=1)

        return joined_df



    def load_prompt_tokens(
            self,
            file_directory: str = "./data/tokenizer_analysis/"
    ) -> pd.DataFrame:
        """
        Load the token analysis data generated by the tokenizer_analysis.ipynb workbook
        The file contains all question prompts and their tokenizations generated
        by each model used in the experiments.

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
            
        Returns
        -------
        token_df : pd.DataFrame
            Pandas Dataframe containing all of the prompt token files
        """

        try:
            token_df = pd.read_excel(f'{file_directory}/prompts_tokenized.xlsx')
        except FileNotFoundError as e:
            print(e)
            print("File not found. Be sure to run the tokenizer_analysis.ipynb notebook to generate the file.")
            token_df = None

        return token_df


    def load_sentence_level_similarities(
            self,
            file_directory: str = "./data/tokenizer_analysis/"
    ) -> pd.DataFrame:
        """
        Load the sentence level embedding similarity comparisons generated by the tokenizer_analysis.ipynb workbook
        Scores are based on cosine similarity (distance) between the semantic embeddings (SentenceTransformers)
        generated for a NL question and a corresponding gold query for each naturalness level.

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
            
        Returns
        -------
        similarity_df : pd.DataFrame
            Pandas Dataframe containing all of the question-query similarity scores for each naturalness level
        """

        try:
            similarity_df = pd.read_excel(f'{file_directory}/question-identifier-sentence-similarity.xlsx')
        except FileNotFoundError as e:
            print(e)
            print("File not found. Be sure to run the tokenizer_analysis.ipynb notebook to generate the file.")
            similarity_df = None

        return similarity_df
    

    def load_world_level_similarities(
            self,
            file_directory: str = "./data/tokenizer_analysis/"
    ) -> pd.DataFrame:
        """
        Load the word - identifier level embedding similarity comparisons generated by the tokenizer_analysis.ipynb workbook.
        scores are based on the highest cosine similarity distance between a schema identifier and a word in the 
        natural language question.

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
            
        Returns
        -------
        similarity_df : pd.DataFrame
            Pandas Dataframe containing all of the identifier-word similarity scores for each naturalness level
        """

        try:
            similarity_df = pd.read_excel(f'{file_directory}/word-identifier-sentence-similarity.xlsx')
            similarity_df['naturalness'] = similarity_df.naturalness.str.upper()
        except FileNotFoundError as e:
            print(e)
            print("File not found. Be sure to run the tokenizer_analysis.ipynb notebook to generate the file.")
            similarity_df = None

        return similarity_df
    

    def load_identifier_token_analysis_files(
            self,
            file_directory: str = './data/tokenizer_analysis/'        
    ) -> pd.DataFrame:
        """
        Load the token analysis data generated by the tokenizer_analysis.ipynb workbook
        The file contains all database identifiers and their tokenizations generated
        by each model used in the experiments.

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
            
        Returns
        -------
        token_df : pd.DataFrame
            Pandas Dataframe containing all of the token files
        """

        try:
            print("Loading identifier token analysis files...")
            token_df = pd.read_excel(f'{file_directory}/identifier-tokens-all-models.xlsx')
            print(token_df.head())
        except FileNotFoundError as e:
            print(e)
            print("File not found. Be sure to run the tokenizer_analysis.ipynb notebook to generate the file.")
            token_df = None

        return token_df
    

    def load_question_token_analysis_files(
            self,
            file_directory: str = './data/tokenizer_analysis/'        
    ) -> pd.DataFrame:
        """
        Load the token analysis data generated by the tokenizer_analysis.ipynb workbook

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
            
        Returns
        -------
        token_df : pd.DataFrame
            Pandas Dataframe containing all of the token files
        """

        try:
            token_df = pd.read_excel(f'{file_directory}/question-tokens-all-models.xlsx')
        except FileNotFoundError as e:
            print(e)
            print("File not found. Be sure to run the tokenizer_analysis.ipynb notebook to generate the file.")
            token_df = None

        return token_df
    

    def load_query_token_character_ratio_file(
            self,
            file_directory: str = './data/tokenizer_analysis'
    ) -> pd.DataFrame:
        """
        Load query-level mean token:char ratios generated by the tokenizer_analysis.ipynb workbook

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
            
        Returns
        -------
        ratio_df : pd.DataFrame
            Pandas Dataframe containing all of the ratio means at the question-query pair level
        """

        try:
            ratio_df = pd.read_excel(f'{file_directory}/query-token-char-ratios.xlsx')
            ratio_df["naturalness"] = ratio_df.naturalness.str.upper()
            ratio_df = ratio_df.rename(columns={"model":"tokenizer_model"})
        except FileNotFoundError as e:
            print(e)
            print("File not found. Be sure to run the tokenizer_analysis.ipynb notebook to generate the file.")
            ratio_df = None

        return ratio_df
    

    def load_annotation_files(
            self, 
            annotation_directory: str = None,
            database: str  = None,
            remove_error_columns: bool = True
    ) -> pd.DataFrame:
        """
        Load all of the human-validated NL-to-SQL annotation files into a single dataframe

        Parameters
        ----------
        annotation_directory : str
            Directory where the annotation files are stored
        database : str
            Name of the database to filter by. If None, all databases will be loaded
        remove_error_columns : bool
            Option to exclude error classification data from annotations. 
            This is because there is an improved error classification method that supersedes this data.
            
        Returns
        -------
        annotation_df : pd.DataFrame
            Pandas Dataframe containing all of the annotation files
        """
        
        if annotation_directory == None:
            annotation_directory = self.config_dict['annotation_dir']
        if database == None:
            database = self.config_dict['database']

        # Get a list of .xlsx files in the annotation directory
        annotation_files = os.listdir(annotation_directory)
        if database != 'all':
            annotation_files = [
                f for f in annotation_files 
                if database in f 
                    and '.xlsx' in f 
                    and '~' not in f]
        else:
            annotation_files = [f for f in annotation_files if '.xlsx' in f and '~' not in f]

        temp_dfs = []
        for file in annotation_files:
            skip = True
            for mdl in self.config_dict['models']:
                if mdl in file:
                    skip = False
            if skip:
                continue  
            temp_df = pd.read_excel(annotation_directory + file)
            if 'gpt-3' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-gpt')[0]
                temp_df['model'] = 'gpt-3.5'
                temp_df['tokenizer_model'] = 'gpt-35-turbo-16k'
            elif 'gpt-4-' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-gpt')[0]
                temp_df['model'] = 'gpt-4-turbo'
                temp_df['tokenizer_model'] = 'gpt-35-turbo-16k'
            elif 'gpt-4o' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-gpt')[0]
                temp_df['model'] = 'gpt-4o'
                temp_df['tokenizer_model'] = 'gpt-35-turbo-16k'
            elif 'gemini-1.5-pro' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-gemini')[0]
                temp_df['model'] = 'gemini-1.5-pro'
                temp_df['tokenizer_model'] = 'gemini'
            elif 'code-bison-32k' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-code-bison-32k')[0]
                temp_df['model'] = 'code-bison-32k'
                temp_df['tokenizer_model'] = 'code-bison'
            elif 'code-bison' in file:
                pass
                # temp_df['database'] = file.split('.xlsx')[0].split('-code-bison')[0]
                # temp_df['model'] = 'code-bison'
            elif 'code-llama-7b' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-code-llama-7b')[0]
                temp_df['model'] = 'code-llama-7b'
                temp_df['tokenizer_model'] = 'code-llama'
            elif 'code-llama-34b' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-code-llama-34b')[0]
                temp_df['model'] = 'code-llama-34b'
                temp_df['tokenizer_model'] = 'code-llama'
            elif 'Phind-CodeLlama-34B-v2' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-Phind-CodeLlama-34B-v2')[0]
                temp_df['model'] = 'Phind-CodeLlama-34B-v2'
                temp_df['tokenizer_model'] = 'code-llama'
            elif 'DINSQL' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-DINSQL')[0]
                temp_df['model'] = 'DINSQL'
                temp_df['tokenizer_model'] = 'gpt-35-turbo-16k'
            elif 'CodeS' in file:
                temp_df['database'] = file.split('.xlsx')[0].split('-CodeS')[0]
                temp_df['model'] = 'CodeS'
                temp_df['tokenizer_model'] = 'gpt-35-turbo-16k'
            temp_df['source_file'] = file


            temp_df['question_number_combined_modules'] = temp_df.apply(
                lambda row: row.number if 'SBODemoUS' not in row.database else (
                    self.config_dict['sbod_module_number'][row.database.split("-")[1]] + row.number
                    ),
                    axis=1
            )

            temp_df['naturalness_order'] = temp_df.col_naturalness_modifier.apply(
                lambda x: self.config_dict['naturalness_order'][x]
            )

            temp_df['schema_identifier_N1'] = temp_df.apply(
                lambda row: row.schema_col_N1 + row.schema_tab_N1, axis = 1
            )
            temp_df['schema_identifier_N2'] = temp_df.apply(
                lambda row: row.schema_col_N2 + row.schema_tab_N2, axis = 1
            )
            temp_df['schema_identifier_N3'] = temp_df.apply(
                lambda row: row.schema_col_N3 + row.schema_tab_N3, axis = 1
            )
            temp_df['schema_identifier_N1_pct'] = temp_df.apply(
                lambda row: row.schema_identifier_N1 / (row.schema_tab_count + row.schema_col_count), axis = 1
            )
            temp_df['schema_identifier_N2_pct'] = temp_df.apply(
                lambda row: row.schema_identifier_N2 / (row.schema_tab_count + row.schema_col_count), axis = 1
            )
            temp_df['schema_identifier_N3_pct'] = temp_df.apply(
                lambda row: row.schema_identifier_N3 / (row.schema_tab_count + row.schema_col_count), axis = 1
            )

            temp_df['Qg_identifier_N1'] = temp_df.apply(
                lambda row: row.Qg_col_N1 + row.Qg_tab_N1, axis = 1
            )
            temp_df['Qg_identifier_N2'] = temp_df.apply(
                lambda row: row.Qg_col_N2 + row.Qg_tab_N2, axis = 1
            )
            temp_df['Qg_identifier_N3'] = temp_df.apply(
                lambda row: row.Qg_col_N3 + row.Qg_tab_N3, axis = 1
            )

            temp_df['Qg_identifier_N1_pct'] = temp_df.apply(
                lambda row: row.Qg_identifier_N1 / (row.Qg_tot_tabs + row.Qg_tot_cols), axis = 1
            )
            temp_df['Qg_identifier_N2_pct'] = temp_df.apply(
                lambda row: row.Qg_identifier_N2 / (row.Qg_tot_tabs + row.Qg_tot_cols), axis = 1
            )
            temp_df['Qg_identifier_N3_pct'] = temp_df.apply(
                lambda row: row.Qg_identifier_N3 / (row.Qg_tot_tabs + row.Qg_tot_cols), axis = 1
            )

            print(file)
            temp_df['model_order'] = temp_df.model.apply(
                lambda x: self.config_dict['model_order'][x]
            )

            temp_dfs.append(temp_df)

        annotation_df = pd.concat(
            temp_dfs,
            axis=0
        )
        annotation_df['query_stat_count'] = annotation_df.query_stats.apply(
            lambda x: len(x.split(','))
            )
        annotation_df['database'] = annotation_df.apply(
            lambda row: row.database.split("-")[0] if "SBO" not in row.database else "-".join(row.database.split("-")[:2]), 
            axis=1)
        
        if remove_error_columns:
            deprecated_cols = [
                'sql_server_errors', 
                'error_classification', 
                'syntax_error_count', 
                'hallucination_count', 
                'misplaced_column_count'
                ]
            annotation_df = annotation_df.drop(deprecated_cols, axis=1)

        return annotation_df
    


    def load_identifier_crosswalks(
            self,
            file_directory = "./db/schema-xwalks/consolidated_and_validated",
            SBODemo_full = False
    ) -> pd.DataFrame:
        """
        Load a single dataframe containing identifier naturalness crosswalk data from all databases

        Parameters
        ----------
        file_directory : str
            Directory where the files are stored.
        SBODemo_full : bool
            Use crosswalk containing ALL SBODemo identifiers (as opposed to the benchmark subset)

        Returns
        -------
        A single dataframe containing identifier naturalness crosswalk data from all databases
        """
        directory_files = os.listdir(file_directory)
        file_list = []
        for f in directory_files:
            if not SBODemo_full and "US-full" in f:
                continue
            elif SBODemo_full and "US-consolidated" in f:
                continue
            if "consolidated-xwalk.xlsx" in f and "~" not in f:
                file_list.append(f)

        xwalk_df = pd.concat([pd.read_excel(f"{file_directory}/{f}") for f in file_list])
        return xwalk_df



def export_gold_data():
    loader = ConsolidatedResultsLoader()
    df = loader.get_joined_dataframes()
    export_columns = list(df.columns)
    exclude_columns = [
        "hints", "notes", "tab_naturalness_modifier", "Qg_col_N4", "Qg_tab_N4", "schema_col_N4", "schema_tab_N4", "level_0"
    ]
    export_columns = [c for c in export_columns if c not in exclude_columns]
    df = df[export_columns]
    date_stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    df.to_excel(f"./data/gold-data/analysis-gold-data-{date_stamp}.xlsx", index=False)


def load_identifier_crosswalks_test():
    loader = ConsolidatedResultsLoader()
    loader.load_identifier_crosswalks()

def load_annotation_files_test():
    loader = ConsolidatedResultsLoader()
    df = loader.get_joined_dataframes(jointype="inner")
    print(df.shape[0])
    df[[
        "source_file", "database", "model", "question_number", "question", "naturalness", "recall"]].groupby([
            "source_file", "database", "model", "question_number", "question", "naturalness"
        ]).count().query("database=='CratersWildlifeObservations' and naturalness=='N4'").to_excel("./temp_data/duplicate_issues.xlsx")
    

    

if __name__ == "__main__":
    export_gold_data()
    # load_identifier_crosswalks_test()
    # load_annotation_files_test()
    
    
