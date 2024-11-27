import pandas as pd
import os

cwd = os.getcwd() + "/schema-scores/"
files = os.listdir(cwd)
print(files)
excel_files = [f for f in files if ('.xlsx' in f and 'consolidated' not in f)]

consolidated_score_df = pd.read_excel(cwd + files[0])
consolidated_score_df['DATABASE_NAME'] = files[0].replace('xlsx', '')

for file in excel_files[1:]:
    print("Adding", file)
    db_name = file.replace('.xlsx', "")
    score_df = pd.read_excel(cwd + file)
    score_df['DATABASE_NAME'] = db_name
    consolidated_score_df = pd.concat([consolidated_score_df, score_df])

consolidated_score_df.to_excel(cwd + 'consolidated-scores-7-18-2023-2.xlsx')