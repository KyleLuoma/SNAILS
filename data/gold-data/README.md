# Gold Data Folder

This folder is dedicated exclusively to storing data files that must remain intact and should not be modified. 

## Contents:

### Schema classification data:

#### File: consolidated-scores-5-9-2024-no-whitespace.xlsx

**Description:** A file containing 3,504 table names and 13,723 column names, their predicted naturalness scores, and manually validated/modified naturalness scores

**Purpose:** Used for schema naturalness lookup for already-classified schemas and also used to train next generation of fine tuned schema naturalness classification models.

**Date created:** 9 May 2024

**Contents description:**
This excel file containes three worksheets: distinct-table, distinct-column, and manual-scores.

    - distinct-table: Contains table name, predicted table score (PRED_TABLE_SCORE) predicted by the SNAILS naturalness classifier, and final score. Final score is the human-modified score that reflects a review of the predicted score and, if required, a modification to the predicted score.
    - distinct-column: Same as distinct-table except for columns.
    - manual-scores: reference to prior manual scoring for consistency


#### File: identifier-scores-evaluated-5-9-2024.xlsx

**Description:** A file containing 17,213 database identifiers and their human-validated naturalness scores

**Purpose:** Used for more streamlined schema naturalness lookup. 

**Date created:** 5-9-2024

**Contents description:**
This file contains a single worksheet with all of the deduplicated identifiers scored and saved in the file consolidated-scores-5-9-2024-no-whitespace.xlsx


#### File: analysis-gold-data-2024-11-14.xlsx
**Description:** A file containing the output of the experiment setup stage of our analysis. The data is generated using the load_consolidated_results.py script. Each row represents a single NL->SQL inference for a given database, naturalness level, and LLM.
Individual performance annotation files are stored in ./nl-to-sql_performance_annotations.

##### ---------- Columns ----------

**tokenizer_model:** LLM tokenizer used for token-based analysis

**database:** name of the database associated with the NL Question : SQL pair

**naturalness:** Naturalness level of the database schema (native, N1, N2, N3)

**question_number:** NL:SQL pair number for the database (can be found in ./queries)	

**question:** Natural language question
	
**query_gold:** The correct SQL query over the native schema

**schema_pruning:** 1 / True is schema_pruning (i.e., subsetting, filtering, etc.) was used, 0 / False if not.

**prompt:** The prompt fed to the LLM for SQL inference

**query_predicted:** query_predicted with identifiers converted to the native schema

**query_predicted_on_naturalized_schema:** The predicted SQL as returned from the LLM 

**query_stats:** A JSON object containing query stats generated by the query parser analyzer

**Qg_col_N1:** A count of Regular (N1) naturalness columns in the gold query

**Qg_tot_cols:** A count of all columns in the gold query

**Qg_col_N2:** A count of Low (N2) naturalness columns in the gold query

**Qg_col_N3:** A count of Least (N3) naturalness columns in the gold query

**Qg_tab_N1:** A count of Regular (N1) naturalness tables in the gold query	

**Qg_tot_tabs:** A count of all tables in the gold query

**Qg_tab_N2:** A count of Low (N2) naturalness tables in the gold query

**Qg_tab_N3:** A count of Least (N3) naturalness tables in the gold query	
	
***schema_col_N1:*** A count of Regular (N1) naturalness columns in the database schema

**schema_col_N2:** A count of Low (N2) naturalness columns in the database schema

**schema_col_N3:** A count of Least (N3) naturalness columns in the database schema

**schema_tab_N1:** A count of Regular (N1) naturalness tables in the database schema

**schema_tab_N2:** A count of Low (N2) naturalness tables in the database schema

**schema_tab_N3:** A count of Least (N3) naturalness tables in the database schema

**schema_tab_count:** Total number of tables in the database schema

**schema_col_count:** Total number of columns in the database schema

**Qg_col_N1_pct:** Percentage of Regular (N1) naturalness columns in the gold query

**Qg_col_N2_pct:** Percentage of Low (N2) naturalness columns in the gold query

**Qg_col_N3_pct:** Percentage of Least (N3) naturalness columns in the gold query

