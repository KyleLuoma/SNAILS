import json
import pandas as pd
from tqdm import tqdm

names_dict = {
        "TABLE_NAME": [],
        "COLUMN_NAME": [],
        "DATABASE_NAME": []
    }

with open("./schema-scores/spider-realistic/spider-realistic-tables.json", "r") as f:
    spider = json.loads(f.read())
    for db_dict in spider:
        for i, t in enumerate(db_dict["table_names"]):
            for c in db_dict["column_names"]:
                if c[0] == i:
                    print(t, c[1])
                    names_dict["TABLE_NAME"].append(t)
                    names_dict["COLUMN_NAME"].append(c[1])
                    names_dict["DATABASE_NAME"].append(db_dict["db_id"])

df = pd.DataFrame(names_dict)

df.to_csv(
    "./schema-scores/spider-realistic/spider_realistic_schemas.csv",
    index=False
    )