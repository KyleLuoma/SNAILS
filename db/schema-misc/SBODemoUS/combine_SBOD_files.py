import os
import pandas as pd

path =  "./schema-misc/SBODemoUS/"

file_list = os.listdir(path)
file_list = [f for f in file_list if (f.endswith(".xlsx") and "SBOD_table_column_descriptions" in f)]

combined_df = pd.read_excel(path + file_list[0])

for f in file_list[1:]:
    print(f)
    df = pd.read_excel(path + f)
    combined_df = pd.concat([combined_df, df], axis=0)

combined_df.to_excel(path + "SBOD_table_column_descriptions_combined.xlsx", index=False)