**Qg_tab_N1_pct:** Percentage of Regular (N1) naturalness tables in the gold query

**Qg_tab_N2_pct:** Percentage of Low (N2) naturalness tables in the gold query

**Qg_tab_N3_pct:** Percentage of Least (N3) naturalness tables in the gold query

**schema_col_N1_pct:** Percentage of Regular (N1) naturalness columns in the database schema

**schema_col_N2_pct:** Percentage of Low (N2) naturalness columns in the database schema

**schema_col_N3_pct:** Percentage of Least (N3) naturalness columns in the database schema

**schema_tab_N1_pct:** Percentage of Regular (N1) naturalness tables in the database schema

**schema_tab_N2_pct:** Percentage of Low (N2) naturalness tables in the database schema

**schema_tab_N3_pct:** Percentage of Least (N3) naturalness tables in the database schema

**result_set_match:** True/False indicator of result set comparison / semantic evaluation	

**result_set_compare_note:** Plain text result set failure reason description	

**string_match:** True/False indicator of gold : predicted string matching

**matching_tables:** Set of tables that appear in both gold and predicted queries.

**matching_columns:** Set of columns that appear in both gold and predicted queries.

**missing_tables:** Set of tables that are present in the gold query but missing in the predicted query.

**missing_columns:** Set of columns that are present in the gold query but missing in the predicted query.

**extra_tables:** Set of tables that are present in the predicted query but not in the gold query.

**extra_columns:** Set of columns that are present in the predicted query but not in the gold query.

**recall:** The ratio of correctly predicted elements (matching) to the total relevant elements (matching + missing).

**precision:** The ratio of correctly predicted elements (matching) to the total predicted elements (matching + extra).

**f1:** The harmonic mean of recall and precision, providing a balance between the two metrics.

**manual_match:** True / False human-validated matching assessment, dependent variable in execution accuracy analysis.	

**review_notes:** Human-validator notes.

**model:** LLM used for SQL prediction	

**source_file:** Annotation file in ./nl-to-sql_performance_annotations from which the above columns were retrieved	

**question_number_combined_modules:** Applies only to SBODemoUS database, prevents duplicate question numbers when modules are combined.	

**naturalness_order:** For value sorting on naturalness

**schema_identifier_N1:** A count of Regular (N1) naturalness identifiers in the database schema

**schema_identifier_N2:** A count of Low (N2) naturalness identifiers in the database schema

**schema_identifier_N3:** A count of Least (N3) naturalness identifiers in the database schema

**schema_identifier_N1_pct:** Percentage of Regular (N1) naturalness identifiers in the database schema

**schema_identifier_N2_pct:** Percentage of Low (N2) naturalness identifiers in the database schema

**schema_identifier_N3_pct:** Percentage of Least (N3) naturalness identifiers in the database schema

**Qg_identifier_N1:** A count of Regular (N1) naturalness identifiers in the gold query

**Qg_identifier_N2:** A count of Low (N2) naturalness identifiers in the gold query

**Qg_identifier_N3:** A count of Least (N3) naturalness identifiers in the gold query

**Qg_identifier_N1_pct:** Percentage of Regular (N1) naturalness identifiers in the gold query

**Qg_identifier_N2_pct:** Percentage of Low (N2) naturalness identifiers in the gold query

**Qg_identifier_N3_pct:** Percentage of Least (N3) naturalness identifiers in the gold query

**model_order:** For sorting on LLM (used in our analysis)

**query_stat_count:** A count of elements in the query_stats column	

**question_tokens:** A count of tokens in the NL question, as tokenized using the model in the tokenizer_model column	

**prompt_token_count:** A count of tokens in the NL prompt, as tokenized using the model in the tokenizer_model column

**word_level_mean_max_cosine_similarity:** The mean of the max cosine similarity between each NL question word and an identifier in the gold query.	

**sentence_level_cosine_similarity:** Cosine similarity between the embeddings of the NL question and the gold query.	

**mean_token_char_ratio:** The mean of the token_char_ratio for each identifier in the gold query. token_char_ration is the number of tokens in an identifier divided by the number of characters in an identifier. It is generated in tokenizer_analysis.ipynb cell # 21.