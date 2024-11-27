import json
import pandas as pd
from tqdm import tqdm

names_dict = {
        "TABLE_NAME": [],
        "COLUMN_NAME": [],
        "DATABASE_NAME": []
    }

with open("./schema-scores/schemapile/schemapile_public.json", "r") as f:
    sp = json.loads(f.read())
    for db in tqdm(sp):
        for table in sp[db]["TABLES"]:
            if "." in table:
                table_nodot = table.split(".")[1]
            else:
                table_nodot = table
            for column in sp[db]["TABLES"][table]["COLUMNS"]:
                names_dict["TABLE_NAME"].append(table_nodot)
                names_dict["COLUMN_NAME"].append(column)
                names_dict["DATABASE_NAME"].append(db)

df = pd.DataFrame(names_dict)

df.to_csv(
    "./schema-scores/schemapile/schemapile_schemas.csv",
    index=False
    )


    


